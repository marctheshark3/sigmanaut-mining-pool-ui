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
from utils.find_miner_id import ReadTokens
from utils.shark_api import ApiReader
from utils.get_erg_prices import PriceReader
from utils.calculate import calculate_mining_effort, calculate_time_to_find_block
from datetime import datetime
# sharkapi = ApiReader(config_path="../conf")
priceapi = PriceReader()

debug = False
server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage

button_color = large_text_color
Session(server)


color_discrete_map = {
    'Rolling Effort': 'black', 
    'effort': 'white',      
    'networkDifficulty': large_text_color 
}

def setup_mining_page_callbacks(app, sharkapi):

    @app.callback([Output('s4', 'children'), Output('s5', 'children'), Output('s6', 'children'),],
                  [Input('mp-interval-7', 'n')],
                  [State('url', 'pathname')])
    
    def update_miner_id(n, pathname):
        print('GETTING IDs')
        miner = unquote(pathname.lstrip('/'))
        bins = [[] for _ in range(3)]
        find_tokens = ReadTokens()
        token = find_tokens.get_latest_miner_id(miner)
        if token == None:
            payout_text = 'Min Payout: 0.5 ERG'
            min_payout = create_image_text_block(text=payout_text, image='min-payout.png')
            ad_1_text = 'Consider minting a MINER ID'
            ad_1 = create_image_text_block(text=ad_1_text, image='min-payout.png')
            ad_2_text = 'Swap to ERG Native Tokens'
            ad_2 = create_image_text_block(text=ad_2_text, image='min-payout.png')
            return [min_payout, ad_1, ad_2]
        miner_id = find_tokens.get_token_description(token['tokenId'])
        print(miner_id)
        
        payout_text = 'Minimum Payout: {}'.format(miner_id['minimumPayout'])
        tokens = miner_id['tokens']
        header = html.H1('Miner ID Parameters', style={'color': 'white', 'textAlign': 'center',})

        tokens_swap = [create_image_text_block(text=payout_text, image='min-payout.png')]
        for token in tokens:
            temp_text = '{}: {}%'.format(token['token'], token['value'])
            img = 'ergo.png'
            tokens_swap.append(create_image_text_block(text=temp_text, image=img))
        
        
        for i, func in enumerate(tokens_swap):
            min_bin = min(bins, key=len)
            min_bin.append(func)
        print('COMPLETE')
        return bins[0], bins[1], bins[2]
        
    @app.callback([Output('mp-stats', 'children'),],
                  [Input('mp-interval-4', 'n')],
                  [State('url', 'pathname')])

    def update_front_row(n, pathname):

        miner = unquote(pathname.lstrip('/'))
        wallet = miner

        if miner != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:3], wallet[-5:])
        else:
            short_wallet = wallet
        
        block_data = sharkapi.get_block_stats()
        block_df = pd.DataFrame(block_data)
        pool_data = sharkapi.get_pool_stats()
        try:
            recent_block = max(block_df['created'])
            pool_effort = calculate_mining_effort(pool_data['networkdifficulty'], pool_data['networkhashrate'],
                                         pool_data['poolhashrate'], recent_block)
        except Exception as e:
            pool_effort = 0

        pool_ttf = calculate_time_to_find_block(pool_data['networkdifficulty'], pool_data['networkhashrate'], pool_data['poolhashrate'])
        pool_hash = round(pool_data['poolhashrate'] / 1e9, 2)

        my_data = sharkapi.get_miner_stats(wallet)
        my_hash = round(my_data['current_hashrate'] / 1e6, 2)
        my_recent_block = my_data['last_block_found']['timestamp']
        
        my_effort = calculate_mining_effort(pool_data['networkdifficulty'], pool_data['networkhashrate'],
                                         my_hash * 1e6, my_recent_block)

        my_ttf = calculate_time_to_find_block(pool_data['networkdifficulty'], pool_data['networkhashrate'], my_hash * 1e6)
    
        ### GATHERING POOL AND YOUR HASH TTF AND EFFORT ###
        pool_effort_text = '{}%'.format(pool_effort)
        pool_ttf_text = '{} Days'.format(pool_ttf)
        pool_hash_text = '{} GH/s'.format(pool_hash)
        
        your_effort_text = '{}%'.format(my_effort)
        your_ttf_text = '{} Days'.format(my_ttf)
        your_hash_text = '{} MH/s'.format(my_hash)

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
        miner_data = sharkapi.get_miner_stats(wallet)

        total_paid = miner_data['total_paid']
        miner_data['pendingshares'] = 'TBD'
        miner_data['price [$]'] = round(priceapi.get()[1], 3)
        miner_data['schema'] = 'PPLNS'
        try:
            miner_data['last_payment'] = miner_data['last_payment']['date'][:10]
        except Exception:
            miner_data['last_payment'] = 'Keep Mining!'
        miner_data['total_paid'] = round(miner_data['total_paid'], 3)

        payment_images ={
            'pendingshares': 'min-payout.png',
             'balance': 'triangle.png',
             'total_paid': 'ergo.png',
             'last_payment': 'coins.png',
             'price [$]': 'ergo.png',
             'schema': 'ergo.png',
            }
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, miner_data[key]), image=payment_images[key]) for key in payment_images.keys() if key != 'lastPaymentLink']

        
        return payment_children[:3], payment_children[3:]
   
    @app.callback([
                 
                    Output('s3', 'children'),],
                  [Input('mp-interval-1', 'n')],
                  [State('url', 'pathname')])

    def update_outside(n, pathname):
        miner = unquote(pathname.lstrip('/')) 

        miner_data = sharkapi.get_miner_stats(miner)

        miner_data['Participation [%]'] = -1
        miner_data['tx_link'] = miner_data['last_payment']['tx_link']
        miner_data['paid_today'] = round(miner_data['paid_today'], 2)
        images ={'Participation [%]': 'smileys.png',
                         'paid_today': 'ergo.png',
                         'tx_link': 'ergo.png',
                        }
        
        payment_children = [create_image_text_block(text='{}: {}'.format(key, miner_data[key]), image=images[key]) for key in images.keys() if key != 'tx_link']
        if miner_data['tx_link']:
            link = html.Div(style=bottom_row_style, children=[
                            html.Img(src='assets/{}'.format('ergo.png'), style=bottom_image_style),
                            html.Span(dcc.Link('Last Payment Link', href=miner_data['tx_link'], target='_blank'), style={'padding': '10px'})])
            
            payment_children.append(link)

        md = 4
    
        return [payment_children]

    @app.callback([Output('chart', 'figure'),Output('chart-title', 'children'),],
                  [Input('mp-interval-2', 'n_intervals'),
                  Input('chart-dropdown', 'value')],
                 [State('url', 'pathname')])
    
    def update_charts(n_intervals, chart, pathname):
        wallet = unquote(pathname.lstrip('/'))

        if chart == 'workers':
            workers_data = sharkapi.get_miner_workers(wallet)
            rows = []
            for worker, data in workers_data.items():
                for entry in data:
                    rows.append({
                        'worker': worker,
                        'created': datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')),
                        'hashrate': entry['hashrate'] / 1e6,
                        'sharesPerSecond': entry['sharesPerSecond']
                    })
        
            # Create the DataFrame
            df = pd.DataFrame(rows)

            df.sort_index(inplace=True)
            try:
                miner_performance_chart = px.line(df, 
                      x='created', 
                      y='hashrate', 
                      color='worker', 
                      labels={'hashrate': 'Mh/s', 'created': 'Time'},
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
            except ValueError:
                return [{}, 'NO RECENT HASH']
            return [miner_performance_chart, 'WORKER HASHRATE OVER TIME']

        elif chart == 'payments':
            workers_data = sharkapi.get_miner_payment_stats(wallet)
            df = pd.DataFrame(workers_data)
  
            try:
                df = df.sort_values('created')
            except Exception as e:
                # return [[None], 'PAYMENT OVER TIME']
                df = pd.DataFrame(columns=['created', 'amount'])
            
    
            payment_chart = px.line(df, 
                  x='created', 
                  y='amount', 
                  labels={'amount': 'Paid [ERG]', 'created': 'Date'},
                  markers=True)
    
            payment_chart.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(font=dict(color='#FFFFFF')),
                titlefont=dict(color='#FFFFFF'),
                xaxis=dict(title='Date', color='#FFFFFF',showgrid=False, showline=False, zeroline=False),
                yaxis=dict(title='Paid [ERG]', color='#FFFFFF')
            )
            return [payment_chart, 'PAYMENT OVER TIME']
            
    

    
    @app.callback([Output('table-2', 'data'),
                Output('table-title', 'children'),],
                  [Input('mp-interval-3', 'n_intervals'),
                   Input('table-dropdown', 'value')],
                 [State('url', 'pathname')])
    
    def update_table(n_intervals, table, pathname):
        wallet = unquote(pathname.lstrip('/'))

        if wallet != 'Enter Your Address':
            short_wallet = '{}...{}'.format(wallet[:3], wallet[-5:])
        else:
            short_wallet = wallet
    
        if table == 'workers':
            workers_data = sharkapi.get_miner_stats(wallet)
            pool_data = sharkapi.get_pool_stats()
            df = pd.DataFrame(workers_data['workers'])

            try:
                last_block_found = workers_data['last_block_found']['timestamp']
                df['effort'] =  [calculate_mining_effort(pool_data['networkdifficulty'], pool_data['networkhashrate'],
                                         hash, last_block_found) for hash in df.hashrate]
                
            except Exception as e:
                print(e, 'EXCEPTION')
                df['effort'] = 'TBD'

            df['ttf'] = [calculate_time_to_find_block(pool_data['networkdifficulty'], pool_data['networkhashrate'],
                                     hash) for hash in df.hashrate]
            df['hashrate'] = round(df['hashrate'] / 1e6, 2)
            df = df.rename(columns={"effort": "Current Effort [%]", "hashrate": "MH/s", 'ttf': 'TTF [Days]'})
            
            title_2 = 'WORKER DATA'

        elif table == 'blocks':
            title_2 = 'Your Blocks Found'
            data = sharkapi.get_my_blocks(wallet)
            df = pd.DataFrame(data)

            if df.empty:
                return [], title_2
           
            df['effort'] = round(100 * df['effort'], 2)
            df = df.filter(['created', 'blockheight', 'effort', 'reward', 'confirmationprogress'])
            df = df.rename(columns={'created': 'Time Found', 'blockheight': 'Height',
                                    'effort': 'Effort [%]', 'confirmationprogress': 'Confirmation [%]'})
            
            
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        return data, title_2

    @app.callback([
                   Output('mp-banners', 'children'),
                  ],
                  [Input('mp-interval-5', 'n_intervals')])
    def update_banners(n): 
        # df = db_sync.db.fetch_data('block')
        # bf = df[df.time_found == max(df.time_found)]
        # confirmation_number = bf.confirmationprogress.item()
        confirmation_number = 100
        flag = False
        if confirmation_number < 50:
            flag = True

        if flag:
            banners = [html.Img(src='assets/block_found.gif', style={'height': 'auto%', 'width': 'auto'})]
        elif not flag:
            banners = []

        return [dbc.Row(id='mp-banners', justify='center', children=banners)]
                                

