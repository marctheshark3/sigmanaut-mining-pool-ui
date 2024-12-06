from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc
from flask import Flask
from flask_session import Session
from utils.dash_utils import (
    card_color, background_color, large_text_color, small_text_color,
    bottom_row_style, top_row_style, table_style, bottom_image_style
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
    'top_row_style': top_row_style,
    'large_text_color': large_text_color,
    'small_text_color': small_text_color,
    'card_color': card_color,
    'background_color': background_color,
    'table_style': table_style,
    'bottom_row_style': bottom_row_style,
    'bottom_image_style': bottom_image_style
}

def setup_mining_page_callbacks(app, api_reader):
    """Register all callbacks for the mining page"""
    priceapi = PriceReader()
    register_callbacks(app, api_reader, priceapi, styles)


def get_layout(sharkapi):
    md = 4
    return html.Div([
        dbc.Container(
            fluid=True,
            style={
                'backgroundColor': background_color,
                'padding': '15px',
                'justifyContent': 'center',
                'fontFamily': 'sans-serif',
                'color': '#FFFFFF',
                'maxWidth': '960px'
            },
            children=[
                # Intervals
                dcc.Interval(id='mp-interval-1', interval=30*1000),
                dcc.Interval(id='mp-interval-2', interval=30*1000),
                dcc.Interval(id='mp-interval-3', interval=30*1000),
                dcc.Interval(id='mp-interval-4', interval=30*1000),
                dcc.Interval(id='mp-interval-5', interval=30*1000),
                dcc.Interval(id='mp-interval-7', interval=30*1000),

                # Header and Stats
                html.H1('ERGO Sigmanaut Mining Pool', 
                       style={'color': 'white', 'textAlign': 'center'}),
                html.Div(id='mp-stats'),

                # Payment and Mining Stats
                dbc.Row(justify='center', style={'padding': '20px'}, children=[
                    dbc.Col(md=md, style={'padding': '7px'}, children=[
                        dbc.Card(style=bottom_row_style, id='s1')
                    ]),
                    dbc.Col(md=md, style={'padding': '7px'}, children=[
                        dbc.Card(style=bottom_row_style, id='s2')
                    ]),
                    dbc.Col(md=md, style={'padding': '7px'}, children=[
                        dbc.Card(style=bottom_row_style, id='s3')
                    ]),
                    dbc.Col(md=md, style={'padding': '7px'}, children=[
                        dbc.Card(style=bottom_row_style, id='s4')
                    ]),
                    dbc.Col(md=md, style={'padding': '7px'}, children=[
                        dbc.Card(style=bottom_row_style, id='s5')
                    ]),
                    dbc.Col(md=md, style={'padding': '7px'}, children=[
                        dbc.Card(style=bottom_row_style, id='s6')
                    ]),
                ]),

                dbc.Row(id='mp-banners', justify='center'),

                # Charts Section
                html.Div([
                    html.Div([
                        html.H1(id='chart-title', children='Select Chart Type',
                               style={'fontSize': '24px'}),
                        dcc.Dropdown(
                            id='chart-dropdown',
                            options=[
                                {'label': 'Worker Hashrate Over Time', 'value': 'workers'},
                                {'label': 'Payment Over Time', 'value': 'payments'}
                            ],
                            value='workers',
                            style={'width': '300px', 'color': 'black'}
                        )
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '10px'
                    }),
                    dcc.Graph(id='chart', style={'backgroundColor': card_color, 'padding': '20px'})
                ]),

                # Tables Section
                html.Div([
                    html.Div([
                        html.H1(id='table-title', children='Select Data Type',
                               style={'fontSize': '24px'}),
                        dcc.Dropdown(
                            id='table-dropdown',
                            options=[
                                {'label': 'Your Worker Data', 'value': 'workers'},
                                {'label': 'Your Block Data', 'value': 'blocks'}
                            ],
                            value='blocks',
                            style={'width': '300px', 'color': 'black'}
                        )
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '10px'
                    }),
                    dash_table.DataTable(
                        id='table-2',
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