from flask import Flask, request, jsonify

app = Flask(__name__)

# Dummy token validation function
def validate_token(token):
    # Example: Validate your token here (e.g., database lookup)
    # For this example, any token is considered valid
    return True

@app.route('/data', methods=['GET'])
def get_data():
    token = request.headers.get('Authorization')
    if token and validate_token(token):
        # Fetch and return the data specific to the token
        return jsonify({"message": "Here is your data", "data": {}})
    else:
        return jsonify({"error": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(debug=True)
