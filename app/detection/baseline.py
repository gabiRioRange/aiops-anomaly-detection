"""Métodos baseline de detecção de anomalias."""
import numpy as np
import pandas as pd
from typing import Tuple, List
from loguru import logger


class ZScoreDetector:
    """Detector baseado em Z-score."""
    
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.mean_ = None
        self.std_ = None
    
    def fit(self, X: np.ndarray) -> 'ZScoreDetector':
        """Calcula média e desvio padrão."""
        self.mean_ = np.mean(X)
        self.std_ = np.std(X)
        logger.debug(f"Z-score fitted: mean={self.mean_:.2f}, std={self.std_:.2f}")
        return self
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prediz anomalias e retorna scores."""
        if self.mean_ is None or self.std_ is None:
            raise ValueError("Detector precisa ser fitted primeiro")
        
        # Evita divisão por zero
        if self.std_ == 0:
            return np.zeros(len(X), dtype=bool), np.zeros(len(X))
        
        z_scores = np.abs((X - self.mean_) / self.std_)
        anomalies = z_scores > self.threshold
        
        # Normaliza scores para 0-1
        scores = np.clip(z_scores / (self.threshold * 2), 0, 1)
        
        return anomalies, scores
    
    def fit_predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fit e predict em um passo."""
        return self.fit(X).predict(X)


class MovingAverageDetector:
    """Detector baseado em média e desvio móvel."""
    
    def __init__(self, window_size: int = 10, threshold: float = 3.0):
        self.window_size = window_size
        self.threshold = threshold
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detecta anomalias usando janela móvel."""
        if len(X) < self.window_size:
            logger.warning(f"Série com {len(X)} pontos < window_size {self.window_size}")
            return np.zeros(len(X), dtype=bool), np.zeros(len(X))
        
        df = pd.DataFrame({'value': X})
        
        # Calcula média e desvio móvel
        rolling_mean = df['value'].rolling(window=self.window_size, center=False).mean()
        rolling_std = df['value'].rolling(window=self.window_size, center=False).std()
        
        # Evita divisão por zero
        rolling_std = rolling_std.replace(0, 1e-6)
        
        # Calcula z-score local
        z_scores = np.abs((df['value'] - rolling_mean) / rolling_std)
        
        # Primeiros pontos não têm janela completa
        z_scores[:self.window_size] = 0
        
        anomalies = z_scores > self.threshold
        scores = np.clip(z_scores / (self.threshold * 2), 0, 1)
        
        return anomalies.values, scores.values
    
    def fit_predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fit e predict (não precisa fit para este método)."""
        return self.predict(X)


def generate_reason(method: str, score: float, value: float, threshold: float = None) -> str:
    """Gera explicação textual da anomalia."""
    if method == "z-score":
        sigma = score * threshold * 2 if threshold else score * 6
        return f"Valor {value:.2f} está {sigma:.1f} desvios padrão da média"
    elif method == "moving-average":
        return f"Valor {value:.2f} diverge significativamente da média móvel local"
    else:
        return f"Score de anomalia: {score:.3f}"
