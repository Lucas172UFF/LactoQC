import pytest
from datetime import date, datetime

from LactoQC.domain.model import (
    CollectionPoint,
    MeasurementType,
    MeasurementUnit,
    Measurement,
    Specification,
    NonConformity,
    DailyClosure
)

def make_chlorine_specification():
    return Specification(
        measurement_type=MeasurementType.CHLORINE,
        measurement_unit=MeasurementUnit.MG_L,
        min_value=0.2,
        max_value=0.5
    )

def make_ph_specification():
    return Specification(
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        min_value=6.5,
        max_value=7.5
    )

def make_temperature_specification():
    return Specification(
        measurement_type=MeasurementType.TEMPERATURE,
        measurement_unit=MeasurementUnit.CELSIUS,
        min_value=0.0,
        max_value=100.0
    )

def make_collection_point():
    return CollectionPoint(
        id_=1,
        name="Sala 1",
        location="Bloco A",
        specifications=[
            make_chlorine_specification(),
            make_ph_specification(),
            make_temperature_specification(),
        ],
    )

def make_measurement(id_, measurement_type, day, value):
    units = {
        MeasurementType.CHLORINE: MeasurementUnit.MG_L,
        MeasurementType.PH: None,
        MeasurementType.TEMPERATURE: MeasurementUnit.CELSIUS,
    }
    return Measurement(
        id_=id_,
        measurement_date=datetime(day.year, day.month, day.day, 8, 0),
        value=value,
        measurement_unit=units[measurement_type],
        measurement_type=measurement_type,
    )
    
def test_create_ph_specification():
    spec = make_ph_specification()
    assert spec.measurement_type == MeasurementType.PH
    assert spec.measurement_unit is None
    assert spec.min_value == 6.5
    assert spec.max_value == 7.5

def test_create_chlorine_specification():
    spec = make_chlorine_specification()
    assert spec.measurement_type == MeasurementType.CHLORINE
    assert spec.measurement_unit == MeasurementUnit.MG_L
    assert spec.min_value == 0.2
    assert spec.max_value == 0.5

def test_create_temperature_specification():
    spec = make_temperature_specification()
    assert spec.measurement_type == MeasurementType.TEMPERATURE
    assert spec.measurement_unit == MeasurementUnit.CELSIUS
    assert spec.min_value == 0.0
    assert spec.max_value == 100.0

def test_specification_rejects_min_greater_than_max():
    with pytest.raises(ValueError):
        Specification(
            measurement_type=MeasurementType.PH,
            measurement_unit=None,
            min_value=8.0,
            max_value=7.0
        )

def test_specification_rejects_invalid_unit_for_measurement_type():
    with pytest.raises(ValueError):
        Specification(
            measurement_type=MeasurementType.PH,
            measurement_unit=MeasurementUnit.MG_L,
            min_value=6.5,
            max_value=7.5
        )

def test_specification_is_value_within_specification():
    spec = make_ph_specification()
    assert spec.is_value_within_specification(7.0) == True
    assert spec.is_value_within_specification(6.0) == False
    assert spec.is_value_within_specification(8.0) == False
    assert spec.is_value_within_specification(6.5) == True
    assert spec.is_value_within_specification(7.5) == True

def test_create_ph_measurement():
    measurement = Measurement(
        id_=1,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=7.0
    )
    assert measurement.id_ == 1
    assert measurement.measurement_type == MeasurementType.PH
    assert measurement.measurement_unit == None
    assert measurement.value == 7.0

def test_create_chlorine_measurement():
    measurement = Measurement(
        id_=2,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.CHLORINE,
        measurement_unit=MeasurementUnit.MG_L,
        value=0.3
    )
    assert measurement.id_ == 2
    assert measurement.measurement_type == MeasurementType.CHLORINE
    assert measurement.measurement_unit == MeasurementUnit.MG_L
    assert measurement.value == 0.3

