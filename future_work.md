# Future Work and Research Directions

This section outlines several promising directions for expanding the "AI-Enabled Detection of Exoplanets" pipeline, suitable for a master's thesis or advanced research project.

## 1. Multi-Planet System Search (Iterative BLS)
Currently, the pipeline searches for the single most dominant periodic transit signal in the light curve. However, many systems (such as L 98-59 or TRAPPIST-1) contain multiple transiting planets.
- **Proposed Implementation**: Implement a recursive transit search. Once a transit candidate is detected, fit its shape, mask the in-transit data points (set them to NaN or interpolate over them), and run the Box Least Squares (BLS) search on the remaining out-of-transit data. Repeat this process until no statistically significant signals (e.g., SNR < 5.0) are found.

## 2. Advanced Deep Learning Architectures
While 1D CNN and CNN-LSTM models are effective at identifying phase-folded transit shapes, newer architectures could improve classification accuracy, especially for marginal (low-SNR) detections.
- **Transformers / Self-Attention**: Implement a Time-Series Transformer or a Vision Transformer (ViT) on the folded phase profile. Attention mechanisms can help the model focus on ingress/egress boundaries and distinguish them from stellar pulsation or spot activity.
- **2D CNNs on Centroid Images**: TESS files contain pixel level data. Rather than using the integrated light curve flux, train 2D CNNs directly on the raw pixel files to classify planetary signals, similar to NASA's Kepler Robovetter or Astronet.

## 3. Pixel-Level Centroid Offset Vetting
A major source of false positives in TESS is Background Eclipsing Binaries (BEBs). When TESS observes a star, light from a nearby, deep eclipsing binary can bleed into the target's aperture, creating a shallow transit-like dip.
- **Proposed Implementation**: Calculate the center-of-light (centroid position) of the star during the transit. If the transit signal is coming from a background star, the centroid will shift towards that background star when the primary target is dimmed. Integrating centroid shift calculation into the feature engineering step will allow the ML models to easily detect and filter out background blends.

## 4. Gaussian Process (GP) Detrending
The Savitzky-Golay filter is fast and simple, but it can sometimes distort transit shapes if the window size is not selected carefully.
- **Proposed Implementation**: Implement Gaussian Process regression (e.g., using `celerite` or `george`) with a periodic or quasi-periodic kernel. GPs can model stellar activity (such as active regions growing and decaying as the star rotates) with high physical accuracy, enabling cleaner detrending without altering transit depths.

## 5. GPU-Accelerated Pipelines
Processing thousands of light curves is computationally intensive, particularly the BLS period search and Monte Carlo error simulations.
- **Proposed Implementation**: Port the BLS grid search to CUDA/GPUs using libraries like CuPy or JAX, allowing real-time processing of large catalogs like the TESS Full-Frame Images (FFIs).
