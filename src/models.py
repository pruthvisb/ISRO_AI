import os
import joblib
import numpy as np
import pandas as pd
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

logger = logging.getLogger(__name__)

# Class labels mapping
CLASSES = ["exoplanet", "eclipsing_binary", "stellar_blend", "starspot", "noise"]
CLASS_TO_IDX = {cls: idx for idx, cls in enumerate(CLASSES)}
IDX_TO_CLASS = {idx: cls for idx, cls in enumerate(CLASSES)}

def build_rf_model():
    """Builds a Random Forest Classifier."""
    return RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)

def build_xgb_model():
    """Builds an XGBoost Classifier."""
    return XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric='mlogloss', n_jobs=-1)

def build_lgbm_model():
    """Builds a LightGBM Classifier."""
    return LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, verbose=-1)

# --- PYTORCH DEEP LEARNING MODEL DEFINITIONS ---

class CNN1D(nn.Module):
    """
    1D Convolutional Neural Network (CNN) for folded light curve phase profiles in PyTorch.
    Input shape: (batch_size, 1, 200)
    """
    def __init__(self, num_classes=5):
        super(CNN1D, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(2)
        
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(2)
        
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool3 = nn.MaxPool1d(2)
        
        # 200 -> 100 -> 50 -> 25 length after three pools of pool_size=2
        self.fc1 = nn.Linear(128 * 25, 64)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(64, num_classes)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        x = x.view(x.size(0), -1) # Flatten
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class CNNLSTM(nn.Module):
    """
    CNN-LSTM Hybrid Model in PyTorch.
    Combines feature extraction of Conv1D layers with temporal sequence modeling of LSTM.
    Input shape: (batch_size, 1, 200)
    """
    def __init__(self, num_classes=5):
        super(CNNLSTM, self).__init__()
        self.conv1 = nn.Conv1d(1, 16, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(16)
        self.pool1 = nn.MaxPool1d(2)
        
        self.conv2 = nn.Conv1d(16, 32, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(32)
        self.pool2 = nn.MaxPool1d(2)
        
        # Input shape to LSTM: (batch_size, seq_len, input_size) -> (batch, 50, 32)
        self.lstm = nn.LSTM(input_size=32, hidden_size=64, batch_first=True)
        self.fc1 = nn.Linear(64, 64)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(64, num_classes)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x) # (batch, 32, 50)
        
        # Reshape for LSTM: (batch, seq_len, input_size)
        x = x.transpose(1, 2) # (batch, 50, 32)
        
        # LSTM forward pass
        out, _ = self.lstm(x)
        # Take the last time step output
        x = out[:, -1, :]
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class ExoplanetClassifierPipeline:
    """
    Unified pipeline to train, save, and evaluate all 5 models as an ensemble.
    Using scikit-learn/XGBoost/LightGBM for tabular and PyTorch for deep learning.
    """
    def __init__(self, model_dir="models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.rf = None
        self.xgb = None
        self.lgbm = None
        self.cnn = None
        self.cnn_lstm = None
        self.feature_columns = None

    def train_tabular_models(self, X_train, y_train):
        """Trains RF, XGBoost, and LightGBM models."""
        self.feature_columns = list(X_train.columns)
        
        logger.info("Training Random Forest Classifier...")
        self.rf = build_rf_model()
        self.rf.fit(X_train, y_train)
        joblib.dump(self.rf, os.path.join(self.model_dir, "rf_model.pkl"))
        
        logger.info("Training XGBoost Classifier...")
        self.xgb = build_xgb_model()
        self.xgb.fit(X_train, y_train)
        joblib.dump(self.xgb, os.path.join(self.model_dir, "xgb_model.pkl"))
        
        logger.info("Training LightGBM Classifier...")
        self.lgbm = build_lgbm_model()
        self.lgbm.fit(X_train, y_train)
        joblib.dump(self.lgbm, os.path.join(self.model_dir, "lgbm_model.pkl"))
        
        # Save feature columns metadata
        joblib.dump(self.feature_columns, os.path.join(self.model_dir, "feature_columns.pkl"))

    def train_deep_models(self, X_train_curves, y_train, epochs=15, batch_size=32):
        """Trains PyTorch CNN and CNN-LSTM models."""
        # Standardize shape to (samples, 1, 200) for PyTorch Conv1d
        X_train_reshaped = np.expand_dims(X_train_curves, axis=1).astype(np.float32)
        y_train_tensor = torch.tensor(y_train, dtype=torch.long)
        X_train_tensor = torch.tensor(X_train_reshaped, dtype=torch.float32)
        
        dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 1. Train CNN
        logger.info("Training 1D CNN Model in PyTorch...")
        self.cnn = CNN1D()
        self._train_pytorch_model(self.cnn, dataloader, epochs)
        torch.save(self.cnn.state_dict(), os.path.join(self.model_dir, "cnn_model.pth"))
        
        # 2. Train CNN-LSTM
        logger.info("Training CNN-LSTM Hybrid Model in PyTorch...")
        self.cnn_lstm = CNNLSTM()
        self._train_pytorch_model(self.cnn_lstm, dataloader, epochs)
        torch.save(self.cnn_lstm.state_dict(), os.path.join(self.model_dir, "cnn_lstm_model.pth"))

    def _train_pytorch_model(self, model, dataloader, epochs):
        model.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        for epoch in range(epochs):
            for X_batch, y_batch in dataloader:
                optimizer.zero_grad()
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch)
                loss.backward()
                optimizer.step()

    def load_models(self):
        """Loads all pre-trained models from disk."""
        try:
            self.rf = joblib.load(os.path.join(self.model_dir, "rf_model.pkl"))
            self.xgb = joblib.load(os.path.join(self.model_dir, "xgb_model.pkl"))
            self.lgbm = joblib.load(os.path.join(self.model_dir, "lgbm_model.pkl"))
            self.feature_columns = joblib.load(os.path.join(self.model_dir, "feature_columns.pkl"))
            
            # Load PyTorch state dicts
            self.cnn = CNN1D()
            self.cnn.load_state_dict(torch.load(os.path.join(self.model_dir, "cnn_model.pth"), map_location='cpu'))
            self.cnn.eval()
            
            self.cnn_lstm = CNNLSTM()
            self.cnn_lstm.load_state_dict(torch.load(os.path.join(self.model_dir, "cnn_lstm_model.pth"), map_location='cpu'))
            self.cnn_lstm.eval()
            
            logger.info("All models successfully loaded from disk.")
            return True
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {str(e)}")
            return False

    def predict_probabilities(self, tabular_features, folded_curve):
        """
        Runs inference across all 5 models and returns individual probabilities and an ensemble average.
        """
        # Format tabular features
        if isinstance(tabular_features, dict):
            df = pd.DataFrame([tabular_features])
            X = df[self.feature_columns]
        else:
            X = tabular_features[self.feature_columns]
            
        # Format folded curves
        curve_input = np.array(folded_curve, dtype=np.float32)
        if len(curve_input.shape) == 1:
            curve_input = np.expand_dims(curve_input, axis=0) # shape (1, 200)
        # Expand for PyTorch channels: (batch, 1, 200)
        curve_input_tensor = torch.tensor(np.expand_dims(curve_input, axis=1), dtype=torch.float32)
        
        # Predict tabular
        rf_prob = self.rf.predict_proba(X)[0]
        xgb_prob = self.xgb.predict_proba(X)[0]
        lgbm_prob = self.lgbm.predict_proba(X)[0]
        
        # Predict deep learning models using PyTorch forward pass
        with torch.no_grad():
            cnn_logits = self.cnn(curve_input_tensor)
            cnn_prob = torch.softmax(cnn_logits, dim=1).numpy()[0]
            
            cnn_lstm_logits = self.cnn_lstm(curve_input_tensor)
            cnn_prob_lstm = torch.softmax(cnn_lstm_logits, dim=1).numpy()[0]
            
        # Simple average ensemble
        ensemble_prob = (rf_prob + xgb_prob + lgbm_prob + cnn_prob + cnn_prob_lstm) / 5.0
        
        return {
            "Random Forest": rf_prob,
            "XGBoost": xgb_prob,
            "LightGBM": lgbm_prob,
            "1D CNN": cnn_prob,
            "CNN-LSTM": cnn_prob_lstm,
            "Ensemble": ensemble_prob
        }
