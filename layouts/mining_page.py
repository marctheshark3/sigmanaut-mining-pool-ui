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

from flask_login import LoginManager, UserMixin, login_user
from flask import Flask, request, session, redirect, url_for
from flask_session import Session 

server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage

Session(server)

price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")


def setup_mining_page_callbacks(app):
    
    @app.callback([Output('first-row', 'children'),
                   Output('second-row', 'children'),
                  Output('mining-stats', 'children'),
                  Output('miner-performance-plot', 'figure'),
                  Output('network-difficulty-plot', 'figure'),
                  Output('miner-blocks', 'figure'),
                  Output('top-miner-chart', 'figure'),
                  Output('estimated-reward', 'figure'),
                  Output('block-stats', 'data'),
                   Output('effort', 'figure'),
                  ],
                  [Input('mining-page-interval', 'n_intervals')],
                 [State('url', 'pathname')])
    def update_output(n_intervals, pathname):
        print('updating mining page')
        wallet = unquote(pathname.lstrip('/'))
        print(wallet)
        
        if wallet != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:5], wallet[-5:])
        else:
            short_wallet = wallet
    
        mining_df, performance_df = sigma_reader.get_mining_stats(wallet)
        block_df, miner_df, effort_df = sigma_reader.get_block_stats(wallet)
        pool_df, _ = sigma_reader.get_pool_stats(wallet)
        top_miner_df = sigma_reader.get_all_miner_data(wallet)
        miner_reward_df = sigma_reader.get_estimated_payments(wallet)
        miner_performance = sigma_reader.get_miner_samples(wallet)
        btc_price, erg_price = price_reader.get(debug=True)

        
    
        try:
            pool_hash = round(pool_df[pool_df['Pool Stats'] == 'poolHashrate [Gh/s]']['Values'].iloc[0], 5)
            network_difficulty = round(pool_df[pool_df['Pool Stats'] == 'networkDifficulty [Peta]']['Values'].iloc[0], 5)
            network_hashrate = round(pool_df[pool_df['Pool Stats'] == 'networkHashrate [Th/s]']['Values'].iloc[0], 5)
            
        except IndexError:
            print('POOL API EXCEPTION TRIGGERED!!!!')
            pool_hash = -10
            network_difficulty = -10
            network_hashrate = -10
        last_block_timestamp = '2024-03-19T20:00:00Z'
        print(sigma_reader.latest_block)
        current_effort = sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, pool_hash, sigma_reader.latest_block)
            
        your_total_hash = round(performance_df[performance_df['Worker'] == 'Totals']['Hashrate [Mh/s]'].iloc[0], 5)
        avg_block_effort = round(effort_df[effort_df['Mining Stats'] == 'Average Block Effort']['Values'].iloc[0], 5)
        
        # Masking Values we dont need in the tables
        mask = performance_df['Worker'] == 'Totals'
        mask_performance_df = performance_df[~mask]
        
        values_to_drop = ['networkHashrate [Th/s]', 'networkDifficulty [Peta]',
                          'poolHashrate [Gh/s]', 'networkType', 'connectedPeers', 'rewardType']
        mask = pool_df['Pool Stats'].isin(values_to_drop)
        pool_df = pool_df[~mask]

        first = dbc.Row(justify='center', children=[create_row_card(btc_price, 'BTC PRICE ($)'),
                                                 create_row_card(erg_price, 'ERG PRICE ($)'),
                                                 create_row_card(network_hashrate, 'Network Hashrate Th/s'),
                                                 create_row_card(network_difficulty, 'Network Difficulty PH/s')])

        second = dbc.Row(justify='center', children=[create_row_card(pool_hash, 'Pool Hashrate GH/s'),
                                                 create_row_card(your_total_hash, 'Your Hashrate MH/s'),
                                                 create_row_card(avg_block_effort, 'Pool Effort'),
                                                 create_row_card(current_effort, 'Current Block Effort %')])

        
        
        # first col, payment stats -mining_df, second performance - mask_performance_df, pool and net stats - pool-df
        payment = dict(zip(mining_df['Mining Stats'], mining_df['Values']))

        payment_images ={'pendingShares': 'mining_temp.png',
                         'pendingBalance': 'mining_temp.png',
                         'totalPaid': 'mining_temp.png',
                         'todayPaid': 'mining_temp.png',
                         'lastPayment': 'mining_temp.png',
                         'lastPaymentLink': 'mining_temp.png'}
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, payment[key]), image=payment_images[key]) for key in payment.keys() if key != 'lastPaymentLink']
        link = html.Div(style=metric_row_style, children=[
                        html.Img(src='assets/{}'.format('mining_temp.png'), style=image_style),
                        html.Span(dcc.Link('Last Payment Link', href=payment['lastPaymentLink'], target='_blank'), style={'padding': '10px'})])
        payment_children.append(link)
        payment_children.insert(0, html.H3('Pool Settings', style={'color': '#FFA500', 'fontWeight': 'bold'}))

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
        third = dbc.Row(justify='center', children=[
            dbc.Col(md=md, children=[dbc.Card(style=card_style, children=payment_children)]),
            dbc.Col(md=md, children=[dbc.Card(style=card_style, children=pool_children)]),
            dbc.Col(md=md, children=[dbc.Card(style=card_style, children=performance_children)])
        ])

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
            xaxis=dict(title='Time', color='#FFFFFF'),
            yaxis=dict(title='Hashrate', color='#FFFFFF')
        )

        net_diff_plot={'data': [go.Scatter(x=block_df['Time Found'], y=block_df['networkDifficulty'],
                                    mode='lines+markers', name='Network Difficulty', line={'color': '#00CC96'})],
                   
                   'layout': go.Layout(
                                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       margin={'l': 40, 'b': 40, 't': 50, 'r': 50}, hovermode='closest',
                                       legend={'font': {'color': '#FFFFFF'}}, font=dict(color='#FFFFFF'))}

        miner_chart = create_pie_chart(miner_df, 'miner', 'Number of Blocks Found')
        top_miner_chart = create_pie_chart(top_miner_df, 'miner', 'hashrate')
        estimated_reward = create_pie_chart(miner_reward_df, 'miner', 'reward', est_reward=True)

        effort_chart = create_bar_chart(block_df, x='Time Found', y='effort',
                                    color='networkDifficulty', 
                                    labels={'Time Found': 'Block Creation Date',
                                            'effort': 'Effort', 'networkDifficulty': 'Network Difficulty'})

        block_df = block_df.sort_values('Time Found')
        block_df['Rolling Effort'] = block_df['effort'].expanding().mean()
        response_df = block_df.melt(id_vars = ['Time Found', 'networkDifficulty'], value_vars=['Rolling Effort', 'effort',])
        effort_response_chart = px.line(response_df, 
              x='Time Found', 
              y='value', 
              color='variable', 
              markers=True)      

        effort_response_chart.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Miner',
            legend=dict(font=dict(color='#FFFFFF')),
            titlefont=dict(color='#FFFFFF'),
            xaxis=dict(title='Block Found Time', color='#FFFFFF'),
            yaxis=dict(title='Effort', color='#FFFFFF'),
        )

        block_stats = dash_table.DataTable(columns=[{"name": i, "id": i} for i in block_df.columns],
                                            data=block_df.to_dict('records'), style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white',
                                                          'fontWeight': 'bold', 'textAlign': 'center',},
                                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',
                                                        'border': '1px solid black',},
                                            style_data_conditional=[{'if': {'column_id': 'status', 'filter_query': '{status} eq confirmed'},
                                                                     'backgroundColor': 'lightgreen', 'color': 'black', 'after': {'content': '" ✔"'}}],
                                            style_as_list_view=True,  style_cell_conditional=[{'if': {'column_id': c},
                                                                                               'textAlign': 'left'} for c in ['Name', 'status']],
                                            style_header_conditional=[{'if': {'column_id': 'status'}, 'textAlign': 'center'}])

        block_data = block_df.to_dict('records')

        # print(first, second)
        return first, second, third, miner_performance_chart, net_diff_plot, miner_chart, top_miner_chart, estimated_reward, block_data, effort_response_chart
                                

