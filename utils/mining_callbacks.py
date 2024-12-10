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
from .calculate import calculate_pplns_participation
from .find_miner_id import ReadTokens
import logging

logger = logging.getLogger(__name__)

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
        [Output('mp-stats', 'children')],
        [Input('mp-interval-4', 'n')],
        [State('url', 'pathname')]
    )
    def update_front_row(n, pathname):
        try:
            miner = unquote(pathname.lstrip('/'))
            pool_data = sharkapi.get_pool_stats()
            miner_data = sharkapi.get_miner_stats(miner)
            
            if not miner_data:
                return [html.Div("No miner data available")]

            pool_stats = calculate_pool_stats(sharkapi)
            miner_stats = calculate_miner_stats(sharkapi, miner, pool_data)
            
            stats_cards = [
                create_stat_row("Pool Stats", pool_stats, styles['top_row_style'], styles['large_text_color']),
                create_stat_row("Miner Stats", miner_stats, styles['top_row_style'], styles['large_text_color'])
            ]
            
            return [dbc.Row(stats_cards, justify='center')]
        except Exception as e:
            logger.error(f"Error in update_front_row: {e}", exc_info=True)
            return [html.Div("Error loading stats")]

    @app.callback(
        [Output('s1', 'children'), Output('s2', 'children')],
        [Input('mp-interval-1', 'n')],
        [State('url', 'pathname')]
    )
    def update_middle(n, pathname):
        try:
            wallet = unquote(pathname.lstrip('/'))
            # need to parse this correctly as it is typed as optional and should be a Dict
            miner_data = sharkapi.get_miner_stats(wallet)
            text = 'miner STATSSSSSS {}'.format(miner_data)
            logger.info(text)
            if not miner_data:
                return [], []
    
            price = round(priceapi.get()[1], 3)
            payments = miner_data.payments
            # Safely access nested attributes
            
            payments = miner_data.payments
            stats = {
                'balance': round(miner_data.balance, 3),
                'paid_today': round(payments['paid_today'], 2),
                'total_paid': round(payments['total_paid'], 3),
                'last_payment': payments['last_payment']['date'][:10],
                'price [$]': price,
                'schema': 'PPLNS'
            }
            
            images = {
                'balance': 'triangle.png',
                'paid_today': 'ergo.png',
                'total_paid': 'ergo.png',
                'last_payment': 'coins.png',
                'price [$]': 'ergo.png',
                'schema': 'ergo.png'
            }
            
            children = [create_image_text_block(f"{k}: {v}", images[k]) for k, v in stats.items()]
            return children[:3], children[3:]
        except Exception as e:
            logger.error(f"Error in update_middle: {e}", exc_info=True)
            return [], []

    @app.callback(
        [Output('s3', 'children')],
        [Input('mp-interval-1', 'n')],
        [State('url', 'pathname')]
    )
    def update_outside(n, pathname):
        try:
            miner = unquote(pathname.lstrip('/'))
            miner_data = sharkapi.get_miner_stats(miner)
            pool_data = sharkapi.get_pool_stats()
            
            # Get share stats from the correct endpoint
            shares_data = sharkapi.get_shares()
            
            participation, total_shares = calculate_pplns_participation(shares_data, pool_data, 0.5)
            
            stats = {
                'Participation [%]': round(participation.get(miner, 0) * 100, 3),
                'Pending Shares': round(participation.get(miner, 0) * total_shares, 2)
            }
            
            images = {
                'Participation [%]': 'smileys.png',
                'Pending Shares': 'min-payout.png'
            }
            
            children = [create_image_text_block(f"{k}: {v}", images[k]) for k, v in stats.items()]
            # logger.info(miner_data.payments['last_payment']['tx_id'])
            if hasattr(miner_data, 'payments') and miner_data.payments.get('last_payment', {}).get('tx_id'):
                link = 'https://ergexplorer.com/transactions#{}'.format(miner_data.payments['last_payment']['tx_id'])
                children.append(create_payment_link(link, styles))
            
            return [children]
        except Exception as e:
            logger.error(f"Error in update_outside: {e}", exc_info=True)
            return [[]]

    @app.callback(
        [Output('s4', 'children'), Output('s5', 'children'), Output('s6', 'children')],
        [Input('mp-interval-7', 'n')],
        [State('url', 'pathname')]
    )
    def update_miner_id(n, pathname):
        try:
            logger.info('Starting miner ID update')
            miner = unquote(pathname.lstrip('/'))
            
            find_tokens = ReadTokens()
            token = find_tokens.get_latest_miner_id(miner)
            
            if token is None:
                # Create more compact default cards with consistent styling
                defaults = [
                    html.Div([
                        html.Div(
                            className="d-flex align-items-center",
                            # style={
                            #     'backgroundColor': '#27374D',
                            #     'padding': '10px',
                            #     'borderRadius': '8px',
                            #     'margin': '5px',
                            #     'minHeight': '60px'  # Minimum height to maintain consistency
                            # },
                            children=[
                                html.Img(
                                    src='assets/min-payout.png',
                                    style={'height': '24px', 'marginRight': '8px'}
                                ),
                                html.Span(text, style={'color': 'white', 'fontSize': '14px'})
                            ]
                        )
                    ]) for text in ['Min Payout: 0.5 ERG', 'Consider minting a MINER ID', 'Swap to ERG Native Tokens']
                ]
                return defaults[0], defaults[1], defaults[2]
    
            try:
                miner_id = find_tokens.get_token_description(token['tokenId'])
                logger.debug(f'Retrieved miner ID: {miner_id}')
                
                # Create minimal height cards
                tokens_swap = [
                    html.Div(
                        className="d-flex align-items-center",
                        style={
                            # 'backgroundColor': '#27374D',
                            # 'padding': '8px 12px',
                            # 'borderRadius': '8px',
                            # 'height': 'auto',
                            # 'minHeight': '36px',
                            # 'marginBottom': '2px'
                        },
                        children=[
                            html.Img(
                                src='assets/min-payout.png',
                                style={'height': '20px', 'marginRight': '8px', 'width': 'auto'}
                            ),
                            html.Span(
                                f"Minimum Payout: {miner_id['minimumPayout']}",
                                style={'color': 'white', 'fontSize': '14px', 'whiteSpace': 'nowrap'}
                            )
                        ]
                    )
                ]
                
                # Add token distribution cards
                for token_info in miner_id['tokens']:
                    tokens_swap.append(
                        html.Div(
                            className="d-flex align-items-center",
                            style={
                                # 'backgroundColor': '#27374D',
                                # 'padding': '8px 12px',
                                # 'borderRadius': '8px',
                                # 'height': 'auto',
                                # 'minHeight': '36px',
                                # 'marginBottom': '2px'
                            },
                            children=[
                                html.Img(
                                    src='assets/ergo.png',
                                    style={'height': '20px', 'marginRight': '8px', 'width': 'auto'}
                                ),
                                html.Span(
                                    f"{token_info['token']}: {token_info['value']}%",
                                    style={'color': 'white', 'fontSize': '14px', 'whiteSpace': 'nowrap'}
                                )
                            ]
                        )
                    )
                
                # Distribute elements across bins, ensuring even distribution
                bins = [[] for _ in range(3)]
                for i, element in enumerate(tokens_swap):
                    bins[i % 3].append(element)
                
                # Create wrapper divs for each column
                column_wrappers = [
                    html.Div(
                        bin_content,
                        # style={
                        #     'display': 'flex',
                        #     'flexDirection': 'column',
                        #     'gap': '2px',  # Reduced gap between items
                        #     'flex': '1',
                        #     'minHeight': '45px',  # Minimum height for container
                        #     'maxHeight': '150px'  # Maximum height to prevent excessive space
                        # }
                    ) if bin_content else html.Div()
                    for bin_content in bins
                ]
                
                return column_wrappers[0], column_wrappers[1], column_wrappers[2]
                
            except Exception as e:
                logger.error(f'Error processing miner ID: {str(e)}', exc_info=True)
                return [], [], []
                
        except Exception as e:
            logger.error(f'Error in update_miner_id: {str(e)}', exc_info=True)
            return [], [], []

    @app.callback(
        [Output('chart', 'figure'), Output('chart-title', 'children')],
        [Input('chart-dropdown', 'value'), Input('mp-interval-2', 'n_intervals')],
        [State('url', 'pathname')]
    )
    def update_charts(chart_type, n, pathname):
        try:
            wallet = unquote(pathname.lstrip('/'))
            
            if chart_type == 'workers':
                return create_worker_chart(sharkapi, wallet)
            elif chart_type == 'payments':
                return create_payment_chart(sharkapi, wallet)
                
            return {}, 'Select chart type'
        except Exception as e:
            logger.error(f"Error in update_charts: {e}", exc_info=True)
            return {}, 'Error loading chart'

    @app.callback(
        [Output('table-2', 'data'), Output('table-title', 'children')],
        [Input('table-dropdown', 'value'), Input('mp-interval-3', 'n_intervals')],
        [State('url', 'pathname')]
    )
    def update_table(table_type, n, pathname):
        try:
            wallet = unquote(pathname.lstrip('/'))
            
            if not table_type:
                table_type = 'workers'
            
            if table_type == 'workers':
                return create_workers_table(sharkapi, wallet)
            elif table_type == 'blocks':
                return create_blocks_table(sharkapi, wallet)
                
            return [], 'Select data type'
        except Exception as e:
            logger.error(f"Error in update_table: {e}", exc_info=True)
            return [], 'Error loading table'

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