# Football ML: Evolution Roadmap

This document outlines the strategic plan to evolve the project from a functional prototype to a professional-grade predictive analytics platform.

---

## 🗺️ Phase 1: Foundation & Data Infrastructure
**Goal:** Replace flat-file storage with a relational database and automate the data lifecycle.

- **Transition to SQLite:** Migrate raw JSON and processed CSVs to a structured SQLite database (`football.db`).
    - Schema: `competitions`, `teams`, `matches`, `standings`, `features`.
- **Automated Ingestion Pipeline:** Create a GitHub Action or local `systemd` timer to run `cli.ingest` and `cli.process` every 24 hours.
- **SQL-Based Feature Store:** Refactor `DataProcessor` to read/write directly from SQL, enabling faster incremental updates rather than full re-processes.

## 🧪 Phase 2: Advanced ML & Feature Engineering
**Goal:** Increase predictive accuracy and capture deeper team dynamics.

- **Hyperparameter Optimization:** Integrate `Optuna` to tune XGBoost (learning rate, depth, subsampling).
- **Advanced Features:**
    - **Venue-Specific Form:** Rolling stats calculated separately for Home and Away matches.
    - **ELO/Glicko-2 Ratings:** Implement a relative strength index that persists across seasons.
    - **Expected Goals (xG) Proxy:** Derive a "danger index" based on shots on target (if API tier allows) or goal efficiency.
- **Model Versioning:** Implement a simple local model registry to track performance history.

## 📈 Phase 3: Visualization & UX Enhancement
**Goal:** Provide deeper insights through interactive and high-fidelity visuals.

- **Interactive Charts (Chart.js):**
    - "Form Trajectory": Line charts showing points/goals trend over the season.
    - "Sim Distribution": Violin or Box plots showing the spread of projected points for each team.
- **Enhanced Match Details:** Detailed H2H history and "Win Probability" evolution.
- **Real-time Simulation Progress:** Use WebSockets (Flask-SocketIO) to show simulation progress bars in the UI.

## 🏗️ Phase 4: Reliability, Scale & Deployment
**Goal:** Ensure the system is robust, testable, and ready for the cloud.

- **Asynchronous Task Queue:** Integrate `Celery` + `Redis` to move heavy Monte Carlo simulations and data ingestion to background workers.
- **Testing Suite:** 
    - Unit tests for feature engineering (ensuring zero data leakage).
    - Integration tests for the Flask API.
- **Containerization (Docker):** Create a multi-stage Dockerfile (Web, Worker, Redis) for simplified deployment.
- **Production Web Server:** Move from Flask's dev server to `Gunicorn` with `Nginx`.

---

## 📅 Implementation Timeline

| Week | Focus | Deliverables |
| :--- | :--- | :--- |
| **Week 1** | **Infrastructure** | SQL Schema, Migration Scripts, Automated CLI. |
| **Week 2** | **ML Engine** | Tuned Models, Venue Stats, ELO Integration. |
| **Week 3** | **Frontend/UX** | Interactive Charts, Detailed H2H, Sim Visuals. |
| **Week 4** | **Reliability** | Celery/Redis, Dockerization, Testing Suite. |
| **Week 5** | **Polish/Deploy** | Nginx Setup, Final Evals, Deployment to VPS/Cloud. |

---

## 📈 Success Metrics
- **Accuracy:** Increase match outcome accuracy from current (~45%) to >52%.
- **Latency:** Reduce dashboard load time (with simulations) from ~3s to <500ms using caching/async.
- **Stability:** 100% automated data freshness without manual intervention.
