from utils.reader import SigmaWalletReader, PriceReader
from utils.dash_utils import create_pie_chart, create_bar_chart, create_table_component
from dash import Dash, html, dash_table, dcc, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

price_reader = PriceReader()
sigma_reader = SigmaWalletReader(config_path="../conf")
wallet = 'ADDRESS'

def update_charts(wallet_address):
    global wallet
    wallet = wallet_address
    
    global mining_df, performance_df, block_df, miner_df, effort_df, pool_df, top_miner_df, btc_price, erg_price, your_total_hash, pool_hash, network_hashrate, avg_block_effort, network_difficulty
        
    # sigma_reader.set_wallet(wallet)
    short_wallet = '{}...{}'.format(wallet[:5], wallet[-5:])

    mining_df, performance_df = sigma_reader.get_mining_stats(wallet)
    block_df, miner_df, effort_df = sigma_reader.get_block_stats(wallet)
    pool_df, top_miner_df = sigma_reader.get_pool_stats(wallet)
    btc_price, erg_price = price_reader.get(debug=False)

    try:
        pool_hash = round(pool_df[pool_df['Pool Stats'] == 'poolHashrate [Gh/s]']['Values'].iloc[0], 5)
        network_difficulty = round(pool_df[pool_df['Pool Stats'] == 'networkDifficulty [Peta]']['Values'].iloc[0], 5)
        network_hashrate = round(pool_df[pool_df['Pool Stats'] == 'networkHashrate [Th/s]']['Values'].iloc[0], 5)
        
    except IndexError:
        print('POOL API EXCEPTION TRIGGERED!!!!')
        pool_hash = -10
        network_difficulty = -10
        network_hashrate = -10
        
    your_total_hash = round(performance_df[performance_df['Worker'] == 'Totals']['Hashrate [Mh/s]'].iloc[0], 5)
    avg_block_effort = round(effort_df[effort_df['Mining Stats'] == 'Average Block Effort']['Values'].iloc[0], 5)
    
    # Masking Values we dont need in the tables
    mask = performance_df['Worker'] == 'Totals'
    mask_performance_df = performance_df[~mask]
    
    values_to_drop = ['networkHashrate [Th/s]', 'networkDifficulty [Peta]',
                      'poolHashrate [Gh/s]', 'networkType', 'connectedPeers', 'rewardType']
    mask = pool_df['Pool Stats'].isin(values_to_drop)
    pool_df = pool_df[~mask]
    
    # Creating Charts
    miner_chart = create_pie_chart(miner_df, 'miner', 'Number of Blocks Found')
    top_miner_chart = create_pie_chart(top_miner_df, 'miner', 'hashrate')
    estimated_reward = create_pie_chart(top_miner_df, 'miner', 'ProjectedReward', est_reward=True)
    
    
    effort_chart = create_bar_chart(block_df, x='Time Found', y='effort',
                                    color='networkDifficulty', 
                                    labels={'Time Found': 'Block Creation Date',
                                            'effort': 'Effort', 'networkDifficulty': 'Network Difficulty'})

    
    # # adding a circle to the effort chart if you found the block
    # try:
    #     my_wallet_blocks = block_df[block_df['my_wallet']]
    # except KeyError:
    #     block_df['my_wallet'] = 'NO WALLET SUBMITTED'
    #     my_wallet_blocks = block_df[block_df['my_wallet']]

    # block_df = block_df.drop(['my_wallet'], axis=1) # might need to change the name of this df
    # effort_chart.add_trace(go.Scatter(x=my_wallet_blocks['Time Found'], y=my_wallet_blocks['effort'], mode='markers',
    #                                   marker=dict(color='Red', size=10, symbol='circle'), name='My Wallet'))

    # Network Difficulty Plot
    net_diff_plot={'data': [go.Scatter(x=block_df['Time Found'], y=block_df['networkDifficulty'],
                                    mode='lines+markers', name='Network Difficulty', line={'color': '#00CC96'})],
                   
                   'layout': go.Layout(title='Ergo Network Difficulty Over Time', titlefont={'color': '#FFFFFF'},
                                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       margin={'l': 40, 'b': 40, 't': 50, 'r': 50}, hovermode='closest',
                                       legend={'font': {'color': '#FFFFFF'}}, font=dict(color='#FFFFFF'))}

    # Define the style for the crypto prices
    metric_style = {
        'padding': '20px',
        'fontSize': '20px',
        'margin': '10px',
        'border': '1px solid #555',  # Adjusted for dark mode
        'borderRadius': '5px',
        'background': '#333',  # Dark background
        'color': '#fff',  # Light text color
        'boxShadow': '0 2px 4px rgba(255,255,255,.1)',  # Subtle white shadow for depth
        'minWidth': '150px',  # Ensure blocks don't become too narrow
        'textAlign': 'center'  # Center text horizontally
    }

    # Create the crypto prices HTML div elements as a row
    crypto_prices_row = html.Div([
                                html.Div(f"BTC: ${btc_price}", style=metric_style),
                                html.Div(f"ERG: ${erg_price}", style=metric_style),
                                html.Div(f"Total Hashrate: {your_total_hash} Mh/s", style=metric_style),
                                html.Div(f"Pool Hashrate: {pool_hash} Gh/s", style=metric_style),
                                html.Div(f"Network Hashrate: {network_hashrate} Th/s", style=metric_style),
                                html.Div(f"Average Block Effort: {avg_block_effort}", style=metric_style),
                                html.Div(f"Network Difficulty: {network_difficulty} P", style=metric_style),
                            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'center'})

    if wallet == 'ADDRESS':
        dashboard_title = 'Sigma Mining Pool Dashboard - ENTER YOUR ADDRESS'
    else:
        dashboard_title = 'Sigma Mining Pool Dashboard - {}'.format(short_wallet)
    return miner_chart, top_miner_chart, estimated_reward, effort_chart, mining_df, mask_performance_df, pool_df, crypto_prices_row, dashboard_title, block_df, net_diff_plot
    
