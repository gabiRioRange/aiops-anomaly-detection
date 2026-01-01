"""Testes para detecção de anomalias."""
import pytest
import numpy as np
from datetime import datetime, timedelta

from app.detection.baseline import ZScoreDetector, MovingAverageDetector
from app.detection.ml_detectors import IsolationForestDetector, LOFDetector
from app.detection.engine import AnomalyDetectionEngine


@pytest.fixture
def normal_data():
    """Dados normais sem anomalias."""
    return np.random.normal(50, 5, 100)


@pytest.fixture
def data_with_spike():
    """Dados com spike anômalo."""
    data = np.random.normal(50, 5, 100)
    data[50] = 200  # Spike
    return data


@pytest.fixture
def timestamps():
    """Timestamps de exemplo."""
    start = datetime.now()
    return [start + timedelta(minutes=i) for i in range(100)]


class TestZScoreDetector:
    """Testes para Z-Score detector."""
    
    def test_fit_predict_normal_data(self, normal_data):
        detector = ZScoreDetector(threshold=3.0)
        anomalies, scores = detector.fit_predict(normal_data)
        
        assert len(anomalies) == len(normal_data)
        assert anomalies.sum() < len(normal_data) * 0.05  # Menos de 5% anomalias
    
    def test_detect_spike(self, data_with_spike):
        detector = ZScoreDetector(threshold=3.0)
        anomalies, scores = detector.fit_predict(data_with_spike)
        
        assert anomalies[50] == True  # Spike detectado
        assert scores[50] > 0.5  # Score alto


class TestMovingAverageDetector:
    """Testes para Moving Average detector."""
    
    def test_detect_with_window(self, normal_data):
        detector = MovingAverageDetector(window_size=10, threshold=3.0)
        anomalies, scores = detector.fit_predict(normal_data)
        
        assert len(anomalies) == len(normal_data)
        assert len(scores) == len(normal_data)
    
    def test_small_data(self):
        detector = MovingAverageDetector(window_size=10)
        small_data = np.array([1, 2, 3])
        anomalies, scores = detector.fit_predict(small_data)
        
        assert len(anomalies) == 3
        assert anomalies.sum() == 0  # Nenhuma anomalia em dados pequenos


class TestIsolationForestDetector:
    """Testes para Isolation Forest."""
    
    def test_fit_predict(self, normal_data):
        detector = IsolationForestDetector(contamination=0.1)
        anomalies, scores = detector.fit_predict(normal_data)
        
        assert len(anomalies) == len(normal_data)
        assert 0 <= anomalies.sum() <= len(normal_data) * 0.15  # ~10% anomalias
    
    def test_detect_spike(self, data_with_spike):
        detector = IsolationForestDetector(contamination=0.05)
        anomalies, scores = detector.fit_predict(data_with_spike)
        
        assert anomalies[50] == True  # Spike detectado


class TestLOFDetector:
    """Testes para LOF detector."""
    
    def test_fit_predict(self, normal_data):
        detector = LOFDetector(contamination=0.1)
        anomalies, scores = detector.fit_predict(normal_data)
        
        assert len(anomalies) == len(normal_data)
        assert len(scores) == len(normal_data)


class TestAnomalyDetectionEngine:
    """Testes para o engine principal."""
    
    def test_detect_zscore(self, timestamps, normal_data):
        engine = AnomalyDetectionEngine()
        result = engine.detect(timestamps, normal_data.tolist(), method="z-score")
        
        assert result["method"] == "z-score"
        assert "anomalies" in result
        assert "scores" in result
        assert result["anomaly_count"] >= 0
    
    def test_detect_isolation_forest(self, timestamps, data_with_spike):
        engine = AnomalyDetectionEngine()
        result = engine.detect(
            timestamps, 
            data_with_spike.tolist(), 
            method="isolation-forest",
            sensitivity="high"
        )
        
        assert result["anomaly_count"] > 0
        assert result["anomalies"][50] == True
    
    def test_group_anomalies(self, timestamps):
        engine = AnomalyDetectionEngine()
        
        # Cria anomalias próximas
        anomalies = [False] * 100
        anomalies[20:25] = [True] * 5  # Grupo 1
        anomalies[30:35] = [True] * 5  # Grupo 2 (dentro da janela)
        
        scores = [0.0] * 100
        for i in range(20, 35):
            scores[i] = 0.8
        
        values = [50.0] * 100
        
        events = engine.group_anomalies(
            timestamps, anomalies, scores, values, "cpu"
        )
        
        assert len(events) > 0
        assert events[0]["metric"] == "cpu"
        assert "priority" in events[0]
