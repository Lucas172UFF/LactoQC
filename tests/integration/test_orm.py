from datetime import datetime
from sqlalchemy import text
from LactoQC.domain.models import (
    CollectionPoint,
    Measurement,
    MeasurementType,
    MeasurementUnit,
    Specification
)

def make_specifications():
    return [
        Specification(MeasurementType.CHLORINE, 0.2, 0.5, MeasurementUnit.MG_L),
        Specification(MeasurementType.PH, 6.5, 7.5, None),
        Specification(MeasurementType.TEMPERATURE, 0.0, 100.0, MeasurementUnit.CELSIUS),
    ]

def test_orm_saves_collection_point_with_specifications(session):
    collection_point = CollectionPoint(1, "Collection Point 1", "Location 1", specifications=make_specifications())

    session.add(collection_point)
    session.commit()

    assert list(
        session.execute(
            text(
                "SELECT id, name, location FROM collection_points"
                )
            )
        ) == [
        (1, "Collection Point 1", "Location 1")
    ]
    assert list(
        session.execute(
            text(
                "SELECT collection_point_id, measurement_type, measurement_unit FROM specifications ORDER BY id"
                )
            )
        ) == [
        (1, "CHLORINE", "MG_L"),
        (1, "PH", None),
        (1, "TEMPERATURE", "CELSIUS"),
    ]

def test_orm_loads_collection_point_with_specifications(session):
    session.execute(
        text(
            "INSERT INTO collection_points (id, name, location) VALUES (1, 'Collection Point 1', 'Location 1')"
            )
        )
    session.execute(
        text(
        "INSERT INTO specifications "
        "(collection_point_id, measurement_type, min_value, max_value, measurement_unit) VALUES "
        "(1, 'CHLORINE', 0.2, 0.5, 'MG_L'), "
        "(1, 'PH', 6.5, 7.5, NULL), "
        "(1, 'TEMPERATURE', 0.0, 100.0, 'CELSIUS')"
        )
    )

    collection_point = session.query(CollectionPoint).one()

    assert collection_point.id_ == 1
    assert collection_point.name == "Collection Point 1"
    assert [s.measurement_type for s in collection_point.specifications] == [
        MeasurementType.CHLORINE, MeasurementType.PH, MeasurementType.TEMPERATURE,
    ]
    assert collection_point.specifications[1].measurement_unit is None


def test_orm_saves_non_conformity_linked_to_measurement(session):
    collection_point = CollectionPoint(1, "Collection Point 1", "Location 1", specifications=make_specifications())
    collection_point.add_measurement(
        Measurement(10, datetime(2026, 9, 28, 8, 0), 0.1, MeasurementUnit.MG_L, MeasurementType.CHLORINE)
    )

    session.add(collection_point)
    session.commit()

    assert list(session.execute(text(
        "SELECT number, measurement_id FROM non_conformities"
    ))) == [(1, 10)]