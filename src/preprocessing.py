import numpy as np
import pandas as pd
import scipy.signal as signal
from astropy.io import fits
from astropy.stats import sigma_clip
import logging

logger = logging.getLogger(__name__)

def load_tess_fits(filepath):
    """
    Load a raw TESS FITS file using Astropy and extract time, SAP flux, and PDCSAP flux.
    """
    logger.info(f"Loading FITS file: {filepath}")
    try:
        with fits.open(filepath) as hdul:
            # TESS light curve data is stored in the first extension table
            data = hdul[1].data
            time = np.array(data['TIME'], dtype=float)
            sap_flux = np.array(data['SAP_FLUX'], dtype=float)
            pdcsap_flux = np.array(data['PDCSAP_FLUX'], dtype=float)
            
            # Create a clean dataframe
            df = pd.DataFrame({
                'time': time,
                'sap_flux': sap_flux,
                'pdcsap_flux': pdcsap_flux
            })
            return df
    except Exception as e:
        logger.error(f"Error reading FITS file {filepath}: {str(e)}")
        raise

def preprocess_light_curve(time, flux, window_length=101, polyorder=2, sigma=3.0):
    """
    Cleans a light curve:
    1. Removes missing values (NaNs).
    2. Normalizes the flux (divides by median).
    3. Removes outliers using sigma clipping.
    4. Detrends stellar variability using a Savitzky-Golay filter.
    """
    # 1. Remove NaNs
    mask_nan = np.isnan(time) | np.isnan(flux)
    t_clean = time[~mask_nan]
    f_clean = flux[~mask_nan]
    
    if len(t_clean) == 0:
        raise ValueError("Light curve contains only NaN values.")

    # 2. Normalize
    median_flux = np.median(f_clean)
    f_normalized = f_clean / median_flux

    # 3. Outlier removal using sigma clipping
    # We clip against a smoothed version of the curve to avoid clipping real transits
    smooth_flux = signal.savgol_filter(f_normalized, window_length=min(window_length, len(f_normalized) // 2 * 2 + 1), polyorder=polyorder)
    residual = f_normalized - smooth_flux
    
    clipped = sigma_clip(residual, sigma=sigma, maxiters=5)
    mask_outliers = clipped.mask
    
    t_no_outliers = t_clean[~mask_outliers]
    f_no_outliers = f_normalized[~mask_outliers]

    # 4. Detrending (Flattening)
    # We apply Savitzky-Golay to the outlier-removed normalized flux
    window_length = min(window_length, len(f_no_outliers) // 2 * 2 + 1)
    if window_length < 3:
        window_length = 3
    trend = signal.savgol_filter(f_no_outliers, window_length=window_length, polyorder=polyorder)
    f_detrended = f_no_outliers / trend

    return t_no_outliers, f_no_outliers, f_detrended

# --- LIGHT CURVE SIMULATOR ---

def simulate_trapezoid_transit(time, period, depth, duration, t0, ingress_ratio=0.1):
    """
    Generates a trapezoidal transit signal.
    - ingress_ratio: fraction of duration spent in ingress/egress.
    """
    phase = ((time - t0 + period / 2) % period) - period / 2
    transit_signal = np.zeros_like(time)
    
    half_dur = duration / 2
    ingress_dur = duration * ingress_ratio
    flat_dur = half_dur - ingress_dur
    
    abs_phase = np.abs(phase)
    
    # Inside flat bottom of transit
    flat_mask = abs_phase <= flat_dur
    transit_signal[flat_mask] = -depth
    
    # Ingress/Egress slopes
    slope_mask = (abs_phase > flat_dur) & (abs_phase < half_dur)
    # Linear interpolation
    transit_signal[slope_mask] = -depth * (half_dur - abs_phase[slope_mask]) / ingress_dur
    
    return transit_signal

def generate_red_noise(time, scale=0.0005, correlation=0.9):
    """
    Generates red (1/f) noise using an AR(1) autoregressive process.
    """
    noise = np.zeros(len(time))
    noise[0] = np.random.normal(0, scale)
    for i in range(1, len(time)):
        noise[i] = correlation * noise[i-1] + np.sqrt(1 - correlation**2) * np.random.normal(0, scale)
    return noise

def simulate_light_curve(class_label, time=None, period=None, seed=None):
    """
    Simulates a synthetic light curve for training/validation.
    Classes:
    - 'exoplanet': Flat + transit dips + noise
    - 'eclipsing_binary': Primary/secondary eclipses + ellipsoidal variations + noise
    - 'stellar_blend': Flat + very shallow transit dips + noise
    - 'starspot': Sinusoidal modulations + noise
    - 'noise': Pure white + red noise
    """
    if seed is not None:
        np.random.seed(seed)
        
    if time is None:
        # Simulate a 27-day TESS sector with 2000 points
        time = np.linspace(0, 27.2, 2000)
        
    n_points = len(time)
    base_flux = np.ones(n_points)
    
    # Base noise parameters
    white_noise_std = np.random.uniform(0.0002, 0.001)
    red_noise_scale = np.random.uniform(0.0003, 0.0015)
    
    white_noise = np.random.normal(0, white_noise_std, n_points)
    red_noise = generate_red_noise(time, scale=red_noise_scale, correlation=0.95)
    total_noise = white_noise + red_noise
    
    signal_flux = np.zeros(n_points)
    
    if class_label == 'exoplanet':
        if period is None:
            period = np.random.uniform(1.5, 10.0)
        depth = np.random.uniform(0.003, 0.015) # 3 to 15 ppt
        duration = np.random.uniform(0.05, 0.15) # in days (~1.2 to 3.6 hours)
        t0 = np.random.uniform(0.1, period)
        signal_flux = simulate_trapezoid_transit(time, period, depth, duration, t0)
        
    elif class_label == 'eclipsing_binary':
        if period is None:
            period = np.random.uniform(2.0, 12.0)
        t0 = np.random.uniform(0.1, period)
        # Primary eclipse
        depth_pri = np.random.uniform(0.02, 0.08) # 20 to 80 ppt (deep!)
        dur_pri = np.random.uniform(0.08, 0.2)
        sig_pri = simulate_trapezoid_transit(time, period, depth_pri, dur_pri, t0, ingress_ratio=0.15)
        # Secondary eclipse (phase offset by 0.5)
        depth_sec = depth_pri * np.random.uniform(0.3, 0.7)
        dur_sec = dur_pri * np.random.uniform(0.9, 1.1)
        t0_sec = t0 + period / 2
        sig_sec = simulate_trapezoid_transit(time, period, depth_sec, dur_sec, t0_sec, ingress_ratio=0.15)
        # Ellipsoidal variation (gravitational distortion)
        ellipsoidal = -np.random.uniform(0.001, 0.005) * np.cos(4 * np.pi * (time - t0) / period)
        signal_flux = sig_pri + sig_sec + ellipsoidal
        
    elif class_label == 'stellar_blend':
        # Background eclipsing binary or diluted planet transit
        if period is None:
            period = np.random.uniform(1.5, 8.0)
        depth = np.random.uniform(0.0003, 0.0012) # extremely shallow (0.3 to 1.2 ppt)
        duration = np.random.uniform(0.05, 0.12)
        t0 = np.random.uniform(0.1, period)
        signal_flux = simulate_trapezoid_transit(time, period, depth, duration, t0)
        
    elif class_label == 'starspot':
        # Rotating starspots cause quasi-sinusoidal stellar variability
        rot_period = np.random.uniform(2.0, 15.0)
        amp = np.random.uniform(0.004, 0.02) # 4 to 20 ppt amplitude
        phase_offset = np.random.uniform(0, 2 * np.pi)
        # Primary rotation frequency + first harmonic representing secondary spot
        rot_signal = amp * np.sin(2 * np.pi * time / rot_period + phase_offset)
        harmonic_signal = (amp * np.random.uniform(0.2, 0.5)) * np.sin(4 * np.pi * time / rot_period + np.random.uniform(0, 2*np.pi))
        # Add a slow spot decay/evolution trend
        decay_trend = np.linspace(1.0, np.random.uniform(0.7, 1.0), n_points)
        signal_flux = (rot_signal + harmonic_signal) * decay_trend
        
    elif class_label == 'noise':
        # Pure noise target
        signal_flux = np.zeros(n_points)
        
    # Combine signals and noise
    flux = base_flux + signal_flux + total_noise
    return time, flux
