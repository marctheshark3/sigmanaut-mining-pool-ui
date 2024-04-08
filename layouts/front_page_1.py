import dash
from dash import html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
from utils.api_reader import SigmaWalletReader, PriceReader
from pandas import DataFrame
from utils.dash_utils import metric_row_style, image_style, create_row_card, card_style, image_card_style, bottom_row_style, bottom_image_style, card_color, large_text_color, small_text_color, background_color
import plotly.graph_objs as go
import plotly.express as px

from dash import html
price_reader = PriceReader()
# sigma_reader = SigmaWalletReader(config_path="../conf")

debug = False

button_color = large_text_color


# refactor this into dash_utils
def create_image_text_block(image, text, value):
    return html.Div(style=bottom_row_style, children=[
                    html.Img(src='assets/{}'.format(image), style=bottom_image_style),
                    html.Span(text, style={'padding': '5px', 'color': 'white'}),
                    html.Span(value, style={'padding': '5px', 'color': large_text_color})])

# Style for the card containers
card_style = {
    'backgroundColor': card_color,
    'color': small_text_color,
    'padding': '25px',
    'justifyContent': 'center',
}

top_card_style = {
    'backgroundColor': card_color,
    'color': small_text_color,
    'height': '225px',
    'padding': '15px',
    'justifyContent': 'center',
    'textAlign': 'center',
    'justify': 'center',    
}

top_image_style = {
    'width': '120px',
    'display': 'block',  # Use block display style
    'margin-left': 'auto',  # Auto margins for horizontal centering
    'margin-right': 'auto', 
    'margin-top': 'auto',  # Auto margins for vertical centering (if container allows)
    'margin-bottom': 'auto',
    'max-width': '100%',  # Ensures the image is responsive and does not overflow its container
    'height': 'auto',  # Keeps image aspect ratio
    'padding': '10px'}

# Style for the metric rows inside the cards
metric_row_style = {
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'flex-start',
    'fontSize': '13px',
}

color_discrete_map = {
    'Rolling Effort': 'black', 
    'effort': 'white',      
    'networkDifficulty': large_text_color 
}

table_style = {'backgroundColor': card_color, 'color': large_text_color,
               'fontWeight': 'bold', 'textAlign': 'center', 'border': '1px solid black',}

image_style = {'height': '24px'}

def create_row_card(image, h2_text, p_text):
    return dbc.Col(dbc.Card(style=top_card_style, children=[
        dbc.CardImg(src=image, top=True, style=top_image_style),
        html.H2(h2_text, style={'color': large_text_color}),
        html.P(p_text)]), style={'marginRight': 'auto', 'marginLeft': 'auto'}, width=4,)

