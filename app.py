from dash import Dash, html, dcc, Input, Output, State
from layouts import front_page, mining_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.api_reader import ApiReader
from utils.data_manager import DataManager
from flask_login import LoginManager, UserMixin
from flask import Flask, session
from flask_session import Session 
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Flask(__name__)
server.config.update({
    'SECRET_KEY': 'your_super_secret_key',
    'SESSION_TYPE': 'filesystem'
})
Session(server)

login_manager = LoginManager()
login_manager.init_app(server)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

def initialize_api():
    try:
        data_manager = DataManager('../conf')
        data_manager.update_data()
        api_reader = ApiReader(data_manager)
        logger.info("Successfully initialized API components")
        return data_manager, api_reader
    except Exception as e:
        logger.error(f"Failed to initialize API components: {e}")
        raise

def create_app():
    data_manager, api_reader = initialize_api()

    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])

    @app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
    def display_page(pathname):
        if pathname and pathname != "/":
            mining_address = unquote(pathname.lstrip('/'))
            return mining_page.get_layout(api_reader)
        return front_page.get_layout(api_reader)

    @app.callback(
        Output('url', 'pathname'),
        Input('start-mining-button', 'n_clicks'),
        State('mining-address-input', 'value')
    )
    def navigate_to_main(n_clicks, value):
        if n_clicks and value:
            return f'/{quote(value)}'
        return '/'

    # Register callbacks for both pages
    front_page.setup_front_page_callbacks(app, api_reader)
    mining_page.setup_mining_page_callbacks(app, api_reader)

    return app

try:
    app = create_app()
    server = app.server
except Exception as e:
    logger.error(f"Application startup failed: {e}")
    raise

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)