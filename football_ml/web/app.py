from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
from football_ml.core.inference.predict import Predictor
from football_ml.core.inference.simulation import SeasonSimulator
from football_ml.core.constants import COMP_NAMES

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Initialize core components
predictor = Predictor()
simulator = SeasonSimulator()

def get_latest_team_stats():
    # Load processed features to get latest team stats
    processed_path = "data/processed/match_features.csv"
    if not os.path.exists(processed_path):
        return pd.DataFrame()
    df = pd.read_csv(processed_path)
    return predictor.get_team_latest_stats(df)

@app.route('/')
def index():
    selected_comp = request.args.get('comp', 'PL')
    team_stats = get_latest_team_stats()
    
    if team_stats.empty:
        return "No data found. Please run ingestion and processing scripts.", 500

    upcoming = predictor.predict_upcoming(selected_comp, team_stats)
    
    sim_results = pd.DataFrame()
    standings_path = f"data/raw/{selected_comp}_standings.json"
    if os.path.exists(standings_path) and not upcoming.empty:
        sim_results = simulator.simulate(upcoming, standings_path, num_simulations=500)
    
    # Fetch historical data for charts
    processed_path = "data/processed/match_features.csv"
    chart_data = {}
    if os.path.exists(processed_path):
        df = pd.read_csv(processed_path)
        comp_df = df[df['competition'] == selected_comp].sort_values('utcDate')
        
        # Get top 5 teams in standings to keep chart clean
        top_teams = []
        if not sim_results.empty:
            top_teams = sim_results.head(5)['team'].tolist()
        
        for team in top_teams:
            team_matches = comp_df[(comp_df['home_team'] == team) | (comp_df['away_team'] == team)]
            elo_history = []
            for _, row in team_matches.iterrows():
                val = row['home_elo'] if row['home_team'] == team else row['away_elo']
                elo_history.append({'x': row['utcDate'][:10], 'y': float(val)})
            chart_data[team] = elo_history

    return render_template('index.html', 
                           selected_comp=selected_comp,
                           comp_name=COMP_NAMES.get(selected_comp, selected_comp),
                           all_comps=COMP_NAMES,
                           upcoming=upcoming.to_dict(orient='records') if not upcoming.empty else [],
                           simulations=sim_results.to_dict(orient='records') if not sim_results.empty else [],
                           chart_data=chart_data)

@app.route('/match/<int:match_id>')
def match_simulation(match_id):
    selected_comp = request.args.get('comp', 'PL')
    team_stats = get_latest_team_stats()
    
    raw_match_path = f"data/raw/{selected_comp}_matches.json"
    if not os.path.exists(raw_match_path):
        return "Competition data not found", 404
        
    with open(raw_match_path, 'r') as f:
        data = json.load(f)
    
    match = next((m for m in data.get('matches', []) if m['id'] == match_id), None)
    if not match:
        return "Match not found", 404
        
    home = match['homeTeam']['name']
    away = match['awayTeam']['name']
    
    if home not in team_stats.index or away not in team_stats.index:
        return "Team stats not found", 404
        
    features = [
        team_stats.loc[home, 'rolling_pts'],
        team_stats.loc[away, 'rolling_pts'],
        team_stats.loc[home, 'rolling_gf'],
        team_stats.loc[home, 'rolling_ga'],
        team_stats.loc[away, 'rolling_gf'],
        team_stats.loc[away, 'rolling_ga']
    ]
    
    probs = predictor.m_out.predict_proba([features])[0]
    ou_prob = predictor.m_ou.predict_proba([features])[0][1]
    
    match_data = {
        'home': home,
        'away': away,
        'prob_home': float(probs[0]),
        'prob_draw': float(probs[1]),
        'prob_away': float(probs[2]),
        'prob_over_2_5': float(ou_prob)
    }
    
    return render_template('match.html', match=match_data)

@app.route('/custom-match', methods=['GET', 'POST'])
def custom_match():
    team_stats = get_latest_team_stats()
    all_teams = sorted(team_stats.index.tolist())
    
    if request.method == 'POST':
        home = request.form.get('home_team')
        away = request.form.get('away_team')
        
        if home == away:
            return "Teams must be different", 400
            
        features = [
            team_stats.loc[home, 'rolling_pts'],
            team_stats.loc[away, 'rolling_pts'],
            team_stats.loc[home, 'rolling_gf'],
            team_stats.loc[home, 'rolling_ga'],
            team_stats.loc[away, 'rolling_gf'],
            team_stats.loc[away, 'rolling_ga']
        ]
        
        probs = predictor.m_out.predict_proba([features])[0]
        ou_prob = predictor.m_ou.predict_proba([features])[0][1]
        
        match_data = {
            'home': home,
            'away': away,
            'prob_home': float(probs[0]),
            'prob_draw': float(probs[1]),
            'prob_away': float(probs[2]),
            'prob_over_2_5': float(ou_prob)
        }
        return render_template('match.html', match=match_data)
        
    return render_template('custom_selection.html', teams=all_teams)

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, port=5001)
