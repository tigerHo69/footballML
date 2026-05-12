import os
import time
import requests
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

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

def fetch_data(endpoint, params=None):
    """Fetch data with rate limiting (10 req/min -> 1 req every 6 seconds)"""
    url = f"{BASE_URL}/{endpoint}"
    print(f"Fetching: {url} with params: {params}")
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit reached. Sleeping for 60 seconds...")
        time.sleep(60)
        return fetch_data(endpoint, params)
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def ingest_all():
    if not API_KEY:
        print("Error: FOOTBALL_DATA_API_KEY not found in .env")
        return

    os.makedirs("data/raw", exist_ok=True)

    for comp in FREE_COMPETITIONS:
        print(f"\nProcessing Competition: {comp}")
        
        # 1. Fetch Standings
        standings = fetch_data(f"competitions/{comp}/standings")
        if standings:
            save_json(standings, f"data/raw/{comp}_standings.json")
            time.sleep(6) # Respect rate limit
            
        # 2. Fetch Matches
        matches = fetch_data(f"competitions/{comp}/matches")
        if matches:
            save_json(matches, f"data/raw/{comp}_matches.json")
            time.sleep(6) # Respect rate limit

if __name__ == "__main__":
    ingest_all()
