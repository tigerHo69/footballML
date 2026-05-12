from flask import Flask, render_template, request
import pandas as pd
import os
import traceback
from football_ml.core.inference.predict import Predictor
from football_ml.core.inference.simulation import SeasonSimulator
from football_ml.core.constants import COMP_NAMES
from football_ml.core.data.db_manager import DatabaseManager

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Initialize core components
predictor = Predictor()
simulator = SeasonSimulator()
db = DatabaseManager()

@app.errorhandler(Exception)
def handle_exception(e):
    print("!!! SERVER ERROR !!!")
    print(traceback.format_exc())
    return "Internal Server Error. Check server logs.", 500

def get_latest_team_stats():
    # Read features from SQL
    query = "SELECT * FROM match_features"
    with db.get_connection() as conn:
        df = pd.read_sql_query(query, conn)
    
    if df.empty:
        return pd.DataFrame()
        
    # Join with matches to get team names and dates
    query_teams = '''
        SELECT mf.*, m.utc_date as utcDate, t1.name as home_team, t2.name as away_team, m.competition_code as competition
        FROM match_features mf
        JOIN matches m ON mf.match_id = m.id
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
    '''
    with db.get_connection() as conn:
        full_df = pd.read_sql_query(query_teams, conn)
        
    return predictor.get_team_latest_stats(full_df)

@app.route('/')
def index():
    selected_comp = request.args.get('comp', 'PL')
    team_stats = get_latest_team_stats()
    
    if team_stats.empty:
        return "No data found in database. Please run ingestion and processing scripts.", 500

    upcoming = predictor.predict_upcoming(selected_comp, team_stats)
    
    sim_results = pd.DataFrame()
    standings_path = f"data/raw/{selected_comp}_standings.json"
    if os.path.exists(standings_path) and not upcoming.empty:
        sim_results = simulator.simulate(upcoming, standings_path, num_simulations=500)
    
    # Fetch historical data for charts from SQL
    chart_data = {}
    query_history = '''
        SELECT mf.home_elo, mf.away_elo, m.utc_date as utcDate, t1.name as home_team, t2.name as away_team
        FROM match_features mf
        JOIN matches m ON mf.match_id = m.id
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        WHERE m.competition_code = ?
        ORDER BY m.utc_date ASC
    '''
    with db.get_connection() as conn:
        history_df = pd.read_sql_query(query_history, conn, params=(selected_comp,))
        
    if not history_df.empty:
        top_teams = []
        if not sim_results.empty:
            top_teams = sim_results.head(5)['team'].tolist()
        
        for team in top_teams:
            team_matches = history_df[(history_df['home_team'] == team) | (history_df['away_team'] == team)]
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
    team_stats = get_latest_team_stats()
    
    # Get match details from SQL
    query = '''
        SELECT t1.name as home_team, t2.name as away_team
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        WHERE m.id = ?
    '''
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (match_id,))
        match = cursor.fetchone()
        
    if not match:
        return "Match not found in database", 404
        
    home, away = match
    match_data = predictor.predict_single_match(home, away, team_stats)
    
    if not match_data:
        return "Team stats not found", 404
        
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
            
        match_data = predictor.predict_single_match(home, away, team_stats)
        if not match_data:
            return "Team stats not found", 400
            
        return render_template('match.html', match=match_data)
        
    return render_template('custom_selection.html', teams=all_teams)

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host='0.0.0.0', debug=debug_mode, port=5001)
