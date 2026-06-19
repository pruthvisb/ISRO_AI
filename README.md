# AI-Enabled Detection of Exoplanets from Noisy Astronomical Light Curves

This repository contains a complete, end-to-end AI-enabled pipeline for detecting and classifying exoplanet transit signals from noisy stellar light curves. The project is designed as an interactive research demonstration suitable for science competitions and university research.

It features:
1. **Google Antigravity Portal**: A premium HTML/CSS/JS presentation website featuring a physics-based, real-time exoplanet transit simulator.
2. **Streamlit Science Dashboard**: An interactive application that downloads real TESS light curves, applies preprocessing filters, runs periodogram searches, fits parameters, runs Monte Carlo error analyses, and classifies signals using machine learning.
3. **ML Ensemble Pipeline**: A combination of tabular models (Random Forest, XGBoost, LightGBM) and deep learning models (1D CNN, CNN-LSTM Hybrid in PyTorch) to distinguish exoplanets from false positives (eclipsing binaries, starspots, stellar blends, and instrumental noise).

---

## Folder Structure

```text
d:/trial/
│
├── data/                    # Data storage
│   ├── raw/                 # Downloaded TESS FITS files
│   ├── processed/           # Processed/cleaned CSVs
│   └── simulated/           # Synthetic datasets
│
├── models/                  # Saved models & evaluation reports
│
├── notebooks/
│   └── exoplanet_detection_demo.ipynb  # Interactive walkthrough
│
├── src/                     # Core computational backend
│   ├── __init__.py
│   ├── data_acquisition.py  # Querying & downloading MAST/TESS data
│   ├── preprocessing.py     # Signal cleaners & realistic stellar simulator
│   ├── transit_detection.py # BLS period search & phase-folding
│   ├── feature_engineering.py# Tabular statistics & astronomical vetting metrics
│   ├── models.py            # Random Forest, XGBoost, LGBM, PyTorch CNN/LSTM
│   ├── evaluation.py        # Model training, testing, & evaluation reports
│   ├── confidence.py        # Monte Carlo parameter uncertainty estimation
│   └── visualization.py     # High-fidelity astronomical plotting utilities
│
├── web/                     # Landing page website (branded under Google Antigravity)
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── app.py                   # Streamlit interactive application
├── requirements.txt         # Dependencies list
├── README.md                # Project documentation
├── technical_report.md      # 3-page scientific report
└── future_work.md           # Proposed future developments
```

---

## Installation & Setup

1. **Clone or Download** the repository to your local drive (`d:/trial/`).
2. **Install Dependencies**:
   Ensure you have Python 3.11+ installed. Install the required python libraries using pip:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: PyTorch is required for deep learning models. If it is not installed, pip will fetch it. TensorFlow is not required since the deep learning backend runs fully on PyTorch for compatibility with Python 3.14+.*

---

## How to Run

### 1. Launch the Google Antigravity Presentation Web Portal
Open the file [web/index.html](file:///d:/trial/web/index.html) directly in any modern web browser, or serve it locally using a simple HTTP server:
```bash
python -m http.server 8000 --directory web
```
Then navigate to `http://localhost:8000`. You can interact with the slider controls to simulate planetary sizes, orbit periods, starspot activity, and noise levels.

### 2. Pre-Train the Machine Learning Models
To build the synthetic dataset, train the machine learning ensemble, and generate evaluation logs, execute:
```bash
python -m src.evaluation
```
This script will:
- Generate 120 simulated light curves per class (total 600 curves).
- Preprocess and extract tabular features and 200-bin phase profiles.
- Train all 5 classifiers.
- Save the trained weights to the `models/` directory.
- Print academic metrics (Accuracy, Precision, Recall, F1, Completeness, Confusion Matrix).

### 3. Run the Computational Streamlit Dashboard
Launch the Streamlit dashboard to process real TESS targets or upload your own FITS files:
```bash
streamlit run app.py
```
This opens the dashboard in your browser (usually at `http://localhost:8501`).

---

## AI Ensemble Details

The pipeline uses two data representations:
- **Tabular Features**: Ingested by Random Forest, XGBoost, and LightGBM. Includes metrics like skewness, kurtosis, local high-frequency noise, BLS SNR, odd-even depth differences (to detect eclipsing binaries), and secondary eclipse depths.
- **Phase Profiles (1D Array)**: Binned folded light curves (200 bins) ingested by a 1D Convolutional Neural Network (CNN) and a CNN-LSTM Hybrid model built with PyTorch. These models identify the physical "U-shape" signature of transits.
- **Ensemble consensus**: Averaged class probabilities from all five models determine the final classification and confidence score.
