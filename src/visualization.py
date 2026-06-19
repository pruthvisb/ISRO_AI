import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from src.models import CLASSES

# Apply beautiful astronomical styling
plt.rcParams['figure.facecolor'] = '#0e1117'
plt.rcParams['axes.facecolor'] = '#161a24'
plt.rcParams['savefig.facecolor'] = '#0e1117'
plt.rcParams['text.color'] = '#e0e0e0'
plt.rcParams['axes.labelcolor'] = '#e0e0e0'
plt.rcParams['xtick.color'] = '#a0a0a0'
plt.rcParams['ytick.color'] = '#a0a0a0'
plt.rcParams['grid.color'] = '#2d3748'
plt.rcParams['font.size'] = 10

def plot_light_curve(time, flux, title="Light Curve", color="#3182ce"):
    """
    Plots a time-series light curve.
    """
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.scatter(time, flux, s=1, color=color, alpha=0.6, label="Observations")
    ax.set_title(title, fontsize=12, pad=15, color="#f7fafc")
    ax.set_xlabel("Time (BJD - 2457000, Days)")
    ax.set_ylabel("Normalized Flux")
    ax.legend(facecolor='#161a24', edgecolor='#2d3748', loc="best")
    ax.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    return fig

def plot_raw_vs_cleaned(time_raw, flux_raw, time_clean, flux_clean, trend=None):
    """
    Plots raw vs cleaned/detrended light curves in a 2-row layout.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)
    
    # Raw plot
    ax1.scatter(time_raw, flux_raw, s=1, color="#e53e3e", alpha=0.5, label="Raw SAP Flux")
    if trend is not None:
        ax1.plot(time_clean, trend, color="#ecc94b", linewidth=1.5, label="Stellar Trend")
    ax1.set_title("Data Preprocessing: Raw vs. Cleaned Flux", fontsize=12, pad=15, color="#f7fafc")
    ax1.set_ylabel("Raw Flux (e-/s)")
    ax1.legend(facecolor='#161a24', edgecolor='#2d3748', loc="upper right")
    ax1.grid(True, linestyle=":", alpha=0.5)
    
    # Cleaned plot
    ax2.scatter(time_clean, flux_clean, s=1, color="#3182ce", alpha=0.6, label="Cleaned Detrended Flux")
    ax2.set_xlabel("Time (BJD - 2457000, Days)")
    ax2.set_ylabel("Normalized Flux")
    ax2.legend(facecolor='#161a24', edgecolor='#2d3748', loc="lower right")
    ax2.grid(True, linestyle=":", alpha=0.5)
    
    plt.tight_layout()
    return fig

def plot_bls_periodogram(period_grid, power_grid, best_period):
    """
    Plots the Box Least Squares (BLS) power spectrum.
    """
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(period_grid, power_grid, color="#9f7aea", linewidth=1.2)
    ax.axvline(best_period, color="#ecc94b", linestyle="--", linewidth=1.5, label=f"Best Period: {best_period:.4f} d")
    ax.set_title("Box Least Squares (BLS) Periodogram", fontsize=12, pad=15, color="#f7fafc")
    ax.set_xlabel("Period (Days)")
    ax.set_ylabel("BLS Power")
    ax.legend(facecolor='#161a24', edgecolor='#2d3748', loc="best")
    ax.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    return fig

def plot_folded_transit(phase, flux, binned_phase=None, binned_flux=None, title="Folded Transit Profile"):
    """
    Plots the phase-folded light curve with binned average overlays.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(phase, flux, s=1.5, color="#718096", alpha=0.3, label="Data Points")
    
    if binned_phase is not None and binned_flux is not None:
        ax.plot(binned_phase, binned_flux, color="#ecc94b", linewidth=2.5, label="200-Bin Average Phase Profile")
        
    ax.set_title(title, fontsize=12, pad=15, color="#f7fafc")
    ax.set_xlabel("Phase (Orbit Period Normalized)")
    ax.set_ylabel("Normalized Flux")
    ax.set_xlim(-0.5, 0.5)
    ax.legend(facecolor='#161a24', edgecolor='#2d3748', loc="best")
    ax.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    return fig

def plot_classification_probabilities(probs):
    """
    Plots the probability of each class for the ensemble and individual models.
    """
    df_probs = pd.DataFrame(probs, index=[c.replace('_', ' ').title() for c in CLASSES])
    
    fig, ax = plt.subplots(figsize=(10, 5))
    df_probs.plot(kind='barh', ax=ax, cmap="viridis", width=0.8)
    
    ax.set_title("Model Inference Probabilities", fontsize=12, pad=15, color="#f7fafc")
    ax.set_xlabel("Probability")
    ax.set_xlim(0, 1.0)
    ax.grid(True, linestyle=":", alpha=0.5, axis='x')
    ax.legend(facecolor='#161a24', edgecolor='#2d3748', bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plt.tight_layout()
    return fig

def plot_feature_importance(feature_names, importances, max_features=12):
    """
    Plots feature importances for tabular models.
    """
    indices = np.argsort(importances)[::-1][:max_features]
    names = [feature_names[i] for i in indices]
    vals = [importances[i] for i in indices]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=vals, y=names, ax=ax, palette="plasma", hue=names, legend=False)
    ax.set_title("Random Forest Feature Importance Analysis", fontsize=12, pad=15, color="#f7fafc")
    ax.set_xlabel("Relative Importance")
    ax.grid(True, linestyle=":", alpha=0.5, axis='x')
    
    plt.tight_layout()
    return fig

def plot_confusion_matrix(cm):
    """
    Plots the confusion matrix.
    """
    labels = [c.replace('_', ' ').title() for c in CLASSES]
    
    # Normalize by row
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(cm_norm, annot=True, fmt=".2f", cmap="Blues", 
                xticklabels=labels, yticklabels=labels, ax=ax, 
                cbar=True, annot_kws={"size": 10},
                linewidths=0.5, linecolor='#161a24')
    
    # Custom adjustments for dark theme
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.set_tick_params(color='#a0a0a0')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#e0e0e0')
    
    ax.set_title("Normalized Confusion Matrix", fontsize=12, pad=15, color="#f7fafc")
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    
    plt.tight_layout()
    return fig
