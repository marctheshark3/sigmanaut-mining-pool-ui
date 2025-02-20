import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from pandas import DataFrame
from utils.dash_utils import (
    card_color, background_color, large_text_color, small_text_color,
    card_styles, container_style, table_style, create_image_text_block,
    create_stat_row, bottom_row_style, image_styles, top_card_style, first_row_styles, top_image_style, get_days_ago
)
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from typing import Dict
import uuid
import os
from utils.get_erg_prices import PriceReader
import logging

logger = logging.getLogger(__name__)

priceapi = PriceReader()
button_color = large_text_color

def create_row_card(image, h2_text, p_text):
    return dbc.Col(
        dbc.Card(
            style=top_card_style,
            children=[
                dbc.CardImg(src=image, top=True, style=top_image_style),
                html.H2(h2_text, style={'color': large_text_color, 'margin': '10px 0', 'fontSize': '24px'}),
                html.P(p_text, style={'color': small_text_color, 'margin': '0'})
            ]
        ),
        width=4,
        className="px-2"
    )

def create_image_text_block(text, value):
    return html.Div(style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}, children=[
        html.Span(text, style={'padding': '5px', 'color': 'white'}),
        html.Span(value, style={'padding': '5px', 'color': large_text_color})])

def create_metric_section(image, value, label):
    return html.Div(
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center',
            'flex': '1',
            'padding': '20px'
        },
        children=[
            html.Img(src=image, style=top_image_style),
            html.Div(value, style={'color': large_text_color, 'fontSize': '24px', 'margin': '10px 0'}),
            html.Div(label, style={'color': small_text_color})
        ]
    )

def create_stat_section(stats_list):
    return html.Div(
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'flex': '1',
            'padding': '20px'
        },
        children=[
            html.Div(
                style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '10px'},
                children=[
                    html.Span(text, style={'color': 'white'}),
                    html.Span(value, style={'color': large_text_color, 'marginLeft': '10px'})
                ]
            ) for text, value in stats_list
        ]
    )

