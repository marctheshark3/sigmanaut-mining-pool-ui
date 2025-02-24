from flask import Flask, send_from_directory, jsonify, request, make_response, redirect, url_for
from flask_cors import CORS
import os
import re

app = Flask(__name__, static_folder='build')
# Configure CORS to allow all origins, methods, and headers
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

# Serve static files with proper path handling
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.static_folder, 'static'), filename)

# Handle root path for direct access
@app.route('/')
def root():
    response = make_response(send_from_directory(app.static_folder, 'index.html'))
    add_frame_headers(response)
    return response

# Handle UUID paths for minting
@app.route('/<uuid:id>')
def serve_with_id(id):
    response = make_response(send_from_directory(app.static_folder, 'index.html'))
    add_frame_headers(response)
    return response

# Serve React App for all other paths
@app.route('/<path:path>')
def serve(path):
    # Check if this is a static file request
    if path.startswith('static/'):
        # Extract the filename from the path
        filename = path.replace('static/', '', 1)
        return send_from_directory(os.path.join(app.static_folder, 'static'), filename)
    
    # For all other paths, serve the index.html
    response = make_response(send_from_directory(app.static_folder, 'index.html'))
    add_frame_headers(response)
    return response

def add_frame_headers(response):
    """Add headers to allow framing"""
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
        return add_frame_headers(response)
    
    app.run(host='0.0.0.0', port=3000, threaded=True) 