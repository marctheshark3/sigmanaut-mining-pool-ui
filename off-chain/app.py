from flask import Flask, send_from_directory, jsonify, request, make_response
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='build')
# Configure CORS to allow all origins, methods, and headers
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Create response
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        response = make_response(send_from_directory(app.static_folder, path))
    else:
        response = make_response(send_from_directory(app.static_folder, 'index.html'))
    
    # Add headers to allow framing
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *"
    
    return response

if __name__ == '__main__':
    # Production configuration
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Add default headers to allow framing
    @app.after_request
    def add_header(response):
        response.headers['X-Frame-Options'] = 'ALLOWALL'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *"
        return response
    
    app.run(host='0.0.0.0', port=3000, threaded=True) 