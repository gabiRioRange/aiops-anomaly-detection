"""Aplicação FastAPI principal."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.api.endpoints import detect, health, methods


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia lifecycle da aplicação."""
    # Startup
    setup_logging(debug=settings.debug)
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    
    # Inicializa banco de dados
    await init_db()
    logger.info("Database inicializado")
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação")


# Cria aplicação
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Mini AIOps: Detecção de anomalias em métricas de infraestrutura",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates e static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registra routers
app.include_router(health.router, tags=["Health"])
app.include_router(methods.router, tags=["Methods"])
app.include_router(detect.router, prefix="/api/v1", tags=["Detection"])


@app.get("/")
async def root():
    """Redirect to dashboard."""
    return {"message": "AIOps Anomaly Detection API", "dashboard": "/dashboard"}


@app.get("/dashboard")
async def dashboard():
    """Serve the web dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": {}})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers
    )
