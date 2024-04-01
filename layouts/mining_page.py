from utils.reader import SigmaWalletReader, PriceReader
from utils.dash_utils import metric_row_style, image_style, create_pie_chart, create_bar_chart, create_table_component, create_row_card, create_image_text_block, card_style
from dash import Dash, html, dash_table, dcc, callback_context
from dash.exceptions import PreventUpdate
from urllib.parse import unquote
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import math
from flask_login import LoginManager, UserMixin, login_user
from flask import Flask, request, session, redirect, url_for
from flask_session import Session 
debug = True
server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage
card_color = '#27374D'
background_color = '#526D82'
large_text_color = '#9DB2BF' 
small_text_color = '#DDE6ED'
button_color = large_text_color
Session(server)

price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")

color_discrete_map = {
    'Rolling Effort': card_color, 
    'effort': 'white',      
    'networkDifficulty': large_text_color 
}

def setup_mining_page_callbacks(app):

    @app.callback([Output('second-row', 'children'), Output('mining-stats', 'children')],
                  [Input('interval-1', 'n_intervals'),],
                 [State('url', 'pathname')])
    
    def update_stats(n_intervals, pathname):
        print('updating mining page')
        wallet = unquote(pathname.lstrip('/'))
        print(wallet)
    
        mining_df, performance_df = sigma_reader.get_mining_stats(wallet)
        block_df, _, _ = sigma_reader.get_block_stats(wallet)
        pool_df, _ = sigma_reader.get_pool_stats(wallet)
        _, erg_price = price_reader.get(debug=debug)
        
        try:
            pool_hash = round(pool_df[pool_df['Pool Stats'] == 'poolHashrate [Gh/s]']['Values'].iloc[0], 5)
            network_difficulty = round(pool_df[pool_df['Pool Stats'] == 'networkDifficulty [Peta]']['Values'].iloc[0], 5)
            network_hashrate = round(pool_df[pool_df['Pool Stats'] == 'networkHashrate [Th/s]']['Values'].iloc[0], 5)
            
        except IndexError:
            print('POOL API EXCEPTION TRIGGERED!!!!')
            pool_hash = -10
            network_difficulty = -10
            network_hashrate = -10
        # last_block_timestamp = '2024-03-19T20:00:00Z'
        print(sigma_reader.latest_block)
            
        your_total_hash = round(performance_df[performance_df['Worker'] == 'Totals']['Hashrate [Mh/s]'].iloc[0], 5)
        
        # Masking Values we dont need in the tables
        mask = performance_df['Worker'] == 'Totals'
        mask_performance_df = performance_df[~mask]
        
        values_to_drop = ['networkHashrate [Th/s]', 'networkDifficulty [Peta]',
                          'poolHashrate [Gh/s]', 'networkType', 'connectedPeers', 'rewardType']
        mask = pool_df['Pool Stats'].isin(values_to_drop)
        pool_df = pool_df[~mask]

        last_block_timestamp = block_df['Time Found'].max()
        pool_ttf = sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, pool_hash * 1e3, last_block_timestamp) # assumes MH/s
        your_ttf = sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, your_total_hash, last_block_timestamp)

        pool_effort = sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, pool_hash * 1e3, last_block_timestamp) 
        your_effort = sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, your_total_hash, last_block_timestamp)

        inline_style = {'color': large_text_color, 'display': 'center'}

        
        your_stats = dbc.Col(dbc.Card(style=card_style, children=[
                                                html.H2('Miner Stats', style={'color': large_text_color, 'textAlign': 'center'}),
                                                create_image_text_block('Effort: {}%'.format(your_effort), image='effort.png'),
                                                create_image_text_block('TTF: {} [Days]'.format(your_ttf), image='gauge.png'),
                                                create_image_text_block('Hashrate {} [Mh/s]'.format(your_total_hash), image='bolt.png'),]),)

        pool_stats = dbc.Col(dbc.Card(style=card_style, children=[
                                                html.H2('Pool Stats', style={'color': large_text_color, 'textAlign': 'center'}),
                                                create_image_text_block('Effort: {}%'.format(pool_effort), image='effort.png'),
                                                create_image_text_block('TTF: {} [Days]'.format(pool_ttf), image='gauge.png'),
                                                create_image_text_block('Hashrate {} [Gh/s]'.format(pool_hash), image='boltz.png'),]),)
                                        
        
        metric_stats = dbc.Row(justify='center', children=[pool_stats, your_stats])

        
        
        # first col, payment stats -mining_df, second performance - mask_performance_df, pool and net stats - pool-df
        payment = dict(zip(mining_df['Mining Stats'], mining_df['Values']))
        payment['pendingShares'] = round(payment['pendingShares'], 3)
        payment['totalPaid'] = round(payment['totalPaid'], 3)
        payment['todayPaid'] = round(payment['todayPaid'], 3)
        payment['lastPayment'] = payment['lastPayment'][:-17]
        
        payment['Estimated Reward'] = 23
        payment['Price'] = erg_price
        payment['Schema'] = 'PPLNS'
        print(payment.keys())
        

        payment_images ={'pendingShares': 'blocks.png',
                         'pendingBalance': 'coins.png',
                         'totalPaid': 'ergo.png',
                         'todayPaid': 'coins.png',
                         'lastPayment': 'min-payout.png',
                         
                         'Schema': 'ergo.png',
                         'Estimated Reward': 'ergo.png',
                         'Price': 'ergo.png',
                         'lastPaymentLink': 'ergo.png',
                        }
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, payment[key]), image=payment_images[key]) for key in payment.keys() if key != 'lastPaymentLink']
        link = html.Div(style=metric_row_style, children=[
                        html.Img(src='assets/{}'.format('ergo.png'), style=image_style),
                        html.Span(dcc.Link('Last Payment Link', href=payment['lastPaymentLink'], target='_blank'), style={'padding': '10px'})])
        payment_children.append(link)
        # payment_children.insert(0, html.H3('Pool Settings', style={'color': '#FFA500', 'fontWeight': 'bold'}))

        performance = dict(zip(mask_performance_df['Worker'], mask_performance_df['Hashrate [Mh/s]']))
        performance_images = {key: 'qx-fan-club.png' for key in performance.keys()}
        performance_children = [create_image_text_block(text='{}: {}'.format(key, performance[key]), image=performance_images[key]) for key in performance.keys()]
        performance_children.insert(0, html.H3('Performance Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}))

        pool = dict(zip(pool_df['Pool Stats'], pool_df['Values']))
        pool_images ={'connectedMiners': 'mining_temp.png',
                         'sharesPerSecond': 'mining_temp.png',
                         'lastNetworkBlockTime': 'mining_temp.png',
                         'blockHeight': 'mining_temp.png'}
        pool_children = [create_image_text_block(text='{}: {}'.format(key, pool[key]), image=pool_images[key]) for key in pool.keys()]
        pool_children.insert(0, html.H3('Pool Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}))
        
        md = 4
        
        pool_stats = dbc.Row(justify='center', children=[
            dbc.Col(md=md, children=[dbc.Card(style=card_style, children=payment_children[:3])]),
            dbc.Col(md=md, children=[dbc.Card(style=card_style, children=payment_children[3:6])]),
            dbc.Col(md=md, children=[dbc.Card(style=card_style, children=payment_children[6:])])
        ])
        
        return metric_stats, pool_stats

    
    @app.callback([Output('plot', 'figure'), Output('stats', 'data'),],
                  [Input('interval-2', 'n_intervals'),
                  Input('plot-dropdown', 'value'),
                  Input('table-dropdown', 'value')],
                 [State('url', 'pathname')])

    def update_plots(n_intervals, plot, table, pathname):
        wallet = unquote(pathname.lstrip('/'))
        
        _, performance_df = sigma_reader.get_mining_stats(wallet)
        block_df, _, _ = sigma_reader.get_block_stats(wallet)
        miner_performance = sigma_reader.get_miner_samples(wallet)
        pool_df, _ = sigma_reader.get_pool_stats(wallet)

        try:
            pool_hash = round(pool_df[pool_df['Pool Stats'] == 'poolHashrate [Gh/s]']['Values'].iloc[0], 5)
            network_difficulty = round(pool_df[pool_df['Pool Stats'] == 'networkDifficulty [Peta]']['Values'].iloc[0], 5)
            network_hashrate = round(pool_df[pool_df['Pool Stats'] == 'networkHashrate [Th/s]']['Values'].iloc[0], 5)
            
        except IndexError:
            print('POOL API EXCEPTION TRIGGERED!!!!')
            pool_hash = -10
            network_difficulty = -10
            network_hashrate = -10

        last_block_timestamp = block_df['Time Found'].max()

        mask = performance_df['Worker'] == 'Totals'
        mask_performance_df = performance_df[~mask]

        miner_performance['hashrate'] = miner_performance['hashrate'] / 1e6
        miner_performance_chart = px.line(miner_performance, 
              x='created', 
              y='hashrate', 
              color='worker', 
              labels={'hashrate': 'Hashrate', 'created': 'Time'},
              markers=True)

        miner_performance_chart.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Miner',
            legend=dict(font=dict(color='#FFFFFF')),
            titlefont=dict(color='#FFFFFF'),
            xaxis=dict(title='Time', color='#FFFFFF',showgrid=False, showline=False, zeroline=False),
            yaxis=dict(title='Hashrate', color='#FFFFFF')
        )
        

        effort_chart = create_bar_chart(block_df, x='Time Found', y='effort',
                                    color='networkDifficulty', 
                                    labels={'Time Found': 'Block Creation Date',
                                            'effort': 'Effort', 'networkDifficulty': 'Network Difficulty'})

        block_df = block_df.sort_values('Time Found')
        block_df['Rolling Effort'] = block_df['effort'].expanding().mean()
        response_df = block_df.melt(id_vars = ['Time Found'], value_vars=['Rolling Effort', 'effort', 'networkDifficulty'])
        
        effort_response_chart = px.line(response_df[response_df['variable'] != 'networkDifficulty'], 
                                x='Time Found', 
                                y='value', 
                                color='variable', 
                                color_discrete_map=color_discrete_map, 
                                markers=True)

        # Add 'networkDifficulty' on a secondary y-axis
        effort_response_chart.add_trace(go.Scatter(x=response_df['Time Found'][response_df['variable'] == 'networkDifficulty'], 
                                                   y=response_df['value'][response_df['variable'] == 'networkDifficulty'],
                                                   name='networkDifficulty',
                                                   yaxis='y2',
                                                   marker=dict(color='rgba(255,0,0,0.5)'), # Adjust color accordingly
                                                   mode='lines+markers'))
        
        # Update layout with secondary y-axis
        effort_response_chart.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Metric',
            legend=dict(font=dict(color='#FFFFFF')),
            titlefont=dict(color='#FFFFFF'),
            xaxis=dict(title='Block Found Time', color='#FFFFFF',showgrid=False, showline=False, zeroline=False),
            yaxis=dict(title='Effort', color='#FFFFFF'),
            yaxis2=dict(title='Network Difficulty', color='#FFFFFF', overlaying='y', side='right'),
        )

        block_df = block_df[block_df.my_wallet == True]
        
        latest_block = block_df['Time Found'].max()

        if type(latest_block) != 'str':
            latest_block = last_block_timestamp
        block_df = block_df.filter(['blockHeight', 'effort', 'reward', 'status', 'Time Found', 'networkDifficulty', 'confirmationProgress'])
        block_data = block_df.to_dict('records')
        print(mask_performance_df.columns, 'my latest blocvk', latest_block)
        print(network_difficulty, network_hashrate, latest_block, 'yoooo')
        mask_performance_df['Effort [%]'] = [sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, hash, latest_block) for hash in mask_performance_df['Hashrate [Mh/s]']]
        mask_performance_df['TTF [Days]'] = [sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, hash, latest_block) for hash in mask_performance_df['Hashrate [Mh/s]']]
        # mask_performance_df['Estimated Payout'] = 0
        print(mask_performance_df.columns)

        total_hash = mask_performance_df['Hashrate [Mh/s]'].sum()
        total_effort = sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, total_hash, latest_block)
        total_time_to_find = sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, total_hash, latest_block)
        totals_ls = ['Totals', total_hash, round(mask_performance_df['SharesPerSecond'].sum(), 3),
                     total_effort, total_time_to_find,]
                     # mask_performance_df['Estimated Payout'].sum()]
        print(totals_ls)
        totals = pd.DataFrame([totals_ls], columns=mask_performance_df.columns)
        p_df = pd.concat([mask_performance_df, totals])
        
        # add another row for Totals
        miner_data = p_df.to_dict('records')

        if plot == 'hash':
            chart = miner_performance_chart
        elif plot == 'effort':
            chart = effort_response_chart

        if table == 'worker':
            data = miner_data
        elif table == 'blocks':
            data = block_data
            
        return chart, data

                                

