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
import redis
import socket
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)
logger.info("Application startup - Logging initialized")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

def wait_for_redis(redis_url, max_retries=5, delay=2):
    """Wait for Redis to become available"""
    retries = 0
    while retries < max_retries:
        try:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info(f"Successfully connected to Redis at {redis_url}")
            return True
        except (redis.ConnectionError, socket.gaierror) as e:
            retries += 1
            logger.warning(f"Attempt {retries}/{max_retries} - Failed to connect to Redis: {e}")
            if retries < max_retries:
                time.sleep(delay)
    return False

# Initialize Redis connection for session storage
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
if not wait_for_redis(REDIS_URL):
    logger.error(f"Could not connect to Redis at {REDIS_URL}")
    if os.getenv('FLASK_ENV') != 'development':
        raise RuntimeError("Redis connection failed")

server = Flask(__name__)
server.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', os.urandom(24)),
    'SESSION_TYPE': 'redis',
    'SESSION_REDIS': redis.from_url(REDIS_URL),
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

def create_app():
    def initialize_api():
        try:
            logger.info("Starting API initialization...")
            
            # Change working directory to ensure relative path works
            if os.path.exists('/app'):
                os.chdir('/app')
                logger.info("Changed working directory to /app")
            
            # Set up Hydra configuration
            config_dir = os.path.join(os.getcwd(), 'conf')
            logger.info(f"Using config directory: {config_dir}")
            
            if not os.path.exists(config_dir):
                raise RuntimeError(f"Config directory not found at {config_dir}")
            
            logger.info(f"Attempting to initialize DataManager...")
            data_manager = DataManager('conf')  # Use just the directory name for Hydra
            logger.info("DataManager initialized successfully")
            
            logger.info("Attempting to update data...")
            data_manager.update_data()
            logger.info("Data update completed successfully")
            
            logger.info("Initializing ApiReader...")
            api_reader = ApiReader(data_manager)
            logger.info("Successfully initialized API components")
            return data_manager, api_reader
        except Exception as e:
            logger.error(f"Failed to initialize API components: {e}", exc_info=True)
            raise

    try:
        logger.info("Starting application creation process...")
        data_manager, api_reader = initialize_api()
        logger.info("API initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        update_title=None  # Disable the "Updating..." title during callbacks
    )

    # Register Dash-specific routes with higher limits
    @server.route('/_dash-<path:path>')
    @dash_route_limits()
    def _dash_route(path):
        return dash_app.server._dash_route(path)

    @server.route('/_reload-<path:path>')
    @dash_route_limits()
    def _reload_route(path):
        return dash_app.server._reload_route(path)

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

    dash_app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])

    @dash_app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
    def display_page(pathname):
        if pathname and pathname != "/":
            mining_address = unquote(pathname.lstrip('/'))
            return mining_page.get_layout(api_reader)
        return front_page.get_layout(api_reader)

    @dash_app.callback(
        Output('url', 'pathname'),
        Input('start-mining-button', 'n_clicks'),
        State('mining-address-input', 'value')
    )
    def navigate_to_main(n_clicks, value):
        if n_clicks and value:
            return f'/{quote(value)}'
        return '/'

    # Register callbacks for both pages
    front_page.setup_front_page_callbacks(dash_app, api_reader)
    mining_page.setup_mining_page_callbacks(dash_app, api_reader)

    return dash_app

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        app = create_app()
        logger.info("Application created successfully, starting server...")
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
else:
    try:
        logger.info("Creating application for WSGI...")
        app = create_app()
        application = app.server  # For gunicorn
    except Exception as e:
        logger.error(f"Failed to create application for WSGI: {e}", exc_info=True)
        raise