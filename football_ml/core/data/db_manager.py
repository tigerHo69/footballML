import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="data/football.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Competitions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competitions (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    area_name TEXT
                )
            ''')
            
            # Teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    short_name TEXT,
                    tla TEXT
                )
            ''')
            
            # Matches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY,
                    competition_code TEXT,
                    utc_date TEXT,
                    season_id INTEGER,
                    status TEXT,
                    home_team_id INTEGER,
                    away_team_id INTEGER,
                    home_score INTEGER,
                    away_score INTEGER,
                    winner TEXT,
                    FOREIGN KEY (competition_code) REFERENCES competitions (code),
                    FOREIGN KEY (home_team_id) REFERENCES teams (id),
                    FOREIGN KEY (away_team_id) REFERENCES teams (id)
                )
            ''')
            
            # Standings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS standings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competition_code TEXT,
                    team_id INTEGER,
                    points INTEGER,
                    played_games INTEGER,
                    position INTEGER,
                    FOREIGN KEY (competition_code) REFERENCES competitions (code),
                    FOREIGN KEY (team_id) REFERENCES teams (id)
                )
            ''')
            
            # Features table (For engineered features)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS match_features (
                    match_id INTEGER PRIMARY KEY,
                    home_form REAL,
                    away_form REAL,
                    home_gf_avg REAL,
                    home_ga_avg REAL,
                    away_gf_avg REAL,
                    away_ga_avg REAL,
                    target INTEGER,
                    over_2_5 INTEGER,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            conn.commit()
