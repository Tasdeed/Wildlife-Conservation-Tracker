"""
Wildlife Conservation Tracker - Backend API
"""

from flask import Flask, jsonify
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app)  # Allow frontend to connect

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'

# Test route 
@app.route('/')
def index():
    """API welcome message"""
    return jsonify({
        'message': 'Wildlife Conservation Tracker API',
        'status': 'running',
        'version': '1.0',
        'endpoints': {
            'home': '/',
            'test': '/api/test'
        }
    })

@app.route('/api/test')
def test():
    """Test endpoint to make sure API is working"""
    return jsonify({
        'status': 'success',
        'message': 'API is working!',
        'data': {
            'sample_species': 'African Elephant',
            'status': 'Endangered'
        }
    })

# Run the app
if __name__ == '__main__':
    print("=" * 60)
    print("Wildlife Conservation Tracker API")
    print("=" * 60)
    print("Starting server...")
    print("Open your browser to: http://localhost:5001")
    print("=" * 60)
    app.run(debug=True, port=5001)