def setup_front_page_callbacks(app, api_reader):
    @app.callback(
        Output('link-container', 'children'),
        Input('generate-url-button', 'n_clicks'),
    )
    def generate_link(n_clicks):
        if not n_clicks:
            return []
        id = uuid.uuid4()
        base_url = os.environ.get('BASE_URL', 'http://mint.ergominers.com')
        custom_url = f'{base_url}/miner-id-minter/{id}'
        return html.A(html.Button('Mint NFT'), href=custom_url, target='_blank')

    @app.callback(
        Output('mint-modal', 'is_open'),
        [Input('mint-sigma-bytes-button', 'n_clicks'),
         Input('close-mint-modal', 'n_clicks')],
        [State('mint-modal', 'is_open')]
    )
    def toggle_mint_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        [Output('metric-1', 'children')],
        [Input('fp-int-4', 'n_intervals')]
    )
    def update_first_row(n):
        try:
            data = api_reader.get_pool_stats()
            data['hashrate'] = round(data.get('poolhashrate', 0) / 1e9, 2)
            n_miners = '{}'.format(data.get('connectedminers', 0))
            hashrate = '{} GH/s'.format(data['hashrate'])
            price = round(priceapi.get()[1], 3)
    
            row_1 = dbc.Row(
                dbc.Col(
                    dbc.Card(
                        style={
                            'backgroundColor': card_color,
                            'border': 'none',
                            'borderRadius': '8px',
                            'display': 'flex',
                            'flexDirection': 'row',
                            'padding': '20px',
                            'marginBottom': '20px'
                        },
                        children=[
                            create_metric_section('assets/boltz.png', hashrate, 'Pool Hashrate'),
                            create_metric_section('assets/smileys.png', n_miners, 'Miners Online'),
                            create_metric_section('assets/coins.png', str(price), 'Price ($)')
                        ]
                    ),
                    width=12
                ),
                justify="center"
            )
            return [row_1]
        except Exception as e:
            logger.error(f"Error in update_first_row: {e}")
            return [html.Div("Error loading metrics")]

    @app.callback(
        [Output('metric-2', 'children')],
        [Input('fp-int-1', 'n_intervals')]
    )
    def update_metrics(n):
        try:
            data = api_reader.get_pool_stats()
            block_data = api_reader.get_block_stats()
            
            data['minimumpayment'] = 0.5
            data['fee'] = 0.9
            data['paid'] = api_reader.get_payment_stats()['total_paid']
            data['payoutscheme'] = 'PPLNS'
            data['blocks'] = len(block_data) if block_data else 0
            
            left_stats = [
                ('Minimum Payout:', str(data['minimumpayment'])),
                ('Pool Fee:', f"{data['fee']}%"),
                ('Total Paid:', f"{round(data['paid'], 3)} ERG")
            ]
            
            middle_stats = [
                ('Network Hashrate:', f"{round(data.get('networkhashrate', 0) / 1e12, 2)} TH/s"),
                ('Network Difficulty:', f"{round(data.get('networkdifficulty', 0) / 1e15, 2)}P"),
                ('Block Height:', str(data.get('blockheight', 0)))
            ]
            
            right_stats = [
                ('Schema:', data['payoutscheme']),
                ('Blocks Found:', str(data['blocks'])),
                ('Pool Effort:', str(round(data.get('effort', 0), 3)))
            ]

            # Add demurrage stats
            try:
                logger.info("Fetching demurrage stats...")
                demurrage_stats = api_reader.get_demurrage_stats()
                if not isinstance(demurrage_stats, list):
                    logger.error("Invalid demurrage stats format")
                    demurrage_stats = [
                        ('Next Demurrage:', '0.000 ERG'),
                        ('Last Demurrage:', '0.000 ERG'),
                        ('Last Payment:', 'Error')
                    ]
                logger.info(f"Retrieved demurrage stats: {demurrage_stats}")
            except Exception as e:
                logger.error(f"Error fetching demurrage stats: {e}", exc_info=True)
                demurrage_stats = [
                    ('Next Demurrage:', '0.000 ERG'),
                    ('Last Demurrage:', '0.000 ERG'),
                    ('Last Payment:', 'Error')
                ]

            row_2 = dbc.Row(
                dbc.Col(
                    dbc.Card(
                        style={
                            'backgroundColor': card_color,
                            'border': 'none',
                            'borderRadius': '8px',
                            'display': 'flex',
                            'flexDirection': 'row',
                            'marginBottom': '20px'
                        },
                        children=[
                            create_stat_section(left_stats),
                            html.Div(style={'width': '1px', 'backgroundColor': 'rgba(255,255,255,0.1)'}),
                            create_stat_section(middle_stats),
                            html.Div(style={'width': '1px', 'backgroundColor': 'rgba(255,255,255,0.1)'}),
                            create_stat_section(right_stats),
                            html.Div(style={'width': '1px', 'backgroundColor': 'rgba(255,255,255,0.1)'}),
                            create_stat_section(demurrage_stats)
                        ]
                    ),
                    width=12
                ),
                justify="center"
            )
            return [row_2]
        except Exception as e:
            logger.error(f"Error in update_metrics: {e}")
            return [html.Div("Error loading stats")]

    @app.callback(
        [Output('plot-1', 'figure'), Output('plot-title', 'children')],
        [Input('fp-int-2', 'n_intervals'), Input('chart-dropdown', 'value')]
    )
    def update_plots(n, value):
        try:
            if value == 'effort':
                block_data = api_reader.get_block_stats()
                block_df = pd.DataFrame(block_data)
                if not block_df.empty:
                    block_df['rolling_effort'] = block_df['effort'].expanding().mean()
                    block_df['effort'] = block_df['effort'] * 100
                    title = 'EFFORT AND DIFFICULTY'
                    
                    block_df = block_df.rename(columns={'created': 'time_found'})
                    block_df = block_df.sort_values('time_found')
                    response_df = block_df.melt(id_vars=['time_found'], value_vars=['rolling_effort', 
                                                                                    # 'effort', 'networkdifficulty'
                                                                                   ])
                    
                    effort_response_chart = px.line(
                        response_df[response_df['variable'] != 'networkdifficulty'],
                        x='time_found', y='value', color='variable', markers=True
                    )
                    
                    effort_response_chart.add_trace(
                        go.Scatter(
                            x=response_df['time_found'][response_df['variable'] == 'networkdifficulty'],
                            y=response_df['value'][response_df['variable'] == 'networkdifficulty'],
                            name='networkdifficulty', yaxis='y2',
                            marker=dict(color='rgba(255,0,0,0.5)'),
                            mode='lines+markers'
                        )
                    )
                    
                    effort_response_chart.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        legend_title_text='Metric',
                        legend=dict(font=dict(color='#FFFFFF')),
                        titlefont=dict(color='#FFFFFF'),
                        xaxis=dict(title='Time Found', color='#FFFFFF', showgrid=False, showline=False),
                        yaxis=dict(title='Effort [%]', color='#FFFFFF', side='right'),
                        yaxis2=dict(title='Network Difficulty', color='#FFFFFF', overlaying='y'),
                    )
                    
                    return effort_response_chart, title

            title = 'HASHRATE OVER TIME'
            data = api_reader.get_total_hash_stats()
            performance_df = pd.DataFrame(data)
            
            performance_df = performance_df.rename(columns={
                'timestamp': 'Time',
                'total_hashrate': 'hashrate'
            })
            performance_df['hashrate'] = performance_df['hashrate'] / 1e9
            performance_df = performance_df.sort_values(['Time'])
            
            total_hashrate_plot = {
                'data': [
                    go.Scatter(
                        x=performance_df['Time'],
                        y=performance_df['hashrate'],
                        mode='lines+markers',
                        name='Hashrate Over Time',
                        line={'color': small_text_color}
                    )
                ],
                'layout': go.Layout(
                    xaxis={'showgrid': False, 'title': 'Snap Shot Time'},
                    yaxis={'showgrid': True, 'title': 'GH/s'},
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin={'l': 40, 'b': 40, 't': 50, 'r': 50},
                    hovermode='closest',
                    legend={'font': {'color': '#FFFFFF'}},
                    font=dict(color=small_text_color)
                )
            }
            
            return total_hashrate_plot, title
        except Exception as e:
            logger.error(f"Error in update_plots: {e}")
            return {}, "Error loading chart"

    @app.callback(
        [Output('table', 'data'), Output('dropdown-title', 'children')],
        [Input('fp-int-3', 'n_intervals'), Input('dataset-dropdown', 'value')]
    )
    def update_content(n, selected_data):
        try:
            if selected_data == 'blocks':
                title = 'Blocks Data'
                data = api_reader.get_block_stats()
                block_df = pd.DataFrame(data)
                
                if block_df.empty:
                    return [], title
                
                block_df = block_df.filter(['created', 'blockheight', 'confirmationprogress', 'effort', 'reward', 'miner'])
                block_df['miner'] = ['{}..{}'.format(address[:3], address[-3:]) for address in block_df['miner']]
                block_df = block_df.sort_values(['created'], ascending=False)
                block_df['effort'] = round(block_df['effort'] * 100, 2)
                block_df['reward'] = round(block_df['reward'], 2)
                block_df['confirmationprogress'] = round(block_df['confirmationprogress'], 2)
                block_df['created'] = [data[:10] for data in block_df['created']]
                
                block_df = block_df.rename(columns={
                    'effort': 'Effort [%]',
                    'created': 'Time Found',
                    'blockheight': 'Height',
                    'miner': 'Miner',
                    'reward': 'ERG Reward',
                    'confirmationprogress': 'Confirmation'
                })
                
                return block_df[:15].to_dict('records'), title
                
            elif selected_data == 'miners':
                title = 'Current Top Miners'
                pool_data = api_reader.get_pool_stats()
                data = api_reader.get_live_miner_data()
                df = pd.DataFrame(data)
                
                if not df.empty:
                    df['address'] = ['{}..{}'.format(address[:3], address[-3:]) for address in df['address']]
                    df['hashrate'] = round(df['hashrate'] / 1e6, 2)
                    df['last_block_found'] = [data[:10] if data else None for data in df['last_block_found']]
                    df = df.drop(columns=['lastStatTime', 'sharesPerSecond'])
                    
                    df = df.rename(columns={
                        'address': 'Miner',
                        'hashrate': 'MH/s',
                        'last_block_found': 'Last Block Found'
                    })
                    
                    return df[:15].to_dict('records'), title
                    
            return [], 'Please select an option'
            
        except Exception as e:
            logger.error(f"Error in update_content: {e}")
            return [], 'Error loading data'


