"""Endpoints para informações sobre métodos."""
from fastapi import APIRouter
from typing import List
from app.api.models import MethodInfo

router = APIRouter()


@router.get("/methods", response_model=List[MethodInfo])
async def list_methods():
    """
    Lista todos os métodos de detecção disponíveis.
    """
    methods = [
        MethodInfo(
            name="z-score",
            description="Detecção baseada em desvio padrão da média global. Simples e rápido.",
            category="statistical",
            best_for=["Séries estacionárias", "Detecção rápida", "Baseline"]
        ),
        MethodInfo(
            name="moving-average",
            description="Usa média e desvio móvel para capturar mudanças locais de regime.",
            category="statistical",
            best_for=["Séries com tendências", "Mudanças de padrão", "Sazonalidade"]
        ),
        MethodInfo(
            name="isolation-forest",
            description="Algoritmo de ML que isola anomalias. Robusto e escalável.",
            category="ml",
            best_for=["Dados multivariados", "Anomalias complexas", "Produção"]
        ),
        MethodInfo(
            name="lof",
            description="Local Outlier Factor - detecta outliers baseado em densidade local.",
            category="ml",
            best_for=["Clusters irregulares", "Anomalias de densidade", "Dados não-lineares"]
        ),
        MethodInfo(
            name="dtai-auto",
            description="Método avançado usando dtaianomaly library (Matrix Profile).",
            category="advanced",
            best_for=["Padrões temporais", "Motifs", "Estado da arte"]
        )
    ]
    
    return methods
