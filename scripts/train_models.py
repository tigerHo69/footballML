import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pickle
import os

def train_models():
    df = pd.read_csv("data/processed/match_features.csv")
    
    # Sort by date for temporal split
    df = df.sort_values('utcDate')
    
    features = [
        'home_form', 'away_form', 
        'home_gf_avg', 'home_ga_avg', 
        'away_gf_avg', 'away_ga_avg'
    ]
    
    X = df[features]
    y_outcome = df['target']
    y_over_under = df['over_2_5']
    
    # Temporal Split: 80% train, 20% test
    split_idx = int(len(df) * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_out_train, y_out_test = y_outcome.iloc[:split_idx], y_outcome.iloc[split_idx:]
    y_ou_train, y_ou_test = y_over_under.iloc[:split_idx], y_over_under.iloc[split_idx:]
    
    os.makedirs("models", exist_ok=True)
    
    # 1. Match Outcome Model (H/D/A)
    print("\n--- Training Match Outcome Model (0=Home, 1=Draw, 2=Away) ---")
    model_outcome = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=3, 
        learning_rate=0.1, 
        random_state=42
    )
    model_outcome.fit(X_train, y_out_train)
    
    preds_out = model_outcome.predict(X_test)
    print(f"Outcome Accuracy: {accuracy_score(y_out_test, preds_out):.4f}")
    print(classification_report(y_out_test, preds_out))
    
    with open("models/outcome_model.pkl", "wb") as f:
        pickle.dump(model_outcome, f)
        
    # 2. Over/Under 2.5 Goals Model
    print("\n--- Training Over/Under 2.5 Goals Model ---")
    model_ou = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=3, 
        learning_rate=0.1, 
        random_state=42
    )
    model_ou.fit(X_train, y_ou_train)
    
    preds_ou = model_ou.predict(X_test)
    print(f"Over/Under Accuracy: {accuracy_score(y_ou_test, preds_ou):.4f}")
    print(classification_report(y_ou_test, preds_ou))
    
    with open("models/over_under_model.pkl", "wb") as f:
        pickle.dump(model_ou, f)

if __name__ == "__main__":
    train_models()
