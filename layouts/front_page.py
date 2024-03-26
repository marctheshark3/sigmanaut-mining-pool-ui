import dash
from dash import html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
from utils.reader import SigmaWalletReader, PriceReader
import plotly.graph_objs as go
from dash import html
price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")

data = sigma_reader.get_front_page_data()
_, ergo = price_reader.get(debug=True)
# Pool Metrics
fee = 'Pool Fee: {}%'.format(data['fee'])
paid = 'Cumulative Payments: {}'.format(data['paid'])
blocks_found = 'Blocks Found: {}'.format(data['blocks'])
last_block = 'Last Block Found: {}'.format(data['last_block_found'])
effort= 'Current Pool Effort: {}'.format(data['pool_effort'])
min_payout = 'Minimum Payout: {}'.format(data['minimumPayment'])

payout_schema = 'Pool Payout Schema: {}'.format(data['payoutScheme'])
n_miners = '{}'.format(data['connectedMiners'])
hashrate = '{} GH/s'.format(round(data['poolHashrate'], 3))

# Network Metrics
net_hashrate = 'Network Hashrate: {} TH/s'.format(data['networkHashrate'])
difficulty = 'Network Difficulty: {}P'.format(round(data['networkDifficulty'], 3))
net_block_found = 'Last Block Found on Network: {}'.format(data['lastNetworkBlockTime'])
height = 'Height: {}'.format(data['blockHeight'])

# icon_text_style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start', 'color': 'white', 'padding': '10px', 'marginBottom': '10px'}

# refactor this into dash_utils
def create_image_text_block(image, text):
    return html.Div(style=metric_row_style, children=[
                    html.Img(src='assets/{}'.format(image),
                             style=image_style),
                    html.Span(text, style={'padding': '10px'})])

# Style for the card containers
card_style = {
    'backgroundColor': '#333333',
    'color': 'white',
    'marginBottom': '25px',
    'padding': '25px',
    'justifyContent': 'center',
}

top_card_style = {
    'backgroundColor': '#333333',
    'color': 'white',
    'marginBottom': '25px',
    'padding': '25px',
    'justifyContent': 'center',
    'textAlign': 'center'
}

top_image_style = {'height': '75px', 'padding': '10px'}

# Style for the metric rows inside the cards
metric_row_style = {
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'flex-start',
}

image_style = {'height': '24px'}

def create_row_card(image, h2_text, p_text):
    return dbc.Col(dbc.Card(style=top_card_style, children=[
        html.Img(src=image, style=top_image_style),
        html.H2(h2_text, style={'color': '#FFA500'}),
        html.P(p_text)]),
                   style={'marginRight': 'auto', 'marginLeft': 'auto'})

def setup_front_page_callbacks(app):
    
    @app.callback([Output('a-1', 'children'),
                   Output('a-2', 'children'),
                  Output('total-hashrate-plot', 'figure'),
                  Output('front-page-block-stats', 'data'),],
                  [Input('front-page-interval', 'n_intervals')])
    def update_content(n):
        # if not n or n > 1:
        print('UPDATING FRONT PAGE')
        price_reader = PriceReader()
        sigma_reader = SigmaWalletReader(config_path="../conf")

        data = sigma_reader.get_front_page_data()
        _, ergo = price_reader.get(debug=True)
        # Pool Metrics
        fee = 'Pool Fee: {}%'.format(data['fee'])
        paid = 'Cumulative Payments: {} ERG'.format(round(data['paid'], 3))
        blocks_found = 'Blocks Found: {}'.format(data['blocks'])
        last_block = 'Last Block Found: {}'.format(data['last_block_found'])
        effort = 'Current Block Effort: {}%'.format(round(data['pool_effort'] * 100, 3))
        min_payout = 'Minimum Payout: {}'.format(data['minimumPayment'])
        # print(data)

        payout_schema = 'Pool Payout Schema: {}'.format(data['payoutScheme'])
        n_miners = '{}'.format(data['connectedMiners'])
        hashrate = '{} GH/s'.format(round(data['poolHashrate'], 3))

        # Network Metrics
        net_hashrate = 'Network Hashrate: {} TH/s'.format(round(data['networkHashrate'], 3))
        difficulty = 'Network Difficulty: {}P'.format(round(data['networkDifficulty'], 3))
        net_block_found = 'Last Block Found on Network: {}'.format(data['lastNetworkBlockTime'])
        height = 'Current Height: {}'.format(data['blockHeight'])

        total_hashrate_df = sigma_reader.get_total_hash()
        block_df, miner_df, effort_df = sigma_reader.get_block_stats('')
        block_df = block_df.filter(['Time Found', 'blockHeight', 'miner', 'effort', 'reward'])
        block_data = block_df.to_dict('records')

        total_hashrate_plot={'data': [go.Scatter(x=total_hashrate_df['Date'], y=total_hashrate_df['Hashrate'],
                                    mode='lines+markers', name='Hashrate Over Time', line={'color': '#00CC96'})],
                   
                   'layout': go.Layout(
                                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       margin={'l': 40, 'b': 40, 't': 50, 'r': 50}, hovermode='closest',
                                       legend={'font': {'color': '#FFFFFF'}}, font=dict(color='#FFFFFF'))}

        row_1 = dbc.Row(justify='center',
                        children=[create_row_card('assets/mining_temp.png', hashrate, 'Pool Hashrate'),
                                 create_row_card('assets/mining_temp.png', n_miners, 'Miners Online'),
                                 create_row_card('assets/mining_temp.png', ergo, 'Price ($)')])
        md = 4
        row_2_col_1 = dbc.Row(justify='center', children=[
                                dbc.Col(md=md, children=[
                                    dbc.Card(style=card_style, children=[
                                        # html.H3('Pool Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}),
                                        # create_image_text_block('mining_temp.png', 'Algo: Autolykos V2'),
                                        create_image_text_block('mining_temp.png', min_payout),
                                        create_image_text_block('mining_temp.png', fee),
                                        create_image_text_block('mining_temp.png', paid),
                                    ])
                                ]),
                                dbc.Col(md=md, children=[
                                    dbc.Card(style=card_style, children=[
                                        # html.H3('Pool Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}),
                                        create_image_text_block('mining_temp.png', net_hashrate),
                                        create_image_text_block('mining_temp.png', difficulty),
                                        create_image_text_block('mining_temp.png', height),
                                       ])
                                ]),

                                dbc.Col(md=md, children=[
                                    dbc.Card(style=card_style, children=[
                                        # html.H3('Network Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}),
                                        create_image_text_block('mining_temp.png', payout_schema),
                                        create_image_text_block('mining_temp.png', blocks_found),
                                        create_image_text_block('mining_temp.png', effort),

                                    ])
                                ])])

        return row_1, row_2_col_1, total_hashrate_plot, block_data
        # else:
        #     return ([], [])
                 


