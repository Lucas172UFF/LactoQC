from datetime import datetime, date
import pytest
from LactoQC.service_layer import services
from LactoQC.domain.model import (
    MeasurementType,
    MeasurementUnit
)

SPECS = [
    {"measurement_type": "CHLORINE", "min_value": 0.2, "max_value": 0.5},
    {"measurement_type": "PH", "min_value": 6.5, "max_value": 7.5},
    {"measurement_type": "TEMPERATURE", "min_value": 0.0, "max_value": 100.0},
]


def test_create_collection_point_saves_and_commits(fake_repo, fake_session):
    collection_point = services.create_collection_point(
        fake_repo, fake_session, "Sala 1", "Bloco A", SPECS
    )

    assert fake_repo.get(collection_point.id_) is collection_point
    assert fake_session.committed

def test_create_collection_point_without_all_specifications_does_not_commit(fake_repo, fake_session):
    with pytest.raises(ValueError, match="missing"):
        services.create_collection_point(
            fake_repo, fake_session, "Sala 1", "Bloco A", SPECS[:2] 
        )
    assert fake_repo.list() == []
    assert not fake_session.committed


def test_register_measurement_within_specification_has_no_non_conformity(fake_repo, fake_session):
    collection_point = services.create_collection_point(
        fake_repo, fake_session, "Sala 1", "Bloco A", SPECS
    )
    
    fake_session.committed = False
    
    measurement, new_non_conformities = services.register_measurement(
        fake_repo, fake_session, collection_point.id_, "PH", 7.0, datetime(2026, 9, 29, 8, 0)
    )

    assert new_non_conformities == []
    assert collection_point.non_conformities == []
    assert len(collection_point.measurements) == 1
    assert measurement in collection_point.measurements
    assert fake_session.committed

def test_register_measurement_outside_specification_creates_non_conformity(fake_repo, fake_session):
    collection_point = services.create_collection_point(
        fake_repo, fake_session, "Sala 1", "Bloco A", SPECS
    )

    fake_session.committed = False

    measurement, new_non_conformities = services.register_measurement(
        fake_repo, fake_session, collection_point.id_, "PH", 8.0, datetime(2026, 9, 29, 8, 0)
    )
    
    assert len(new_non_conformities) == 1
    assert new_non_conformities[0].measurement is measurement
    assert collection_point.non_conformities == new_non_conformities
    assert fake_session.committed

def test_register_measurement_accepts_measurement_type_label(fake_repo, fake_session):
    colection_point = services.create_collection_point(
        fake_repo, fake_session, "Sala 1 ", "Bolco A", SPECS
    )

    measurement, _ = services.register_measurement(
        fake_repo, fake_session, colection_point.id_, "Cloro", 0.3, datetime(2026, 9, 29, 8, 9)
    )

    assert measurement.measurement_type == MeasurementType.CHLORINE
    assert measurement.measurement_unit == MeasurementUnit.MG_L

def test_register_measurement_for_unknown_collection_point_raises_lookup_error(fake_repo, fake_session):
    with pytest.raises(LookupError, match="999"):
        services.register_measurement(
            fake_repo, fake_session, 999, "PH", 7.0, datetime(2026, 9, 29, 8, 0)
        )

    assert not fake_session.committed

def test_get_collection_point_unknown_id_raises_lookup_error(fake_repo):
    with pytest.raises(LookupError, match="999"):
        services.get_collection_point(fake_repo, 999)

def test_list_non_conformities_filters_by_collection_point(fake_repo, fake_session):
    point_a = services.create_collection_point(fake_repo, fake_session, "Sala A", "Bloco B", SPECS)
    point_b = services.create_collection_point(fake_repo, fake_session, "Sala B", "Bloco B", SPECS)

    services.register_measurement(fake_repo, fake_session, point_a.id_, "PH", 8.0, datetime(2026, 9, 29, 8, 9))
    services.register_measurement(fake_repo, fake_session, point_b.id_, "PH", 8.0, datetime(2026, 9, 29, 8, 9))

    result = services.list_non_conformities(fake_repo, collection_point_id=point_a.id_)

    assert result == point_a.non_conformities

def test_list_non_conformities_filters_by_period(fake_repo, fake_session):
    collection_point = services.create_collection_point(fake_repo, fake_session, "Sala A", "Bloco A", SPECS)

    services.register_measurement(fake_repo, fake_session, collection_point.id_, "PH", 8.0, datetime(2026, 9, 29, 8, 0))
    _, expected = services.register_measurement(fake_repo, fake_session, collection_point.id_, "PH", 8.0, datetime(2026, 9, 30, 8, 0))

    result = services.list_non_conformities(fake_repo, start=datetime(2026, 9, 30), end=datetime(2026, 10, 30 ))

    assert result == expected

def register_all_measurement_types(fake_repo, fake_session, collection_point_id, day):
    
    measurement_date = datetime(day.year, day.month, day.day, 8, 0)
    services.register_measurement(fake_repo, fake_session, collection_point_id, "CHLORINE", 0.3, measurement_date)
    services.register_measurement(fake_repo, fake_session, collection_point_id, "PH", 7.0, measurement_date)
    services.register_measurement(fake_repo, fake_session, collection_point_id, "TEMPERATURE", 25.0, measurement_date)

def test_close_daily_record_closes_day_and_commits(fake_repo, fake_session):
    
    collection_point = services.create_collection_point(fake_repo, fake_session, "Sala 1", "Bloco A", SPECS)
    day = date(2026, 9, 29)
    register_all_measurement_types(fake_repo, fake_session, collection_point.id_, day)
    fake_session.committed = False

    closure = services.close_daily_record(fake_repo, fake_session, collection_point.id_, day)

    assert collection_point.is_day_closed(day)
    assert closure.day == day
    assert fake_session.committed

def test_close_daily_record_incomplete_day_does_not_commit(fake_repo, fake_session):
    
    collection_point = services.create_collection_point(fake_repo, fake_session, "Sala 1", "Bloco A", SPECS)
    day = date(2026, 9, 29)
    services.register_measurement(fake_repo, fake_session, collection_point.id_, "CHLORINE", 0.3, datetime(2026, 9, 29, 8, 0))
    services.register_measurement(fake_repo, fake_session, collection_point.id_, "PH", 7.0, datetime(2026, 9, 29, 8, 0))
    fake_session.committed = False

    with pytest.raises(ValueError, match="Temperatura"):
        services.close_daily_record(fake_repo, fake_session, collection_point.id_, day)

    assert not collection_point.is_day_closed(day)
    assert not fake_session.committed


def test_close_daily_record_unknown_collection_point_raises_lookup_error(fake_repo, fake_session):
    
    with pytest.raises(LookupError, match="999"):
        services.close_daily_record(fake_repo, fake_session, 999, date(2026, 9, 29))

    assert not fake_session.committed


def test_register_measurement_on_closed_day_raises_and_does_not_commit(fake_repo, fake_session):
    collection_point = services.create_collection_point(fake_repo, fake_session, "Sala 1", "Bloco A", SPECS)
    day = date(2026, 9, 29)
    register_all_measurement_types(fake_repo, fake_session, collection_point.id_, day)
    services.close_daily_record(fake_repo, fake_session, collection_point.id_, day)
    fake_session.committed = False

    with pytest.raises(ValueError, match="already closed"):
        services.register_measurement(fake_repo, fake_session, collection_point.id_, "PH", 7.0, datetime(2026, 9, 29, 9, 0))

    assert len(collection_point.measurements) == 3
    assert not fake_session.committed