"""Detectores baseados em Machine Learning."""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from typing import Tuple, Optional
import pandas as pd
from loguru import logger


class IsolationForestDetector:
    """Detector usando Isolation Forest."""
    
    def __init__(self, contamination: float = 0.01, random_state: int = 42):
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1
        )
        self.fitted_ = False
    
    def _prepare_features(self, X: np.ndarray) -> np.ndarray:
        """Prepara features para o modelo."""
        # Adiciona features derivadas
        features = []
        
        # Valor original
        features.append(X.reshape(-1, 1))
        
        # Diferença com ponto anterior
        diff = np.diff(X, prepend=X[0])
        features.append(diff.reshape(-1, 1))
        
        # Taxa de mudança
        rate = np.where(X[:-1] != 0, diff[1:] / X[:-1], 0)
        rate = np.insert(rate, 0, 0)
        features.append(rate.reshape(-1, 1))
        
        return np.hstack(features)
    
    def fit(self, X: np.ndarray) -> 'IsolationForestDetector':
        """Treina o modelo."""
        X_features = self._prepare_features(X)
        self.model.fit(X_features)
        self.fitted_ = True
        logger.debug(f"IsolationForest fitted com {len(X)} pontos")
        return self
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prediz anomalias."""
        if not self.fitted_:
            raise ValueError("Modelo precisa ser fitted primeiro")
        
        X_features = self._prepare_features(X)
        
        # -1 para anomalia, 1 para normal
        predictions = self.model.predict(X_features)
        anomalies = predictions == -1
        
        # Score: quanto mais negativo, mais anômalo
        scores_raw = self.model.score_samples(X_features)
        
        # Normaliza scores para 0-1 (inverte para maior = mais anômalo)
        scores = 1 / (1 + np.exp(scores_raw))
        
        return anomalies, scores
    
    def fit_predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fit e predict em um passo."""
        return self.fit(X).predict(X)


class LOFDetector:
    """Detector usando Local Outlier Factor."""
    
    def __init__(self, contamination: float = 0.01, n_neighbors: int = 20):
        self.contamination = contamination
        self.n_neighbors = min(n_neighbors, 20)  # Limita para séries pequenas
    
    def _prepare_features(self, X: np.ndarray) -> np.ndarray:
        """Prepara features (similar ao IsolationForest)."""
        features = []
        features.append(X.reshape(-1, 1))
        
        diff = np.diff(X, prepend=X[0])
        features.append(diff.reshape(-1, 1))
        
        rate = np.where(X[:-1] != 0, diff[1:] / X[:-1], 0)
        rate = np.insert(rate, 0, 0)
        features.append(rate.reshape(-1, 1))
        
        return np.hstack(features)
    
    def fit_predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """LOF não precisa de fit separado."""
        X_features = self._prepare_features(X)
        
        # Ajusta n_neighbors se necessário
        n_neighbors = min(self.n_neighbors, len(X) - 1)
        if n_neighbors < 2:
            logger.warning("Série muito curta para LOF, retornando sem anomalias")
            return np.zeros(len(X), dtype=bool), np.zeros(len(X))
        
        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=self.contamination,
            novelty=False
        )
        
        predictions = model.fit_predict(X_features)
        anomalies = predictions == -1
        
        # Scores negativos (mais negativo = mais anômalo)
        scores_raw = -model.negative_outlier_factor_
        
        # Normaliza
        scores = (scores_raw - scores_raw.min()) / (scores_raw.max() - scores_raw.min() + 1e-6)
        
        return anomalies, scores


class ProphetDetector:
    """Detector usando Prophet para séries temporais."""
    
    def __init__(self, changepoint_prior_scale: float = 0.05, seasonality_mode: str = 'additive'):
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_mode = seasonality_mode
        self.model = None
        try:
            from prophet import Prophet
            self.Prophet = Prophet
        except ImportError:
            logger.warning("Prophet não disponível. Instale com: pip install prophet")
            self.Prophet = None
    
    def fit(self, X: np.ndarray, timestamps: Optional[np.ndarray] = None) -> 'ProphetDetector':
        """Treina o modelo Prophet."""
        if self.Prophet is None:
            raise ImportError("Prophet não instalado")
        
        if timestamps is None:
            timestamps = np.arange(len(X))
        
        # Prepara dados para Prophet
        df = pd.DataFrame({
            'ds': pd.to_datetime(timestamps),
            'y': X
        })
        
        self.model = self.Prophet(
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_mode=self.seasonality_mode
        )
        self.model.fit(df)
        logger.debug(f"Prophet fitted com {len(X)} pontos")
        return self
    
    def predict(self, X: np.ndarray, timestamps: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Detecta anomalias usando Prophet."""
        if self.model is None:
            raise ValueError("Modelo não treinado")
        
        if timestamps is None:
            timestamps = np.arange(len(X))
        
        df = pd.DataFrame({
            'ds': pd.to_datetime(timestamps),
            'y': X
        })
        
        # Faz forecast
        forecast = self.model.predict(df[['ds']])
        
        # Calcula resíduos
        residuals = np.abs(X - forecast['yhat'].values)
        
        # Threshold baseado em std dos resíduos
        threshold = forecast['yhat_upper'].values - forecast['yhat'].values
        anomalies = residuals > threshold
        
        # Scores baseados nos resíduos
        scores = residuals / (threshold + 1e-6)
        scores = np.clip(scores, 0, 1)
        
        return anomalies, scores
