import json
import os
import pandas as pd
import numpy as np
import pickle
from datetime import datetime

def load_models():
    with open("models/outcome_model.pkl", "rb") as f:
        m_out = pickle.load(f)
    with open("models/over_under_model.pkl", "rb") as f:
        m_ou = pickle.load(f)
    return m_out, m_ou

def get_team_latest_stats(processed_df):
    """Get the most recent rolling stats for every team"""
    # Sort by date to get the latest row
    latest = processed_df.sort_values('utcDate').groupby('team').tail(1)
    return latest.set_index('team')[['rolling_pts', 'rolling_gf', 'rolling_ga']]

def predict_upcoming(comp_code, m_out, m_ou, team_stats):
    with open(f"data/raw/{comp_code}_matches.json", 'r') as f:
        data = json.load(f)
    
    upcoming = []
    for m in data['matches']:
        if m['status'] == 'SCHEDULED':
            home = m['homeTeam']['name']
            away = m['awayTeam']['name']
            
            if home in team_stats.index and away in team_stats.index:
                features = [
                    team_stats.loc[home, 'rolling_pts'],
                    team_stats.loc[away, 'rolling_pts'],
                    team_stats.loc[home, 'rolling_gf'],
                    team_stats.loc[home, 'rolling_ga'],
                    team_stats.loc[away, 'rolling_gf'],
                    team_stats.loc[away, 'rolling_ga']
                ]
                
                # Predict Outcome Probabilities
                probs = m_out.predict_proba([features])[0]
                # Predict Over 2.5 Probability
                ou_prob = m_ou.predict_proba([features])[0][1]
                
                upcoming.append({
                    'date': m['utcDate'],
                    'home': home,
                    'away': away,
                    'prob_home': probs[0],
                    'prob_draw': probs[1],
                    'prob_away': probs[2],
                    'prob_over_2_5': ou_prob
                })
                
    return pd.DataFrame(upcoming)

def simulate_season(comp_code, upcoming_preds, current_standings_file, num_simulations=1000):
    with open(current_standings_file, 'r') as f:
        standings_data = json.load(f)
    
    # Extract current points
    initial_points = {}
    for table in standings_data['standings']:
        if table['type'] == 'TOTAL':
            for entry in table['table']:
                initial_points[entry['team']['name']] = entry['points']
    
    teams = list(initial_points.keys())
    # results[team][rank] = count
    rank_counts = {team: np.zeros(len(teams) + 1) for team in teams}
    total_points_sum = {team: 0 for team in teams}

    print(f"Running {num_simulations} simulations for {comp_code}...")
    
    for _ in range(num_simulations):
        sim_points = initial_points.copy()
        
        for _, row in upcoming_preds.iterrows():
            # Normalize probabilities to sum to exactly 1.0 to avoid floating-point precision errors
            probs = np.array([row['prob_home'], row['prob_draw'], row['prob_away']], dtype=np.float64)
            probs /= probs.sum()
            
            outcome = np.random.choice(['HOME', 'DRAW', 'AWAY'], p=probs)
            if outcome == 'HOME':
                sim_points[row['home']] += 3
            elif outcome == 'DRAW':
                sim_points[row['home']] += 1
                sim_points[row['away']] += 1
            else:
                sim_points[row['away']] += 3
        
        # Sort and rank
        final_rank = sorted(sim_points.items(), key=lambda x: x[1], reverse=True)
        for rank, (team, pts) in enumerate(final_rank, 1):
            rank_counts[team][rank] += 1
            total_points_sum[team] += pts
            
    # Compile results
    stats = []
    for team in teams:
        stats.append({
            'team': team,
            'avg_points': total_points_sum[team] / num_simulations,
            'prob_win': rank_counts[team][1] / num_simulations,
            'prob_top4': sum(rank_counts[team][1:5]) / num_simulations,
            'prob_relegation': sum(rank_counts[team][-3:]) / num_simulations if len(teams) > 3 else 0
        })
        
    return pd.DataFrame(stats).sort_values('avg_points', ascending=False)

def main():
    m_out, m_ou = load_models()
    
    # We need the raw data to get the team's latest rolling stats
    df = pd.read_csv("data/processed/match_features.csv")
    
    # Construct team stats correctly
    home_df = df.rename(columns={'home_team': 'team', 'home_form': 'rolling_pts', 'home_gf_avg': 'rolling_gf', 'home_ga_avg': 'rolling_ga'})
    away_df = df.rename(columns={'away_team': 'team', 'away_form': 'rolling_pts', 'away_gf_avg': 'rolling_gf', 'away_ga_avg': 'rolling_ga'})
    combined = pd.concat([home_df, away_df])
    team_stats = get_team_latest_stats(combined)
    
    # Try competitions with scheduled matches
    for comp in ["CLI", "PD", "SA", "PL"]:
        print(f"\n--- Checking Predictions for {comp} ---")
        upcoming = predict_upcoming(comp, m_out, m_ou, team_stats)
        
        if not upcoming.empty:
            print(upcoming[['date', 'home', 'away', 'prob_home', 'prob_draw', 'prob_away']].head(10))
            
            print(f"\n--- Simulated Final Standings for {comp} (1 Run) ---")
            standings = simulate_season(comp, upcoming, f"data/raw/{comp}_standings.json")
            print(standings.head(10))
            break
    else:
        print("No scheduled matches found with sufficient data in any competition.")

if __name__ == "__main__":
    main()
