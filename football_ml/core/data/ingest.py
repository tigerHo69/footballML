import os
import time
import requests
import json
from football_ml.core.constants import FREE_COMPETITIONS
from football_ml.core.data.db_manager import DatabaseManager

BASE_URL = "https://api.football-data.org/v4"

class DataIngestor:
    def __init__(self, api_key, db_path="data/football.db"):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
        self.db = DatabaseManager(db_path)

    def fetch_data(self, endpoint, params=None):
        """Fetch data with rate limiting"""
        url = f"{BASE_URL}/{endpoint}"
        print(f"Fetching: {url}")
        
        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limit reached. Sleeping for 60 seconds...")
            time.sleep(60)
            return self.fetch_data(endpoint, params)
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None

    def save_json(self, data, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def _save_to_db(self, comp_code, standings_data, matches_data):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Save Competition
            if matches_data and 'competition' in matches_data:
                c = matches_data['competition']
                area_name = matches_data.get('area', {}).get('name') or standings_data.get('area', {}).get('name') if standings_data else None
                cursor.execute('''
                    INSERT OR REPLACE INTO competitions (code, name, area_name)
                    VALUES (?, ?, ?)
                ''', (c['code'], c['name'], area_name))

            # Save Teams and Standings
            if standings_data and 'standings' in standings_data:
                # Clear old standings for this comp
                cursor.execute('DELETE FROM standings WHERE competition_code = ?', (comp_code,))
                for table in standings_data['standings']:
                    if table['type'] == 'TOTAL':
                        for entry in table['table']:
                            t = entry['team']
                            cursor.execute('''
                                INSERT OR IGNORE INTO teams (id, name, short_name, tla)
                                VALUES (?, ?, ?, ?)
                            ''', (t['id'], t['name'], t['shortName'], t['tla']))
                            
                            cursor.execute('''
                                INSERT INTO standings (competition_code, team_id, points, played_games, position)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (comp_code, t['id'], entry['points'], entry['playedGames'], entry['position']))

            # Save Matches
            if matches_data and 'matches' in matches_data:
                for m in matches_data['matches']:
                    # Ensure teams exist
                    for side in ['homeTeam', 'awayTeam']:
                        t = m[side]
                        cursor.execute('''
                            INSERT OR IGNORE INTO teams (id, name, short_name, tla)
                            VALUES (?, ?, ?, ?)
                        ''', (t['id'], t['name'], t['shortName'], t['tla']))

                    cursor.execute('''
                        INSERT OR REPLACE INTO matches (
                            id, competition_code, utc_date, season_id, status, 
                            home_team_id, away_team_id, home_score, away_score, winner
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        m['id'], comp_code, m['utcDate'], m['season']['id'], m['status'],
                        m['homeTeam']['id'], m['awayTeam']['id'],
                        m['score']['fullTime']['home'], m['score']['fullTime']['away'],
                        m['score']['winner']
                    ))
            conn.commit()

    def ingest_competition(self, comp_code, raw_dir="data/raw"):
        print(f"\nProcessing Competition: {comp_code}")
        
        # 1. Fetch Standings
        standings = self.fetch_data(f"competitions/{comp_code}/standings")
        if standings:
            self.save_json(standings, os.path.join(raw_dir, f"{comp_code}_standings.json"))
            time.sleep(6)
            
        # 2. Fetch Matches
        matches = self.fetch_data(f"competitions/{comp_code}/matches")
        if matches:
            self.save_json(matches, os.path.join(raw_dir, f"{comp_code}_matches.json"))
            time.sleep(6)
            
        # 3. Save to DB
        self._save_to_db(comp_code, standings, matches)

    def ingest_all(self, raw_dir="data/raw"):
        if not self.api_key:
            raise ValueError("API_KEY is required for ingestion")

        for comp in FREE_COMPETITIONS:
            self.ingest_competition(comp, raw_dir)