DASH_INTERVAL_METRICS = 1000*60*30  # 30 minutes for main metrics
DASH_INTERVAL_PLOTS = 1000*60*30    # 30 minutes for plots
DASH_INTERVAL_TABLE = 1000*60*30    # 30 minutes for tables
DASH_INTERVAL_STATS = 1000*60*30    # 30 minutes for detailed stats

def get_layout(api_reader):
    return html.Div([
        dbc.Container(
            fluid=True,
            style=container_style,
            children=[
                # Development mode intervals are more frequent but still reasonable
                dcc.Interval(
                    id='fp-int-1',
                    interval=DASH_INTERVAL_STATS if os.getenv('FLASK_ENV') != 'development' else DASH_INTERVAL_STATS // 2,
                    n_intervals=0
                ),
                dcc.Interval(
                    id='fp-int-2',
                    interval=DASH_INTERVAL_PLOTS if os.getenv('FLASK_ENV') != 'development' else DASH_INTERVAL_PLOTS // 2,
                    n_intervals=0
                ),
                dcc.Interval(
                    id='fp-int-3',
                    interval=DASH_INTERVAL_TABLE if os.getenv('FLASK_ENV') != 'development' else DASH_INTERVAL_TABLE // 2,
                    n_intervals=0
                ),
                dcc.Interval(
                    id='fp-int-4',
                    interval=DASH_INTERVAL_METRICS if os.getenv('FLASK_ENV') != 'development' else DASH_INTERVAL_METRICS // 2,
                    n_intervals=0
                ),
                # Remove unused interval
                # dcc.Interval(id='fp-int-5', interval=DASH_INTERVAL, n_intervals=0),

                # Add Modal for Sigma Bytes Minting
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            "SIGMA BYTES",
                            style={
                                "backgroundColor": "#1a2234",
                                "color": "#fff",
                                "borderBottom": "1px solid rgba(255,255,255,0.1)",
                                "textAlign": "center",
                                "width": "100%",
                                "fontSize": "24px",
                                "letterSpacing": "2px",
                                "padding": "20px"
                            }
                        ),
                        dbc.ModalBody(
                            html.Iframe(
                                src="/mint/?theme=dark",
                                style={
                                    "width": "100%",
                                    "height": "600px",
                                    "border": "none",
                                    "borderRadius": "8px",
                                    "backgroundColor": "#1a2234",
                                    "color": "#fff"
                                }
                            ),
                            style={
                                "backgroundColor": "#1a2234",
                                "padding": "0",
                                "margin": "0"
                            }
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close",
                                id="close-mint-modal",
                                className="ms-auto",
                                style={
                                    "backgroundColor": "#4299e1",
                                    "border": "none",
                                    "padding": "10px 30px",
                                    "borderRadius": "6px",
                                    "color": "#fff",
                                    "fontWeight": "500"
                                }
                            ),
                            style={
                                "backgroundColor": "#1a2234",
                                "borderTop": "1px solid rgba(255,255,255,0.1)",
                                "padding": "20px"
                            }
                        )
                    ],
                    id="mint-modal",
                    size="xl",
                    is_open=False,
                    style={
                        "maxWidth": "100%",
                        "margin": "0",
                        "backgroundColor": "#1a2234"
                    },
                    className="modal-dialog-centered modal-dialog-scrollable",
                    backdrop="static"
                ),

                html.H1(
                    'ERGO Sigmanaut Mining Pool',
                    style={
                        'color': large_text_color,
                        'textAlign': 'center',
                        'letterSpacing': '0.05em',
                        'fontWeight': '500',
                        'marginBottom': '20px'
                    }
                ),

                # First row - Large metric cards
                dbc.Row(id='metric-1', justify='center', style={'marginBottom': '20px'}),

                # Second row - Detailed stats
                dbc.Row(id='metric-2', justify='center', style={'marginBottom': '20px'}),
                dbc.Row(id='banners', justify='center'),

                # Mining Address Input and Button
                dbc.Row([
                    dbc.Col(
                        md=12,
                        children=[
                            dcc.Input(
                                id='mining-address-input',
                                type='text',
                                placeholder='Mining Address',
                                style={
                                    'width': '100%',
                                    'padding': '10px',
                                    'marginTop': '20px',
                                    'borderRadius': '5px',
                                    'maxWidth': '66.666%',
                                    'display': 'block',
                                    'margin': '20px auto'
                                }
                            ),
                        ]
                    )
                ], justify='center', className="g-0"),

                # Start Mining Button
                dbc.Row([
                    dbc.Col(
                        html.Button(
                            'Start Mining ⛏️',
                            id='start-mining-button',
                            style={
                                'width': '100%',
                                'backgroundColor': button_color,
                                'border': 'none',
                                'padding': '15px',
                                'color': 'white',
                                'fontSize': '18px',
                                'borderRadius': '8px',
                                'cursor': 'pointer',
                                'marginBottom': '20px',
                                'marginTop': '20px'
                            }
                        ),
                        width=8
                    )
                ], justify='center'),

                # Mint Sigma Bytes Button
                dbc.Row([
                    dbc.Col(
                        html.Button(
                            'Mint Sigma Bytes 💎',
                            id='mint-sigma-bytes-button',
                            style={
                                'width': '100%',
                                'backgroundColor': '#1a365d',
                                'border': 'none',
                                'padding': '15px',
                                'color': 'white',
                                'fontSize': '18px',
                                'borderRadius': '8px',
                                'cursor': 'pointer',
                                'marginBottom': '20px',
                                'backgroundImage': 'linear-gradient(to right, #1a365d, #2a4365)',
                                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                                'transition': 'all 0.3s ease'
                            }
                        ),
                        width=12
                    )
                ], className="g-0"),

                # Chart Section
                html.Div([
                    html.Div([
                        html.H1(
                            id='plot-title',
                            children='Please select an option',
                            style={
                                'fontSize': '24px',
                                'letterSpacing': '0.03em'
                            }
                        ),
                        dcc.Dropdown(
                            id='chart-dropdown',
                            options=[
                                {'label': 'Hashrate', 'value': 'hash'},
                                {'label': 'Effort', 'value': 'effort'}
                            ],
                            value='hash',
                            style={
                                'width': '300px',
                                'color': 'black',
                                'borderRadius': '4px'
                            }
                        )
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '10px'
                    }),
                    dcc.Graph(
                        id='plot-1',
                        style={
                            'backgroundColor': card_color,
                            'borderRadius': '8px',
                            'padding': '20px'
                        }
                    )
                ]),

                # Data Selection Section
                html.Div([
                    html.Div([
                        html.H1(
                            id='dropdown-title',
                            children='Please select an option',
                            style={
                                'fontSize': '24px',
                                'letterSpacing': '0.03em'
                            }
                        ),
                        dcc.Dropdown(
                            id='dataset-dropdown',
                            options=[
                                {'label': 'Block-Stats', 'value': 'blocks'},
                                {'label': 'Top-Miners', 'value': 'miners'}
                            ],
                            value='blocks',
                            style={
                                'width': '300px',
                                'color': 'black',
                                'borderRadius': '4px'
                            }
                        )
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '10px'
                    }),

                    dash_table.DataTable(
                        id='table',
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'height': 'auto',
                            'minWidth': '180px',
                            'width': '180px',
                            'maxWidth': '180px',
                            'whiteSpace': 'normal',
                            'textAlign': 'left',
                            'padding': '10px'
                        },
                        style_header=table_style,
                        style_data=table_style
                    )
                ])
            ]
        )
    ], style={'backgroundColor': card_color})

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    app.run_server(debug=True)