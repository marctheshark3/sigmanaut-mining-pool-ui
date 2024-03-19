from dash import html, dcc
import dash_bootstrap_components as dbc


top_card_style = {
    'backgroundColor': '#333333',
    'color': 'white',
    'marginBottom': '25px',
    'padding': '25px',
    'justifyContent': 'center',
    'textAlign': 'center'
}


def get_layout():
    return dbc.Container([
        html.H1('Dashboard', id='dashboard-title'),
        
        dcc.Interval(
            id='interval-component',
            interval=1000*10,  # in milliseconds, every 1 minute
            n_intervals=0
        ),

        dbc.Row([
            dbc.Col(html.Div(id='metrics-stats'), style=top_card_style),
        ]),
        
        dbc.Row(id='stats-row', style={'display': 'flex', 'marginTop': '20px'}),
        
        dbc.Row([
            dbc.Col(dcc.Graph(id='miner-performance-plot'), md=6),
            dbc.Col(dcc.Graph(id='network-difficulty-plot'), md=6),
        ]),
        
        dbc.Row([
            dbc.Col(html.Div([
                html.H2('Blocks Found by Miners'),
                dcc.Graph(id='miner-blocks'),
            ]), md=4),
            dbc.Col(html.Div([
                html.H2('Top Miners by Hashrate Mh/s'),
                dcc.Graph(id='top-miner-chart'),
            ]), md=4),
            dbc.Col(html.Div([
                html.H2('Estimated Rewards'),
                dcc.Graph(id='estimated-reward'),
            ]), md=4),
        ], style={'display': 'flex', 'marginTop': '20px'}),
        
        html.H2('Block Effort Over Time', style={'marginTop': '20px'}),
        dcc.Graph(id='effort-chart'),
        
        html.Div([
            html.H2('Block Statistics', style={'marginTop': '20px'}),
            html.Div(id='block-stats-container')  # Placeholder for dynamic DataTable
        ], style={'padding': '20px'}),
        
    ], style={'backgroundColor': 'rgba(17,17,17,1)', 'color': '#FFFFFF', 'padding': '10px'})
