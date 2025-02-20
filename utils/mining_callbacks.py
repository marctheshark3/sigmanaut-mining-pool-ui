from dash.dependencies import Input, Output, State
from urllib.parse import unquote
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import pandas as pd
from datetime import datetime
import plotly.express as px
from .mining_stats import (
    create_stat_row, calculate_pool_stats, calculate_miner_stats
)
from utils.dash_utils import top_row_style
from .calculate import (
    calculate_pplns_participation,
    calculate_time_to_find_block,
    calculate_mining_effort
)
from .find_miner_id import ReadTokens
from utils.components import create_metric_section, create_stat_section
import logging

logger = logging.getLogger(__name__)

def format_hashrate(hashrate):
    """Helper function to format hashrate in appropriate units"""
    if hashrate >= 1e9:
        return f"{round(hashrate / 1e9, 2)} GH/s"
    return f"{round(hashrate / 1e6, 2)} MH/s"

def calculate_ttf(miner_hashrate, network_hashrate, network_difficulty):
    """Calculate Time to Find based on miner's hashrate proportion"""
    try:
        if miner_hashrate <= 0 or network_hashrate <= 0:
            return 0
        
        # Calculate miner's proportion of network hashrate
        miner_proportion = miner_hashrate / network_hashrate
        
        # Expected blocks per day for the network (86400 seconds per day)
        blocks_per_day = 86400 / (network_difficulty / network_hashrate)
        
        # Miner's expected blocks per day
        miner_blocks_per_day = blocks_per_day * miner_proportion
        
        # TTF is reciprocal of blocks per day
        ttf = 1 / miner_blocks_per_day if miner_blocks_per_day > 0 else 0
        
        return round(ttf, 2)
    except Exception as e:
        logger.error(f"Error calculating TTF: {e}")
        return 0

def calculate_miner_effort(miner_hashrate, pool_hashrate):
    """Calculate miner's effort as percentage of pool hashrate"""
    try:
        if miner_hashrate <= 0 or pool_hashrate <= 0:
            return 0
        return (miner_hashrate / pool_hashrate) * 100
    except Exception as e:
        logger.error(f"Error calculating effort: {e}")
        return 0

def create_image_text_block(text, image, style=None):
    """Create an image text block with optional style override"""
    return html.Div(
        style=style or {
            'justifyContent': 'left',
            'backgroundColor': '#27374D',
            'color': 'white',
            'fontSize': '14px'
        },
        children=[
            html.Img(
                src=f'assets/{image}',
                style={'height': '40px', 'justifyContent': 'center'}
            ),
            html.Span(text, style={'padding': '10px'})
        ]
    )

