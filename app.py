import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import joblib

from src.data_acquisition import download_target_fits, PRESETS
from src.preprocessing import load_tess_fits, preprocess_light_curve, simulate_light_curve
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Premium Styling & CSS Injection
st.markdown("""
<style>
    /* Global Background and Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    .reportview-container {
        background: #080a0f;
    }
    
    body, p, div, label {
        font-family: 'Inter', sans-serif;
        color: #f0f2f5;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Custom Header */
    .header-container {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 41, 59, 0.8));
        border: 1px solid rgba(255,255,255,0.08);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2.5rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .header-logo {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #9fa6b2;
    }
    .header-logo span.brand {
        color: #3b82f6;
        font-weight: 700;
    }
    
    .header-title {
        font-size: 2.5rem;
        margin: 0;
        background: linear-gradient(to right, #ffffff, #93c5fd, #a5f3fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-subtitle {
        font-size: 1.05rem;
        color: #9fa6b2;
        margin-top: 0.5rem;
    }
    
    /* Metrics and Layout Cards */
    .metric-card {
        background: rgba(22, 26, 36, 0.7);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.3);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #06b6d4;
        font-family: 'Space Grotesk', sans-serif;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #9fa6b2;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }
    
    /* Status Warning Cards */
    .status-card {
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
    }
    .status-warning {
        background: rgba(245, 158, 11, 0.08);
        border-color: rgba(245, 158, 11, 0.2);
        color: #fef3c7;
    }
    .status-success {
        background: rgba(16, 185, 129, 0.08);
        border-color: rgba(16, 185, 129, 0.2);
        color: #d1fae5;
    }
    
    /* Landing Onboarding Card */
    .welcome-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.6), rgba(30, 41, 59, 0.6));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        margin-top: 2rem;
    }
    .welcome-icon {
        font-size: 3rem;
        margin-bottom: 1.5rem;
        color: #3b82f6;
    }
    .welcome-card h3 {
        font-size: 1.6rem;
        margin-bottom: 1rem;
    }
    .welcome-card p {
        color: #9fa6b2;
        max-width: 600px;
        margin: 0 auto 2rem auto;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# Render Header
st.markdown("""
<div class="header-container">
    <div class="header-logo"><i class="fa-solid fa-user-astronaut"></i> Google <span class="brand">Antigravity</span> Labs</div>
    <div class="header-title">Exoplanet Intelligence Dashboard</div>
    <div class="header-subtitle">Vetting orbital transits in noisy light curves with Deep Learning and Machine Learning ensembles</div>
</div>
""", unsafe_allow_html=True)

# Initialize Classifier Backend
@st.cache_resource
def get_classifier():
    pipeline = ExoplanetClassifierPipeline(model_dir="models")
    # If pre-trained models exist, load them; otherwise train them on the fly
    if not pipeline.load_models():
        logger.info("Pre-trained models not found. Triggering fast training session...")
        from src.evaluation import run_pipeline_training_and_evaluation
        run_pipeline_training_and_evaluation(samples_per_class=35)
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

raw_time, raw_flux = None, None
filename = ""
is_simulated = False
preset_target_name = ""

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
    preset_target_name = target["name"]
    filename = f"tic_{tic_id}_sector_{sector}.fits"
    
    st.sidebar.info(f"Target Details:\n- TIC ID: {tic_id}\n- Sector: {sector}")
    
    # Fetch/Download FITS
    raw_path = os.path.join("data", "raw", filename)
    if not os.path.exists(raw_path):
        with st.spinner("Downloading FITS file from MAST archive..."):
            try:
                raw_path = download_target_fits(tic_id, sector)
            except Exception as e:
                logger.warning(f"Download failed: {str(e)}")
                raw_path = None
            
    if raw_path and os.path.exists(raw_path):
        try:
            df = load_tess_fits(raw_path)
            raw_time = df['time'].values
            raw_flux = df['pdcsap_flux'].values
            if np.isnan(raw_flux).all() or len(raw_flux[~np.isnan(raw_flux)]) < 100:
                raw_flux = df['sap_flux'].values
        except Exception as e:
            st.error(f"Error reading FITS: {str(e)}")
            raw_time = None
            
    # Fallback to simulation if download failed
    if raw_time is None:
        is_simulated = True
        # Generate target-specific simulator profiles
        time_grid = np.linspace(0, 27.2, 2000)
        
        if category == "exoplanet":
            # Simulate a realistic transit (e.g. L 98-59 like)
            period = 5.68 if tic_id == 307210830 else 4.51
            raw_time, raw_flux = simulate_light_curve("exoplanet", time=time_grid, period=period, seed=42)
        elif category == "eclipsing_binary":
            raw_time, raw_flux = simulate_light_curve("eclipsing_binary", time=time_grid, period=3.12, seed=42)
        elif category == "starspot":
            raw_time, raw_flux = simulate_light_curve("starspot", time=time_grid, seed=42)
        else:
            raw_time, raw_flux = simulate_light_curve("noise", time=time_grid, seed=42)

elif source_option == "Upload FITS File":
    uploaded_file = st.sidebar.file_uploader("Upload TESS FITS Light Curve:", type=["fits"])
    if uploaded_file is not None:
        filename = uploaded_file.name
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
            st.error(f"Error loading FITS: {str(e)}")

else: # CSV file
    uploaded_file = st.sidebar.file_uploader("Upload CSV Light Curve:", type=["csv"])
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
    # Handle info box for fallback simulator
    if is_simulated:
        st.markdown(f"""
        <div class="status-card status-warning">
            <strong>⚠️ MAST Archive Connection Offline / Rate Limited</strong><br>
            Could not retrieve raw FITS for <strong>{preset_target_name}</strong> (TIC {tic_id}) from MAST. 
            To demonstrate the pipeline, the Google Antigravity Simulator has generated a high-fidelity physical model of the target.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card status-success">
            <strong>✅ Target Loaded Successfully</strong><br>
            Loaded light curve <strong>{filename}</strong> with {len(raw_time)} observations from disk/archive.
        </div>
        """, unsafe_allow_html=True)
        
    # 1. PREPROCESSING
    with st.spinner("Executing Data Preprocessing..."):
        try:
            clean_time, clean_flux_norm, detrended_flux = preprocess_light_curve(
                raw_time, raw_flux, window_length=sg_window, polyorder=2, sigma=sigma_clip_val
            )
        except Exception as e:
            st.error(f"Preprocessing error: {str(e)}")
            st.stop()
            
    # Display Preprocessing Plots
    st.header("📈 Light Curve Preprocessing")
    
    # Compute trend line for visual comparison
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
        fig_per = plot_bls_periodogram(bls_results["period_grid"], bls_results["power_grid"], bls_results["period"])
        st.pyplot(fig_per)
        plt.close(fig_per)
        
    with col_p2:
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
            fig_prob = plot_classification_probabilities(probs)
            st.pyplot(fig_prob)
            plt.close(fig_prob)
            
        with col_inf2:
            ensemble_prob = probs["Ensemble"]
            predicted_class_idx = np.argmax(ensemble_prob)
            predicted_class_name = CLASSES[predicted_class_idx]
            predicted_class_label = predicted_class_name.replace('_', ' ').title()
            
            conf_details = estimate_confidence_score(
                probs, bls_results["snr"], bls_results["depth"], features["local_noise"]
            )
            
            st.subheader("Ensemble Consensus Results")
            st.markdown(f"**Predicted Class:** `{predicted_class_label}`")
            st.markdown(f"**Classification Confidence:** `{conf_details['confidence_score']:.1f}%`")
            st.markdown(f"**Detection Significance:** `{conf_details['significance']}`")
            st.markdown(f"**Transit Depth / Local Noise Floor:** `{conf_details['depth_to_noise']:.2f}x`")
            
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
            "target": filename if filename else preset_target_name,
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
            file_name=f"analysis_results.csv",
            mime="text/csv"
        )
    else:
        st.error("Classifier backend not initialized. Check model folder.")
else:
    # Landing onboarding message if no file loaded
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-icon"><i class="fa-solid fa-satellite-dish"></i></div>
        <h3>Welcome to the Exoplanet Intelligence Dashboard!</h3>
        <p>This computational tool allows you to ingest astronomical data, remove stellar noise, detect periodic transits, and deploy an AI ensemble to identify true exoplanets.</p>
        <p style="font-size: 0.95rem; font-style: italic;">To begin your analysis, select a preset target star or upload a TESS light curve FITS file in the sidebar menu on the left!</p>
    </div>
    """, unsafe_allow_html=True)
