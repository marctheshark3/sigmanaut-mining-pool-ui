# app.py
from dash import Dash, html, dcc, Input, Output, State

from layouts import front_page, main_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.reader import SigmaWalletReader, PriceReader

reader = SigmaWalletReader('../conf')

app = Dash(__name__, url_base_pathname='/', external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname and pathname != "/":
        # Decode the mining address from the URL
        mining_address = unquote(pathname.lstrip('/'))
        # Use the mining address to generate the page content
        # This is where you might call a function to get the layout based on the mining address
        return main_page.get_layout()
    else:
        return front_page.get_layout()

# Define callback to update page content or handle business logic
@app.callback(
    Output('url', 'pathname'),
    Input('start-mining-button', 'n_clicks'),
    State('mining-address-input', 'value')
)
def navigate_to_main(n_clicks, value):
    if n_clicks and value:
        # Encode the user input to ensure it's safe for URL use
        safe_value = quote(value)
        # Redirect user to a dynamic path based on their input
        return f'/{safe_value}'
    # If there's no input or the button hasn't been clicked, stay on the current page
    return '/'

@app.callback(
    Output('metrics-stats', 'children'),
    [Input('interval-component', 'n_intervals')],
    [State('url', 'pathname')]
)
def update_crypto_prices(n, pathname):
    if pathname:
        wallet = unquote(pathname.split('/')[1])
        # print(wallet)
    if wallet or n > 0:
        print(n, wallet, 'yoyoyoy')
        metric_style = {
            'padding': '20px',
            'fontSize': '20px',
            'margin': '10px',
            'border': '1px solid #555',  # Adjusted for dark mode
            'borderRadius': '5px',
            'background': '#333',  # Dark background
            'color': '#fff',  # Light text color
            # 'boxShadow': '0 2px 4px rgba(255,255,255,.1)',  # Subtle white shadow for depth
            # 'minWidth': '150px',  # Ensure blocks don't become too narrow
            'textAlign': 'center'  # Center text horizontally
        }
        btc_price, erg_price, your_total_hash, pool_hash, net_hash, avg_block_effort, net_diff = reader.get_main_page_metrics(wallet, True)
        layout = html.Div([
                    html.Div(f"BTC: ${btc_price}", style=metric_style),
                    html.Div(f"ERG: ${erg_price}", style=metric_style),
                    html.Div(f"Total Hashrate: {your_total_hash} Mh/s", style=metric_style),
                    html.Div(f"Pool Hashrate: {pool_hash} Gh/s", style=metric_style),
                    html.Div(f"Network Hashrate: {net_hash} Th/s", style=metric_style),
                    html.Div(f"Average Block Effort: {avg_block_effort}", style=metric_style),
                    html.Div(f"Network Difficulty: {net_diff} P", style=metric_style),
                ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'center'})
        return layout


if __name__ == '__main__':
    app.run_server(debug=True)
