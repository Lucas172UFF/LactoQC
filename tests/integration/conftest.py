import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from LactoQC.adapters.orm import metadata, start_mappers_production_batch


@pytest.fixture
def sqlite_engine_production_batch():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    metadata.drop_all(engine)


@pytest.fixture
def sqlite_session_production_batch(sqlite_engine_production_batch):
    start_mappers_production_batch()
    session_factory = sessionmaker(bind=sqlite_engine_production_batch)
    session = session_factory()
    yield session
    session.close()
    clear_mappers()
