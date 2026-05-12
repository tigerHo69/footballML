import os
from dotenv import load_dotenv
from football_ml.core.data.ingest import DataIngestor

def main():
    load_dotenv()
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not api_key:
        print("Error: FOOTBALL_DATA_API_KEY not found in .env")
        return

    ingestor = DataIngestor(api_key)
    ingestor.ingest_all()

if __name__ == "__main__":
    main()
