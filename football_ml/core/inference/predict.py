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

    def predict_single_match(self, home_team, away_team, team_stats):
        if home_team not in team_stats.index or away_team not in team_stats.index:
            return None
            
        h = team_stats.loc[home_team]
        a = team_stats.loc[away_team]
        
        features = [
            h['rolling_pts'], a['rolling_pts'],
            h['rolling_gf'], h['rolling_ga'],
            a['rolling_gf'], a['rolling_ga'],
            h['home_v_form'], a['away_v_form'],
            h['elo'], a['elo']
        ]
        
        probs = self.m_out.predict_proba([features])[0]
        ou_prob = self.m_ou.predict_proba([features])[0][1]
        
        return {
            'home': home_team,
            'away': away_team,
            'prob_home': float(probs[0]),
            'prob_draw': float(probs[1]),
            'prob_away': float(probs[2]),
            'prob_over_2_5': float(ou_prob)
        }

    def predict_upcoming(self, comp_code, team_stats, db_path="data/football.db"):
        from football_ml.core.data.db_manager import DatabaseManager
        db = DatabaseManager(db_path)
        
        query = '''
            SELECT m.id, m.utc_date as date, t1.name as home, t2.name as away
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.id
            JOIN teams t2 ON m.away_team_id = t2.id
            WHERE m.competition_code = ? AND m.status IN ('SCHEDULED', 'TIMED')
        '''
        with db.get_connection() as conn:
            df_upcoming = pd.read_sql_query(query, conn, params=(comp_code,))
            
        if df_upcoming.empty:
            return pd.DataFrame()
        
        results = []
        for _, row in df_upcoming.iterrows():
            home, away = row['home'], row['away']
            
            if home in team_stats.index and away in team_stats.index:
                pred = self.predict_single_match(home, away, team_stats)
                if pred:
                    pred['id'] = row['id']
                    pred['date'] = row['date']
                    results.append(pred)
                    
        return pd.DataFrame(results)
