# 12 Competitions available in the free tier
FREE_COMPETITIONS = [
    'PL',   # Premier League
    'ELC',  # Championship
    'CL',   # Champions League
    'BL1',  # Bundesliga
    'DED',  # Eredivisie
    'FL1',  # Ligue 1
    'PD',   # Primera Division (La Liga)
    'SA',   # Serie A
    'PPL',  # Primeira Liga
    'WC',   # World Cup
    'EC',   # European Championship
    'CLI'   # Copa Libertadores
]

COMP_NAMES = {
    'PL': 'Premier League', 'ELC': 'Championship', 'CL': 'Champions League',
    'BL1': 'Bundesliga', 'DED': 'Eredivisie', 'FL1': 'Ligue 1',
    'PD': 'La Liga', 'SA': 'Serie A', 'PPL': 'Primeira Liga',
    'WC': 'World Cup', 'EC': 'Euro Championship', 'CLI': 'Copa Libertadores'
}

FEATURES = [
    'home_form', 'away_form', 
    'home_gf_avg', 'home_ga_avg', 
    'away_gf_avg', 'away_ga_avg',
    'home_v_form', 'away_v_form',
    'home_elo', 'away_elo'
]
