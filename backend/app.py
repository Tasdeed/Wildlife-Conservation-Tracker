"""
Wildlife Conservation Tracker - Backend API with Database and ML Predictions
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import joblib
import numpy as np

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/wildlife_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# ============================================================================
# LOAD ML MODEL
# ============================================================================

# Load ML model and encoders at startup
try:
    ml_model = joblib.load('ml_model.pkl')
    encoders = joblib.load('encoders.pkl')
    print("✓ ML model and encoders loaded successfully")
except FileNotFoundError:
    ml_model = None
    encoders = None
    print("⚠ ML model not found. Run train_model.py first.")

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Species(db.Model):
    """Species information from IUCN Red List"""
    __tablename__ = 'species'
    
    id = db.Column(db.Integer, primary_key=True)
    taxon_id = db.Column(db.Integer, unique=True)
    scientific_name = db.Column(db.String(200), nullable=False)
    common_name = db.Column(db.String(200))
    kingdom = db.Column(db.String(50))
    phylum = db.Column(db.String(50))
    class_name = db.Column(db.String(50))
    order = db.Column(db.String(50))
    family = db.Column(db.String(50))
    
    # Conservation status
    category = db.Column(db.String(10))  # CR, EN, VU, NT, LC
    population_trend = db.Column(db.String(20))  # Increasing, Decreasing, Stable
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'taxon_id': self.taxon_id,
            'scientific_name': self.scientific_name,
            'common_name': self.common_name,
            'kingdom': self.kingdom,
            'phylum': self.phylum,
            'class': self.class_name,
            'order': self.order,
            'family': self.family,
            'category': self.category,
            'population_trend': self.population_trend
        }

class SpeciesLocation(db.Model):
    """Location data for species observations"""
    __tablename__ = 'species_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(100))
    
    # Relationship
    species = db.relationship('Species', backref='locations')

# ============================================================================
# BASIC API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'Wildlife Conservation Tracker API',
        'version': '1.0',
        'endpoints': {
            'species': '/api/species',
            'species_detail': '/api/species/<id>',
            'predict': '/api/predict/<id>',
            'model_stats': '/api/model/stats'
        }
    })

@app.route('/api/test')
def test():
    """Test endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is working!'})

@app.route('/api/species', methods=['GET'])
def get_all_species():
    """Get all species with optional filtering"""
    # Get query parameters
    category = request.args.get('category')
    trend = request.args.get('trend')
    limit = request.args.get('limit', type=int)
    
    # Build query
    query = Species.query
    
    if category:
        query = query.filter_by(category=category)
    
    if trend:
        query = query.filter_by(population_trend=trend)
    
    if limit:
        query = query.limit(limit)
    
    species_list = query.all()
    
    return jsonify({
        'count': len(species_list),
        'species': [s.to_dict() for s in species_list]
    })

@app.route('/api/species/<int:species_id>', methods=['GET'])
def get_species(species_id):
    """Get a single species by ID"""
    species = Species.query.get(species_id)
    
    if not species:
        return jsonify({'error': 'Species not found'}), 404
    
    return jsonify(species.to_dict())

# ============================================================================
# ML PREDICTION ENDPOINTS
# ============================================================================

@app.route('/api/predict/<int:species_id>', methods=['GET'])
def predict_population_trend(species_id):
    """Predict population trend for a species using ML model"""
    
    if ml_model is None:
        return jsonify({'error': 'ML model not loaded. Run train_model.py first.'}), 500
    
    # Get species from database
    species = Species.query.get(species_id)
    
    if not species:
        return jsonify({'error': 'Species not found'}), 404
    
    # Prepare features
    features = {
        'category': species.category or 'Unknown',
        'kingdom': species.kingdom or 'Unknown',
        'phylum': species.phylum or 'Unknown',
        'class': species.class_name or 'Unknown',
        'order': species.order or 'Unknown',
        'family': species.family or 'Unknown'
    }
    
    # Encode features
    feature_vector = []
    feature_cols = ['category', 'kingdom', 'phylum', 'class', 'order', 'family']
    
    for col in feature_cols:
        try:
            encoded_value = encoders[col].transform([features[col]])[0]
            feature_vector.append(encoded_value)
        except:
            # Handle unknown categories
            feature_vector.append(0)
    
    X = np.array([feature_vector])
    
    # Make prediction
    prediction = ml_model.predict(X)[0]
    prediction_proba = ml_model.predict_proba(X)[0]
    
    # Decode prediction
    predicted_trend = encoders['population_trend'].inverse_transform([prediction])[0]
    
    # Get confidence scores for all classes
    confidence_scores = {}
    for idx, class_name in enumerate(encoders['population_trend'].classes_):
        confidence_scores[class_name] = float(prediction_proba[idx])
    
    # Response
    return jsonify({
        'species_id': species_id,
        'scientific_name': species.scientific_name,
        'common_name': species.common_name,
        'actual_trend': species.population_trend,
        'predicted_trend': predicted_trend,
        'confidence': float(max(prediction_proba)),
        'confidence_scores': confidence_scores,
        'features_used': features
    })

@app.route('/api/model/stats', methods=['GET'])
def model_stats():
    """Get ML model statistics"""
    
    if ml_model is None:
        return jsonify({'error': 'ML model not loaded. Run train_model.py first.'}), 500
    
    # Count species by trend
    total = Species.query.count()
    trends = {}
    
    for trend in ['Increasing', 'Stable', 'Decreasing', 'Unknown']:
        count = Species.query.filter_by(population_trend=trend).count()
        trends[trend] = count
    
    # Count by category
    categories = {}
    for cat in ['CR', 'EN', 'VU']:
        count = Species.query.filter_by(category=cat).count()
        categories[cat] = count
    
    return jsonify({
        'total_species': total,
        'population_trends': trends,
        'categories': categories,
        'model_info': {
            'type': 'Random Forest Classifier',
            'n_estimators': ml_model.n_estimators if hasattr(ml_model, 'n_estimators') else None,
            'features': ['category', 'kingdom', 'phylum', 'class', 'order', 'family'],
            'classes': encoders['population_trend'].classes_.tolist() if encoders else []
        }
    })

# ============================================================================
# DATABASE CLI COMMANDS
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print("✓ Database tables created")

@app.cli.command()
def drop_db():
    """Drop all database tables"""
    db.drop_all()
    print("✓ Database tables dropped")

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=5001)