def register_callbacks(app, sharkapi, priceapi, styles):
    @app.callback(
        [Output('metrics-section', 'children')],
        [Input('mp-metrics-interval', 'n_intervals')],
        [State('url', 'pathname')]
    )
    def update_metrics(n, pathname):
        try:
            miner = unquote(pathname.lstrip('/'))
            miner_data = sharkapi.get_miner_stats(miner)
            pool_data = sharkapi.get_pool_stats()
            shares_data = sharkapi.get_shares()
            
            if not miner_data:
                return [[]]  # Return empty if no data
            
            # Get worker stats for hashrate
            worker_stats = sharkapi.sync_get_miner_workers(miner)
            total_hashrate = 0
            if worker_stats:
                for worker_data in worker_stats.values():
                    if worker_data and len(worker_data) > 0:
                        total_hashrate += worker_data[-1].get('hashrate', 0)
            
            # Get network stats
            network_hashrate = pool_data.get('networkhashrate', 0)
            network_difficulty = pool_data.get('networkdifficulty', 0)
            
            # Get miner's last block timestamp
            blocks = sharkapi.sync_get_my_blocks(miner)
            if blocks:
                last_block_timestamp = blocks[0]['created']  # Most recent block's timestamp
                logger.info(f"Using last block timestamp: {last_block_timestamp}")
                logger.info(f"Network hashrate: {network_hashrate}, Network difficulty: {network_difficulty}, Miner hashrate: {total_hashrate}")
            else:
                last_block_timestamp = None
                logger.warning("No blocks found for miner")
            
            # Calculate TTF using the function from calculate.py
            ttf = calculate_time_to_find_block(
                network_difficulty=network_difficulty,
                network_hashrate=network_hashrate,
                hashrate=total_hashrate
            )
            
            # Calculate current effort using the function from calculate.py
            if last_block_timestamp:
                current_effort = calculate_mining_effort(
                    network_difficulty=network_difficulty,
                    network_hashrate=network_hashrate,
                    hashrate=total_hashrate,
                    last_block_timestamp=last_block_timestamp
                )
                logger.info(f"Calculated current effort: {current_effort}%")
            else:
                current_effort = 0
            
            # Calculate average effort from miner's blocks
            if blocks:
                efforts = [block.get('effort', 0) * 100 for block in blocks]  # Convert to percentage
                avg_effort = sum(efforts) / len(efforts) if efforts else 0
                logger.info(f"Average effort from {len(blocks)} blocks: {avg_effort}%")
                effort_value = f"{round(avg_effort, 2)}% / {round(current_effort, 2)}%"
            else:
                effort_value = "No blocks found yet"
            
            # Create the three main metrics
            metrics = [
                {
                    'image': 'boltz.png',
                    'value': format_hashrate(total_hashrate),
                    'label': 'Hashrate'
                },
                {
                    'image': 'clock.png',
                    'value': f"{ttf} Days",
                    'label': 'Time to Find'
                },
                {
                    'image': 'chart.png',
                    'value': effort_value,
                    'label': 'AVG/LIVE Effort'
                }
            ]
            
            return [[
                html.Div(
                    style={'display': 'flex', 'width': '100%', 'justifyContent': 'space-between'},
                    children=[
                        html.Div(
                            create_metric_section(
                                metric['image'],
                                metric['value'],
                                metric['label'],
                                show_image=False  # Don't show images for main metrics
                            ),
                            style={'flex': '1'}
                        ) for metric in metrics
                    ]
                )
            ]]
        except Exception as e:
            logger.error(f"Error in update_metrics: {e}", exc_info=True)
            return [[]]

    @app.callback(
        [Output('stats-section', 'children')],
        [Input('mp-stats-interval', 'n_intervals')],
        [State('url', 'pathname')]
    )
    def update_stats(n, pathname):
        try:
            miner = unquote(pathname.lstrip('/'))
            miner_data = sharkapi.get_miner_stats(miner)
            pool_data = sharkapi.get_pool_stats()
            shares_data = sharkapi.get_shares()
            find_tokens = ReadTokens()
            token = find_tokens.get_latest_miner_id(miner)
            
            if not miner_data:
                return [[]]

            # Payment Stats
            payment_stats = [
                ('Balance', f"{round(miner_data.balance, 3)} ERG"),
                ('Paid Today', f"{round(miner_data.payments['paid_today'], 2)} ERG"),
                ('Total Paid', f"{round(miner_data.payments['total_paid'], 3)} ERG")
            ]

            # Pool Stats
            price = round(priceapi.get()[1], 3)
            pool_stats = [
                ('Last Payment', miner_data.payments['last_payment']['date'][:10]),
                ('Price', f"${price}"),
                ('Schema', 'PPLNS')
            ]

            # Pool Hashrate Stats (replacing Token Distribution)
            pool_hashrate_stats = [
                ('Minimum Payout', '0.5 ERG'),
                ('Pool Hashrate', format_hashrate(pool_data.get('poolhashrate', 0))),
                ('Network Hashrate', format_hashrate(pool_data.get('networkhashrate', 0)))
            ]

            # Create the three columns
            return [[
                html.Div(
                    style={'display': 'flex', 'width': '100%', 'justifyContent': 'space-between'},
                    children=[
                        create_stat_section(payment_stats),
                        html.Div(style={'width': '1px', 'backgroundColor': 'rgba(255,255,255,0.1)'}),
                        create_stat_section(pool_stats),
                        html.Div(style={'width': '1px', 'backgroundColor': 'rgba(255,255,255,0.1)'}),
                        create_stat_section(pool_hashrate_stats)
                    ]
                )
            ]]
        except Exception as e:
            logger.error(f"Error in update_stats: {e}", exc_info=True)
            return [[]]

    @app.callback(
        [Output('chart', 'figure'), Output('chart-title', 'children')],
        [Input('mp-charts-interval', 'n_intervals'), Input('chart-dropdown', 'value')],
        [State('url', 'pathname')]
    )
    def update_chart(n, chart_type, pathname):
        try:
            miner = unquote(pathname.lstrip('/'))
            
            if chart_type == 'workers':
                title = 'WORKER HASHRATE OVER TIME'
                data = sharkapi.sync_get_miner_workers(miner)
                if not data:
                    return {}, title
                
                # Process worker data
                rows = []
                for worker, entries in data.items():
                    for entry in entries:
                        rows.append({
                            'Time': entry['timestamp'],
                            'Hashrate': entry['hashrate'] / 1e6,
                            'Worker': worker
                        })
                
                df = pd.DataFrame(rows)
                if df.empty:
                    return {}, title
                
                fig = px.line(
                    df,
                    x='Time',
                    y='Hashrate',
                    color='Worker',
                    title=title
                )
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    yaxis_title='MH/s'
                )
                
                return fig, title
                
            else:  # payments
                title = 'PAYMENT HISTORY'
                data = sharkapi.sync_get_miner_payment_stats(miner)
                if not data:
                    return {}, title
                    
                df = pd.DataFrame(data)
                df = df.rename(columns={
                    'timestamp': 'Time',
                    'amount': 'Amount'
                })
                
                fig = px.bar(
                    df,
                    x='Time',
                    y='Amount',
                    title=title
                )
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    yaxis_title='ERG'
                )
                
                return fig, title
                
        except Exception as e:
            logger.error(f"Error in update_chart: {e}", exc_info=True)
            return {}, "Error loading chart"

    @app.callback(
        [Output('table-2', 'data'), Output('table-title', 'children')],
        [Input('mp-charts-interval', 'n_intervals'), Input('table-dropdown', 'value')],
        [State('url', 'pathname')]
    )
    def update_table(n, table_type, pathname):
        try:
            miner = unquote(pathname.lstrip('/'))
            
            if table_type == 'workers':
                title = 'Worker Data'
                data = sharkapi.sync_get_miner_workers(miner)
                if not data:
                    return [], title
                
                # Process worker data
                rows = []
                for worker, entries in data.items():
                    if entries:
                        latest = entries[-1]
                        rows.append({
                            'Worker': worker,
                            'Time': latest['timestamp'],
                            'Hashrate (MH/s)': round(latest['hashrate'] / 1e6, 2)
                        })
                
                df = pd.DataFrame(rows)
                return df.to_dict('records'), title
                
            else:  # blocks
                title = 'Block Data'
                data = sharkapi.sync_get_my_blocks(miner)
                if not data:
                    return [], title
                    
                df = pd.DataFrame(data)
                if df.empty:
                    return [], title
                    
                df = df.rename(columns={
                    'created': 'Time Found',
                    'blockheight': 'Height',
                    'effort': 'Effort',
                    'reward': 'Reward (ERG)'
                })
                
                df['Effort'] = df['Effort'] * 100  # Convert to percentage
                df = df[['Time Found', 'Height', 'Effort', 'Reward (ERG)']]
                
                return df.to_dict('records'), title
                
        except Exception as e:
            logger.error(f"Error in update_table: {e}", exc_info=True)
            return [], "Error loading table"

    # Create a new interval component for bonus eligibility updates (30 minutes)
    app.layout.children.append(dcc.Interval(id='bonus-eligibility-interval', interval=1000*60*30))

    @app.callback(
        [Output('bonus-eligibility-section', 'children')],
        [Input('bonus-eligibility-interval', 'n_intervals')],
        [State('url', 'pathname')]
    )
    def update_bonus_eligibility(n, pathname):
        try:
            if not pathname or pathname == '/':
                return [html.Div()]

            # Extract wallet address from pathname
            wallet = unquote(pathname.split('/')[-1])
            if not wallet:
                return [html.Div()]

            # Get bonus eligibility data
            bonus_data = sharkapi.get_bonus_eligibility(wallet)
            if not bonus_data:
                return [create_metric_section(
                    'mining-reward-icon-2.png',
                    'No Data',
                    'Bonus Token Eligibility'
                )]

            # Create the display value
            status = '✓ Eligible' if bonus_data['eligible'] else '✗ Not Eligible'
            days_info = f"{bonus_data['qualifying_days']}/{bonus_data['total_days_active']} days"
            
            # Only add warning if not eligible and needs days
            if not bonus_data['eligible'] and bonus_data['needs_days']:
                days_info += ' (More days needed)'

            # Combine status and days info
            display_value = f"{status}\n{days_info}"

            return [create_metric_section(
                'mining-reward-icon-2.png',
                display_value,
                'Bonus Token Eligibility'
            )]

        except Exception as e:
            logger.error(f"Error updating bonus eligibility: {e}")
            return [create_metric_section(
                'mining-reward-icon-2.png',
                'Error',
                'Bonus Token Eligibility'
            )]

