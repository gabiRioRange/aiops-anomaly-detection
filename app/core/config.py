"""Configurações da aplicação."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Configurações do projeto."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Settings
    app_name: str = "AIOps Anomaly Detection"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./anomalies.db"
    
    # Detection Settings
    default_contamination: float = 0.01
    default_window_size: int = 10
    z_score_threshold: float = 3.0
    anomaly_grouping_window_seconds: int = 300  # 5 minutos
    
    # Sensitivity levels
    sensitivity_low: float = 0.05
    sensitivity_medium: float = 0.01
    sensitivity_high: float = 0.005
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1


settings = Settings()
