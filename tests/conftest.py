import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from LactoQC.adapters.orm import metadata, start_mappers
from LactoQC.entrypoints.flask_app import create_app

@pytest.fixture(scope="function")
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def session_factory(in_memory_db):
    start_mappers()
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