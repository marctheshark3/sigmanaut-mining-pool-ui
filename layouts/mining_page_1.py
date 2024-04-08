from utils.api_reader import SigmaWalletReader, PriceReader
from utils.dash_utils import image_style, create_pie_chart, create_bar_chart, create_table_component, create_row_card, create_image_text_block, card_style, image_card_style, bottom_row_style, card_color, background_color, large_text_color, small_text_color, bottom_image_style, top_row_style, table_style
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
debug = True
server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage

button_color = large_text_color
Session(server)

price_reader = PriceReader()
# sigma_reader = SigmaWalletReader(config_path="../conf")

color_discrete_map = {
    'Rolling Effort': 'black', 
    'effort': 'white',      
    'networkDifficulty': large_text_color 
}

def setup_mining_page_callbacks(app, reader):
    @app.callback([Output('mp-stats', 'children'),],
                  [Input('mp-interval-4', 'n')],
                  [State('url', 'pathname')])

    def update_front_row(n, pathname):

        wallet = unquote(pathname.lstrip('/'))

        if wallet != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:5], wallet[-5:])
        else:
            short_wallet = wallet

        worker_df = reader.get_latest_worker_samples(True)
        my_worker_df = worker_df[worker_df.Miner == short_wallet]
        my_total_hash = round(my_worker_df.Hashrate[0],)
        my_effort = my_worker_df.Effort[0]
        my_ttf = my_worker_df.TTF[0]
        print('ttf', my_ttf, my_effort, my_total_hash)
        
        block_df = reader.block_df
        block_df['miner'] = block_df['miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)
        block_df['my_wallet'] = block_df['miner'].apply(lambda address: address == wallet)
        my_blocks = block_df[block_df.my_wallet == True]


        ### GATHERING POOL AND YOUR HASH TTF AND EFFORT ###
        pool_effort_text = '{}%'.format(reader.data['poolEffort'])
        pool_ttf_text = '{} Days'.format(reader.data['poolTTF'])
        pool_hash_text = '{} GH/s'.format(reader.data['poolHashrate'])
        
        your_effort_text = '{}%'.format(my_effort)
        your_ttf_text = '{} Days'.format(my_ttf)
        your_hash_text = '{} MH/s'.format(my_total_hash)

        ### CARDS FOR THE ABOVE METRICS
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

        ### GATHER THE NEXT STATS FOR PAYMENT ###
        stats = dbc.Row(justify='center', children=[pool_stats, your_stats])
        return [stats]

    @app.callback([ Output('s1', 'children'), Output('s2', 'children'),],
                  [Input('mp-interval-1', 'n')],
                  [State('url', 'pathname')])

    def update_middle(n, pathname):
        wallet = unquote(pathname.lstrip('/'))

        ### PAYMENT STATS ###
        my_payment = reader.get_miner_payment_stats(wallet)

        payment_images ={
            'Pending Shares': 'min-payout.png',
             'Pending Balance': 'triangle.png',
             'Total Paid': 'ergo.png',
             'Last Payment': 'coins.png',
             'Price': 'ergo.png',
             'Schema': 'ergo.png',
            }
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, my_payment[key]), image=payment_images[key]) for key in payment_images.keys() if key != 'lastPaymentLink']

        
        return payment_children[:3], payment_children[3:]
   
    @app.callback([
                 
                    Output('s3', 'children'),],
                  [Input('mp-interval-1', 'n')],
                  [State('url', 'pathname')])

    def update_outside(n, pathname):
        wallet = unquote(pathname.lstrip('/'))

        ### PAYMENT STATS ###
        my_payment = reader.get_miner_payment_stats(wallet)
        all_payment_stats = [reader.get_miner_payment_stats(wallet) for wallet in reader.get_miner_ls()]
        miners = reader.get_miner_ls()
        ls = []
        for miner in miners:
            d = reader.get_miner_payment_stats(miner)
            shares =  d['Pending Shares']
            ls.append([miner, shares])
        
        df = pd.DataFrame(ls, columns=['Miner', 'Shares'])
        total = df.Shares.sum()
        df['participation'] = [shares / total for shares in df.Shares] 
        df['reward'] = df['participation'] * reader.block_reward
        my_df = df[df.Miner == wallet]
        participation = round(my_df['participation'].values[0] * 100, 3)

        my_payment['Participation [%]']= participation

        payment_images ={'Participation [%]': 'smileys.png',
                         'Paid Today': 'ergo.png',
                         'lastPaymentLink': 'ergo.png',
                        }
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, my_payment[key]), image=payment_images[key]) for key in payment_images.keys() if key != 'lastPaymentLink']
        link = html.Div(style=bottom_row_style, children=[
                        html.Img(src='assets/{}'.format('ergo.png'), style=bottom_image_style),
                        html.Span(dcc.Link('Last Payment Link', href=my_payment['lastPaymentLink'], target='_blank'), style={'padding': '10px'})])
        
        payment_children.append(link)

        md = 4
    
        return [payment_children]

    @app.callback([Output('chart', 'figure'),],
                  [Input('mp-interval-2', 'n_intervals')],
                 [State('url', 'pathname')])
    
    def update_charts(n_intervals, pathname):
        wallet = unquote(pathname.lstrip('/'))
        
        block_df = reader.block_df #
        worker_performace = reader.miner_sample_df
        print(worker_performace.columns, 'colz')
        my_worker_performance = worker_performace[worker_performace.miner == wallet]
        print(my_worker_performance)
        

        miner_performance_chart = px.line(my_worker_performance, 
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
        return [miner_performance_chart]
    

    
    @app.callback([Output('table-2', 'data'),
                Output('table-title', 'children'),],
                  [Input('mp-interval-3', 'n_intervals'),
                   Input('table-dropdown', 'value')],
                 [State('url', 'pathname')])
    
    def update_table(n_intervals, table, pathname):
        wallet = unquote(pathname.lstrip('/'))

        if wallet != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:5], wallet[-5:])
        else:
            short_wallet = wallet
    
        if table == 'workers':
            df = reader.get_latest_worker_samples(False)
            df = df[df.miner == wallet]       
            df = df.filter(['worker', 'hashrate', 'sharesPerSecond', 'Effort', 'TTF'])
            df = df.rename(columns={"Effort": "Current Effort [%]", "hashrate": "MH/s", 'TTF': 'TTF [Days]'})
            
            title_2 = 'WORKER DATA'

        elif table == 'blocks':
            block_df = reader.block_df #
            my_block_df = block_df[block_df.miner == wallet]
            df = my_block_df
            print(df.columns)
            df = df.filter(['Time Found', 'blockHeight', 'effort [%]', 'reward [erg]', 'Confirmation [%]'])
            title_2 = 'Your Blocks Found'
            
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        # print(first, second)
        return data, title_2
                                

def get_layout(reader):
    md=4
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': background_color, 'padding': '15px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px'},
                           children=[
                               
                               dcc.Interval(id='mp-interval-1', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='mp-interval-2', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='mp-interval-3', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='mp-interval-4', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': 'white', 'textAlign': 'center',}), 
                               dbc.Row(id='mp-stats', justify='center',),
                               # dbc.Row(id='mp-metrics', justify='center', style={'padding': '20px'}),
                               dbc.Row(justify='center', style={'padding': '20px'}, children=[
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s1')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s2')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s3')],)]),
                                            

                               html.H2('Worker Hashrate Over Time', style={'color': 'white', 'textAlign': 'center',}),
                               dcc.Graph(id='chart', style={'backgroundColor': card_color, 'padding': '20px'}),

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
                               
                       # html.Div(children=[html.H2('Block Statistics'), 
                       dash_table.DataTable(id='table-2',
                                            style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header=table_style,
                                            style_data=table_style,

                                           ),
                           ]),], style={'backgroundColor': card_color})  # This sets the background color for the whole page

if __name__ == '__main__':
    reader = SigmaWalletReader('../conf')
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout(reader)
    setup_front_page_callbacks(app, reader)
    app.run_server(debug=True)