def test_create_temperature_measurement():
    measurement = Measurement(
        id_=3,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.TEMPERATURE,
        measurement_unit=MeasurementUnit.CELSIUS,
        value=25.0
    )
    assert measurement.id_ == 3
    assert measurement.measurement_type == MeasurementType.TEMPERATURE
    assert measurement.measurement_unit == MeasurementUnit.CELSIUS
    assert measurement.value == 25.0

def test_measurement_rejects_invalid_unit_for_measurement_type():
    with pytest.raises(ValueError):
        Measurement(
            id_=4,
            measurement_date=datetime(2024, 6, 1, 12, 0),
            measurement_type=MeasurementType.PH,
            measurement_unit=MeasurementUnit.MG_L,
            value=7.0
        )

def test_create_collection_point_without_specifications_measurements_non_conformities():
    with pytest.raises(ValueError):
        CollectionPoint(
            id_=1,
            name="Sample Point 1",
            location="Location 1",
        )
        

def test_create_collection_point_within_specifications():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=2,
        name="Sample Point A",
        location="Location A",
        specifications=specs,
    )
    assert collection_point.id_ == 2
    assert collection_point.name == "Sample Point A"
    assert collection_point.location == "Location A"
    assert len(collection_point.specifications) == 3

def test_reject_collection_point_missing_specifications():
    with pytest.raises(ValueError):
        CollectionPoint(
            id_=3,
            name="Sample Point B",
            location="Location B",
            specifications=[
                make_ph_specification(),
            ]
        )

def test_reject_collection_point_with_two_specifications_of_same_measurement_type():
    with pytest.raises(ValueError):
        CollectionPoint(
            id_=4,
            name="Sample Point C",
            location="Location C",
            specifications=[
                make_ph_specification(),
                make_ph_specification(),
                make_chlorine_specification(),
                make_temperature_specification()
            ]
        )

def test_add_measurement_to_collection_point():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=5,
        name="Sample Point D",
        location="Location D",
        specifications=specs,
    )
    measurement = Measurement(
        id_=5,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=7.0
    )
    collection_point.add_measurement(measurement)
    assert len(collection_point.measurements) == 1
    assert collection_point.measurements[0] == measurement

def test_add_measurement_outside_min_value_specification_creates_non_conformity():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=6,
        name="Sample Point E",
        location="Location E",
        specifications=specs,
    )
    measurement = Measurement(
        id_=6,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=5.0 
    )
    collection_point.add_measurement(measurement)
    assert len(collection_point.measurements) == 1
    assert len(collection_point.non_conformities) == 1
    non_conformity = collection_point.non_conformities[0]
    assert non_conformity.measurement == measurement
    assert non_conformity.specification == specs[0]

def test_add_measurement_outside_max_value_specification_creates_non_conformity():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=7,
        name="Sample Point F",
        location="Location F",
        specifications=specs,
    )
    measurement = Measurement(
        id_=7,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=8.0 
    )
    collection_point.add_measurement(measurement)
    assert len(collection_point.measurements) == 1
    assert len(collection_point.non_conformities) == 1
    non_conformity = collection_point.non_conformities[0]
    assert non_conformity.measurement == measurement
    assert non_conformity.specification == specs[0]

def test_add_measurement_within_limit_values_specification_does_not_create_non_conformity():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=8,
        name="Sample Point G",
        location="Location G",
        specifications=specs,
    )
    measurement = Measurement(
        id_=8,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=7.5
    )
    measurement2 = Measurement(
        id_=9,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=6.5
    )
    collection_point.add_measurement(measurement)
    collection_point.add_measurement(measurement2)
    assert len(collection_point.measurements) == 2
    assert len(collection_point.non_conformities) == 0

def test_add_chlorine_measurement_outside_specification_creates_non_conformity():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=10,
        name="Sample Point H",
        location="Location H",
        specifications=specs,
    )
    measurement = Measurement(
        id_=10,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.CHLORINE,
        measurement_unit=MeasurementUnit.MG_L,
        value=0.1 
    )
    collection_point.add_measurement(measurement)
    assert len(collection_point.measurements) == 1
    assert len(collection_point.non_conformities) == 1
    non_conformity = collection_point.non_conformities[0]
    assert non_conformity.measurement == measurement
    assert non_conformity.specification == specs[1]

