import numpy as np
import logging
from astropy.timeseries import BoxLeastSquares

logger = logging.getLogger(__name__)

def run_monte_carlo_uncertainty(time, flux, best_params, noise_level, n_trials=25):
    """
    Performs Monte Carlo simulations by perturbing the light curve with white noise.
    For each trial, runs a localized BLS search to estimate the distribution
    and standard deviation (uncertainty) of the orbital parameters:
    - Period (P)
    - Mid-transit time (t0)
    - Transit depth
    - Transit duration
    """
    logger.info(f"Starting Monte Carlo uncertainty estimation ({n_trials} trials)...")
    
    periods = []
    t0s = []
    depths = []
    durations = []
    
    # Restrict BLS search grid around the best-fit period to accelerate computations
    p_best = best_params["period"]
    p_min = max(0.2, p_best * 0.95)
    p_max = p_best * 1.05
    
    # Fast period grid
    period_grid = np.linspace(p_min, p_max, 100)
    duration_grid = np.linspace(best_params["duration"] * 0.7, best_params["duration"] * 1.3, 5)
    
    for i in range(n_trials):
        # Perturb flux with Gaussian noise scaled to the local noise estimate
        noise_perturbation = np.random.normal(0, noise_level, len(flux))
        perturbed_flux = flux + noise_perturbation
        
        try:
            bls = BoxLeastSquares(time, perturbed_flux)
            results = bls.power(period_grid, duration_grid)
            
            best_idx = np.argmax(results.power)
            
            p_val = results.period[best_idx]
            t0_val = results.transit_time[best_idx]
            d_val = results.depth[best_idx]
            dur_val = results.duration[best_idx]
            
            periods.append(p_val.value if hasattr(p_val, 'value') else p_val)
            t0s.append(t0_val.value if hasattr(t0_val, 'value') else t0_val)
            depths.append(d_val.value if hasattr(d_val, 'value') else d_val)
            durations.append(dur_val.value if hasattr(dur_val, 'value') else dur_val)
        except Exception:
            continue
            
    # Calculate standard deviations (1-sigma uncertainties)
    if len(periods) > 1:
        p_err = np.std(periods)
        t0_err = np.std(t0s)
        depth_err = np.std(depths)
        dur_err = np.std(durations)
    else:
        # Fallback values if trials failed
        p_err = p_best * 0.01
        t0_err = best_params["t0"] * 0.01
        depth_err = best_params["depth"] * 0.1
        dur_err = best_params["duration"] * 0.1
        
    return {
        "period_err": float(p_err),
        "t0_err": float(t0_err),
        "depth_err": float(depth_err),
        "duration_err": float(dur_err),
        "trials_run": len(periods)
    }

def estimate_confidence_score(ensemble_probs, bls_snr, transit_depth, noise_level):
    """
    Computes a final exoplanet detection confidence score (0 to 100%) and significance.
    Combines:
    1. The Ensemble exoplanet probability.
    2. The BLS signal-to-noise ratio (SNR).
    3. The transit depth compared to the local noise floor.
    """
    exoplanet_prob = ensemble_probs["Ensemble"][0] # exoplanet is class index 0
    
    # 1. Signficance of depth
    # depth / noise ratio
    depth_significance = transit_depth / (noise_level + 1e-8)
    
    # 2. Score mapping
    # An SNR > 7.0 is the standard threshold for astronomical detection (e.g. Kepler SPOC)
    snr_factor = min(1.0, bls_snr / 10.0) # saturated at SNR = 10
    depth_factor = min(1.0, depth_significance / 5.0) # saturated at 5x noise
    
    # Combine probability with signal strength
    raw_score = 0.5 * exoplanet_prob + 0.3 * snr_factor + 0.2 * depth_factor
    
    # Convert to percentage
    confidence_percentage = float(np.clip(raw_score * 100.0, 0.0, 100.0))
    
    # Define significance classification
    if bls_snr < 4.0:
        significance = "Insignificant / False Alarm"
    elif bls_snr < 7.0:
        significance = "Low Significance / Candidate"
    elif bls_snr < 12.0:
        significance = "Moderate Significance / High Candidate"
    else:
        significance = "High Significance / Confirmed Detection"
        
    return {
        "confidence_score": confidence_percentage,
        "significance": significance,
        "depth_to_noise": float(depth_significance)
    }
