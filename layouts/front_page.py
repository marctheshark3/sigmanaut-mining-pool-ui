import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.reader import SigmaWalletReader, PriceReader
price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")

data = sigma_reader.get_front_page_data()

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

image_style = {'height': '48px', 'marginRight': '10px',}
icon_text_style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start', 'color': 'white', 'padding': '10px', 'marginBottom': '10px'}

# refactor this into dash_utils
def create_image_text_block(image, text):
    cell = html.Div(style=metric_row_style, children=[
                    html.Img(src='assets/{}'.format(image), style=image_style),
                    html.Span(text, style={'padding': '10px'})
                ])
    return cell
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

def get_layout():
    return dbc.Container(fluid=True, style={'backgroundColor': '#1e1e1e', 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif'},
                           children=[html.H1('ERGO Sigmanaut Mining Pool', style={'color': '#FFA500', 'textAlign': 'center',}),
                                     # Metrics overview row
                                     dbc.Row(justify='center', style={'padding': '20px'}, children=[
                                         dbc.Col(dbc.Card(style=top_card_style, children=[
                                             html.Img(src='assets/mining_temp.png', style=top_image_style),
                                             html.H2(hashrate, style={'color': '#FFA500'}),
                                             html.P("Hashrate")]),
                                                 width=3, lg=3, style={'marginRight': '5px', 'marginLeft': '5px'}),
        
                                    dbc.Col(dbc.Card(style=top_card_style, children=[
                                        html.Img(src='assets/mining_temp.png', style=top_image_style),
                                        html.H2(n_miners, style={'color': '#FFA500'}),
                                        html.P("Miners")
                                    ]), width=3, lg=3, style={'marginRight': '5px', 'marginLeft': '5px'}),
                            
                                    dbc.Col(dbc.Card(style=top_card_style, children=[
                                        html.Img(src='assets/mining_temp.png', style=top_image_style),
                                        html.H2('$1.9', style={'color': '#FFA500'}),
                                        html.P("Price")
                                    ]), width=3, lg=3, md=6,style={'marginRight': '5px', 'marginLeft': '5px'}),
                                    
                                ]),
                                    # Detailed stats
                                    dbc.Row(justify='center', style={'padding': '20px'}, children=[
                                        dbc.Col(md=6, children=[
                                            dbc.Card(style=card_style, children=[
                                                html.H3('Pool Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}),
                                                create_image_text_block('mining_temp.png', 'Algo: Autolykos V2'),
                                                create_image_text_block('mining_temp.png', 'Current Reward: 30'),
                                                # create_image_text_block('mining_temp.png', 'Price: $1.9'),
                                                create_image_text_block('mining_temp.png', paid),
                                                create_image_text_block('mining_temp.png', payout_schema),
                                                create_image_text_block('mining_temp.png', min_payout),
                                            ])
                                        ]),
                                        
                                        dbc.Col(md=6, children=[
                                            dbc.Card(style=card_style, children=[
                                                html.H3('Network Stats', style={'color': '#FFA500', 'fontWeight': 'bold'}),
                                
                                                create_image_text_block('mining_temp.png', difficulty),
                                                create_image_text_block('mining_temp.png', net_block_found),
                                                create_image_text_block('mining_temp.png', height),
                                                
                                            ])
                                        ]),
                                    ]),
                                
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
                                    html.H1('CONNECTING TO THE POOL', style={'color': '#FFA500', 'textAlign': 'center',}),
                                
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
                                    ],style={'backgroundColor': '#333333', 'color': 'white', 'padding': '20px', 'code': {'color': '#333333'}}),

    
])

if __name__ == '__main__':

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    app.run_server(debug=True)
