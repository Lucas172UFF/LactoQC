import pytest
from LactoQC.adapters.repository import AbstractCollectionPointRepository
from LactoQC.domain.models import (
    CollectionPoint,
    MeasurementType,
    MeasurementUnit,
    Specification, 
)


class FakeCollectionPointRepository(AbstractCollectionPointRepository):
    def __init__(self):
        self.collection_points = {}

    def add(self, collection_point: CollectionPoint) -> None:
        self.collection_points[collection_point.id_] = collection_point

    def get(self, collection_point_id: str) -> CollectionPoint:
        return self.collection_points.get(collection_point_id)

    def list(self) -> list[CollectionPoint]:
        return list(self.collection_points.values())

def make_specification() -> list[Specification]:
    return [
        Specification(MeasurementType.CHLORINE, 0.2, 0.5, MeasurementUnit.MG_L),
        Specification(MeasurementType.PH, 6.5, 7.5, None),
        Specification(MeasurementType.TEMPERATURE, 0.0, 100.0, MeasurementUnit.CELSIUS),
    ]

def make_collection_point(id_: int, name: str, location: str) -> CollectionPoint:
    return CollectionPoint(
        id_=id_,
        name=name,
        location=location,
        specifications=make_specification(),
    )

def test_fake_repository_added_collection_point():
    repo = FakeCollectionPointRepository()
    collection_point = make_collection_point(1, "Collection Point 1", "Location 1")
    repo.add(collection_point)
    assert repo.get(collection_point.id_) == collection_point

def test_fake_repository_returns_none_for_unknown_id():
    repo = FakeCollectionPointRepository()
    assert repo.get(999) is None

def test_fake_repository_lists_collection_points():
    repo = FakeCollectionPointRepository()
    collection_point1 = make_collection_point(1, "Collection Point 1", "Location 1")
    collection_point2 = make_collection_point(2, "Collection Point 2", "Location 2")
    repo.add(collection_point1)
    repo.add(collection_point2)
    collection_points = repo.list()
    assert len(collection_points) == 2
    assert collection_point1 in collection_points
    assert collection_point2 in collection_points

def test_abstract_repository_cannot_be_instantiated():
    with pytest.raises(TypeError):
        AbstractCollectionPointRepository()