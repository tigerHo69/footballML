import json
import os
import pandas as pd
import pickle
from football_ml.core.constants import FEATURES

class Predictor:
    def __init__(self, model_dir="models"):
        self.m_out, self.m_ou = self.load_models(model_dir)

    def load_models(self, model_dir):
        with open(os.path.join(model_dir, "outcome_model.pkl"), "rb") as f:
            m_out = pickle.load(f)
        with open(os.path.join(model_dir, "over_under_model.pkl"), "rb") as f:
            m_ou = pickle.load(f)
        return m_out, m_ou

    def get_team_latest_stats(self, processed_df):
        # Extract the latest stats for each team from the processed match features
        home_stats = processed_df.rename(columns={
            'home_team': 'team', 'home_form': 'rolling_pts', 
            'home_gf_avg': 'rolling_gf', 'home_ga_avg': 'rolling_ga',
            'home_v_form': 'venue_form', 'home_elo': 'elo'
        })
        away_stats = processed_df.rename(columns={
            'away_team': 'team', 'away_form': 'rolling_pts', 
            'away_gf_avg': 'rolling_gf', 'away_ga_avg': 'rolling_ga',
            'away_v_form': 'venue_form', 'away_elo': 'elo'
        })
        
        combined = pd.concat([home_stats, away_stats]).sort_values('utcDate')
        latest = combined.groupby('team').tail(1)
        
        # We also need the latest venue-specific form for both venues
        latest_home = home_stats.sort_values('utcDate').groupby('team').tail(1).set_index('team')['venue_form']
        latest_away = away_stats.sort_values('utcDate').groupby('team').tail(1).set_index('team')['venue_form']
        
        latest_stats = latest.set_index('team')[['rolling_pts', 'rolling_gf', 'rolling_ga', 'elo']]
        latest_stats['home_v_form'] = latest_home
        latest_stats['away_v_form'] = latest_away
        
        return latest_stats.fillna(0)

    def predict_upcoming(self, comp_code, team_stats, raw_dir="data/raw"):
        path = os.path.join(raw_dir, f"{comp_code}_matches.json")
        if not os.path.exists(path):
            return pd.DataFrame()
            
        with open(path, 'r') as f:
            data = json.load(f)
        
        upcoming = []
        for m in data.get('matches', []):
            if m['status'] in ['SCHEDULED', 'TIMED']:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                
                if home in team_stats.index and away in team_stats.index:
                    h = team_stats.loc[home]
                    a = team_stats.loc[away]
                    
                    features = [
                        h['rolling_pts'], a['rolling_pts'],
                        h['rolling_gf'], h['rolling_ga'],
                        a['rolling_gf'], a['rolling_ga'],
                        h['home_v_form'], a['away_v_form'],
                        h['elo'], a['elo']
                    ]
                    
                    probs = self.m_out.predict_proba([features])[0]
                    ou_prob = self.m_ou.predict_proba([features])[0][1]
                    
                    upcoming.append({
                        'id': m['id'],
                        'date': m['utcDate'],
                        'home': home,
                        'away': away,
                        'prob_home': float(probs[0]),
                        'prob_draw': float(probs[1]),
                        'prob_away': float(probs[2]),
                        'prob_over_2_5': float(ou_prob)
                    })
                    
        return pd.DataFrame(upcoming)
