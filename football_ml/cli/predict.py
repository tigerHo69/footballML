import pandas as pd
from football_ml.core.inference.predict import Predictor
from football_ml.core.inference.simulation import SeasonSimulator
from football_ml.core.constants import FREE_COMPETITIONS

def main():
    predictor = Predictor()
    simulator = SeasonSimulator()
    
    df = pd.read_csv("data/processed/match_features.csv")
    team_stats = predictor.get_team_latest_stats(df)
    
    for comp in FREE_COMPETITIONS:
        print(f"\n--- Predictions for {comp} ---")
        upcoming = predictor.predict_upcoming(comp, team_stats)
        
        if not upcoming.empty:
            print(upcoming[['date', 'home', 'away', 'prob_home', 'prob_draw', 'prob_away']].head())
            print(f"\n--- Simulation for {comp} ---")
            standings = simulator.simulate(upcoming, f"data/raw/{comp}_standings.json", num_simulations=100)
            print(standings.head())
            break

if __name__ == "__main__":
    main()
