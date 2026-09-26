import pytest

from LactoQC.domain.models import (
    CollectionPoint,
    MeasurementType,
    MeasurementUnit,
    Measurement,
    Specification,
    NonConformity,
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
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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
            measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
        measurement_type=MeasurementType.PH,
        measurement_unit=None,
        value=7.5
    )
    measurement2 = Measurement(
        id_=9,
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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
        measurement_date="2024-06-01T12:00:00Z",
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