from dash import Dash, html, dcc, Input, Output, State
from layouts import front_page, mining_page
from urllib.parse import quote, unquote
import dash_bootstrap_components as dbc
from utils.api_reader import ApiReader
from utils.data_manager import DataManager
from flask_login import LoginManager, UserMixin
from flask import Flask, session, send_from_directory, request
from flask_session import Session 
import logging
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

server = Flask(__name__)
server.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', os.urandom(24)),
    'SESSION_TYPE': 'filesystem',
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 1800  # 30 minutes
})

# Initialize Flask extensions
Session(server)
CORS(server, resources={r"/api/*": {"origins": os.getenv('ALLOWED_ORIGINS', '*')}})

# Configure rate limits based on environment
is_development = os.getenv('FLASK_ENV') == 'development'

# Initialize rate limiter with Redis storage
limiter = Limiter(
    app=server,
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"] if is_development else ["500 per day", "100 per hour"],
    storage_uri=os.getenv('REDIS_URL', "memory://"),
    strategy="moving-window"  # Changed to moving window for better handling of burst requests
)

def is_dash_route():
    """Check if the current request is for a Dash route"""
    path = request.path
    return any(path.startswith(prefix) for prefix in ['/_dash', '/_reload', '/__webpack', '/sockjs-node'])

# Exempt static files and development routes from rate limiting
@limiter.request_filter
def exempt_paths():
    path = request.path
    
    # Always exempt Dash routes in development
    if is_development and is_dash_route():
        return True
    
    # Always exempt websocket connections
    if request.environ.get('HTTP_UPGRADE', '').lower() == 'websocket':
        return True
    
    # Exempt static files and health checks
    return any([
        path.startswith('/static/'),
        path.startswith('/assets/'),
        path.startswith('/mint/'),
        path.endswith(('.js', '.css', '.png', '.jpg', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.json', '.map')),
        path == '/health'
    ])

# Special high-limit decorator for Dash development routes
def dash_route_limits():
    """Decorator to apply very high limits to Dash routes"""
    def decorator(f):
        if is_development:
            return limiter.limit("10000 per hour")(f)  # Much higher limit for development
        return f
    return decorator

# Register Dash-specific routes with higher limits
@server.route('/_dash-<path:path>')
@dash_route_limits()
def _dash_route(path):
    return app.server._dash_route(path)

@server.route('/_reload-<path:path>')
@dash_route_limits()
def _reload_route(path):
    return app.server._reload_route(path)

# Apply specific rate limits to API endpoints
@limiter.limit("500 per day")
@limiter.limit("100 per hour")
@server.route("/api/<path:path>")
def api_routes(path):
    # Your API route handling code here
    pass

# Apply higher rate limits to static files
@limiter.limit("2000 per day")
@limiter.limit("500 per hour")
@server.route("/static/<path:filename>")
def serve_app_static(filename):
    return send_from_directory('static', filename)

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
    try:
        data_manager, api_reader = initialize_api()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        update_title=None  # Disable the "Updating..." title during callbacks
    )

    # Add routes to serve React app
    @server.route('/mint/')
    @server.route('/mint')
    def serve_react_app():
        return send_from_directory('off-chain/build', 'index.html')

    # Serve static files for React app
    @server.route('/mint/static/<path:path>')
    def serve_mint_static(path):
        return send_from_directory('off-chain/build/static', path)

    # Serve root files from the React build directory
    @server.route('/mint/<path:filename>')
    def serve_mint_files(filename):
        try:
            return send_from_directory('off-chain/build', filename)
        except:
            return send_from_directory('off-chain/build', 'index.html')

    # Add security headers but allow iframe embedding for the modal
    @server.after_request
    def add_security_headers(response):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; frame-ancestors 'self'"
        return response

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

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        app = create_app()
        server = app.server
        logger.info("Application created successfully, starting server...")
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise