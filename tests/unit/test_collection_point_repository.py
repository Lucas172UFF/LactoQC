import pytest
from LactoQC.adapters.repository import AbstractCollectionPointRepository
from LactoQC.domain.model import (
    CollectionPoint,
    MeasurementType,
    MeasurementUnit,
    Specification, 
)


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

def test_fake_repository_added_collection_point(fake_repo):
    collection_point = make_collection_point(1, "Collection Point 1", "Location 1")
    fake_repo.add(collection_point)
    assert fake_repo.get(collection_point.id_) == collection_point

def test_fake_repository_returns_none_for_unknown_id(fake_repo):
    assert fake_repo.get(999) is None

def test_fake_repository_lists_collection_points(fake_repo):
    collection_point1 = make_collection_point(1, "Collection Point 1", "Location 1")
    collection_point2 = make_collection_point(2, "Collection Point 2", "Location 2")
    fake_repo.add(collection_point1)
    fake_repo.add(collection_point2)
    collection_points = fake_repo.list()
    assert len(collection_points) == 2
    assert collection_point1 in collection_points
    assert collection_point2 in collection_points

def test_abstract_repository_cannot_be_instantiated():
    with pytest.raises(TypeError):
        AbstractCollectionPointRepository()

def test_fake_repository_assigns_id_when_missing(fake_repo):
    collection_point = make_collection_point(None, "Collection Point 1", "Location 1")
    fake_repo.add(collection_point)
    assert collection_point.id_ == 1