def get_layout():
    return dbc.Container(fluid=True, style={'backgroundColor': '#1e1e1e', 'color': '#FFFFFF', 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif'},
                           children=[
                               dcc.Interval(id='mining-page-interval', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': '#FFA500', 'textAlign': 'center',}),
                                 # Metrics overview row
                                 dbc.Row(id='first-row', justify='center', style={'padding': '20px'}),
                               
                               dbc.Row(id='second-row', justify='center', style={'padding': '20px'}),
                               dbc.Row(id='mining-stats', justify='center', style={'padding': '20px'}),
                               html.H2('Hashrate Over Time'),
                               dcc.Graph(id='miner-performance-plot'),

                            dbc.Row(children=[
                               html.Div(children=[html.H2('Effort & Rolling Effort Over Time'),
                               dcc.Graph(id='effort'),],
                                        style={'flex': 1,}
                                       ),
               
                                html.Div(children=[html.H2('Ergo Network Difficulty Over Time'),
                               dcc.Graph(id='network-difficulty-plot'),],
                                         style={'flex': 1,},)]),
                                             
                               
                               
                               
                               dbc.Row(children=[
                                   html.Div(children=[html.H2('Blocks Found by Miners'),
                                                      dcc.Graph(id='miner-blocks'),],
                                            style={'flex': 1,}
                                           ),
                   
                                    html.Div(children=[html.H2('Top Miners by Hashrate Mh/s'),
                                                       dcc.Graph(id='top-miner-chart')],
                                             style={'flex': 1,}
                                            ), 
                                    html.Div(children=[html.H2('Estimated Rewards'),
                                                       dcc.Graph(id='estimated-reward')],
                                             style={'flex': 1,}
                                            ),],
                                      
                                      ),
                               
                       html.Div(children=[html.H2('Block Statistics'), 
                       dash_table.DataTable(id='block-stats',
                                            style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white',
                                                          'fontWeight': 'bold', 'textAlign': 'center',},
                                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',
                                                        'border': '1px solid black',},
                                            style_data_conditional=[{'if': {'column_id': 'status', 'filter_query': '{status} eq confirmed'},
                                                                     'backgroundColor': 'lightgreen', 'color': 'black', 'after': {'content': '" ✔"'}}],
                                            style_as_list_view=True,  style_cell_conditional=[{'if': {'column_id': c},
                                                                                               'textAlign': 'left'} for c in ['Name', 'status']],
                                            style_header_conditional=[{'if': {'column_id': 'status'}, 'textAlign': 'center'}])]),
            ],)

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    setup_front_page_callbacks(app)
    app.run_server(debug=True)