def get_layout():
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': background_color, 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px'},
                           children=[
                               dcc.Interval(id='interval-1', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='interval-2', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': 'white', 'textAlign': 'center',}),
                                 # Metrics overview row
                            # dbc.Row(id='first-row', justify='center', style={'padding': '20px'}),
                               
                               dbc.Row(id='second-row', justify='center', style={'padding': '15px'}),
                               dbc.Row(id='mining-stats', justify='center', style={'padding': '15px'}),
                               # html.H2('Hashrate Over Time', style={'padding': '10px'}),
                               # dcc.Graph(id='miner-performance-plot'),

                               html.Div(
                                    [
                                        html.Div(
                                            html.H1(
                                                id='dropdown-title',
                                                children='Please select an option',
                                                style={'fontSize': '24px'}
                                            ),
                                            style={'flex': '1'}
                                        ),
                                        html.Div(
                                            dcc.Dropdown(
                                                id='plot-dropdown',
                                                options=[
                                                    {'label': 'Hashrate Over Time', 'value': 'hash'},
                                                    {'label': 'Effort & Difficulty', 'value': 'effort'}
                                                ],
                                                value='hash',  # Default value
                                                style={'width': '300px', 'color': 'black'}
                                            ),
                                            style={'flex': '1'}
                                        )
                                    ],
                                    style={
                                        'display': 'flex', 
                                        'justifyContent': 'space-between', 
                                        'alignItems': 'center',
                                        'padding': '10px'
                                    }
                                ),

                               dcc.Graph(id='plot'),
                               

                            #    dbc.Row(children=[
                            #    html.Div(children=[html.H2('Hashrate Over Time', style={'padding': '10px'}),
                            #    dcc.Graph(id='miner-performance-plot'),],
                            #             style={'flex': 1,}
                            #            )]),

                            # dbc.Row(children=[
                            #    html.Div(children=[html.H2('Effort & Rolling Effort Over Time'),
                            #    dcc.Graph(id='effort'),],
                            #             style={'flex': 1,}
                            #            )]),
                           html.Div(
                                        [
                                            html.Div(
                                                html.H1(
                                                    # id='dropdown-title',
                                                    children='Please select an option',
                                                    style={'fontSize': '24px'}
                                                ),
                                                style={'flex': '1'}
                                            ),
                                            html.Div(
                                                dcc.Dropdown(
                                                    id='table-dropdown',
                                                    options=[
                                                        {'label': 'Your Block Stats', 'value': 'blocks'},
                                                        {'label': 'Worker Stats', 'value': 'worker'}
                                                    ],
                                                    value='worker',  # Default value
                                                    style={'width': '300px', 'color': 'black'}
                                                ),
                                                style={'flex': '1'}
                                            )
                                        ],
                                        style={
                                            'display': 'flex', 
                                            'justifyContent': 'space-between', 
                                            'alignItems': 'center',
                                            'padding': '10px'
                                        }
                                    ),
                                   
                       html.Div(children=[
                       dash_table.DataTable(id='stats', fixed_rows={'headers': True},
                                            style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': 0, 'fontWeight': 'bold', 'textAlign': 'center',},
                                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'whiteSpace': 'normal',
                                                        'height': 'auto',
                                                        'lineHeight': '15px',
                                                        'border': '1px solid black',},
                                            style_data_conditional=[{'if': {'column_id': 'status', 'filter_query': '{status} eq confirmed'},
                                                                     'backgroundColor': 'lightgreen', 'color': 'black', 'after': {'content': '" ✔"'}}],
                                            style_as_list_view=True,  style_cell_conditional=[{'if': {'column_id': c},
                                                                                               'textAlign': 'left'} for c in ['Name', 'status']],
                                            style_header_conditional=[{'if': {'column_id': 'status'}, 'textAlign': 'center'}])]),

            #                    html.Div(children=[html.H2('Worker Stats'), 
            #            dash_table.DataTable(id='miner-stats',fixed_rows={'headers': True}, 
            #                                 style_table={'overflowX': 'auto'},
            #                                 style_cell={'height': 'auto', 'minWidth': '180px',
            #                                             'width': '180px', 'maxWidth': '180px',
            #                                             'whiteSpace': 'normal', 'textAlign': 'left',
            #                                             'padding': '10px',},
            #                                 style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': 0, 'fontWeight': 'bold', 'textAlign': 'center',},
            #                                 style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',
            #                                             'border': '1px solid black',},
            #                                 style_data_conditional=[{'if': {'column_id': 'status', 'filter_query': '{status} eq confirmed'},
            #                                                          'backgroundColor': 'lightgreen', 'color': 'black', 'after': {'content': '" ✔"'}}],
            #                                 style_as_list_view=True,  style_cell_conditional=[{'if': {'column_id': c},
            #                                                                                    'textAlign': 'left'} for c in ['Name', 'status']],
            #                                 style_header_conditional=[{'if': {'column_id': 'status'}, 'textAlign': 'center'}])]),
            ],)], style={'backgroundColor': card_color})  # This sets the background color for the whole page

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    setup_front_page_callbacks(app)
    app.run_server(debug=True)