def get_layout(sharkapi):
    md=4
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': background_color, 'padding': '15px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px'},
                           children=[
                               
                               dcc.Interval(id='mp-interval-1', interval=60*1000*5, n_intervals=0),
                               dcc.Interval(id='mp-interval-2', interval=60*1000*5, n_intervals=0),
                               dcc.Interval(id='mp-interval-3', interval=60*1000*5, n_intervals=0),
                               dcc.Interval(id='mp-interval-4', interval=60*1000*5, n_intervals=0),
                               dcc.Interval(id='mp-interval-5', interval=60*1000*5, n_intervals=0),
                               dcc.Interval(id='mp-interval-7', interval=60*1000*5, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': 'white', 'textAlign': 'center',}), 
                               dbc.Row(id='mp-stats', justify='center',),
                               # dbc.Row(id='mp-metrics', justify='center', style={'padding': '20px'}),
                               dbc.Row(justify='center', style={'padding': '20px'}, children=[
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s1')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s2')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s3')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s4')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s5')],),
                                            dbc.Col(md=md, style={'padding': '7px'}, children=[dbc.Card(style=bottom_row_style, id='s6')],),
                               
                               ]),
                                            
                               dbc.Row(id='mp-banners', justify='center'),       

                               html.Div(
                                    [
                                        html.Div(
                                            html.H1(
                                                id='chart-title',
                                                children='Please select an option',
                                                style={'fontSize': '24px'}
                                            ),
                                            style={'flex': '1'}
                                        ),
                                        html.Div(
                                            dcc.Dropdown(
                                                id='chart-dropdown',
                                                options=[
                                                    {'label': 'Worker Hashrate Over Time', 'value': 'workers'},
                                                    {'label': 'Payment Over Time', 'value': 'payments'}
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

# if __name__ == '__main__':
#     reader = SigmaWalletReader('../conf')
#     app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
#     app.layout = get_layout(reader)
#     setup_front_page_callbacks(app, reader)
#     app.run_server(debug=True)