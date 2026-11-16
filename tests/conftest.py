import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from LactoQC.adapters.orm import metadata, start_all_mappers
from LactoQC.entrypoints.flask_app import create_app
from LactoQC.adapters.repository import FakeCollectionPointRepository, FakeProductionBatchRepository


class FakeSession:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True

    def close(self):
        pass


@pytest.fixture
def fake_repo():
    return FakeCollectionPointRepository()

@pytest.fixture
def production_batch_repo():
    return FakeProductionBatchRepository()

@pytest.fixture
def fake_session():
    return FakeSession()

@pytest.fixture(scope="function")
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def session_factory(in_memory_db):
    start_all_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()

@pytest.fixture(scope="function")
def session(session_factory):
    session = session_factory()
    yield session
    session.close()

@pytest.fixture
def client(session_factory):
    app = create_app(session_factory)
    app.config["TESTING"] = True
    return app.test_client()
@pytest.fixture
def sqlite_engine_production_batch():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    metadata.drop_all(engine)


@pytest.fixture
def sqlite_session_production_batch(sqlite_engine_production_batch):
    start_all_mappers()
    session_factory = sessionmaker(bind=sqlite_engine_production_batch)
    session = session_factory()
    yield session
    session.close()
    clear_mappers()
