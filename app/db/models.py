"""Modelos SQLAlchemy para persistência."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    """Base declarativa para modelos."""
    pass


class DetectionHistory(Base):
    """Histórico de detecções."""
    
    __tablename__ = "detection_history"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(100), index=True, nullable=False)
    metric_name = Column(String(50), index=True, nullable=False)
    method = Column(String(50), nullable=False)
    sensitivity = Column(String(20), nullable=False)
    
    total_points = Column(Integer, nullable=False)
    anomaly_count = Column(Integer, nullable=False)
    anomaly_percentage = Column(Float, nullable=False)
    detection_time_ms = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DetectionHistory {self.resource_id} {self.metric_name} {self.created_at}>"


class AnomalyEvent(Base):
    """Eventos de anomalia agrupados (conceito AIOps)."""
    
    __tablename__ = "anomaly_events"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(100), index=True, nullable=False)
    metric_name = Column(String(50), index=True, nullable=False)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    max_score = Column(Float, nullable=False)
    anomaly_points = Column(Integer, nullable=False)
    peak_value = Column(Float, nullable=False)
    priority = Column(Float, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AnomalyEvent {self.resource_id} {self.start_time} priority={self.priority}>"


class MetricSnapshot(Base):
    """Snapshot de métricas para análise histórica."""
    
    __tablename__ = "metric_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(100), index=True, nullable=False)
    metric_name = Column(String(50), index=True, nullable=False)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<MetricSnapshot {self.resource_id} {self.metric_name} {self.timestamp}>"