def setup_front_page_callbacks(app, reader):
    reader.update_data()

    @app.callback([Output('metric-1', 'children')],
                   [Input('fp-int-4', 'n_intervals')])

    def update_first_row(n):
        reader.update_data()
        data = reader.data
        # data = reader.get_front_page_data() # 
        # _, ergo = price_reader.get(debug=debug)
        ergo = reader.erg_price
        # payout_schema = 'Schema: {}'.format(data['payoutScheme'])
        n_miners = '{}'.format(data['connectedMiners'])
        hashrate = '{} GH/s'.format(round(data['poolHashrate'], 3))

        row_1 = dbc.Row(justify='center', align='stretch',
                        children=[create_row_card('assets/boltz.png', hashrate, 'Pool Hashrate'),
                                 create_row_card('assets/smileys.png', n_miners, 'Miners Online'),
                                 create_row_card('assets/coins.png', ergo, 'Price ($)')])
        return [row_1]
        

    @app.callback([
                   Output('metric-2', 'children'),],
                   [Input('fp-int-1', 'n_intervals')])

    def update_metrics(n):
        # reader.update_data()
        data = reader.data

        md = 4
        row_2 = dbc.Row(children=[
                    dbc.Col(md=md, style={'padding': '10px'}, children=[
                        dbc.Card(style=bottom_row_style, children=[
                            create_image_text_block('min-payout.png', 'Minimum Payout:', data['minimumPayment']),
                            create_image_text_block('percentage.png', 'Pool Fee:', '{}%'.format(data['fee'])),
                            create_image_text_block('ergo.png', 'Total Paid:', '{} ERG'.format(round(data['paid'], 3))),
                        ])
                    ]),
                    dbc.Col(md=md, style={'padding': '10px'}, children=[
                        dbc.Card(style=bottom_row_style, children=[
                            create_image_text_block('bolt.png', 'Network Hashrate:', '{} TH/s'.format(round(data['networkHashrate'], 3))),
                            create_image_text_block('gauge.png', 'Network Difficulty:', '{}P'.format(round(data['networkDifficulty'], 3))),
                            create_image_text_block('height.png', 'Block Height:', data['blockHeight']),
                           ])
                    ]),
    
                    dbc.Col(md=md, style={'padding': '10px'}, children=[
                        dbc.Card(style=bottom_row_style, children=[
                            create_image_text_block('triangle.png', 'Schema:', data['payoutScheme']),
                            create_image_text_block('ergo.png', 'Blocks Found:', data['blocks']),
                            create_image_text_block('ergo.png', 'Current Block Effort:', round(data['poolEffort'], 3)),
                        ])
                    ])])
        return [row_2]
               
    @app.callback([Output('plot-1', 'figure'),Output('plot-title', 'children'),],
                   [Input('fp-int-2', 'n_intervals'), Input('chart-dropdown', 'value')])

    def update_plots(n, value):
        
        if value == 'effort':
            block_df = reader.block_df
            title = 'EFFORT AND DIFFICULTY'
            
            block_df = block_df.sort_values('Time Found')
            # block_df['Rolling Effort'] = block_df['effort'].expanding().mean()
            response_df = block_df.melt(id_vars = ['Time Found'], value_vars=['Rolling Effort', 'effort', 'networkDifficulty'])
            
            effort_response_chart = px.line(response_df[response_df['variable'] != 'networkDifficulty'], 
                                    x='Time Found', 
                                    y='value', 
                                    color='variable', 
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
                xaxis=dict(title='Time Found', color='#FFFFFF',showgrid=False, showline=False),
                yaxis=dict(title='Effort [%]', color='#FFFFFF', side='right'),
                yaxis2=dict(title='Network Difficulty', color='#FFFFFF', overlaying='y'),
            )
            
            return effort_response_chart, title
            
        title = 'HASHRATE OVER TIME'
        total_hashrate_df = reader.get_total_hash_data()
        total_hashrate_df = total_hashrate_df.sort_values(['Date'])
        total_hashrate_df['Hashrate'] = total_hashrate_df['Hashrate']

        total_hashrate_plot={'data': [go.Scatter(x=total_hashrate_df['Date'], y=total_hashrate_df['Hashrate'],
                                    mode='lines+markers', name='Hashrate Over Time', line={'color': small_text_color})],
                   
                   'layout': go.Layout(xaxis =  {'showgrid': False, 'title': 'Snap Shot Time'},yaxis = {'showgrid': True, 'title': 'GH/s'},        
                                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       margin={'l': 40, 'b': 40, 't': 50, 'r': 50}, hovermode='closest',
                                       legend={'font': {'color': '#FFFFFF'}}, font=dict(color=small_text_color))}

        return total_hashrate_plot, title
        
    
    @app.callback([
                   Output('table', 'data'),
                   Output('dropdown-title', 'children'),
                  ],
                  [Input('fp-int-3', 'n_intervals'),
                  Input('dataset-dropdown', 'value')])

    def update_content(n, selected_data):   
        block_df= reader.block_df        
        if selected_data == 'blocks':
            block_df['Confirmation'] = round(block_df['confirmationProgress'], 2)
            
            block_df = block_df.filter(['Time Found', 'blockHeight', 'miner', 'effort [%]', 'reward [erg]', 'Confirmation [%]'])
            
            df = block_df
            df['miner'] = df['miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)
            title = 'Blocks Data'
        elif selected_data == 'miners':
            df = reader.get_latest_worker_samples(totals=True)
            df = df.rename(columns={"Effort": "Current Effort [%]", "Hashrate": "MH/s", 'TTF': 'TTF [Days]'})
            title = 'Current Top Miners'

        else:
            df = DataFrame()  # Empty dataframe as a fallback
            title = 'Please select an option'
        
        columns = [{"name": i, "id": i} for i in df.columns]
        table_data = df.to_dict('records')
        
        return table_data, title


def get_layout(reader):
    return html.Div([dbc.Container(fluid=True, style={'backgroundColor': background_color, 'padding': '10px', 'justifyContent': 'center', 'fontFamily': 'sans-serif',  'color': '#FFFFFF', 'maxWidth': '960px' },
                           children=[
                               dcc.Interval(id='fp-int-1', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='fp-int-2', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='fp-int-3', interval=60*1000, n_intervals=0),
                               dcc.Interval(id='fp-int-4', interval=60*1000, n_intervals=0),

                               html.H1('ERGO Sigmanaut Mining Pool', style={'color': large_text_color, 'textAlign': 'center',}),                                   
                                 # Metrics overview row
                                 dbc.Row(id='metric-1', justify='center', style={'padding': '5px'}),

                                # Detailed stats
                                dbc.Row(id='metric-2', justify='center', style={'padding': '5px'}),

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
                                        'width': '97.5%',
                                    })
                                ]),

                               html.Div(
                                    [
                                        html.Div(
                                            html.H1(
                                                id='plot-title',
                                                children='Please select an option',
                                                style={'fontSize': '24px'}
                                            ),
                                            style={'flex': '1'}
                                        ),
                                        html.Div(
                                            dcc.Dropdown(
                                                id='chart-dropdown',
                                                options=[
                                                    {'label': 'Hashrate', 'value': 'hash'},
                                                    {'label': 'Effort', 'value': 'effort'}
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
                                dcc.Graph(id='plot-1',  style={'backgroundColor': card_color}),
                       
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