import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, accuracy_score
import pickle
import os
import optuna
from football_ml.core.constants import FEATURES

class ModelTrainer:
    def __init__(self, model_dir="models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

    def optimize_hyperparameters(self, X, y, is_multiclass=True):
        def objective(trial):
            param = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'random_state': 42,
                'n_jobs': -1
            }
            model = xgb.XGBClassifier(**param)
            
            # Simple temporal split for validation
            split = int(len(X) * 0.8)
            X_train, X_val = X.iloc[:split], X.iloc[split:]
            y_train, y_val = y.iloc[:split], y.iloc[split:]
            
            model.fit(X_train, y_train)
            return model.score(X_val, y_val)

        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=20)
        return study.best_params

    def train(self, processed_csv="data/processed/match_features.csv"):
        df = pd.read_csv(processed_csv)
        df = df.sort_values('utcDate')
        
        X = df[FEATURES]
        y_outcome = df['target']
        y_over_under = df['over_2_5']
        
        split_idx = int(len(df) * 0.8)
        X_train_full, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_out_train_full, y_out_test = y_outcome.iloc[:split_idx], y_outcome.iloc[split_idx:]
        y_ou_train_full, y_ou_test = y_over_under.iloc[:split_idx], y_over_under.iloc[split_idx:]
        
        print("\n--- Optimizing Outcome Model ---")
        best_out_params = self.optimize_hyperparameters(X_train_full, y_out_train_full, is_multiclass=True)
        model_outcome = xgb.XGBClassifier(**best_out_params, random_state=42)
        model_outcome.fit(X_train_full, y_out_train_full)
        
        print("\n--- Optimizing Over/Under Model ---")
        best_ou_params = self.optimize_hyperparameters(X_train_full, y_ou_train_full, is_multiclass=False)
        model_ou = xgb.XGBClassifier(**best_ou_params, random_state=42)
        model_ou.fit(X_train_full, y_ou_train_full)
        
        # Evaluate
        self._evaluate("Outcome", y_out_test, model_outcome.predict(X_test))
        self._evaluate("Over/Under", y_ou_test, model_ou.predict(X_test))
        
        # Save
        self.save_model(model_outcome, "outcome_model.pkl")
        self.save_model(model_ou, "over_under_model.pkl")
        
        return model_outcome, model_ou

    def _evaluate(self, name, y_true, y_pred):
        print(f"\n--- {name} Model ---")
        print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")
        print(classification_report(y_true, y_pred))

    def save_model(self, model, filename):
        path = os.path.join(self.model_dir, filename)
        with open(path, "wb") as f:
            pickle.dump(model, f)
