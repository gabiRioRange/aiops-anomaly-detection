"""Engine principal de detecção de anomalias."""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from datetime import datetime
import time
from loguru import logger

from app.detection.baseline import ZScoreDetector, MovingAverageDetector, generate_reason
from app.detection.ml_detectors import IsolationForestDetector, LOFDetector, ProphetDetector
from app.detection.advanced import DTAIDetector, DTAI_AVAILABLE
from app.core.config import settings


class AnomalyDetectionEngine:
    """Engine que coordena diferentes métodos de detecção."""
    
    def __init__(self):
        self.methods = {
            "z-score": self._detect_zscore,
            "moving-average": self._detect_moving_average,
            "isolation-forest": self._detect_isolation_forest,
            "lof": self._detect_lof,
            "prophet": self._detect_prophet,
            "dtai-auto": self._detect_dtai_auto
        }
    
    def get_contamination_by_sensitivity(self, sensitivity: str) -> float:
        """Retorna contamination baseado na sensibilidade."""
        sensitivity_map = {
            "low": settings.sensitivity_low,
            "medium": settings.sensitivity_medium,
            "high": settings.sensitivity_high
        }
        return sensitivity_map.get(sensitivity, settings.default_contamination)
    
    def detect(
        self, 
        timestamps: List[datetime],
        values: List[float],
        method: str = "isolation-forest",
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Detecta anomalias em uma série temporal.
        
        Args:
            timestamps: Lista de timestamps
            values: Lista de valores
            method: Método de detecção
            sensitivity: Nível de sensibilidade
            
        Returns:
            Dicionário com resultados da detecção
        """
        start_time = time.time()
        
        # Converte para numpy array
        X = np.array(values, dtype=float)
        
        if len(X) == 0:
            return self._empty_result(0)
        
        # Seleciona método
        if method not in self.methods:
            logger.warning(f"Método {method} não encontrado, usando isolation-forest")
            method = "isolation-forest"
        
        # Executa detecção
        contamination = self.get_contamination_by_sensitivity(sensitivity)
        
        try:
            anomalies, scores = self.methods[method](X, contamination)
        except Exception as e:
            logger.error(f"Erro na detecção com {method}: {e}")
            anomalies = np.zeros(len(X), dtype=bool)
            scores = np.zeros(len(X))
        
        # Monta resultado
        detection_time = (time.time() - start_time) * 1000  # ms
        
        result = {
            "method": method,
            "anomalies": anomalies.tolist(),
            "scores": scores.tolist(),
            "timestamps": timestamps,
            "values": values,
            "anomaly_count": int(anomalies.sum()),
            "detection_time_ms": round(detection_time, 2)
        }
        
        logger.info(
            f"Detecção completa: {method} | "
            f"{result['anomaly_count']}/{len(X)} anomalias | "
            f"{detection_time:.2f}ms"
        )
        
        return result
    
    def _detect_zscore(self, X: np.ndarray, contamination: float) -> Tuple[np.ndarray, np.ndarray]:
        """Detecção por Z-score."""
        detector = ZScoreDetector(threshold=settings.z_score_threshold)
        return detector.fit_predict(X)
    
    def _detect_moving_average(
        self, 
        X: np.ndarray, 
        contamination: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Detecção por média móvel."""
        detector = MovingAverageDetector(
            window_size=settings.default_window_size,
            threshold=settings.z_score_threshold
        )
        return detector.fit_predict(X)
    
    def _detect_isolation_forest(
        self, 
        X: np.ndarray, 
        contamination: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Detecção por Isolation Forest."""
        detector = IsolationForestDetector(contamination=contamination)
        return detector.fit_predict(X)
    
    def _detect_lof(self, X: np.ndarray, contamination: float) -> Tuple[np.ndarray, np.ndarray]:
        """Detecção por Local Outlier Factor."""
        detector = LOFDetector(contamination=contamination)
        return detector.fit_predict(X)
    
    def _detect_prophet(self, X: np.ndarray, contamination: float) -> Tuple[np.ndarray, np.ndarray]:
        """Detecção usando Prophet."""
        try:
            detector = ProphetDetector()
            return detector.fit_predict(X)
        except ImportError:
            logger.warning("Prophet não disponível, usando isolation-forest")
            return self._detect_isolation_forest(X, contamination)
    
    def _detect_dtai_auto(
        self, 
        X: np.ndarray, 
        contamination: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Detecção usando dtaianomaly (modo auto)."""
        if not DTAI_AVAILABLE:
            logger.warning("dtaianomaly não disponível, usando isolation-forest")
            return self._detect_isolation_forest(X, contamination)
        
        detector = DTAIDetector(method="matrix-profile", contamination=contamination)
        return detector.fit_predict(X)
    
    def _empty_result(self, length: int) -> Dict[str, Any]:
        """Retorna resultado vazio."""
        return {
            "method": "none",
            "anomalies": [False] * length,
            "scores": [0.0] * length,
            "timestamps": [],
            "values": [],
            "anomaly_count": 0,
            "detection_time_ms": 0.0
        }
    
    def group_anomalies(
        self, 
        timestamps: List[datetime],
        anomalies: List[bool],
        scores: List[float],
        values: List[float],
        metric_name: str
    ) -> List[Dict[str, Any]]:
        """
        Agrupa anomalias próximas no tempo em eventos únicos.
        Conceito AIOps: reduzir ruído de alertas.
        """
        if not any(anomalies):
            return []
        
        events = []
        current_event = None
        window_seconds = settings.anomaly_grouping_window_seconds
        
        for i, (ts, is_anom, score, val) in enumerate(zip(timestamps, anomalies, scores, values)):
            if not is_anom:
                if current_event:
                    events.append(current_event)
                    current_event = None
                continue
            
            if current_event is None:
                # Inicia novo evento
                current_event = {
                    "start_time": ts,
                    "end_time": ts,
                    "metric": metric_name,
                    "max_score": score,
                    "anomaly_points": 1,
                    "peak_value": val,
                    "timestamps": [ts],
                    "values": [val]
                }
            else:
                # Verifica se está dentro da janela
                time_diff = (ts - current_event["end_time"]).total_seconds()
                
                if time_diff <= window_seconds:
                    # Continua evento atual
                    current_event["end_time"] = ts
                    current_event["max_score"] = max(current_event["max_score"], score)
                    current_event["anomaly_points"] += 1
                    current_event["timestamps"].append(ts)
                    current_event["values"].append(val)
                    
                    if score > current_event["max_score"]:
                        current_event["peak_value"] = val
                else:
                    # Evento anterior finalizado, inicia novo
                    events.append(current_event)
                    current_event = {
                        "start_time": ts,
                        "end_time": ts,
                        "metric": metric_name,
                        "max_score": score,
                        "anomaly_points": 1,
                        "peak_value": val,
                        "timestamps": [ts],
                        "values": [val]
                    }
        
        # Adiciona último evento se existir
        if current_event:
            events.append(current_event)
        
        # Calcula duração e prioridade
        for event in events:
            duration = (event["end_time"] - event["start_time"]).total_seconds()
            event["duration_seconds"] = duration
            
            # Prioridade baseada em score e duração
            event["priority"] = self._calculate_priority(
                event["max_score"],
                event["anomaly_points"],
                duration
            )
        
        # Ordena por prioridade (maior primeiro)
        events.sort(key=lambda x: x["priority"], reverse=True)
        
        logger.info(f"Agrupamento AIOps: {len(anomalies)} anomalias → {len(events)} eventos")
        
        return events
    
    def _calculate_priority(self, max_score: float, points: int, duration: float) -> float:
        """
        Calcula prioridade do evento (conceito AIOps).
        Maior score + mais pontos + maior duração = maior prioridade
        """
        score_weight = 0.5
        points_weight = 0.3
        duration_weight = 0.2
        
        # Normaliza componentes
        score_norm = max_score  # já está 0-1
        points_norm = min(points / 10, 1.0)  # até 10 pontos = 1.0
        duration_norm = min(duration / 600, 1.0)  # até 10 min = 1.0
        
        priority = (
            score_weight * score_norm +
            points_weight * points_norm +
            duration_weight * duration_norm
        )
        
        return round(priority, 3)


# Instância global do engine
detection_engine = AnomalyDetectionEngine()
