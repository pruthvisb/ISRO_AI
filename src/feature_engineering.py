import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
import logging
from src.transit_detection import perform_bls_search, get_phase_folded_lc, bin_folded_light_curve

logger = logging.getLogger(__name__)

def calculate_odd_even_depth_diff(time, flux, period, t0, duration):
    """
    Computes the difference in transit depth between odd and even transits.
    A significant difference is a strong indicator of an Eclipsing Binary (EB).
    """
    # Identify which transit epoch each point belongs to
    epochs = np.round((time - t0) / period)
    
    # Define in-transit mask
    phase = ((time - t0 + period / 2) % period) - period / 2
    in_transit = np.abs(phase) < (duration / 2)
    
    odd_mask = (epochs % 2 == 1) & in_transit
    even_mask = (epochs % 2 == 0) & in_transit
    out_mask = ~in_transit
    
    median_out = np.median(flux[out_mask]) if np.any(out_mask) else 1.0
    
    # Calculate odd depth
    if np.any(odd_mask):
        depth_odd = median_out - np.median(flux[odd_mask])
    else:
        depth_odd = 0.0
        
    # Calculate even depth
    if np.any(even_mask):
        depth_even = median_out - np.median(flux[even_mask])
    else:
        depth_even = 0.0
        
    # Normalized absolute difference
    avg_depth = (depth_odd + depth_even) / 2
    if avg_depth > 0:
        return np.abs(depth_odd - depth_even) / avg_depth
    else:
        return 0.0

def calculate_secondary_eclipse_depth(folded_phase, binned_flux, duration_phase):
    """
    Calculates the maximum depth of a secondary dip in the folded light curve
    outside of the primary transit (phase range around 0).
    """
    # Primary transit is centered at 0. Mask out the primary transit region
    # primary transit duration in phase space is duration / period
    out_primary = np.abs(folded_phase) > (duration_phase * 1.2)
    
    if not np.any(out_primary):
        return 0.0
        
    out_flux = binned_flux[out_primary]
    
    # Secondary eclipse is usually a smooth dip. Let's find the minimum of a rolling median 
    # to avoid single-point outliers representing a false eclipse
    rolling_min = 1.0 - np.min(out_flux)
    
    return float(max(0.0, rolling_min))

def extract_features(time, raw_flux, clean_flux, detrended_flux):
    """
    Extracts all statistical, BLS-derived, and folding-derived features from a target.
    """
    features = {}
    
    # 1. Global statistics on raw flux
    features['raw_mean'] = float(np.mean(raw_flux))
    features['raw_std'] = float(np.std(raw_flux))
    features['raw_skew'] = float(skew(raw_flux))
    features['raw_kurt'] = float(kurtosis(raw_flux))
    
    # 2. Global statistics on cleaned/detrended flux
    features['detrended_std'] = float(np.std(detrended_flux))
    features['detrended_skew'] = float(skew(detrended_flux))
    features['detrended_kurt'] = float(kurtosis(detrended_flux))
    
    # 3. Local noise estimate
    # standard deviation of the difference between consecutive points (high-frequency noise)
    features['local_noise'] = float(np.std(np.diff(detrended_flux)) / np.sqrt(2))
    
    # 4. BLS search features
    bls_results, _, _ = perform_bls_search(time, detrended_flux)
    
    features['bls_period'] = bls_results['period']
    features['bls_t0'] = bls_results['t0']
    features['bls_depth'] = bls_results['depth']
    features['bls_duration'] = bls_results['duration']
    features['bls_snr'] = bls_results['snr']
    features['bls_power'] = bls_results['power']
    
    # 5. Folded light curve statistics
    folded_phase, folded_flux = get_phase_folded_lc(time, detrended_flux, bls_results['period'], bls_results['t0'])
    binned_phase, binned_flux = bin_folded_light_curve(folded_phase, folded_flux, n_bins=200)
    
    features['folded_std'] = float(np.std(binned_flux))
    features['folded_skew'] = float(skew(binned_flux))
    features['folded_kurt'] = float(kurtosis(binned_flux))
    
    # 6. Advanced Vetting Features
    # Ingress duration ratio
    features['transit_snr'] = features['bls_depth'] / (features['local_noise'] + 1e-8)
    
    # Odd-even depth difference
    features['odd_even_diff'] = calculate_odd_even_depth_diff(
        time, detrended_flux, bls_results['period'], bls_results['t0'], bls_results['duration']
    )
    
    # Secondary eclipse depth
    duration_phase = bls_results['duration'] / bls_results['period']
    features['secondary_depth'] = calculate_secondary_eclipse_depth(binned_phase, binned_flux, duration_phase)
    
    return features, binned_flux
