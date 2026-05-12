# ⚽ Football ML: Predictive Season Analytics

A comprehensive Machine Learning pipeline and interactive dashboard that predicts football match outcomes, goal totals, and simulates final league standings using the [football-data.org](https://www.football-data.org/) API.

---

## 🚀 Purpose
The primary goal of this project is to build a reliable predictive model for football matches even under the **Free Tier constraints** of sports data APIs. Since historical data is often locked behind paywalls, this project employs **dynamic in-season feature engineering** to capture team momentum, defensive/offensive strength, and home/away venue bias from the current season's sequence of results.

---

## 🏗️ Architecture

The project is organized into a clean, functional package structure to separate concerns and ensure maintainability:

- **`football_ml/core/`**: The core business logic.
    - **`data/`**: Handles ingestion from the Football-Data.org API and complex rolling feature engineering using Pandas.
    - **`ml/`**: Manages the training pipeline for XGBoost models, including temporal splitting and evaluation.
    - **`inference/`**: High-performance prediction engines and Monte Carlo simulators for seasonal projections.
- **`football_ml/cli/`**: Lightweight command-line wrappers for every stage of the pipeline.
- **`football_ml/web/`**: A modern Flask-powered dashboard for data visualization.

---

## ✨ Key Features

- **Temporal Feature Safety:** All rolling features (Form, Goals For, Goals Against) are calculated using a `shift()` window to prevent data leakage. Matches are only predicted using stats available *prior* to kickoff.
- **Monte Carlo Season Simulation:** Instead of simple point projections, the engine runs 500+ stochastic simulations per league to generate a probability distribution of final rankings.
- **Multi-Status Prediction:** Supports both `SCHEDULED` and `TIMED` match statuses to ensure accurate predictions throughout the season's varying scheduling phases.
- **Responsive Dashboard:** A full-featured web UI with Bootstrap 5, featuring real-time prediction badges, win/draw/loss probability bars, and dark mode support.

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
Run the modules in order to build the local database and train the models:
```bash
# Fetch fresh data
python3 -m football_ml.cli.ingest

# Generate features
python3 -m football_ml.cli.process

# Train XGBoost models
python3 -m football_ml.cli.train

# Launch the Dashboard
python3 -m football_ml.web.app
```

---

## 📊 Directory Structure
- `football_ml/`: Main application package.
  - `core/`: Shared logic for data, ML, and inference.
  - `cli/`: Command-line wrappers.
  - `web/`: Web application and assets.
- `data/raw/`: Raw API JSON response storage.
- `data/processed/`: Engineered CSV datasets.
- `models/`: Pickled XGBoost model files.
- `GEMINI.md`: Comprehensive technical instructions for AI agents.

---

## ⚖️ License
This project is for educational and research purposes. Football data provided by [football-data.org](https://www.football-data.org/).
