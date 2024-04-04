# app.py
from dash import Dash, html, dcc, Input, Output, State

from layouts import front_page, main_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.reader import SigmaWalletReader, PriceReader
from layouts.front_page import setup_front_page_callbacks
from layouts.main_page import setup_main_page_callbacks


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

setup_front_page_callbacks(app)
setup_main_page_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
