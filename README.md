# ⚽ Football ML: Predictive Season Analytics

A comprehensive Machine Learning pipeline and interactive dashboard that predicts football match outcomes, goal totals, and simulates final league standings using the [football-data.org](https://www.football-data.org/) API.

---

## 🚀 Purpose
The primary goal of this project is to build a reliable predictive model for football matches even under the **Free Tier constraints** of sports data APIs. Since historical data is often locked behind paywalls, this project employs **dynamic in-season feature engineering** to capture team momentum, defensive/offensive strength, and home/away venue bias from the current season's sequence of results.

---

## 🏗️ Architecture

The project is designed as a modular 4-stage pipeline:

### 1. Data Ingestion (`scripts/ingest_data.py`)
- **Source:** REST API v4 from `football-data.org`.
- **Logic:** Fetches standings and match fixtures for 12 major competitions.
- **Resilience:** Implements rate-limiting (10 req/min) and automatic retry logic.

### 2. Feature Engineering (`scripts/process_data.py`)
- **Temporal Safety:** Uses a `shift()` based rolling window (5 games) to ensure no "future data" leaks into training.
- **Engineered Metrics:** 
  - **Form:** Points per game over the last 5 matches.
  - **Attack/Defense Strength:** Rolling average of goals scored vs. goals conceded.
  - **Venue Bias:** Performance metrics weighted by Home vs. Away status.

### 3. Model Training (`scripts/train_models.py`)
- **Algorithms:** Employs **XGBoost Classifiers** for multi-class classification (H/D/A) and binary classification (Over/Under 2.5 goals).
- **Validation:** Uses a temporal hold-out set (the final 20% of chronologically ordered matches) for realistic performance evaluation.

### 4. Simulation & Inference (`app.py` & `scripts/predict.py`)
- **Monte Carlo Engine:** Runs 500+ stochastic simulations per league to project final point distributions.
- **Dashboard:** A Flask-powered web UI with a responsive Light/Dark mode, visual match odds, and probability-based league tables.

---

## 🛠️ Setup & Usage

### 1. Prerequisites
- Python 3.9+
- A free API key from [football-data.org](https://www.football-data.org/).

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
FOOTBALL_DATA_API_KEY=your_api_key_here
```

### 3. Installation
```bash
pip install -r requirements.txt
```

### 4. Running the Pipeline
Run the scripts in order to build the local database and train the models:
```bash
# Fetch fresh data
python3 scripts/ingest_data.py

# Generate features
python3 scripts/process_data.py

# Train XGBoost models
python3 scripts/train_models.py

# Launch the Dashboard
python3 app.py
```

---

## 📊 Directory Structure
- `data/raw/`: Raw API JSON response storage.
- `data/processed/`: Engineered CSV datasets.
- `models/`: Pickled XGBoost model files.
- `scripts/`: Modular Python logic for each pipeline stage.
- `templates/`: HTML/Bootstrap UI for the dashboard.
- `GEMINI.md`: Comprehensive technical instructions for AI agents.

---

## ⚖️ License
This project is for educational and research purposes. Football data provided by [football-data.org](https://www.football-data.org/).
