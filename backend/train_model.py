"""
Wildlife Conservation Tracker - Machine Learning Model
Random Forest Classifier for Population Trend Prediction

Features:
- Conservation category (CR, EN, VU)
- Taxonomy (kingdom, phylum, class, order, family)
- Engineered features from categorical data

Target:
- Population trend (Increasing, Stable, Decreasing)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
from app import app, db, Species

# Feature encoders (will be saved for predictions)
encoders = {}

def load_data_from_database():
    """Load species data from PostgreSQL database"""
    print("=" * 60)
    print("LOADING DATA FROM DATABASE")
    print("=" * 60)
    
    with app.app_context():
        # Get all species
        all_species = Species.query.all()
        
        # Convert to list of dictionaries
        data = []
        for s in all_species:
            data.append({
                'id': s.id,
                'scientific_name': s.scientific_name,
                'category': s.category,
                'kingdom': s.kingdom,
                'phylum': s.phylum,
                'class': s.class_name,
                'order': s.order,
                'family': s.family,
                'population_trend': s.population_trend
            })
        
        df = pd.DataFrame(data)
        
        print(f"\nTotal species loaded: {len(df)}")
        print(f"\nPopulation trend distribution:")
        print(df['population_trend'].value_counts())
        
        return df

def prepare_features(df):
    """Prepare features for machine learning"""
    print("\n" + "=" * 60)
    print("PREPARING FEATURES")
    print("=" * 60)
    
    # Separate labeled and unlabeled data
    labeled_df = df[df['population_trend'] != 'Unknown'].copy()
    unlabeled_df = df[df['population_trend'] == 'Unknown'].copy()
    
    print(f"\nLabeled samples: {len(labeled_df)}")
    print(f"Unlabeled samples: {len(unlabeled_df)}")
    
    if len(labeled_df) < 10:
        print("\n❌ ERROR: Not enough labeled data to train model!")
        print("Need at least 10 labeled species.")
        return None, None, None, None
    
    # Fill missing values
    labeled_df = labeled_df.fillna('Unknown')
    unlabeled_df = unlabeled_df.fillna('Unknown')
    
    # Feature columns
    feature_cols = ['category', 'kingdom', 'phylum', 'class', 'order', 'family']
    
    # Encode categorical features
    for col in feature_cols:
        if col not in encoders:
            encoders[col] = LabelEncoder()
            # Fit on all data (labeled + unlabeled) to handle unseen categories
            all_values = pd.concat([labeled_df[col], unlabeled_df[col]])
            encoders[col].fit(all_values)
        
        labeled_df[f'{col}_encoded'] = encoders[col].transform(labeled_df[col])
        if len(unlabeled_df) > 0:
            unlabeled_df[f'{col}_encoded'] = encoders[col].transform(unlabeled_df[col])
    
    # Encode target variable
    if 'population_trend' not in encoders:
        encoders['population_trend'] = LabelEncoder()
        encoders['population_trend'].fit(labeled_df['population_trend'])
    
    labeled_df['trend_encoded'] = encoders['population_trend'].transform(labeled_df['population_trend'])
    
    # Feature matrix
    encoded_cols = [f'{col}_encoded' for col in feature_cols]
    X_labeled = labeled_df[encoded_cols].values
    y_labeled = labeled_df['trend_encoded'].values
    
    X_unlabeled = unlabeled_df[encoded_cols].values if len(unlabeled_df) > 0 else None
    
    print(f"\nFeature matrix shape: {X_labeled.shape}")
    print(f"Target vector shape: {y_labeled.shape}")
    
    return X_labeled, y_labeled, X_unlabeled, unlabeled_df

def train_model(X, y):
    """Train Random Forest classifier"""
    print("\n" + "=" * 60)
    print("TRAINING RANDOM FOREST MODEL")
    print("=" * 60)
    
    # Split data for training and testing
    # Note: Not using stratify because we have very few samples in some classes
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    
    # Train Random Forest
    print("\nTraining Random Forest with 100 estimators...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        class_weight='balanced'  # Handle class imbalance
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✓ Model trained successfully!")
    print(f"Test Accuracy: {accuracy:.2%}")
    
    # Cross-validation (use fewer folds due to small sample size)
    print("\nPerforming 3-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=3)
    print(f"Cross-validation scores: {cv_scores}")
    print(f"Average CV accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
    
    # Classification report
    print("\nClassification Report:")
    try:
        print(classification_report(
            y_test, y_pred,
            target_names=encoders['population_trend'].classes_,
            zero_division=0
        ))
    except:
        # Fallback if some classes not in test set
        print(classification_report(y_test, y_pred, zero_division=0))
    
    # Confusion matrix
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # Feature importance
    print("\nFeature Importances:")
    feature_names = ['category', 'kingdom', 'phylum', 'class', 'order', 'family']
    importances = model.feature_importances_
    for name, importance in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {importance:.4f}")
    
    return model

def predict_unknown_trends(model, X_unlabeled, unlabeled_df):
    """Predict population trends for unlabeled species"""
    print("\n" + "=" * 60)
    print("PREDICTING UNKNOWN POPULATION TRENDS")
    print("=" * 60)
    
    if X_unlabeled is None or len(X_unlabeled) == 0:
        print("\nNo unlabeled species to predict.")
        return
    
    # Make predictions
    predictions = model.predict(X_unlabeled)
    prediction_proba = model.predict_proba(X_unlabeled)
    
    # Decode predictions
    predicted_trends = encoders['population_trend'].inverse_transform(predictions)
    
    # Get confidence scores
    max_probas = prediction_proba.max(axis=1)
    
    # Show results
    print(f"\nPredicted {len(predictions)} species")
    print("\nPrediction distribution:")
    unique, counts = np.unique(predicted_trends, return_counts=True)
    for trend, count in zip(unique, counts):
        print(f"  {trend}: {count}")
    
    # Show some examples
    print("\nSample predictions (high confidence):")
    sorted_indices = np.argsort(max_probas)[::-1][:10]
    
    for idx in sorted_indices:
        species_id = unlabeled_df.iloc[idx]['id']
        name = unlabeled_df.iloc[idx]['scientific_name']
        pred_trend = predicted_trends[idx]
        confidence = max_probas[idx]
        print(f"  ID {species_id}: {name} → {pred_trend} ({confidence:.2%} confidence)")
    
    # Update database
    print("\nUpdating database with predictions...")
    with app.app_context():
        updated_count = 0
        for idx, species_id in enumerate(unlabeled_df['id']):
            species = Species.query.get(species_id)
            if species:
                species.population_trend = predicted_trends[idx]
                updated_count += 1
        
        try:
            db.session.commit()
            print(f"✓ Updated {updated_count} species in database")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating database: {e}")

def save_model_and_encoders(model):
    """Save trained model and encoders"""
    print("\n" + "=" * 60)
    print("SAVING MODEL AND ENCODERS")
    print("=" * 60)
    
    # Save model
    joblib.dump(model, 'ml_model.pkl')
    print("✓ Saved model to ml_model.pkl")
    
    # Save encoders
    joblib.dump(encoders, 'encoders.pkl')
    print("✓ Saved encoders to encoders.pkl")
    
    print("\nModel artifacts saved successfully!")

def main():
    """Main training pipeline"""
    print("\n" + "=" * 60)
    print("WILDLIFE CONSERVATION TRACKER - ML MODEL TRAINING")
    print("=" * 60)
    
    # Load data
    df = load_data_from_database()
    
    # Prepare features
    X_labeled, y_labeled, X_unlabeled, unlabeled_df = prepare_features(df)
    
    if X_labeled is None:
        return
    
    # Train model
    model = train_model(X_labeled, y_labeled)
    
    # Predict unknown trends
    if X_unlabeled is not None:
        predict_unknown_trends(model, X_unlabeled, unlabeled_df)
    
    # Save model
    save_model_and_encoders(model)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add prediction endpoint to Flask API")
    print("2. Test predictions via API")
    print("3. Build React frontend")

if __name__ == '__main__':
    main()