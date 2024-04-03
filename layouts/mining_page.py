from utils.reader import SigmaWalletReader, PriceReader
from utils.dash_utils import image_style, create_pie_chart, create_bar_chart, create_table_component, create_row_card, create_image_text_block, card_style, image_card_style, bottom_row_style, card_color, background_color, large_text_color, small_text_color, bottom_image_style, top_row_style
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
debug = False
server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage

button_color = large_text_color
Session(server)

price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")

color_discrete_map = {
    'Rolling Effort': 'black', 
    'effort': 'white',      
    'networkDifficulty': large_text_color 
}

def setup_mining_page_callbacks(app):
    def get_net_stats(wallet):
        pool_df, _ = sigma_reader.get_pool_stats(wallet) 
        try:
            pool_hash = round(pool_df[pool_df['Pool Stats'] == 'poolHashrate [Gh/s]']['Values'].iloc[0], 2)
            network_difficulty = round(pool_df[pool_df['Pool Stats'] == 'networkDifficulty [Peta]']['Values'].iloc[0], 2)
            network_hashrate = round(pool_df[pool_df['Pool Stats'] == 'networkHashrate [Th/s]']['Values'].iloc[0], 2)
            
        except IndexError:
            print('POOL API EXCEPTION TRIGGERED!!!!')
            pool_hash = -10
            network_difficulty = -10
            network_hashrate = -10     
        return pool_hash, network_difficulty, network_hashrate

    @app.callback([Output('mp-stats', 'children'),
                  Output('mp-metrics', 'children'),],
                  [Input('mp-interveral-1', 'n')],
                  [State('url', 'pathname')])

    def update(n, pathname):
        wallet = unquote(pathname.lstrip('/'))

        if wallet != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:5], wallet[-5:])
        else:
            short_wallet = wallet
    
        mining_df, performance_df = sigma_reader.get_mining_stats(wallet)
        pool_df, _ = sigma_reader.get_pool_stats(wallet) 
        _, erg_price = price_reader.get(debug=debug)
        block_df, miner_df, effort_df = sigma_reader.get_block_stats(wallet)

        last_block_timestamp = max(block_df['Time Found'])
        my_blocks = block_df[block_df.my_wallet == True]
        try:
            my_last_block_timestamp = max(my_blocks['Time Found'])
        except ValueError:
            my_last_block_timestamp = min(block_df['Time Found'])
          
        pool_hash, network_difficulty, network_hashrate = get_net_stats(wallet)

        your_total_hash = round(performance_df[performance_df['Worker'] == 'Totals']['Hashrate [Mh/s]'].iloc[0], 2)
        
        current_effort = sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, pool_hash * 1e3, last_block_timestamp)
        pool_ttf = sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, pool_hash * 1e3, last_block_timestamp)
        
        pool_effort_text = '{}%'.format(current_effort)
        pool_ttf_text = '{} Days'.format(pool_ttf)
        pool_hash_text = '{} GH/s'.format(pool_hash)

        your_effort = sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, your_total_hash, my_last_block_timestamp)
        your_ttf = sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, your_total_hash, my_last_block_timestamp)
        
        your_effort_text = '{}%'.format(your_effort)
        your_ttf_text = '{} Days'.format(your_ttf)
        your_hash_text = '{} MH/s'.format(your_total_hash)
                    
        # Masking Values we dont need in the tables
        mask = performance_df['Worker'] == 'Totals'
        mask_performance_df = performance_df[~mask]
        
        values_to_drop = ['networkHashrate [Th/s]', 'networkDifficulty [Peta]',
                          'poolHashrate [Gh/s]', 'networkType', 'connectedPeers', 'rewardType']
        mask = pool_df['Pool Stats'].isin(values_to_drop)
        pool_df = pool_df[~mask]

        pool_stats = dbc.Col(dbc.Card(style=top_row_style, children=[
                                                # html.Img(src=image, style=top_image_style),
                                                html.H2('Pool Stats', style={'color': large_text_color, 'textAlign': 'center'}),
                                                dbc.Row([ 
                                                    dbc.Col([html.H4('Hashrate', style={'color': large_text_color}),  html.P(pool_hash_text),]),
                                                    dbc.Col([html.H4('TTF', style={'color': large_text_color}),  html.P(pool_ttf_text),]),
                                                    dbc.Col([html.H4('Effort', style={'color': large_text_color}), html.P(pool_effort_text)])]),]),
                                                                 style={'marginRight': 'auto', 'marginLeft': 'auto'})

        your_stats = dbc.Col(dbc.Card(style=top_row_style, children=[
                                                # html.Img(src=image, style=top_image_style),
                                                html.H2('Miner Stats', style={'color': large_text_color, 'textAlign': 'center'}),
                                                dbc.Row([ 
                                                    dbc.Col([html.H4('Hashrate', style={'color': large_text_color}),  html.P(your_hash_text),]),
                                                    dbc.Col([html.H4('TTF', style={'color': large_text_color}),  html.P(your_ttf_text),]),
                                                    dbc.Col([html.H4('Effort', style={'color': large_text_color}), html.P(your_effort_text)])]),]),
                                                                 style={'marginRight': 'auto', 'marginLeft': 'auto'})
        
        stats = dbc.Row(justify='center', children=[pool_stats, your_stats])
        
        payment = dict(zip(mining_df['Mining Stats'], mining_df['Values']))
        
        payment['Pending Shares'] = round(payment.pop('pendingShares'), 3)
        payment['Pending Balance'] = round(payment.pop('pendingBalance'), 3)
        payment['Total Paid'] = round(payment.pop('totalPaid'), 3)
        payment['Paid Today'] = payment.pop('todayPaid')
        payment['Last Payment'] = payment.pop('lastPayment')[:-17]
        payment['Price'] = erg_price

        miners = sigma_reader.get_miner_ls()
        ls = []
        for miner in miners:
            df, _ = sigma_reader.get_mining_stats(miner)
            shares = df[df['Mining Stats'] == 'pendingShares'].Values[0]
            ls.append([miner, shares])
        
        df = pd.DataFrame(ls, columns=['Miner', 'Shares'])
        total = df.Shares.sum()
        df['participation'] = [shares / total for shares in df.Shares] 
        df['reward'] = df['participation'] * 30
        my_df = df[df.Miner == wallet]
        participation = round(my_df['participation'].values[0] * 100, 3)
        print(participation)

        
        payment['Participation [%]']= participation
        payment['Schema'] = 'PPLNS'

        payment_images ={'Pending Shares': 'min-payout.png',
                         'Pending Balance': 'triangle.png',
                         'Total Paid': 'ergo.png',
                         'Paid Today': 'ergo.png',
                         'Last Payment': 'coins.png',
                         'Participation [%]': 'smileys.png',
                         'Price': 'ergo.png',
                         'Schema': 'ergo.png',
                         'lastPaymentLink': 'ergo.png',
                        }
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, payment[key]), image=payment_images[key]) for key in payment.keys() if key != 'lastPaymentLink']
        link = html.Div(style=bottom_row_style, children=[
                        html.Img(src='assets/{}'.format('ergo.png'), style=bottom_image_style),
                        html.Span(dcc.Link('Last Payment Link', href=payment['lastPaymentLink'], target='_blank'), style={'padding': '10px'})])
        
        payment_children.append(link)

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
        
        metrics = dbc.Row(children=[
                                dbc.Col(md=md, children=[
                                    dbc.Card(style=bottom_row_style, children=payment_children[:3])
                                ]),
                                dbc.Col(md=md, children=[
                                    dbc.Card(style=bottom_row_style, children=payment_children[3:6])
                                ]),

                                dbc.Col(md=md, children=[
                                    dbc.Card(style=bottom_row_style, children=payment_children[6:])
                                ])])
        
        return stats, metrics 

    
    @app.callback([
                Output('chart', 'figure'),
                Output('table-2', 'data'),
                Output('table-title', 'children'),
                  ],
                  [Input('mp-interveral-2', 'n_intervals'), Input('table-dropdown', 'value')],
                 [State('url', 'pathname')])
    
    def update_charts(n_intervals, table, pathname):
        print('updating mining page')
        wallet = unquote(pathname.lstrip('/'))
        print(wallet)
        pool_hash, network_difficulty, network_hashrate = get_net_stats(wallet)
        if wallet != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:5], wallet[-5:])
        else:
            short_wallet = wallet
    
        print(wallet, 'wallllllllet')
        block_df, miner_df, effort_df = sigma_reader.get_block_stats(wallet) #
        pool_df, _ = sigma_reader.get_pool_stats(wallet)

        miner_performance = sigma_reader.get_miner_samples(wallet) #        
        last_block_timestamp = max(block_df['Time Found'])
        
        values_to_drop = ['networkHashrate [Th/s]', 'networkDifficulty [Peta]',
                          'poolHashrate [Gh/s]', 'networkType', 'connectedPeers', 'rewardType']
        
        mask = pool_df['Pool Stats'].isin(values_to_drop)
        pool_df = pool_df[~mask]

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

        my_block_df = block_df[block_df.miner == short_wallet]
        try:
            latest = max(my_block_df['Time Found'])
        except ValueError:
            latest = min(block_df['Time Found'])
        
        if not isinstance(latest, str):
            print('triggered')
            latest = min(block_df['Time Found'])
        print(latest, '1')
        
        plot = miner_performance_chart

        df = sigma_reader.get_all_miner_data(wallet)
        # print(wallet)
        # print(latest)
        latest_data = df[df.created == max(df.created)]
        my_data = latest_data[latest_data.my_wallet == True]
        my_data = my_data.filter(['worker', 'hashrate', 'sharesPerSecond'])
        total_hash = my_data.hashrate.sum()
        total_shares = my_data.sharesPerSecond.sum()
        ls = ['Totals', total_hash, total_shares]
        d = pd.DataFrame([ls], columns=['worker', 'hashrate', 'sharesPerSecond'])
        work_data = pd.concat([my_data, d])
        print(latest, 'miningpage latest')

        work_data['ttf'] = [sigma_reader.calculate_time_to_find_block(network_difficulty, network_hashrate, hash, latest) for hash in work_data.hashrate]
        work_data['effort'] = [sigma_reader.calculate_mining_effort(network_difficulty, network_hashrate, hash, latest) for hash in work_data.hashrate]

        work_data['hashrate'] = round(work_data['hashrate'], 3)
        work_data['sharesPerSecond'] = round(work_data['sharesPerSecond'], 3)

        if table == 'workers':
            df = work_data
            title_2 = 'WORKER DATA'

        elif table == 'blocks':
            df = my_block_df
            title_2 = 'Your Blocks Found'
        else:
            df = work_data
            title_2 = 'WORKER DATA'
            
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        # print(first, second)
        return plot, data, title_2
                                

