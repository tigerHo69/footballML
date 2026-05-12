# Football ML Project Instructions

This project is a Machine Learning pipeline for predicting football match outcomes, goal totals, and simulating season-end standings using the `football-data.org` API.

## Project Overview
- **Objective:** Predict Match Outcomes (H/D/A), Over/Under 2.5 Goals, and simulate final league standings.
- **Data Source:** [football-data.org](https://www.football-data.org/) (v4 API).
- **Core Strategy:** Since the free tier lacks historical data, the models use **rolling in-season features** (last 5 games form, goal averages) to capture team momentum and strength.
- **Key Technologies:** Python 3, Flask, XGBoost, Pandas, Scikit-learn.

## Directory Structure
- `data/raw/`: Raw JSON files fetched from the API (Standings and Matches).
- `data/processed/`: Structured CSV file (`match_features.csv`) with engineered rolling features.
- `scripts/`: Modular Python scripts for the ML lifecycle.
- `models/`: Pickled XGBoost models (`outcome_model.pkl`, `over_under_model.pkl`).
- `templates/`: HTML templates for the Flask dashboard.
- `notebooks/`: Directory for Jupyter notebooks (exploratory analysis).

## Building and Running

### 1. Prerequisites
- Python 3.9+
- A valid `FOOTBALL_DATA_API_KEY` in a `.env` file at the root.
- Install dependencies: `pip3 install -r requirements.txt`

### 2. Execution Pipeline
Run these scripts in order to set up the environment:
1.  **Ingest Data:** `python3 scripts/ingest_data.py` (Fetches data for 12 free-tier leagues).
2.  **Process Features:** `python3 scripts/process_data.py` (Calculates rolling stats and prepares CSV).
3.  **Train Models:** `python3 scripts/train_models.py` (Trains XGBoost classifiers).
4.  **Start Dashboard:** `python3 app.py` (Starts Flask on port 5001).

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
