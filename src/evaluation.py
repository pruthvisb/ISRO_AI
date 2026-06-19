import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import logging
import joblib

from src.preprocessing import simulate_light_curve, preprocess_light_curve
from src.feature_engineering import extract_features
from src.models import ExoplanetClassifierPipeline, CLASSES, CLASS_TO_IDX, IDX_TO_CLASS

# Set logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_training_dataset(samples_per_class=100, seed=42):
    """
    Generates a synthetic dataset of light curves for all 5 classes,
    preprocesses them, and extracts features for tabular models and binned profiles for deep learning.
    """
    logger.info(f"Generating training dataset ({samples_per_class} samples per class)...")
    np.random.seed(seed)
    
    features_list = []
    curves_list = []
    labels_list = []
    
    time = np.linspace(0, 27.2, 1000) # standard TESS-like time grid
    
    for cls in CLASSES:
        logger.info(f"Simulating class: {cls}")
        for i in range(samples_per_class):
            # 1. Simulate light curve
            t, raw_flux = simulate_light_curve(cls, time=time)
            
            # 2. Preprocess
            try:
                t_clean, f_clean, f_detrend = preprocess_light_curve(t, raw_flux, window_length=51, polyorder=2)
                
                # 3. Feature engineering
                feat, binned_curve = extract_features(t_clean, raw_flux, f_clean, f_detrend)
                
                features_list.append(feat)
                curves_list.append(binned_curve)
                labels_list.append(CLASS_TO_IDX[cls])
            except Exception as e:
                logger.warning(f"Failed to process simulated {cls} curve: {str(e)}. Skipping...")
                continue
                
    df_features = pd.DataFrame(features_list)
    arr_curves = np.array(curves_list)
    arr_labels = np.array(labels_list)
    
    logger.info(f"Dataset generated. Total successful samples: {len(df_features)}")
    return df_features, arr_curves, arr_labels

def compute_metrics(y_true, y_pred, y_prob):
    """
    Computes all academic evaluation metrics.
    """
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    # Compute multi-class ROC-AUC
    try:
        roc_auc = roc_auc_score(y_true, y_prob, multi_class='ovr', average='weighted')
    except Exception:
        roc_auc = 0.0
        
    cm = confusion_matrix(y_true, y_pred)
    
    # Compute detection completeness (Recall for exoplanet transit class)
    exoplanet_idx = CLASS_TO_IDX["exoplanet"]
    completeness = recall_score(y_true, y_pred, labels=[exoplanet_idx], average=None)[0]
    
    # Compute False Positive Rate (FPR) for exoplanet class
    # FPR = FP / (FP + TN)
    # FP: non-exoplanet predicted as exoplanet
    # TN: non-exoplanet predicted as non-exoplanet
    fp = np.sum((y_pred == exoplanet_idx) & (y_true != exoplanet_idx))
    tn = np.sum((y_pred != exoplanet_idx) & (y_true != exoplanet_idx))
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    return {
        "Accuracy": accuracy,
        "Precision (Weighted)": precision,
        "Recall (Weighted)": recall,
        "F1-Score (Weighted)": f1,
        "ROC-AUC (Weighted)": roc_auc,
        "Detection Completeness (Planet Recall)": completeness,
        "False Positive Rate (Planet FPR)": fpr,
        "Confusion Matrix": cm
    }

def run_pipeline_training_and_evaluation(samples_per_class=35):
    """
    Main training and validation loop.
    """
    # 1. Generate Data
    df_feat, arr_curves, arr_labels = generate_training_dataset(samples_per_class=samples_per_class)
    
    # Fill any remaining NaNs in features
    df_feat = df_feat.fillna(0.0)
    
    # 2. Train-Test Split (80/20)
    indices = np.arange(len(df_feat))
    train_idx, test_idx = train_test_split(indices, test_size=0.2, random_state=42, stratify=arr_labels)
    
    X_train_feat = df_feat.iloc[train_idx]
    X_test_feat = df_feat.iloc[test_idx]
    
    X_train_curves = arr_curves[train_idx]
    X_test_curves = arr_curves[test_idx]
    
    y_train = arr_labels[train_idx]
    y_test = arr_labels[test_idx]
    
    # 3. Train models
    pipeline = ExoplanetClassifierPipeline(model_dir="models")
    pipeline.train_tabular_models(X_train_feat, y_train)
    pipeline.train_deep_models(X_train_curves, y_train, epochs=12, batch_size=32)
    
    # 4. Evaluate models
    logger.info("Evaluating models on test set...")
    
    test_probs = []
    for idx in range(len(X_test_feat)):
        tab_feat = X_test_feat.iloc[idx].to_dict()
        curve = X_test_curves[idx]
        probs = pipeline.predict_probabilities(tab_feat, curve)
        test_probs.append(probs["Ensemble"])
        
    test_probs = np.array(test_probs)
    test_preds = np.argmax(test_probs, axis=1)
    
    # Compute metrics
    metrics = compute_metrics(y_test, test_preds, test_probs)
    
    # Display results
    print("\n" + "="*50)
    print("ENSEMBLE PIPELINE EVALUATION METRICS")
    print("="*50)
    for k, v in metrics.items():
        if k != "Confusion Matrix":
            print(f"{k:<40}: {v:.4f}")
    print("="*50)
    
    print("\nConfusion Matrix:")
    print(metrics["Confusion Matrix"])
    
    # Save validation reports
    report = classification_report(y_test, test_preds, target_names=CLASSES, output_dict=True)
    df_report = pd.DataFrame(report).transpose()
    df_report.to_csv("models/classification_report.csv")
    
    # Save confusion matrix for streamlit
    np.save("models/confusion_matrix.npy", metrics["Confusion Matrix"])
    
    # Save overall metrics
    flat_metrics = {k: float(v) for k, v in metrics.items() if k != "Confusion Matrix"}
    joblib.dump(flat_metrics, "models/evaluation_metrics.pkl")
    
    logger.info("Pipeline training and evaluation completed successfully!")
    return metrics

if __name__ == "__main__":
    run_pipeline_training_and_evaluation()