def create_worker_chart(sharkapi, wallet):
    try:
        worker_data = sharkapi.sync_get_miner_workers(wallet)  # Changed to sync_get_miner_workers
        if not worker_data:
            return {}, 'No worker data available'
        
        rows = []
        for worker, data in worker_data.items():
            for entry in data:
                try:
                    rows.append({
                        'worker': worker,
                        'created': datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')),
                        'hashrate': entry['hashrate'] / 1e6
                    })
                except (ValueError, KeyError):
                    continue
        
        if not rows:
            return {}, 'NO RECENT HASH'
            
        df = pd.DataFrame(rows)
        fig = px.line(
            df, 
            x='created',
            y='hashrate',
            color='worker',
            labels={'hashrate': 'Mh/s', 'created': 'Time'},
            markers=True
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Miner',
            legend=dict(font=dict(color='#FFFFFF')),
            titlefont=dict(color='#FFFFFF'),
            xaxis=dict(title='Time', color='#FFFFFF', showgrid=False, showline=False, zeroline=False),
            yaxis=dict(title='Hashrate', color='#FFFFFF')
        )
        
        return fig, 'WORKER HASHRATE OVER TIME'
    except Exception as e:
        logger.error(f"Error in create_worker_chart: {e}", exc_info=True)
        return {}, 'Error creating chart'

