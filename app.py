# app.py
from dash import Dash, html, dcc, Input, Output, State

from layouts import front_page, mining_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.api_reader import SigmaWalletReader, PriceReader
from layouts.front_page import setup_front_page_callbacks
from layouts.mining_page import setup_mining_page_callbacks
from flask_login import LoginManager, UserMixin, login_user
from flask import Flask, request, session, redirect, url_for
from flask_session import Session 
from utils.dash_utils import set_theme

# Initialize theme settings
url = 'https://raw.githubusercontent.com/marctheshark3/ergo-fan-clubs/main/pool/conf.yaml'
current_hash, theme_config = set_theme(url) 

# Initialize Flask app
server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a random secret key
server.config['SESSION_TYPE'] = 'filesystem'  # Example: filesystem-based session storage
Session(server)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)

# Mock user database (you will replace this with your actual user authentication mechanism)
class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    # Load user from database or other source
    user = User()
    user.id = user_id
    
reader = SigmaWalletReader('../conf')
reader.update_data()
app = Dash(__name__, url_base_pathname='/', server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server 
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    dcc.Interval(id='theme-interval', interval=60*1000, n_intervals=0),  # Check every minute
    dcc.Store(id='theme-store', data=theme_config)  # Store theme settings
    
])

@app.callback(
    Output('theme-store', 'data'),
    Input('theme-interval', 'n_intervals'),
    State('theme-store', 'data')
)
def update_theme(n_intervals, stored_theme):
    global current_hash
    url ='https://raw.githubusercontent.com/marctheshark3/ergo-fan-clubs/main/pool/conf.yaml'
    new_hash, new_theme_config = set_theme(url)
    if new_hash != current_hash:
        current_hash = new_hash
        print(f"Theme updated: {new_theme_config}")
        return new_theme_config
    return stored_theme


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'), Input('theme-store', 'data')]
)
def display_page(pathname, theme_data):
    if pathname and pathname != "/":
        mining_address = unquote(pathname.lstrip('/'))
        return mining_page.get_layout(reader, theme_data)
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
