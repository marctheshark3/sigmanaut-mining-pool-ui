# In mining_page.py
from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc
from flask import Flask
from flask_session import Session
from utils.dash_utils import (
    card_color, background_color, large_text_color, small_text_color,
    card_styles, container_style, table_style, bottom_row_style,
    top_row_style, image_styles
)
from utils.mining_callbacks import register_callbacks
from utils.get_erg_prices import PriceReader
import logging

logger = logging.getLogger(__name__)

debug = False
server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'
server.config['SESSION_TYPE'] = 'filesystem'
Session(server)

styles = {
    'card_styles': card_styles,
    'large_text_color': large_text_color,
    'small_text_color': small_text_color,
    'card_color': card_color,
    'background_color': background_color,
    'table_style': table_style,
    'bottom_row_style': bottom_row_style,
    'top_row_style': top_row_style,
    'bottom_image_style': image_styles['bottom'],
    'top_image_style': image_styles['top']
}

def get_layout(sharkapi):
    return html.Div([
        dbc.Container(
            fluid=True,
            style=container_style,
            children=[
                # Intervals
                dcc.Interval(id='mp-interval-1', interval=30*1000),
                dcc.Interval(id='mp-interval-2', interval=30*1000),
                dcc.Interval(id='mp-interval-3', interval=30*1000),
                dcc.Interval(id='mp-interval-4', interval=30*1000),
                dcc.Interval(id='mp-interval-5', interval=30*1000),
                dcc.Interval(id='mp-interval-7', interval=30*1000),

                # Header
                html.H1(
                    'ERGO Sigmanaut Mining Pool',
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'padding': '30px 0',
                        'fontSize': '2.5em',
                        'letterSpacing': '0.05em',
                        'fontWeight': '500'
                    }
                ),
                
                # Stats section
                html.Div(id='mp-stats', style={'margin': '20px 0'}),

                # Payment and Mining Stats with conditional card heights
                dbc.Row(
                    justify='center',
                    style={'padding': '10px 0'},
                    children=[
                        dbc.Col(
                            md=4,
                            style={'padding': '5px'},
                            children=[
                                dbc.Card(
                                    style={
                                        'backgroundColor': card_color,
                                        'padding': '8px',
                                        'margin': '2px',
                                        'borderRadius': '8px',
                                        'height': '50px' if i > 3 else '180px',
                                        'display': 'flex',
                                        'flexDirection': 'column',
                                        'justifyContent': 'center'
                                    },
                                    id=f's{i}'
                                )
                            ]
                        ) for i in range(1, 7)
                    ]
                ),

                # Banners
                dbc.Row(id='mp-banners', justify='center', style={'margin': '20px 0'}),

                # Charts Section
                html.Div([
                    html.Div([
                        html.H1(
                            id='chart-title',
                            children='Select Chart Type',
                            style={
                                'fontSize': '1.5em',
                                'letterSpacing': '0.03em',
                                'padding': '10px 0'
                            }
                        ),
                        dcc.Dropdown(
                            id='chart-dropdown',
                            options=[
                                {'label': 'Worker Hashrate Over Time', 'value': 'workers'},
                                {'label': 'Payment Over Time', 'value': 'payments'}
                            ],
                            value='workers',
                            style={
                                'width': '300px',
                                'color': 'black',
                                'backgroundColor': 'white',
                                'border': 'none',
                                'borderRadius': '4px'
                            }
                        )
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '20px 10px'
                    }),
                    dcc.Graph(
                        id='chart',
                        style={
                            'backgroundColor': card_color,
                            'padding': '20px',
                            'borderRadius': '8px',
                            'marginTop': '10px'
                        }
                    )
                ], style={'margin': '30px 0'}),

                # Tables Section
                html.Div([
                    html.Div([
                        html.H1(
                            id='table-title',
                            children='Select Data Type',
                            style={
                                'fontSize': '1.5em',
                                'letterSpacing': '0.03em',
                                'padding': '10px 0'
                            }
                        ),
                        dcc.Dropdown(
                            id='table-dropdown',
                            options=[
                                {'label': 'Your Worker Data', 'value': 'workers'},
                                {'label': 'Your Block Data', 'value': 'blocks'}
                            ],
                            value='blocks',
                            style={
                                'width': '300px',
                                'color': 'black',
                                'backgroundColor': 'white',
                                'border': 'none',
                                'borderRadius': '4px'
                            }
                        )
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '20px 10px'
                    }),
                    dash_table.DataTable(
                        id='table-2',
                        style_table={
                            'overflowX': 'auto',
                            'borderRadius': '8px',
                            'backgroundColor': card_color
                        },
                        style_cell={
                            'height': 'auto',
                            'minWidth': '180px',
                            'width': '180px',
                            'maxWidth': '180px',
                            'whiteSpace': 'normal',
                            'textAlign': 'left',
                            'padding': '15px',
                            'letterSpacing': '0.02em'
                        },
                        style_header=table_style,
                        style_data=table_style
                    )
                ], style={'margin': '30px 0'})
            ]
        )
    ], style={'backgroundColor': card_color})

def setup_mining_page_callbacks(app, api_reader):
    """Register all callbacks for the mining page"""
    priceapi = PriceReader()
    register_callbacks(app, api_reader, priceapi, styles)

def init_mining_page(server, sharkapi):
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )
    
    priceapi = PriceReader()
    app.layout = get_layout(sharkapi)
    register_callbacks(app, sharkapi, priceapi, styles)
    
    return app

if __name__ == '__main__':
    from utils.api_reader import ApiReader
    from utils.data_manager import DataManager
    
    data_manager = DataManager("../conf")
    sharkapi = ApiReader(data_manager)
    
    app = init_mining_page(server, sharkapi)
    app.run_server(debug=debug)
else:
    # For production/wsgi
    from utils.api_reader import ApiReader
    from utils.data_manager import DataManager
    
    data_manager = DataManager("../conf")
    sharkapi = ApiReader(data_manager)
    
    app = init_mining_page(server, sharkapi)