miner_chart, top_miner_chart, estimated_reward, effort_chart, mining_df, mask_performance_df, pool_df, crypto_prices_row, dashboard_title, block_df, net_diff_plot= update_charts(wallet)

app.layout = html.Div(children=[
    html.H1(id='dashboard-title', children=[]),

    html.Label('Enter your wallet ID:'),
    dcc.Input(id='wallet-input', type='text', value=''),
    html.Button('Submit', id='submit-btn', n_clicks=0),
    html.Div(id='output-container'),
    
    html.Div(id='crypto-prices', children=[]),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # in milliseconds, every 1 minutes
        n_intervals=0
    ),
  
    html.Div([html.Div(create_table_component('Payment Stats', 'mining-stats',
                                           mining_df.columns, mining_df, max_table_width='400px'), style={'flex': '1'}),
              html.Div(create_table_component('Your Performance Stats', 'performance-stats',
                                               mask_performance_df.columns, mask_performance_df, max_table_width='600px'), style={'flex': '1'}),
              html.Div(create_table_component('Pool and Network Stats', 'pool-stats',
                                           pool_df.columns, pool_df, max_table_width='520px'), style={'flex': '1'}),],
             style={'display': 'flex'}),
    
    dcc.Graph(id='network-difficulty-plot', figure=net_diff_plot, style={'backgroundColor': 'rgba(17,17,17,1)'}),
    
    html.Div(children=[html.Div(children=[html.H2('Blocks Found by Miners'),
                                          dcc.Graph(id='miner-blocks', figure=miner_chart),],
                                          style={'flex': 1}),
                       
    html.Div(children=[html.H2('Top Miners by Hashrate Mh/s'),
                       dcc.Graph(id='top-miner-chart', figure=top_miner_chart)],
             style={'flex': 1}), 
    html.Div(children=[html.H2('Estimated Rewards'),
                       dcc.Graph(id='estimated-reward', figure=estimated_reward)],
             style={'flex': 1}),],
             style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px'}),

    html.Div(children=[html.H2('Block Effort Over Time'),
                       dcc.Graph(id='effort-chart', figure=effort_chart)],
             style={'margin-top': '20px'}),

    html.Div(children=[html.H2('Block Statistics'), 
                       dash_table.DataTable(id='block-stats', columns=[{"name": i, "id": i} for i in block_df.columns],
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
                                            style_header_conditional=[{'if': {'column_id': 'status'}, 'textAlign': 'center'}])],
             style={'padding': '20px'})],
                      style={'backgroundColor': 'rgba(17,17,17,1)', 'color': '#FFFFFF', 'padding': '10px'})


@app.callback([
    Output('dashboard-title', 'children'),
    Output('miner-blocks', 'figure'),
    Output('top-miner-chart', 'figure'),
    Output('estimated-reward', 'figure'),
    Output('effort-chart', 'figure'),
    Output('crypto-prices', 'children'),
    Output('mining-stats', 'data'),  # Adding Output for the mining-stats DataTable
    Output('performance-stats', 'data'),  # Adding Output for the performance-stats DataTable
    Output('pool-stats', 'data'),  # Adding Output for the pool-stats DataTable
    Output('block-stats', 'data'),  
    Output('network-difficulty-plot', 'figure'), 
    Input('submit-btn', 'n_clicks'),
    State('wallet-input', 'value')
], [Input('interval-component', 'n_intervals')])

def update_output(n_clicks, wallet_address, n_intervals):
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    print(f"Callback triggered by: {trigger_id}")

    if trigger_id == 'interval-component':
        wallet_address = wallet
    
    if n_clicks > 0:  # Only update after the first click to avoid initial unwanted API call
        print(f'Wallet ID entered: "{wallet_address}"')
    else:
        pass
    miner_chart, top_miner_chart, estimated_reward, effort_chart, mining_df, mask_performance_df, pool_df, crypto_prices_row, dashboard_title, block_df, net_diff_plot = update_charts(wallet_address)

    # Convert DataFrames to lists of dictionaries for DataTables
    mining_stats_data = mining_df.to_dict('records')
    performance_stats_data = mask_performance_df.to_dict('records')
    pool_stats_data = pool_df.to_dict('records')
    block_data = block_df.to_dict('records')

    # Return the new figures and data
    return (
        dashboard_title, miner_chart, top_miner_chart, estimated_reward, effort_chart, 
        crypto_prices_row, 
        mining_stats_data, performance_stats_data, pool_stats_data, block_data, net_diff_plot
    )

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)