def get_layout():
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': '#1e1e1e', 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px' },
                           children=[
                               dcc.Interval(id='front-page-interval', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': '#FFA500', 'textAlign': 'center',}),                                   
                                 # Metrics overview row
                                 dbc.Row(id='a-1', justify='center', style={'padding': '20px'}),

                                # Detailed stats
                                dbc.Row(id='a-2', justify='center', style={'padding': '20px'}),

                                # Start Mining Button
                                dbc.Row(justify='center', children=[
                                    html.Button('Start Mining ⛏️', id='start-mining-button', style={
                                        'marginTop': '20px',
                                        'backgroundColor': '#FFA500',
                                        'border': 'none',
                                        'padding': '10px 20px',
                                        'color': 'white',
                                        'fontSize': '20px',
                                        'borderRadius': '5px'
                                    })
                                ]),

                                # Mining Address Input
                                dbc.Row(justify='center', children=[
                                    dbc.Col(md=8, children=[
                                        dcc.Input(id='mining-address-input', type='text', placeholder='Mining Address', style={
                                            'width': '100%',
                                            'padding': '10px',
                                            'marginTop': '20px',
                                            'marginBottom': '50px',
                                            'borderRadius': '5px'
                                        }),
                                    ])
                                ]),
                               # dcc.Graph(id='total-hashrate-plot'),
                               dbc.Row(children=[
                                   html.Div(children=[html.H2('Pool Hashrate over Time'),
                                                      dcc.Graph(id='total-hashrate-plot'),],
                                            style={'flex': 1,}),]),

                               html.Div(children=[html.H2('Block Statistics'), 
                       dash_table.DataTable(id='front-page-block-stats',
                                            style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white',
                                                          'fontWeight': 'bold', 'textAlign': 'center',},
                                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',
                                                        'border': '1px solid black',},)]),

                               
                               html.H1('CONNECTING TO THE POOL', style={'color': '#FFA500', 'textAlign': 'center', 'padding': '10px',}),

                                # Column for the markdown
                                html.Div(children=[
                                    dcc.Markdown('''
                                        ## Choose A Port
                                        Based on your hashrate and TLS specificity choose the port that is right for you. 

                                        - Port 3052 - Lower than 10GH/s - No TLS
                                        - Port 3053 - Higher than 10GH/s - No TLS
                                        - Port 3054 - Lower than 10GH/s - TLS
                                        - Port 3055 - Higher than 10GH/s - TLS

                                        ### Connecting to the Pool
                                        The pools url is 15.204.211.130

                                        So if you want TLS and under 10GH/s the port you would choose is 3054 and so on

                                        #### HIVEOS
                                        1. Set "Pool URL" to 15.204.211.130:3054 

                                        #### MMPOS
                                        1. Modify an existing or create a new pool in Management
                                        2. In Hostname enter the URL: 15.204.211.130
                                        3. Port: 3054

                                        #### Linux or Windows
                                        1. Edit the .sh file for the specific miner, in this case lolminer
                                        2. In the pool argument enter the full url with port of choice
                                        ```
                                        POOL=15.204.211.130:3054
                                        WALLET=<your_wallet_address>.QX-Fan-Club
                                        ./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
                                        while [ $? -eq 42 ]; do
                                        sleep 10s
                                        ./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
                                        done
                                        ```

                                        ## Updating the Dashboard from git
                                        ```
                                        docker compose pull # pulls the latest docker image
                                        docker compose up -d # Runs the UI
                                        docker compose down # Stops the UI
                                        ```

                                        Shout out to Vipor.Net for the dashboard inspiration! 
                                        ''')
                                ],
                                         style={'backgroundColor': '#333333', 'color': 'white', 'padding': '20px', 'code': {'color': '#333333'}})])],
    style={'backgroundColor': '#2a2a2a'}  # This sets the background color for the whole page
)

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    setup_front_page_callbacks(app)
    app.run_server(debug=True)
