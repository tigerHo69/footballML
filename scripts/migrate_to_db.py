import json
import os
from football_ml.core.data.ingest import DataIngestor
from football_ml.core.constants import FREE_COMPETITIONS

def migrate_json_to_db():
    ingestor = DataIngestor("MOCK_KEY") # We don't need real key for _save_to_db
    raw_dir = "data/raw"
    
    for comp in FREE_COMPETITIONS:
        standings_path = os.path.join(raw_dir, f"{comp}_standings.json")
        matches_path = os.path.join(raw_dir, f"{comp}_matches.json")
        
        standings = None
        if os.path.exists(standings_path):
            with open(standings_path, 'r') as f:
                standings = json.load(f)
        
        matches = None
        if os.path.exists(matches_path):
            with open(matches_path, 'r') as f:
                matches = json.load(f)
        
        if standings or matches:
            print(f"Migrating {comp} to DB...")
            ingestor._save_to_db(comp, standings, matches)

if __name__ == "__main__":
    migrate_json_to_db()
