import json
import os
import pandas as pd
import numpy as np
from glob import glob

def load_matches(comp_code):
    with open(f"data/raw/{comp_code}_matches.json", 'r') as f:
        data = json.load(f)
    return data['matches']

def process_matches(matches):
    df_list = []
    for m in matches:
        # We only care about finished matches for training
        if m['status'] != 'FINISHED':
            continue
            
        row = {
            'match_id': m['id'],
            'utcDate': m['utcDate'],
            'competition': m['competition']['code'],
            'season': m['season']['id'],
            'home_team': m['homeTeam']['name'],
            'away_team': m['awayTeam']['name'],
            'home_score': m['score']['fullTime']['home'],
            'away_score': m['score']['fullTime']['away'],
            'winner': m['score']['winner'] # HOME_TEAM, AWAY_TEAM, DRAW
        }
        df_list.append(row)
    
    if not df_list:
        return pd.DataFrame()

    df = pd.DataFrame(df_list)
    df['utcDate'] = pd.to_datetime(df['utcDate'])
    df = df.sort_values('utcDate')
    return df

def calculate_rolling_features(df, window=5):
    """
    Calculate rolling features (Form, Goals Scored, Goals Conceded) 
    for each team within a competition season.
    """
    # Create a long-form dataframe where each row is a team's performance in a match
    home_matches = df[['utcDate', 'home_team', 'home_score', 'away_score', 'winner']].copy()
    home_matches.columns = ['date', 'team', 'goals_for', 'goals_against', 'winner']
    home_matches['is_home'] = 1
    home_matches['points'] = home_matches['winner'].map({'HOME_TEAM': 3, 'DRAW': 1, 'AWAY_TEAM': 0})
    
    away_matches = df[['utcDate', 'away_team', 'away_score', 'home_score', 'winner']].copy()
    away_matches.columns = ['date', 'team', 'goals_for', 'goals_against', 'winner']
    away_matches['is_home'] = 0
    away_matches['points'] = away_matches['winner'].map({'AWAY_TEAM': 3, 'DRAW': 1, 'HOME_TEAM': 0})
    
    team_matches = pd.concat([home_matches, away_matches]).sort_values('date')
    
    # Calculate rolling metrics
    team_stats = team_matches.groupby('team', group_keys=False).apply(lambda x: x.sort_values('date')).reset_index(drop=True)
    
    # We must SHIFT the rolling metrics so that a match at time T only sees data from T-1 and before
    group = team_stats.groupby('team')
    team_stats['rolling_pts'] = group['points'].transform(lambda x: x.shift().rolling(window, min_periods=1).mean())
    team_stats['rolling_gf'] = group['goals_for'].transform(lambda x: x.shift().rolling(window, min_periods=1).mean())
    team_stats['rolling_ga'] = group['goals_against'].transform(lambda x: x.shift().rolling(window, min_periods=1).mean())
    
    # Merge back into the original dataframe
    # Merge for home team
    df = df.merge(
        team_stats[['date', 'team', 'rolling_pts', 'rolling_gf', 'rolling_ga']], 
        left_on=['utcDate', 'home_team'], 
        right_on=['date', 'team'], 
        how='left'
    ).rename(columns={
        'rolling_pts': 'home_form', 
        'rolling_gf': 'home_gf_avg', 
        'rolling_ga': 'home_ga_avg'
    }).drop(['date', 'team'], axis=1)
    
    # Merge for away team
    df = df.merge(
        team_stats[['date', 'team', 'rolling_pts', 'rolling_gf', 'rolling_ga']], 
        left_on=['utcDate', 'away_team'], 
        right_on=['date', 'team'], 
        how='left'
    ).rename(columns={
        'rolling_pts': 'away_form', 
        'rolling_gf': 'away_gf_avg', 
        'rolling_ga': 'away_ga_avg'
    }).drop(['date', 'team'], axis=1)
    
    return df

def main():
    os.makedirs("data/processed", exist_ok=True)
    comp_files = glob("data/raw/*_matches.json")
    
    all_processed = []
    
    for f in comp_files:
        comp_code = os.path.basename(f).split('_')[0]
        print(f"Processing features for {comp_code}...")
        
        matches = load_matches(comp_code)
        if not matches:
            continue
            
        df = process_matches(matches)
        if df.empty:
            continue
            
        df = calculate_rolling_features(df)
        all_processed.append(df)
        
    final_df = pd.concat(all_processed)
    final_df['target'] = final_df['winner'].map({'HOME_TEAM': 0, 'DRAW': 1, 'AWAY_TEAM': 2})
    final_df['total_goals'] = final_df['home_score'] + final_df['away_score']
    final_df['over_2_5'] = (final_df['total_goals'] > 2.5).astype(int)
    
    # Drop rows with NaN in rolling features (usually the first few games of the season)
    final_df = final_df.dropna(subset=['home_form', 'away_form'])
    
    final_df.to_csv("data/processed/match_features.csv", index=False)
    print(f"Saved {len(final_df)} rows to data/processed/match_features.csv")

if __name__ == "__main__":
    main()