def get_layout():
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': background_color, 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px'},
                           children=[
                               
                               dcc.Interval(id='mp-interveral-1', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='mp-interveral-2', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': 'white', 'textAlign': 'center',}), 
                               dbc.Row(id='mp-stats', justify='center', style={'padding': '20px'}),
                               dbc.Row(id='mp-metrics', justify='center', style={'padding': '20px'}),

                               html.H2('Worker Hashrate Over Time', style={'color': 'white', 'textAlign': 'center',}),
                               dcc.Graph(id='chart', style={'backgroundColor': card_color}),

                               html.Div(
                                    [
                                        html.Div(
                                            html.H1(
                                                id='table-title',
                                                children='Please select an option',
                                                style={'fontSize': '24px'}
                                            ),
                                            style={'flex': '1'}
                                        ),
                                        html.Div(
                                            dcc.Dropdown(
                                                id='table-dropdown',
                                                options=[
                                                    {'label': 'Your Worker Data', 'value': 'workers'},
                                                    {'label': 'Your Block Data', 'value': 'blocks'}
                                                ],
                                                value='workers',  # Default value
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
                               # dash_table.DataTable(id='table',),
           
                               
                       # html.Div(children=[html.H2('Block Statistics'), 
                       dash_table.DataTable(id='table-2',
                                            style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header={'backgroundColor': card_color, 'color': 'white',
                                                          'fontWeight': 'bold', 'textAlign': 'center',},
                                            style_data={'backgroundColor': card_color, 'color': 'white',
                                                        'border': '1px solid black',},
                                            style_data_conditional=[{'if': {'column_id': 'status', 'filter_query': '{status} eq confirmed'},
                                                                     'backgroundColor': 'lightgreen', 'color': 'black', 'after': {'content': '" ✔"'}}],
                                            style_as_list_view=True,  style_cell_conditional=[{'if': {'column_id': c},
                                                                                               'textAlign': 'left'} for c in ['Name', 'status']],
                                            style_header_conditional=[{'if': {'column_id': 'status'}, 'textAlign': 'center'}])
                                         ]),
            ], style={'backgroundColor': card_color})  # This sets the background color for the whole page

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    setup_front_page_callbacks(app)
    app.run_server(debug=True)