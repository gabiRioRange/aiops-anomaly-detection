"""Endpoints de detecção de anomalias."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio
from datetime import datetime
from loguru import logger

from app.api.models import (
    DetectionRequest, 
    DetectionResponse, 
    SeriesAnomaly, 
    AnomalyPoint
)
from app.detection.engine import detection_engine
from app.db.session import get_db
from app.db.models import DetectionHistory, AnomalyEvent

router = APIRouter()


@router.post("/detect", response_model=DetectionResponse)
async def detect_anomalies(
    request: DetectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Detecta anomalias em uma ou mais séries temporais.
    
    Suporta múltiplas séries em paralelo e agrupa eventos (conceito AIOps).
    """
    try:
        # Processa séries em paralelo
        tasks = [
            _process_single_series(
                series, 
                request.method, 
                request.sensitivity
            )
            for series in request.series
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Salva histórico no banco
        for result in results:
            history = DetectionHistory(
                resource_id=result.resource_id,
                metric_name=result.metric_name,
                method=result.method_used,
                sensitivity=request.sensitivity,
                total_points=result.total_points,
                anomaly_count=result.anomaly_count,
                anomaly_percentage=result.anomaly_percentage,
                detection_time_ms=result.detection_time_ms
            )
            db.add(history)
        
        await db.commit()
        
        # Agrupa eventos (AIOps concept)
        all_grouped_events = []
        for series, result in zip(request.series, results):
            if result.anomaly_count > 0:
                timestamps = [point.timestamp for point in series.data]
                anomalies = [point.is_anomaly for point in result.anomalies]
                scores = [point.score for point in result.anomalies]
                values = [point.value for point in result.anomalies]
                
                events = detection_engine.group_anomalies(
                    timestamps, anomalies, scores, values, series.metric_name
                )
                
                # Salva eventos no banco
                for event in events:
                    db_event = AnomalyEvent(
                        resource_id=series.resource_id,
                        metric_name=series.metric_name,
                        start_time=event["start_time"],
                        end_time=event["end_time"],
                        duration_seconds=event["duration_seconds"],
                        max_score=event["max_score"],
                        anomaly_points=event["anomaly_points"],
                        peak_value=event["peak_value"],
                        priority=event["priority"]
                    )
                    db.add(db_event)
                    
                    # Formata para resposta
                    all_grouped_events.append({
                        "resource_id": series.resource_id,
                        "metric": event["metric"],
                        "start_time": event["start_time"].isoformat(),
                        "end_time": event["end_time"].isoformat(),
                        "duration_seconds": event["duration_seconds"],
                        "priority": event["priority"],
                        "max_score": event["max_score"],
                        "anomaly_points": event["anomaly_points"]
                    })
        
        await db.commit()
        
        total_anomalies = sum(r.anomaly_count for r in results)
        
        logger.info(
            f"Detecção completa: {len(results)} séries | "
            f"{total_anomalies} anomalias | "
            f"{len(all_grouped_events)} eventos agrupados"
        )
        
        return DetectionResponse(
            results=results,
            grouped_events=all_grouped_events if all_grouped_events else None,
            total_series=len(results),
            total_anomalies=total_anomalies
        )
        
    except Exception as e:
        logger.error(f"Erro na detecção: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na detecção: {str(e)}")


async def _process_single_series(
    series, 
    method: str, 
    sensitivity: str
) -> SeriesAnomaly:
    """Processa uma única série temporal."""
    timestamps = [point.timestamp for point in series.data]
    values = [point.value for point in series.data]
    
    # Executa detecção
    result = detection_engine.detect(
        timestamps=timestamps,
        values=values,
        method=method,
        sensitivity=sensitivity
    )
    
    # Monta anomalias
    anomaly_points = []
    for i, (ts, val, is_anom, score) in enumerate(
        zip(timestamps, values, result["anomalies"], result["scores"])
    ):
        reason = None
        if is_anom:
            from app.detection.baseline import generate_reason
            reason = generate_reason(method, score, val)
        
        anomaly_points.append(AnomalyPoint(
            timestamp=ts,
            value=val,
            score=score,
            is_anomaly=is_anom,
            reason=reason
        ))
    
    anomaly_count = result["anomaly_count"]
    total_points = len(values)
    anomaly_percentage = (anomaly_count / total_points * 100) if total_points > 0 else 0
    
    return SeriesAnomaly(
        resource_id=series.resource_id,
        metric_name=series.metric_name,
        method_used=method,
        anomalies=anomaly_points,
        total_points=total_points,
        anomaly_count=anomaly_count,
        anomaly_percentage=round(anomaly_percentage, 2),
        detection_time_ms=result["detection_time_ms"]
    )
