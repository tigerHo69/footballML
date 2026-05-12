from flask import Flask, render_template, jsonify
import pandas as pd
import json
import os
import pickle
from scripts.predict import load_models, get_team_latest_stats, predict_upcoming, simulate_season

app = Flask(__name__)

# Load models once
m_out, m_ou = load_models()

def get_full_data():
    # Load processed features to get latest team stats
    df = pd.read_csv("data/processed/match_features.csv")
    home_df = df.rename(columns={'home_team': 'team', 'home_form': 'rolling_pts', 'home_gf_avg': 'rolling_gf', 'home_ga_avg': 'rolling_ga'})
    away_df = df.rename(columns={'away_team': 'team', 'away_form': 'rolling_pts', 'away_gf_avg': 'rolling_gf', 'away_ga_avg': 'rolling_ga'})
    combined = pd.concat([home_df, away_df])
    team_stats = get_team_latest_stats(combined)
    return team_stats

# Mapping for display names
COMP_NAMES = {
    'PL': 'Premier League', 'ELC': 'Championship', 'CL': 'Champions League',
    'BL1': 'Bundesliga', 'DED': 'Eredivisie', 'FL1': 'Ligue 1',
    'PD': 'La Liga', 'SA': 'Serie A', 'PPL': 'Primeira Liga',
    'WC': 'World Cup', 'EC': 'Euro Championship', 'CLI': 'Copa Libertadores'
}

@app.route('/')
def index():
    from flask import request
    # Default to PL, but allow switching via query param
    selected_comp = request.args.get('comp', 'PL')
    
    team_stats = get_full_data()
    results = []
    
    # Process the selected competition
    upcoming = predict_upcoming(selected_comp, m_out, m_ou, team_stats)
    
    sim_results = pd.DataFrame()
    if os.path.exists(f"data/raw/{selected_comp}_standings.json"):
        # Run more simulations for the single selected league
        sim_results = simulate_season(selected_comp, upcoming, f"data/raw/{selected_comp}_standings.json", num_simulations=500)
    
    return render_template('index.html', 
                           results=results, 
                           selected_comp=selected_comp,
                           comp_name=COMP_NAMES.get(selected_comp, selected_comp),
                           all_comps=COMP_NAMES,
                           upcoming=upcoming.to_dict(orient='records') if not upcoming.empty else [],
                           simulations=sim_results.to_dict(orient='records') if not sim_results.empty else [])

if __name__ == '__main__':
    # Add flask to requirements if not there
    app.run(debug=True, port=5001)
