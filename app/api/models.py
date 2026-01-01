"""Modelos Pydantic para API."""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional
from datetime import datetime


class MetricPoint(BaseModel):
    """Ponto individual de métrica."""
    timestamp: datetime
    value: float
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "timestamp": "2025-12-28T22:00:00",
            "value": 75.5
        }
    })


class TimeSeriesInput(BaseModel):
    """Input de série temporal."""
    resource_id: str = Field(..., description="Identificador do recurso (pod/host/service)")
    metric_name: Literal["cpu", "memory", "requests", "error_rate", "latency"] = Field(
        ..., description="Nome da métrica"
    )
    data: List[MetricPoint] = Field(..., min_length=10, description="Pontos da série temporal")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "resource_id": "pod-web-001",
            "metric_name": "cpu",
            "data": [
                {"timestamp": "2025-12-28T22:00:00", "value": 45.2},
                {"timestamp": "2025-12-28T22:01:00", "value": 48.1}
            ]
        }
    })


class DetectionRequest(BaseModel):
    """Requisição de detecção."""
    series: List[TimeSeriesInput] = Field(..., min_length=1, max_length=10)
    method: Literal[
        "z-score", 
        "moving-average", 
        "isolation-forest", 
        "lof",
        "dtai-auto"
    ] = Field(default="isolation-forest", description="Método de detecção")
    sensitivity: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Sensibilidade da detecção"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "series": [{
                "resource_id": "pod-web-001",
                "metric_name": "cpu",
                "data": [
                    {"timestamp": "2025-12-28T22:00:00", "value": 45.2},
                    {"timestamp": "2025-12-28T22:01:00", "value": 98.5}
                ]
            }],
            "method": "isolation-forest",
            "sensitivity": "medium"
        }
    })


class AnomalyPoint(BaseModel):
    """Ponto anômalo detectado."""
    timestamp: datetime
    value: float
    score: float = Field(..., ge=0.0, le=1.0, description="Score de anomalia (0-1)")
    is_anomaly: bool
    reason: Optional[str] = None


class SeriesAnomaly(BaseModel):
    """Resultado de detecção para uma série."""
    resource_id: str
    metric_name: str
    method_used: str
    anomalies: List[AnomalyPoint]
    total_points: int
    anomaly_count: int
    anomaly_percentage: float
    detection_time_ms: float


class DetectionResponse(BaseModel):
    """Resposta da detecção."""
    results: List[SeriesAnomaly]
    grouped_events: Optional[List[dict]] = None
    total_series: int
    total_anomalies: int


class MethodInfo(BaseModel):
    """Informação sobre método de detecção."""
    name: str
    description: str
    category: Literal["statistical", "ml", "advanced"]
    best_for: List[str]


class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    database_connected: bool
