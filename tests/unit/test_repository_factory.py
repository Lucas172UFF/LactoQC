"""Testes do padrão Abstract Factory (docs/gof.md): a família de repositórios
é escolhida em um único lugar (create_app) e as rotas não conhecem as classes concretas."""
from LactoQC.adapters.repository import (
    AbstractRepositoryFactory,
    FakeCollectionPointRepository,
    FakeProductionBatchRepository,
    InMemoryRepositoryFactory,
    SqlAlchemyCollectionPointRepository,
    SqlAlchemyProductionBatchRepository,
    SqlAlchemyRepositoryFactory,
)
from LactoQC.entrypoints.flask_app import create_app

SPECS = [
    {"measurement_type": "CHLORINE", "min_value": 0.5, "max_value": 5.0},
    {"measurement_type": "PH", "min_value": 6.0, "max_value": 9.5},
    {"measurement_type": "TEMPERATURE", "min_value": 18.0, "max_value": 25.0},
]


class FakeSession:
    def commit(self):
        pass

    def close(self):
        pass


def make_in_memory_client():
    app = create_app(session_factory=FakeSession, repository_factory=InMemoryRepositoryFactory())
    app.config["TESTING"] = True
    return app.test_client()


def test_sqlalchemy_factory_creates_the_whole_sqlalchemy_family_on_the_same_session():
    factory = SqlAlchemyRepositoryFactory()
    session = object()

    cp_repo = factory.collection_points(session)
    pb_repo = factory.production_batches(session)

    assert isinstance(cp_repo, SqlAlchemyCollectionPointRepository)
    assert isinstance(pb_repo, SqlAlchemyProductionBatchRepository)
    assert cp_repo.session is session
    assert pb_repo.session is session


def test_in_memory_factory_creates_the_whole_in_memory_family():
    factory = InMemoryRepositoryFactory()

    assert isinstance(factory.collection_points(None), FakeCollectionPointRepository)
    assert isinstance(factory.production_batches(None), FakeProductionBatchRepository)


def test_in_memory_factory_keeps_state_between_requests():
    factory = InMemoryRepositoryFactory()

    assert factory.collection_points(FakeSession()) is factory.collection_points(FakeSession())
    assert factory.production_batches(FakeSession()) is factory.production_batches(FakeSession())


def test_create_app_uses_sqlalchemy_family_by_default(session_factory):
    app = create_app(session_factory)

    assert isinstance(app.config["REPOSITORY_FACTORY"], SqlAlchemyRepositoryFactory)


def test_api_runs_unchanged_on_the_in_memory_family_without_a_database():
    client = make_in_memory_client()

    created = client.post(
        "/collection-points",
        json={"name": "Sala de envase", "location": "Bloco A", "specifications": SPECS},
    )
    assert created.status_code == 201
    cp_id = created.get_json()["id"]

    measurement = client.post(
        f"/collection-points/{cp_id}/measurements",
        json={"measurement_type": "CHLORINE", "value": 0.1},
    )
    assert measurement.status_code == 201
    new_ncs = measurement.get_json()["non_conformities"]
    assert len(new_ncs) == 1
    assert new_ncs[0]["collection_point_id"] == cp_id

    detail = client.get(f"/collection-points/{cp_id}").get_json()
    assert len(detail["non_conformities"]) == 1
    assert client.get("/production-batches").get_json() == []


def test_a_new_factory_can_be_plugged_without_changing_the_routes():
    class CountingRepositoryFactory(InMemoryRepositoryFactory):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def collection_points(self, session):
            self.calls += 1
            return super().collection_points(session)

    factory = CountingRepositoryFactory()
    assert isinstance(factory, AbstractRepositoryFactory)
    client = create_app(session_factory=FakeSession, repository_factory=factory).test_client()

    client.post("/collection-points", json={"name": "Sala 1", "location": "A", "specifications": SPECS})

    assert factory.calls >= 1
