import pandas as pd
from football_ml.core.inference.predict import Predictor
from football_ml.core.inference.simulation import SeasonSimulator
from football_ml.core.constants import FREE_COMPETITIONS

def main():
    predictor = Predictor()
    simulator = SeasonSimulator()
    
    from football_ml.core.data.db_manager import DatabaseManager
    db = DatabaseManager()
    query_teams = '''
        SELECT mf.*, m.utc_date as utcDate, t1.name as home_team, t2.name as away_team, m.competition_code as competition
        FROM match_features mf
        JOIN matches m ON mf.match_id = m.id
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
    '''
    with db.get_connection() as conn:
        full_df = pd.read_sql_query(query_teams, conn)
    
    team_stats = predictor.get_team_latest_stats(full_df)
    
    for comp in FREE_COMPETITIONS:
        print(f"\n--- Predictions for {comp} ---")
        upcoming = predictor.predict_upcoming(comp, team_stats)
        
        if not upcoming.empty:
            print(upcoming[['date', 'home', 'away', 'prob_home', 'prob_draw', 'prob_away']].head())
            print(f"\n--- Simulation for {comp} ---")
            standings = simulator.simulate(comp, upcoming, num_simulations=100)
            print(standings.head())
            break

if __name__ == "__main__":
    main()
