'''
INITIAL USER PAGE METRICS:
- TOTAL HASHRATE
- TOTAL MINERS
- ALGO
- Reward
- Pool Fee
- Min Payout
- Difficulty
- Amount Paid
- Place to enter address


Algo: VerusHash
Height: 2968098
Reward: 6
Min Pay: 0.001

Fee: 0.8%
Difficulty: 63 M
Price: 0.98336100
Paid:$58.50K (59,489.7 ) 
'''

import dash
from dash import html, dcc, dash_table
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
n_miners = 'Connected Miners: {}'.format(data['connectedMiners'])
hashrate = 'Pool Hashrate: {} GH/s'.format(data['poolHashrate'])

# Network Metrics
net_hashrate = 'Network Hashrate: {} TH/s'.format(data['networkHashrate'])
difficulty = 'Network Difficulty: {}'.format(data['networkDifficulty'])
net_block_found = 'Last Block Found on Network: {}'.format(data['lastNetworkBlockTime'])
height = 'Height: {}'.format(data['blockHeight'])

image_style = {'height': '48px', 'marginRight': '10px',}
icon_text_style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start', 'color': 'white', 'padding': '10px', 'marginBottom': '10px'}

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(style={'backgroundColor': '#1e1e1e', 'color': '#ffffff', 'padding': '50px', 'fontFamily': 'sans-serif'}, children=[
    # Header
    html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}, children=[
        
        html.H1('Sigmanaut Mining Pool - ERGO', style={'color': '#00ddff'}),
        html.Div(style={'display': 'flex', 'gap': '20px'}),
    ]),

    html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}, children=[
        html.Div(style={'textAlign': 'center'}, children=[
        html.Img(src='assets/mining_temp.png', style={'height': '50px', 'marginRight': '10px'}),
        html.H2(hashrate, style={'color': '#00ddff'}),]),

        html.Div(style={'textAlign': 'center'}, children=[
        html.Img(src='assets/mining_temp.png', style={'height': '50px', 'marginRight': '10px'}),
        html.H2(n_miners, style={'color': '#00ddff'}),]),
       
    ]),
    
    # Content
    html.Div(style={'display': 'flex', 'marginTop': '20px',}, children=[
        # Left Column
        html.Div(style={'display': '1', 'alignItems': 'center', 'justifyContent': 'flex-start',}, children=[
            html.H2('Pool Stats', style={'color': '#FFA500'}),
            html.Div(className="metric", style=icon_text_style, children=[
                
                html.Img(src='assets/mining_temp.png', style=image_style),
                html.Span("Algo: Autolykos V2")
                ]),
                
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span("Current Reward: 30")
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span("Price: $1.9")
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span("Price: $1.9")
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span(paid)
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span(payout_schema)
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span(min_payout)
                ]),
            
        ]),
        # Right Column
        html.Div(style={'flex': '1'}, children=[
            html.H2('Network Stats', style={'color': '#FFA500'}),
            html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span(net_hashrate)
                ]),
            
            html.Div(className="metric", style=icon_text_style, children=[
                html.Img(src='assets/mining_temp.png', style=image_style),
                html.Span(difficulty)
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span(net_block_found)
                ]),
                html.Div(className="metric", style=icon_text_style, children=[
                    html.Img(src='assets/mining_temp.png', style=image_style),
                    html.Span(height)
                ]),
        ]),
    ]),

    # Start Mining Button
    html.Button('Start Mining ⛏️', style={'marginTop': '20px', 'backgroundColor': '#00ddff', 'border': 'none', 'padding': '10px 20px', 'color': 'white'}),

    # Mining Address Input
    html.Div(style={'marginTop': '20px'}, children=[
        dcc.Input(type='text', placeholder='Mining Address', style={'width': '100%', 'padding': '10px', }),
    ]),
    html.H1('CONNECTING TO THE POOL', style={'color': '#00ddff'}),

   html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}, children=[
        
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
                1. edit the .sh file for the specific miner, in this case lolminer
                2. n the pool argument enter the full url with port of choice
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
        ],style={'backgroundColor': '#333333', 'color': 'white', 'padding': '20px'}),
   ]),
])

if __name__ == '__main__':
    app.run_server(debug=True)
