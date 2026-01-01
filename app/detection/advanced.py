"""Detectores avançados usando dtaianomaly."""
import numpy as np
from typing import Tuple, Optional
from loguru import logger

try:
    from dtaianomaly import IForest, MatrixProfile
    DTAI_AVAILABLE = True
except ImportError:
    DTAI_AVAILABLE = False
    logger.warning("dtaianomaly não disponível. Instale com: pip install dtaianomaly")


class DTAIDetector:
    """Detector usando dtaianomaly library."""
    
    def __init__(self, method: str = "matrix-profile", contamination: float = 0.01):
        if not DTAI_AVAILABLE:
            raise ImportError("dtaianomaly não está instalado")
        
        self.method = method
        self.contamination = contamination
        
        if method == "matrix-profile":
            self.detector = MatrixProfile()
        elif method == "iforest":
            self.detector = IForest()
        else:
            # Fallback para Matrix Profile
            self.detector = MatrixProfile()
    
    def fit_predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detecta anomalias usando dtaianomaly."""
        try:
            # Reshape para formato esperado
            X_reshaped = X.reshape(-1, 1)
            
            # Fit
            self.detector.fit(X_reshaped)
            
            # Get anomaly scores
            scores = self.detector.decision_function(X_reshaped)
            
            # Normaliza scores para 0-1
            scores_normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-6)
            
            # Define threshold baseado em contamination
            threshold = np.percentile(scores_normalized, (1 - self.contamination) * 100)
            anomalies = scores_normalized > threshold
            
            logger.debug(f"DTAI {self.method} detectou {anomalies.sum()} anomalias")
            
            return anomalies, scores_normalized
            
        except Exception as e:
            logger.error(f"Erro no DTAI detector: {e}")
            # Fallback: retorna sem anomalias
            return np.zeros(len(X), dtype=bool), np.zeros(len(X))
