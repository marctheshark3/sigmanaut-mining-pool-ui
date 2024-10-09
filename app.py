from dash import Dash, html, dcc, Input, Output, State
from layouts import front_page, mining_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.shark_api import DataManager, ApiReader, setup_data_manager_update
from layouts.front_page import setup_front_page_callbacks
from layouts.mining_page import setup_mining_page_callbacks
from flask_login import LoginManager, UserMixin, login_user
from flask import Flask, request, session, redirect, url_for
from flask_session import Session 
import time
import logging

server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_super_secret_key'
server.config['SESSION_TYPE'] = 'filesystem'
Session(server)

login_manager = LoginManager()
login_manager.init_app(server)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id

data_manager = DataManager('../conf')
data_manager.update_data()
# data_manager.start_update_loop(update_interval=60)  # Update every 5 minutes
reader = ApiReader(data_manager)

app = Dash(__name__, url_base_pathname='/', server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server 
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])
setup_data_manager_update(app, data_manager, interval=3 * 60000)  # Update every 60 seconds

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname and pathname != "/":
        mining_address = unquote(pathname.lstrip('/'))
        return mining_page.get_layout(reader)
    else:
        return front_page.get_layout(reader)

@app.callback(
    Output('url', 'pathname'),
    Input('start-mining-button', 'n_clicks'),
    State('mining-address-input', 'value')
)
def navigate_to_main(n_clicks, value):
    if n_clicks and value:
        safe_value = quote(value)
        return f'/{safe_value}'
    return '/'

setup_front_page_callbacks(app, reader)
setup_mining_page_callbacks(app, reader)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)