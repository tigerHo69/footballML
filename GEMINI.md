# Football ML Project Instructions

This project is a Machine Learning pipeline for predicting football match outcomes, goal totals, and simulating season-end standings using the `football-data.org` API.

## Project Overview
- **Objective:** Predict Match Outcomes (H/D/A), Over/Under 2.5 Goals, and simulate final league standings.
- **Data Source:** [football-data.org](https://www.football-data.org/) (v4 API).
- **Core Strategy:** Since the free tier lacks historical data, the models use **rolling in-season features** (last 5 games form, goal averages) to capture team momentum and strength.
- **Key Technologies:** Python 3, Flask, XGBoost, Pandas, Scikit-learn.

## Directory Structure
- `football_ml/core/`: Core business logic (Data, ML, Inference).
- `football_ml/cli/`: Command-line entry points.
- `football_ml/web/`: Flask web application.
- `data/raw/`: Raw JSON files fetched from the API.
- `data/processed/`: Structured CSV file (`match_features.csv`).
- `models/`: Pickled XGBoost models.

## Building and Running

### 1. Prerequisites
- Python 3.9+
- A valid `FOOTBALL_DATA_API_KEY` in a `.env` file at the root.
- Install dependencies: `pip3 install -r requirements.txt`

### 2. Execution Pipeline
Run these modules in order:
1.  **Ingest Data:** `python3 -m football_ml.cli.ingest`
2.  **Process Features:** `python3 -m football_ml.cli.process`
3.  **Train Models:** `python3 -m football_ml.cli.train`
4.  **Start Dashboard:** `python3 -m football_ml.web.app` (Starts Flask on port 5001).

## Development Conventions

### Data Integrity & Temporal Safety
- **No Data Leakage:** When calculating rolling features in `process_data.py`, always `shift()` the stats so a match at time *T* only uses data from *T-1* and earlier.
- **Temporal Split:** Use time-series splits for evaluation (e.g., train on early season, test on late season) rather than random K-Fold.

### API Usage
- **Rate Limiting:** The free tier allows 10 requests per minute. `scripts/ingest_data.py` includes `time.sleep(6)` between calls to ensure compliance.
- **Free Tier Constraints:** Only 12 specific competitions are accessible (PL, PD, SA, etc.). See `scripts/ingest_data.py` for the full list.

### Simulation Logic
- **Monte Carlo:** The `simulate_season` function in `predict.py` runs 500+ iterations to generate probability distributions for final ranks.
- **Normalization:** Always normalize match outcome probabilities before passing to `np.random.choice` to prevent floating-point precision errors.

### UI Standards
- **Dark Mode Support:** The dashboard includes a Light/Dark mode toggle using Bootstrap 5's `data-bs-theme`.
- **Navigation:** Use the `?comp=CODE` query parameter in the Flask route to switch between leagues.