def create_payment_chart(sharkapi, wallet):
    try:
        payment_data = sharkapi.sync_get_miner_payment_stats(wallet)  # Changed to sync_get_miner_payment_stats
        if not payment_data:
            return {}, 'No payment data available'
        
        df = pd.DataFrame(payment_data)
        if df.empty:
            return {}, 'No payment data available'
        
        df = df.sort_values('created')
        fig = px.line(
            df,
            x='created',
            y='amount',
            labels={'amount': 'Paid [ERG]', 'created': 'Date'},
            markers=True
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(font=dict(color='#FFFFFF')),
            titlefont=dict(color='#FFFFFF'),
            xaxis=dict(title='Date', color='#FFFFFF', showgrid=False, showline=False, zeroline=False),
            yaxis=dict(title='Paid [ERG]', color='#FFFFFF')
        )
        
        return fig, 'PAYMENT OVER TIME'
    except Exception as e:
        logger.error(f"Error in create_payment_chart: {e}", exc_info=True)
        return {}, 'Error creating chart'

def create_workers_table(sharkapi, wallet):
    try:
        workers_data = sharkapi.sync_get_miner_stats(wallet)  # Changed to sync_get_miner_stats
        if not workers_data or not workers_data.workers:
            return [], 'No worker data available'
        
        df = pd.DataFrame(workers_data.workers)
        df['hashrate'] = df['hashrate'].apply(lambda x: round(x / 1e6, 2))
        df = df.rename(columns={'hashrate': 'MH/s'})
        
        return df.to_dict('records'), 'WORKER DATA'
    except Exception as e:
        logger.error(f"Error in create_workers_table: {e}", exc_info=True)
        return [], 'Error loading workers'

def create_blocks_table(sharkapi, wallet):
    try:
        blocks = sharkapi.sync_get_my_blocks(wallet)  # Changed to sync_get_my_blocks
        if not blocks:
            return [], 'No blocks found'
        
        df = pd.DataFrame(blocks)
        if not df.empty:
            df['effort'] = round(100 * df['effort'], 2)
            df = df.rename(columns={
                'created': 'Time Found',
                'blockheight': 'Height',
                'effort': 'Effort [%]',
                'confirmationprogress': 'Confirmation [%]'
            })
        
        return df.to_dict('records'), 'YOUR BLOCKS FOUND'
    except Exception as e:
        logger.error(f"Error in create_blocks_table: {e}", exc_info=True)
        return [], 'Error loading blocks'

def create_payment_link(link, styles):
    return html.Div(
        # style=styles['bottom_row_style'],
        children=[
            html.Img(src='assets/ergo.png',
                     style={'height': '40px', 'justifyContent': 'center'}
                    ),
            html.Span(
                dcc.Link('Last Payment Link', href=link, target='_blank'),
                style={'padding': '10px'}
            )
        ]
    )