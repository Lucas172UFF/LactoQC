"""Testes da inicialização da persistência extraída de flask_app.py (refatoração SRP)."""
from sqlalchemy.orm import clear_mappers

from LactoQC.adapters.database import build_session_factory
from LactoQC.adapters.repository import (
    SqlAlchemyCollectionPointRepository,
    SqlAlchemyProductionBatchRepository,
)
from LactoQC.entrypoints.flask_app import create_app


def test_build_session_factory_maps_all_aggregates_and_creates_tables():
    session_factory = build_session_factory("sqlite:///:memory:")
    try:
        session = session_factory()
        # Se algum mapeamento ou tabela faltasse, as consultas abaixo falhariam.
        assert SqlAlchemyCollectionPointRepository(session).list() == []
        assert SqlAlchemyProductionBatchRepository(session).list() == []
        session.close()
    finally:
        clear_mappers()


def test_create_app_without_session_factory_uses_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    try:
        client = create_app().test_client()
        assert client.get("/health").status_code == 200
        assert client.get("/production-batches").status_code == 200
    finally:
        clear_mappers()
