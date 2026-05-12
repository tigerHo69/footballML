import json
import numpy as np
import pandas as pd

class SeasonSimulator:
    def simulate(self, upcoming_preds, current_standings_file, num_simulations=1000):
        with open(current_standings_file, 'r') as f:
            standings_data = json.load(f)
        
        initial_points = {}
        for table in standings_data.get('standings', []):
            if table['type'] == 'TOTAL':
                for entry in table['table']:
                    initial_points[entry['team']['name']] = entry['points']
        
        teams = list(initial_points.keys())
        rank_counts = {team: np.zeros(len(teams) + 1) for team in teams}
        total_points_sum = {team: 0 for team in teams}

        for _ in range(num_simulations):
            sim_points = initial_points.copy()
            
            for _, row in upcoming_preds.iterrows():
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
            
            final_rank = sorted(sim_points.items(), key=lambda x: x[1], reverse=True)
            for rank, (team, pts) in enumerate(final_rank, 1):
                rank_counts[team][rank] += 1
                total_points_sum[team] += pts
                
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
