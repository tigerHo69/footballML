class EloManager:
    def __init__(self, k_factor=32, initial_rating=1500):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings = {}

    def get_rating(self, team):
        return self.ratings.get(team, self.initial_rating)

    def update_ratings(self, home_team, away_team, winner):
        r_home = self.get_rating(home_team)
        r_away = self.get_rating(away_team)

        # Expected score
        e_home = 1 / (1 + 10 ** ((r_away - r_home) / 400))
        e_away = 1 - e_home

        # Actual score
        if winner == 'HOME_TEAM':
            s_home, s_away = 1, 0
        elif winner == 'AWAY_TEAM':
            s_home, s_away = 0, 1
        else:
            s_home, s_away = 0.5, 0.5

        # Update ratings
        new_r_home = r_home + self.k_factor * (s_home - e_home)
        new_r_away = r_away + self.k_factor * (s_away - e_away)
        
        self.ratings[home_team] = new_r_home
        self.ratings[away_team] = new_r_away
        
        return r_home, r_away # Return ratings BEFORE the match for feature calculation
