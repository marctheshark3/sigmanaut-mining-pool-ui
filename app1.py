# app.py
from dash import Dash, html, dcc, Input, Output, State

from layouts import front_page, mining_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.api_reader import SigmaWalletReader, PriceReader
from layouts.front_page_1 import setup_front_page_callbacks
# from layouts.main_page import setup_main_page_callbacks
from layouts.mining_page_1 import setup_mining_page_callbacks
from flask_login import LoginManager, UserMixin, login_user
from flask import Flask, request, session, redirect, url_for
from flask_session import Session 

server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage
Session(server)
reader = SigmaWalletReader('../conf')
reader.update_data()
app = Dash(__name__, url_base_pathname='/', server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server 
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
        return mining_page.get_layout(reader)
    else:
        return front_page.get_layout(reader)

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

setup_front_page_callbacks(app, reader)
setup_mining_page_callbacks(app, reader)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