def test_add_temperature_measurement_outside_specification_creates_non_conformity():
    specs = [
        make_ph_specification(),
        make_chlorine_specification(),
        make_temperature_specification()
    ]
    collection_point = CollectionPoint(
        id_=11,
        name="Sample Point I",
        location="Location I",
        specifications=specs,
    )
    measurement = Measurement(
        id_=11,
        measurement_date=datetime(2024, 6, 1, 12, 0),
        measurement_type=MeasurementType.TEMPERATURE,
        measurement_unit=MeasurementUnit.CELSIUS,
        value=150.0 
    )
    collection_point.add_measurement(measurement)
    assert len(collection_point.measurements) == 1
    assert len(collection_point.non_conformities) == 1
    non_conformity = collection_point.non_conformities[0]
    assert non_conformity.measurement == measurement
    assert non_conformity.specification == specs[2]

def test_close_day_with_all_measurement_types():
    collection_point = make_collection_point()
    day = date(2026, 9, 29)
    
    collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day, 0.3))
    collection_point.add_measurement(make_measurement(2, MeasurementType.PH, day, 7.0))
    collection_point.add_measurement(make_measurement(3, MeasurementType.TEMPERATURE, day, 25.0))

    collection_point.close_day(day)

    assert collection_point.is_day_closed(day)
    assert len(collection_point.daily_closures) == 1
    assert isinstance(collection_point.daily_closures[0], DailyClosure)

def test_close_day_missing_measurement_typ_raises():

    with pytest.raises(ValueError):
        collection_point = make_collection_point()
        day = date(2026, 9, 29)
        
        collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day, 0.3))

        collection_point.close_day(day)

def test_closed_day_ignores_measurements_from_other_days():
    
    with pytest.raises(ValueError):
        collection_point = make_collection_point()
        day0 = date(2026, 9, 29)
        day1 = date(2026, 9, 30)

        collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day0, 0.3))
        collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day1, 0.3))

        collection_point.close_day(day0)

def test_close_day_twice_raises():

    collection_point = make_collection_point()
    day = date(2026, 9, 29)
    
    collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day, 0.3))
    collection_point.add_measurement(make_measurement(2, MeasurementType.PH, day, 7.0))
    collection_point.add_measurement(make_measurement(3, MeasurementType.TEMPERATURE, day, 25.0))

    collection_point.close_day(day)

    with pytest.raises(ValueError):
        collection_point.close_day(day)


def test_add_measurement_on_closed_day_raises():

    collection_point = make_collection_point()
    day = date(2026, 9, 29)
    
    collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day, 0.3))
    collection_point.add_measurement(make_measurement(2, MeasurementType.PH, day, 7.0))
    collection_point.add_measurement(make_measurement(3, MeasurementType.TEMPERATURE, day, 25.0))

    collection_point.close_day(day)

    with pytest.raises(ValueError):
        collection_point.add_measurement(make_measurement(4, MeasurementType.PH, day, 7.0))
    
    assert len(collection_point.measurements) == 3

def test_add_measurement_on_other_day_after_closing_is_allowed():
    collection_point = make_collection_point()
    day = date(2026, 9, 29)
    next_day = date(2026, 9, 30)
    collection_point.add_measurement(make_measurement(1, MeasurementType.CHLORINE, day, 0.3))
    collection_point.add_measurement(make_measurement(2, MeasurementType.PH, day, 7.0))
    collection_point.add_measurement(make_measurement(3, MeasurementType.TEMPERATURE, day, 25.0))
    collection_point.close_day(day)

    collection_point.add_measurement(make_measurement(4, MeasurementType.PH, next_day, 7.0))

    assert len(collection_point.measurements) == 4
    assert not collection_point.is_day_closed(next_day)


def test_new_collection_point_has_no_closed_days():
    collection_point = make_collection_point()

    assert collection_point.daily_closures == []
    assert not collection_point.is_day_closed(date(2026, 9, 29))