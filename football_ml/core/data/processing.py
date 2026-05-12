import os
import pandas as pd
import numpy as np
from football_ml.core.data.db_manager import DatabaseManager
from football_ml.core.ml.elo import EloManager

class DataProcessor:
    def __init__(self, window=5, db_path="data/football.db"):
        self.window = window
        self.db = DatabaseManager(db_path)

    def load_finished_matches(self):
        query = '''
            SELECT m.id as match_id, m.utc_date as utcDate, m.competition_code as competition,
                   m.season_id as season, t1.name as home_team, t2.name as away_team,
                   m.home_score, m.away_score, m.winner
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.id
            JOIN teams t2 ON m.away_team_id = t2.id
            WHERE m.status = 'FINISHED'
        '''
        with self.db.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        
        df['utcDate'] = pd.to_datetime(df['utcDate'])
        return df.sort_values('utcDate')

    def calculate_rolling_features(self, df):
        # 1. Base Rolling Features (Global)
        home_matches = df[['utcDate', 'home_team', 'home_score', 'away_score', 'winner']].copy()
        home_matches.columns = ['date', 'team', 'goals_for', 'goals_against', 'winner']
        home_matches['points'] = home_matches['winner'].map({'HOME_TEAM': 3, 'DRAW': 1, 'AWAY_TEAM': 0})
        
        away_matches = df[['utcDate', 'away_team', 'away_score', 'home_score', 'winner']].copy()
        away_matches.columns = ['date', 'team', 'goals_for', 'goals_against', 'winner']
        away_matches['points'] = away_matches['winner'].map({'AWAY_TEAM': 3, 'DRAW': 1, 'HOME_TEAM': 0})
        
        team_matches = pd.concat([home_matches, away_matches]).sort_values('date')
        
        group = team_matches.groupby('team')
        team_stats = team_matches.copy()
        team_stats['rolling_pts'] = group['points'].transform(lambda x: x.shift().rolling(self.window, min_periods=1).mean())
        team_stats['rolling_gf'] = group['goals_for'].transform(lambda x: x.shift().rolling(self.window, min_periods=1).mean())
        team_stats['rolling_ga'] = group['goals_against'].transform(lambda x: x.shift().rolling(self.window, min_periods=1).mean())
        
        # 2. Venue-Specific Features
        # Home performance when playing at HOME
        home_only = df[['utcDate', 'home_team', 'home_score', 'away_score', 'winner']].copy()
        home_only.columns = ['date', 'team', 'goals_for', 'goals_against', 'winner']
        home_only['points'] = home_only['winner'].map({'HOME_TEAM': 3, 'DRAW': 1, 'AWAY_TEAM': 0})
        home_group = home_only.groupby('team')
        home_only['home_v_form'] = home_group['points'].transform(lambda x: x.shift().rolling(self.window, min_periods=1).mean())
        
        # Away performance when playing AWAY
        away_only = df[['utcDate', 'away_team', 'away_score', 'home_score', 'winner']].copy()
        away_only.columns = ['date', 'team', 'goals_for', 'goals_against', 'winner']
        away_only['points'] = away_only['winner'].map({'AWAY_TEAM': 3, 'DRAW': 1, 'HOME_TEAM': 0})
        away_group = away_only.groupby('team')
        away_only['away_v_form'] = away_group['points'].transform(lambda x: x.shift().rolling(self.window, min_periods=1).mean())

        # 3. ELO Ratings
        elo = EloManager()
        home_elos = []
        away_elos = []
        for _, row in df.iterrows():
            h_elo, a_elo = elo.update_ratings(row['home_team'], row['away_team'], row['winner'])
            home_elos.append(h_elo)
            away_elos.append(a_elo)
        df['home_elo'] = home_elos
        df['away_elo'] = away_elos

        # Merge all back
        df = df.merge(
            team_stats[['date', 'team', 'rolling_pts', 'rolling_gf', 'rolling_ga']], 
            left_on=['utcDate', 'home_team'], right_on=['date', 'team'], how='left'
        ).rename(columns={'rolling_pts': 'home_form', 'rolling_gf': 'home_gf_avg', 'rolling_ga': 'home_ga_avg'}).drop(['date', 'team'], axis=1)
        
        df = df.merge(
            team_stats[['date', 'team', 'rolling_pts', 'rolling_gf', 'rolling_ga']], 
            left_on=['utcDate', 'away_team'], right_on=['date', 'team'], how='left'
        ).rename(columns={'rolling_pts': 'away_form', 'rolling_gf': 'away_gf_avg', 'rolling_ga': 'away_ga_avg'}).drop(['date', 'team'], axis=1)

        df = df.merge(home_only[['date', 'team', 'home_v_form']], left_on=['utcDate', 'home_team'], right_on=['date', 'team'], how='left').drop(['date', 'team'], axis=1)
        df = df.merge(away_only[['date', 'team', 'away_v_form']], left_on=['utcDate', 'away_team'], right_on=['date', 'team'], how='left').drop(['date', 'team'], axis=1)
        
        return df

    def process_all_and_save(self):
        df = self.load_finished_matches()
        if df.empty:
            print("No finished matches found in database.")
            return
            
        # Group by competition to ensure rolling stats don't cross leagues
        processed_list = []
        for comp, comp_df in df.groupby('competition'):
            processed_list.append(self.calculate_rolling_features(comp_df))
            
        final_df = pd.concat(processed_list)
        final_df['target'] = final_df['winner'].map({'HOME_TEAM': 0, 'DRAW': 1, 'AWAY_TEAM': 2})
        final_df['total_goals'] = final_df['home_score'] + final_df['away_score']
        final_df['over_2_5'] = (final_df['total_goals'] > 2.5).astype(int)
        
        final_df = final_df.dropna(subset=['home_form', 'away_form'])
        
        # Save to SQL Features table
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Ensure the table matches the new features
            cursor.execute('DROP TABLE IF EXISTS match_features')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS match_features (
                    match_id INTEGER PRIMARY KEY,
                    home_form REAL, away_form REAL,
                    home_gf_avg REAL, home_ga_avg REAL,
                    away_gf_avg REAL, away_ga_avg REAL,
                    home_v_form REAL, away_v_form REAL,
                    home_elo REAL, away_elo REAL,
                    target INTEGER, over_2_5 INTEGER,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            for _, row in final_df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO match_features (
                        match_id, home_form, away_form, home_gf_avg, home_ga_avg, 
                        away_gf_avg, away_ga_avg, home_v_form, away_v_form,
                        home_elo, away_elo, target, over_2_5
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    int(row['match_id']), float(row['home_form']), float(row['away_form']),
                    float(row['home_gf_avg']), float(row['home_ga_avg']),
                    float(row['away_gf_avg']), float(row['away_ga_avg']),
                    float(row['home_v_form']) if not pd.isna(row['home_v_form']) else 0,
                    float(row['away_v_form']) if not pd.isna(row['away_v_form']) else 0,
                    float(row['home_elo']), float(row['away_elo']),
                    int(row['target']), int(row['over_2_5'])
                ))
            conn.commit()
            
        print(f"Saved {len(final_df)} rows to SQLite.")
        return final_df
