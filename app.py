import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import joblib

from src.data_acquisition import download_target_fits, PRESETS
from src.preprocessing import load_tess_fits, preprocess_light_curve
from src.transit_detection import perform_bls_search, get_phase_folded_lc, bin_folded_light_curve
from src.feature_engineering import extract_features
from src.models import ExoplanetClassifierPipeline, CLASSES, IDX_TO_CLASS
from src.confidence import run_monte_carlo_uncertainty, estimate_confidence_score
from src.visualization import (
    plot_raw_vs_cleaned, 
    plot_bls_periodogram, 
    plot_folded_transit, 
    plot_classification_probabilities
)

# Page Configuration
st.set_page_config(
    page_title="Google Antigravity — Exoplanet Intelligence Dashboard",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    h1 {
        font-family: 'Space Grotesk', sans-serif;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        color: white;
        border: none;
        font-weight: 600;
    }
    .metric-card {
        background-color: #161a24;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #06b6d4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #9fa6b2;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🔭 Exoplanet Intelligence Portal")
st.markdown("*Powered by Google Antigravity Labs — AI-Enabled Detection of Exoplanets from Noisy Light Curves*")

# Initialize Pipeline
@st.cache_resource
def get_classifier():
    pipeline = ExoplanetClassifierPipeline(model_dir="models")
    # If pre-trained models exist, load them; otherwise train them on the fly
    if not pipeline.load_models():
        st.warning("Pre-trained models not found. Running training script to build models...")
        from src.evaluation import run_pipeline_training_and_evaluation
        run_pipeline_training_and_evaluation(samples_per_class=100)
        pipeline.load_models()
    return pipeline

try:
    classifier = get_classifier()
except Exception as e:
    st.error(f"Error loading models: {str(e)}")
    classifier = None

# Sidebar Controls
st.sidebar.header("📁 Light Curve Source")
source_option = st.sidebar.radio(
    "Choose Input Method:",
    ("Use Presets (Real TESS Targets)", "Upload FITS File", "Upload CSV File")
)

target_data = None
raw_time, raw_flux = None, None
filename = ""

if source_option == "Use Presets (Real TESS Targets)":
    st.sidebar.subheader("Select Preset Target:")
    category = st.sidebar.selectbox("Category:", list(PRESETS.keys()))
    targets = PRESETS[category]
    target_names = [t["name"] for t in targets]
    selected_target_name = st.sidebar.selectbox("Target Star:", target_names)
    
    # Get details
    target = next(t for t in targets if t["name"] == selected_target_name)
    tic_id = target["tic_id"]
    sector = target["sector"]
    filename = f"tic_{tic_id}_sector_{sector}.fits"
    
    st.sidebar.info(f"Target Details:\n- TIC ID: {tic_id}\n- Sector: {sector}")
    
    # Fetch/Download FITS
    raw_path = os.path.join("data", "raw", filename)
    if not os.path.exists(raw_path):
        with st.spinner("Downloading FITS file from MAST archive..."):
            raw_path = download_target_fits(tic_id, sector)
            
    if raw_path and os.path.exists(raw_path):
        try:
            df = load_tess_fits(raw_path)
            # Use PDCSAP flux for standard processing as it is corrected for systematics
            raw_time = df['time'].values
            raw_flux = df['pdcsap_flux'].values
            # Fallback to SAP if PDCSAP has too many NaNs
            if np.isnan(raw_flux).all() or len(raw_flux[~np.isnan(raw_flux)]) < 100:
                raw_flux = df['sap_flux'].values
        except Exception as e:
            st.error(f"Error reading downloaded FITS: {str(e)}")
    else:
        st.error("Failed to acquire FITS file from archive.")

elif source_option == "Upload FITS File":
    uploaded_file = st.sidebar.file_uploader("Upload TESS FITS Light Curve:", type=["fits"])
    if uploaded_file is not None:
        filename = uploaded_file.name
        # Save temp file
        temp_path = os.path.join("data", "raw", filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            df = load_tess_fits(temp_path)
            raw_time = df['time'].values
            raw_flux = df['pdcsap_flux'].values
            if np.isnan(raw_flux).all():
                raw_flux = df['sap_flux'].values
        except Exception as e:
            st.error(f"Error loading uploaded FITS: {str(e)}")

else: # CSV file
    uploaded_file = st.sidebar.file_uploader("Upload CSV Light Curve (columns must be 'time' and 'flux'):", type=["csv"])
    if uploaded_file is not None:
        filename = uploaded_file.name
        try:
            df = pd.read_csv(uploaded_file)
            if 'time' in df.columns and 'flux' in df.columns:
                raw_time = df['time'].values
                raw_flux = df['flux'].values
            else:
                st.error("CSV file must contain 'time' and 'flux' columns.")
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")

# Preprocessing Options in Sidebar
st.sidebar.header("⚙️ Preprocessing Options")
sg_window = st.sidebar.slider("Savitzky-Golay Window Length (Detrending):", min_value=11, max_value=401, value=101, step=10)
sigma_clip_val = st.sidebar.slider("Sigma-Clipping Threshold:", min_value=2.0, max_value=6.0, value=3.0, step=0.5)

# Main Processing Flow
if raw_time is not None and raw_flux is not None:
    st.info(f"Loaded light curve **{filename}** with {len(raw_time)} datapoints.")
    
    # 1. PREPROCESSING
    with st.spinner("Executing Data Preprocessing..."):
        try:
            # Clean and detrend
            clean_time, clean_flux_norm, detrended_flux = preprocess_light_curve(
                raw_time, raw_flux, window_length=sg_window, polyorder=2, sigma=sigma_clip_val
            )
        except Exception as e:
            st.error(f"Preprocessing error: {str(e)}")
            st.stop()
            
    # Display Preprocessing Plots
    st.header("📈 Light Curve Preprocessing")
    
    # Compute trend line for visual comparison
    # Trend is clean_flux_norm / detrended_flux
    trend_flux = clean_flux_norm / detrended_flux
    fig_prep = plot_raw_vs_cleaned(raw_time, raw_flux, clean_time, clean_flux_norm, trend=trend_flux)
    st.pyplot(fig_prep)
    plt.close(fig_prep)
    
    # 2. TRANSIT SIGNAL DETECTION (BLS)
    st.header("🔍 Box Least Squares (BLS) Period Search")
    with st.spinner("Searching for periodic transit dips..."):
        bls_results, bls_obj, results_raw = perform_bls_search(clean_time, detrended_flux)
        
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Orbital Period</div><div class="metric-value">{bls_results["period"]:.5f} d</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Transit Depth</div><div class="metric-value">{bls_results["depth"]*1000:.3f} ppt</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Transit Duration</div><div class="metric-value">{bls_results["duration"]*24:.2f} hrs</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Mid-Transit Time (t0)</div><div class="metric-value">{bls_results["t0"]:.4f} BJD</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Signal-to-Noise Ratio</div><div class="metric-value">{bls_results["snr"]:.2f}</div></div>', unsafe_allow_html=True)
        
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        # Plot periodogram
        fig_per = plot_bls_periodogram(bls_results["period_grid"], bls_results["power_grid"], bls_results["period"])
        st.pyplot(fig_per)
        plt.close(fig_per)
        
    with col_p2:
        # Plot folded transit
        folded_phase, folded_flux = get_phase_folded_lc(clean_time, detrended_flux, bls_results["period"], bls_results["t0"])
        binned_phase, binned_flux = bin_folded_light_curve(folded_phase, folded_flux, n_bins=200)
        
        fig_fold = plot_folded_transit(folded_phase, folded_flux, binned_phase, binned_flux)
        st.pyplot(fig_fold)
        plt.close(fig_fold)
        
    # 3. FEATURE ENGINEERING & ML CLASSIFICATION
    st.header("🤖 Machine Learning Classifier Ensemble")
    
    if classifier is not None:
        with st.spinner("Extracting features and running classifier ensemble..."):
            features, binned_profile = extract_features(clean_time, raw_flux, clean_flux_norm, detrended_flux)
            probs = classifier.predict_probabilities(features, binned_profile)
            
        col_inf1, col_inf2 = st.columns([3, 2])
        
        with col_inf1:
            # Plot probability bar chart
            fig_prob = plot_classification_probabilities(probs)
            st.pyplot(fig_prob)
            plt.close(fig_prob)
            
        with col_inf2:
            # Ensemble consensus classification
            ensemble_prob = probs["Ensemble"]
            predicted_class_idx = np.argmax(ensemble_prob)
            predicted_class_name = CLASSES[predicted_class_idx]
            predicted_class_label = predicted_class_name.replace('_', ' ').title()
            
            # Estimate confidence and significance
            conf_details = estimate_confidence_score(
                probs, bls_results["snr"], bls_results["depth"], features["local_noise"]
            )
            
            st.subheader("Ensemble Consensus Results")
            st.markdown(f"**Predicted Class:** `{predicted_class_label}`")
            st.markdown(f"**Classification Confidence:** `{conf_details['confidence_score']:.1f}%`")
            st.markdown(f"**Detection Significance:** `{conf_details['significance']}`")
            st.markdown(f"**Transit Depth / Local Noise Floor:** `{conf_details['depth_to_noise']:.2f}x`")
            
            # Color indicator
            if predicted_class_name == "exoplanet":
                st.success("🎯 Solid Exoplanet Transit Candidate Detected!")
            elif predicted_class_name == "eclipsing_binary":
                st.warning("⚖️ Eclipsing Binary Signal Detected (Deep / V-shaped).")
            elif predicted_class_name == "stellar_blend":
                st.info("🌐 Potential Diluted Blend / Background Eclipse.")
            elif predicted_class_name == "starspot":
                st.info("🔆 Rotational spot modulation or stellar activity.")
            else:
                st.error("❌ High Noise Profile / False Positive.")
                
        # 4. UNCERTAINTY ESTIMATION (MONTE CARLO SIMULATIONS)
        st.header("🎲 Parameter Uncertainty Estimation (Monte Carlo)")
        mc_run = st.checkbox("Execute Monte Carlo Simulations (Runs 20 Perturbations)", value=False)
        
        if mc_run:
            with st.spinner("Simulating noise perturbations and re-fitting orbital parameters..."):
                mc_results = run_monte_carlo_uncertainty(
                    clean_time, detrended_flux, bls_results, features["local_noise"], n_trials=20
                )
                
            st.subheader("Monte Carlo Fit Parameters (1-Sigma Errors)")
            col_mc1, col_mc2, col_mc3, col_mc4 = st.columns(4)
            with col_mc1:
                st.markdown(f"**Period (P):**\n`{bls_results['period']:.5f} ± {mc_results['period_err']:.5f} days`")
            with col_mc2:
                st.markdown(f"**Transit Depth:**\n`{bls_results['depth']*1000:.3f} ± {mc_results['depth_err']*1000:.3f} ppt`")
            with col_mc3:
                st.markdown(f"**Duration (W):**\n`{bls_results['duration']*24:.3f} ± {mc_results['duration_err']*24:.3f} hrs`")
            with col_mc4:
                st.markdown(f"**Mid-Transit Time (t0):**\n`{bls_results['t0']:.4f} ± {mc_results['t0_err']:.4f} BJD`")
                
        # 5. DATA DOWNLOADS
        st.header("📥 Download Analysis Results")
        results_data = {
            "target": filename,
            "predicted_class": predicted_class_name,
            "confidence_score": conf_details["confidence_score"],
            "significance": conf_details["significance"],
            "period_days": bls_results["period"],
            "depth_fraction": bls_results["depth"],
            "duration_days": bls_results["duration"],
            "t0_bjd": bls_results["t0"],
            "bls_snr": bls_results["snr"]
        }
        
        df_results = pd.DataFrame([results_data])
        csv_buffer = df_results.to_csv(index=False)
        st.download_button(
            label="Download Classification Summary CSV",
            data=csv_buffer,
            file_name=f"{filename}_analysis_results.csv",
            mime="text/csv"
        )
    else:
        st.error("Classifier backend not initialized. Check model folder.")
else:
    # Landing message if no file loaded
    st.info("👈 Please select a preset target star or upload a TESS light curve FITS file in the sidebar to begin analysis!")
