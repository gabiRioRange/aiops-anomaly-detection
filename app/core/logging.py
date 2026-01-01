"""Configuração de logging estruturado."""
import sys
from loguru import logger


def setup_logging(debug: bool = False):
    """Configura o sistema de logging."""
    
    # Remove handler padrão
    logger.remove()
    
    # Console logging
    log_level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # File logging com rotação
    logger.add(
        "logs/anomalies_{time:YYYY-MM-DD}.log",
        rotation="500 MB",
        retention="10 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        serialize=False,
    )
    
    # Erros em arquivo separado
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="100 MB",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    return logger
