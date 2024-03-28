import dash
from dash import html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
from utils.reader import SigmaWalletReader, PriceReader
from pandas import DataFrame
import plotly.graph_objs as go
from dash import html
price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")

debug = True
data = sigma_reader.get_front_page_data()
_, ergo = price_reader.get(debug=debug)
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

card_color = '#27374D'
background_color = '#526D82'
large_text_color = '#9DB2BF' 
small_text_color = '#DDE6ED'
button_color = large_text_color


# refactor this into dash_utils
def create_image_text_block(image, text, value):
    return html.Div(style=metric_row_style, children=[
                    html.Img(src='assets/{}'.format(image), style=image_style),
                    html.Span(text, style={'padding': '10px', 'color': 'white'}),
                    html.Span(value, style={'color': large_text_color})])

# Style for the card containers
card_style = {
    'backgroundColor': card_color,
    'color': small_text_color,
    # 'marginBottom': '25px',
    'padding': '25px',
    'justifyContent': 'center',
    'border': '1px solid {}'.format(large_text_color),
}

top_card_style = {
    'backgroundColor': card_color,
    'color': small_text_color,
    'marginBottom': '15px',
    'padding': '25px',
    'justifyContent': 'center',
    'textAlign': 'center',
    'border': '1px solid {}'.format(large_text_color),
}

top_image_style = {'height': '150px', 'padding': '10px'}

# Style for the metric rows inside the cards
metric_row_style = {
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'flex-start',
    'fontSize': '13px',
}

table_style = {'backgroundColor': 'rgb(50, 50, 50)', 'color': large_text_color,
               'fontWeight': 'bold', 'textAlign': 'center', 'border': '1px solid black',}

image_style = {'height': '24px'}

def create_row_card(image, h2_text, p_text):
    return dbc.Col(dbc.Card(style=top_card_style, children=[
        html.Img(src=image, style=top_image_style),
        html.H2(h2_text, style={'color': large_text_color}),
        html.P(p_text)]), style={'marginRight': 'auto', 'marginLeft': 'auto'})

def setup_front_page_callbacks(app):
    
    @app.callback([Output('a-1', 'children'),
                   Output('a-2', 'children'),
                   Output('total-hashrate-plot', 'figure'),
                   Output('table', 'data'),
                   Output('dropdown-title', 'children'),
                  ],
                  [Input('front-page-interval', 'n_intervals'),
                  Input('dataset-dropdown', 'value')])

    def update_content(n, selected_data):
        # if not n or n > 1:
        print('UPDATING FRONT PAGE')
        price_reader = PriceReader()
        sigma_reader = SigmaWalletReader(config_path="../conf")
 
        data = sigma_reader.get_front_page_data()
        _, ergo = price_reader.get(debug=debug)
        # Pool Metrics
        fee = 'Pool Fee: {}%'.format(data['fee'])
        paid = 'Total Paid: {} ERG'.format(round(data['paid'], 3))
        blocks_found = 'Blocks Found: {}'.format(data['blocks'])
        last_block = 'Last Block Found: {}'.format(data['last_block_found'])
        effort = 'Current Block Effort: {}%'.format(round(data['pool_effort'] * 100, 3))
        min_payout = 'Minimum Payout: {}'.format(data['minimumPayment'])
        # print(data)

        payout_schema = 'Schema: {}'.format(data['payoutScheme'])
        n_miners = '{}'.format(data['connectedMiners'])
        hashrate = '{} GH/s'.format(round(data['poolHashrate'], 3))

        # Network Metrics
        net_hashrate = 'Net Hashrate: {} TH/s'.format(round(data['networkHashrate'], 3))
        difficulty = 'Net Difficulty: {}P'.format(round(data['networkDifficulty'], 3))
        net_block_found = 'Last Block Found on Network: {}'.format(data['lastNetworkBlockTime'])
        height = 'Height: {}'.format(data['blockHeight'])

        total_hashrate_df = sigma_reader.get_total_hash()
        top_miner_df = sigma_reader.get_all_miner_data('')
        block_df, miner_df, effort_df = sigma_reader.get_block_stats('')
        block_df = block_df.filter(['Time Found', 'blockHeight', 'miner', 'effort', 'reward', 'status'])
        
        block_data = block_df.to_dict('records')

        total_hashrate_df = total_hashrate_df.sort_values(['Date'])

        total_hashrate_plot={'data': [go.Scatter(x=total_hashrate_df['Date'], y=total_hashrate_df['Hashrate'],
                                    mode='lines+markers', name='Hashrate Over Time', line={'color': card_color})],
                   
                   'layout': go.Layout(xaxis =  {'showgrid': False},yaxis = {'showgrid': True},        
                                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       margin={'l': 40, 'b': 40, 't': 50, 'r': 50}, hovermode='closest',
                                       legend={'font': {'color': '#FFFFFF'}}, font=dict(color=card_color))}

        row_1 = dbc.Row(justify='center',
                        children=[create_row_card('assets/mining_temp.png', hashrate, 'Pool Hashrate'),
                                 create_row_card('assets/mining_temp.png', n_miners, 'Miners Online'),
                                 create_row_card('assets/mining_temp.png', ergo, 'Price ($)')])
        md = 4
        row_2_col_1 = dbc.Row(justify='center', children=[
                                dbc.Col(md=md, children=[
                                    dbc.Card(style=card_style, children=[
                                        create_image_text_block('mining_temp.png', 'Minimum Payout:', data['minimumPayment']),
                                        create_image_text_block('mining_temp.png', 'Pool Fee:', '{}%'.format(data['fee'])),
                                        create_image_text_block('mining_temp.png', 'Total Paid:', '{} ERG'.format(round(data['paid'], 3))),
                                    ])
                                ]),
                                dbc.Col(md=md, children=[
                                    dbc.Card(style=card_style, children=[
                                        create_image_text_block('mining_temp.png', 'Network Hashrate:',
                                                                '{} TH/s'.format(round(data['networkHashrate'], 3))),
                                        create_image_text_block('mining_temp.png', 'Network Difficulty:',
                                                                '{}P'.format(round(data['networkDifficulty'], 3))),
                                        create_image_text_block('mining_temp.png', 'Block Height:', data['blockHeight']),
                                       ])
                                ]),

                                dbc.Col(md=md, children=[
                                    dbc.Card(style=card_style, children=[
                                        create_image_text_block('mining_temp.png', 'Schema:', data['payoutScheme']),
                                        create_image_text_block('mining_temp.png', 'Blocks Found:', data['blocks']),
                                        create_image_text_block('mining_temp.png', 'Effort:', round(data['pool_effort'], 3)),
                                    ])
                                ])])

        if selected_data == 'blocks':
            df = block_df
            title = 'Blocks Data'
        elif selected_data == 'miners':
            ls = []
            for miner in top_miner_df.miner.unique():
                temp = top_miner_df[top_miner_df.miner == miner]
                ls.append([miner, temp.hashrate.sum(), temp.sharesPerSecond.sum()])
            
            df = DataFrame(ls, columns=['Miner', 'Hashrate', 'SharesPerSecond'])
            title = 'Current Top Miners'

        else:
            df = DataFrame()  # Empty dataframe as a fallback
            title = 'Please select an option'
        
        columns = [{"name": i, "id": i} for i in df.columns]
        table_data = df.to_dict('records')
        
        return row_1, row_2_col_1, total_hashrate_plot, table_data, title


