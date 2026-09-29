from datetime import datetime

from LactoQC.adapters.repository import SqlAlchemyCollectionPointRepository
from LactoQC.domain.models import (
    CollectionPoint,
    Measurement,
    MeasurementType,
    MeasurementUnit,
    Specification,
)


def make_specifications():
    return [
        Specification(MeasurementType.CHLORINE, 0.2, 0.5, MeasurementUnit.MG_L),
        Specification(MeasurementType.PH, 6.5, 7.5, None),
        Specification(MeasurementType.TEMPERATURE, 0.0, 100.0, MeasurementUnit.CELSIUS),
    ]


def make_collection_point(id_=1, name="Collection Point 1"):
    return CollectionPoint(id_, name, "Location 1", specifications=make_specifications())


def test_repository_can_retrieve_saved_collection_point(session_factory):
    collection_point = make_collection_point()
    collection_point.add_measurement(
        Measurement(10, datetime(2026, 9, 28, 8, 0), 0.9, MeasurementUnit.MG_L, MeasurementType.CHLORINE)
    )
    with session_factory() as session:
        SqlAlchemyCollectionPointRepository(session).add(collection_point)
        session.commit()

    with session_factory() as session:
        retrieved = SqlAlchemyCollectionPointRepository(session).get(1)

        assert retrieved.name == "Collection Point 1"
        assert len(retrieved.specifications) == 3
        assert [m.id_ for m in retrieved.measurements] == [10]
        assert retrieved.non_conformities[0].measurement is retrieved.measurements[0]


def test_repository_get_returns_none_for_unknown_id(session):
    assert SqlAlchemyCollectionPointRepository(session).get(999) is None


def test_repository_lists_collection_points(session):
    repo = SqlAlchemyCollectionPointRepository(session)
    repo.add(make_collection_point(2, "Collection Point 2"))
    repo.add(make_collection_point(1, "Collection Point 1"))
    session.commit()

    assert [cp.name for cp in repo.list()] == ["Collection Point 1", "Collection Point 2"]