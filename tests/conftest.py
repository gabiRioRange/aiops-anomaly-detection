"""Configuração para testes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.models import Base


@pytest.fixture
def client():
    """Cliente de teste para FastAPI."""
    return TestClient(app)


@pytest.fixture
async def db_session():
    """Sessão de banco de dados para testes."""
    # Cria engine em memória para testes
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Cria todas as tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Cria sessão
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Limpa após teste
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)