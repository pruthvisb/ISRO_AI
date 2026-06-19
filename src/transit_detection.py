import numpy as np
import logging
from astropy.timeseries import BoxLeastSquares

logger = logging.getLogger(__name__)

def perform_bls_search(time, flux, min_period=0.5, max_period=15.0, min_duration=0.02, max_duration=0.25):
    """
    Executes a Box Least Squares (BLS) period search on the light curve.
    Returns:
        results_dict: Dictionary containing best-fit parameters.
        bls_obj: The raw astropy BoxLeastSquares object.
        results: The raw BoxLeastSquaresResults object.
    """
    logger.info(f"Running Box Least Squares (BLS) periodogram search...")
    
    # Establish duration grid (typical exoplanet transits last 0.5 to 6 hours)
    # Convert duration grid to days
    durations = np.linspace(min_duration, max_duration, 10)
    
    try:
        # Initialize astropy BLS
        # Astropy BLS expects flux centered around 1.0 or 0.0. Since we detrended to 1.0, this is perfect.
        bls = BoxLeastSquares(time, flux)
        
        # Generate a fast period grid of 1000 points
        periods = np.linspace(min_period, max_period, 1000)
        
        # Calculate periodogram
        results = bls.power(periods, durations)
        
        # Extract best parameters
        best_idx = np.argmax(results.power)
        best_period = results.period[best_idx]
        best_t0 = results.transit_time[best_idx]
        best_depth = results.depth[best_idx]
        best_duration = results.duration[best_idx]
        best_power = results.power[best_idx]
        
        # Calculate SNR (Signal-to-Noise Ratio)
        # Astropy's depth_snr is a good metric, but we can also compute the standard SNR
        # SNR = depth / standard_deviation_of_residuals * sqrt(n_transit_points)
        depth_snr = results.depth_snr[best_idx]
        
        # Double check if any NaNs exist
        if np.isnan(depth_snr) or depth_snr < 0:
            depth_snr = 0.0
            
        p_grid = results.period.value if hasattr(results.period, 'value') else results.period
        pow_grid = results.power.value if hasattr(results.power, 'value') else results.power
        
        results_dict = {
            "period": float(best_period.value if hasattr(best_period, 'value') else best_period),
            "t0": float(best_t0.value if hasattr(best_t0, 'value') else best_t0),
            "depth": float(best_depth.value if hasattr(best_depth, 'value') else best_depth),
            "duration": float(best_duration.value if hasattr(best_duration, 'value') else best_duration),
            "snr": float(depth_snr.value if hasattr(depth_snr, 'value') else depth_snr),
            "power": float(best_power.value if hasattr(best_power, 'value') else best_power),
            "period_grid": np.asarray(p_grid),
            "power_grid": np.asarray(pow_grid)
        }
        
        logger.info(f"BLS Complete. Best Period: {best_period:.4f} days, SNR: {depth_snr:.2f}, Depth: {best_depth*1000:.2f} ppt")
        return results_dict, bls, results
        
    except Exception as e:
        logger.error(f"Error during BLS search: {str(e)}")
        # Return fallback values
        return {
            "period": 1.0, "t0": 0.0, "depth": 0.0, "duration": 0.1, "snr": 0.0, "power": 0.0,
            "period_grid": np.linspace(min_period, max_period, 100), "power_grid": np.zeros(100)
        }, None, None

def get_phase_folded_lc(time, flux, period, t0):
    """
    Phase-folds the time array to range [-0.5, 0.5] relative to t0.
    """
    # Calculate phase (from -0.5 to 0.5)
    folded_phase = ((time - t0 + period / 2) % period) / period - 0.5
    
    # Sort by phase
    sort_idx = np.argsort(folded_phase)
    return folded_phase[sort_idx], flux[sort_idx]

def bin_folded_light_curve(phase, flux, n_bins=200):
    """
    Bins the folded light curve phase and flux into a fixed number of bins.
    This provides a fixed-length vector input for CNN and LSTM models.
    """
    bin_edges = np.linspace(-0.5, 0.5, n_bins + 1)
    binned_phase = (bin_edges[:-1] + bin_edges[1:]) / 2
    binned_flux = np.ones(n_bins)
    
    for i in range(n_bins):
        mask = (phase >= bin_edges[i]) & (phase < bin_edges[i+1])
        if np.any(mask):
            binned_flux[i] = np.mean(flux[mask])
        else:
            # Interpolate from adjacent bins if empty
            binned_flux[i] = 1.0
            
    # Apply a quick linear interpolation for any empty bins
    nan_mask = np.isnan(binned_flux)
    if np.any(nan_mask):
        binned_flux[nan_mask] = np.interp(binned_phase[nan_mask], binned_phase[~nan_mask], binned_flux[~nan_mask])
        
    return binned_phase, binned_flux