def get_layout():
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': background_color, 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px' },
                           children=[
                               dcc.Interval(id='front-page-interval', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': large_text_color, 'textAlign': 'center',}),                                   
                                 # Metrics overview row
                                 dbc.Row(id='a-1', justify='center', style={'padding': '5px'}),

                                # Detailed stats
                                dbc.Row(id='a-2', justify='center', style={'padding': '5px'}),

                               # Mining Address Input
                                dbc.Row(justify='center', children=[
                                    dbc.Col(md=8, children=[
                                        dcc.Input(id='mining-address-input', type='text', placeholder='Mining Address', style={
                                            'width': '100%',
                                            'padding': '10px',
                                            'marginTop': '20px',
                                            'borderRadius': '5px'
                                        }),
                                    ])
                                ]),

                                # Start Mining Button
                                dbc.Row(justify='center', children=[
                                    html.Button('Start Mining ⛏️', id='start-mining-button', style={
                                        'marginTop': '20px',
                                        'backgroundColor': button_color,
                                        'border': 'none',
                                        'padding': '10px 20px',
                                        'color': 'white',
                                        'fontSize': '20px',
                                        'borderRadius': '5px',
                                         'marginBottom': '50px',
                                    })
                                ]),
                                
                               # dcc.Graph(id='total-hashrate-plot'),
                               dbc.Row(children=[
                                   html.Div(children=[html.H2('Pool Hashrate over Time - [GH/s]'),
                                                      dcc.Graph(id='total-hashrate-plot'),],
                                            style={'flex': 1,}),]),

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
                                                id='dataset-dropdown',
                                                options=[
                                                    {'label': 'Block-Stats', 'value': 'blocks'},
                                                    {'label': 'Top-Miners', 'value': 'miners'}
                                                ],
                                                value='blocks',  # Default value
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
                       

                       dash_table.DataTable(id='table',
                                            style_table={'overflowX': 'auto'},
                                            style_cell={'height': 'auto', 'minWidth': '180px',
                                                        'width': '180px', 'maxWidth': '180px',
                                                        'whiteSpace': 'normal', 'textAlign': 'left',
                                                        'padding': '10px',},
                                            style_header=table_style,
                                            style_data=table_style,),

                               
                               html.H1('CONNECTING TO THE POOL',
                                       style={'color': 'white', 'textAlign': 'center', 'padding': '10px',}),

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
                                         style={'backgroundColor': background_color, 'color': 'white', 'padding': '20px', 'code': {'color': card_color}})])],
    style={'backgroundColor': card_color}  # This sets the background color for the whole page
)

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = get_layout()
    setup_front_page_callbacks(app)
    app.run_server(debug=True)
