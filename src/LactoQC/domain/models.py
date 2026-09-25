from datetime import datetime
from enum import Enum


class MeasurementType(Enum):
    CHLORINE = "Cloro"
    PH = "pH"
    TEMPERATURE = "Temperatura"


class MeasurementUnit(Enum):
    MG_L = "mg/L"
    CELSIUS = "°C"

EXPECTED_UNITS = {
    MeasurementType.CHLORINE: MeasurementUnit.MG_L,
    MeasurementType.PH: None,  # pH is unitless
    MeasurementType.TEMPERATURE: MeasurementUnit.CELSIUS,
}

class Measurement:
    def __init__(
        self, id_:int, measurement_date:datetime , value:float, 
        measurement_unit:MeasurementUnit | None, measurement_type:MeasurementType
        ):
        self.id_ = id_
        self.measurement_date = measurement_date
        self.value = value
        self.measurement_unit = measurement_unit
        self.measurement_type = measurement_type

        self._verify_unit()

    def _verify_unit(self):
        expected_unit = EXPECTED_UNITS.get(self.measurement_type)
        if self.measurement_unit != expected_unit:
            raise ValueError(f"Measurement unit {self.measurement_unit} does not match expected unit {expected_unit} for measurement type {self.measurement_type.value}.")


class Specification:
    def __init__(
        self, measurement_type:MeasurementType, min_value:float, 
        max_value:float, measurement_unit:MeasurementUnit | None
        ):
        self.measurement_type = measurement_type
        self.min_value = min_value
        self.max_value = max_value
        self.measurement_unit = measurement_unit

        self._verify_min_max_values()
        self._verify_unit()
    
    def _verify_min_max_values(self):
        if self.min_value > self.max_value:
            raise ValueError("Minimum value cannot be greater than maximum value.")

    def _verify_unit(self):
        expected_unit = EXPECTED_UNITS.get(self.measurement_type)
        if self.measurement_unit != expected_unit:
            raise ValueError(f"Specification unit {self.measurement_unit} does not match expected unit {expected_unit} for measurement type {self.measurement_type.value}.")

    def is_value_within_specification(self, value:float) -> bool:
        return self.min_value <= value <= self.max_value


class NonConformity:
    def __init__(self, id_:int, measurement:Measurement, specification:Specification, description:str):
        self.id_ = id_
        self.measurement = measurement
        self.specification = specification
        self.description = description


class CollectionPoint:
    def __init__(
        self, id_:int, name:str, location:str,
        measurements:list[Measurement] | None = None, specifications:list[Specification] | None = None, 
        non_conformities:list[NonConformity] | None = None
        ):
        self.id_ = id_
        self.name = name
        self.location = location
        self.measurements = measurements if measurements is not None else []
        self.specifications = specifications if specifications is not None else []
        self.non_conformities = non_conformities if non_conformities is not None else []

        self._validate_specifications()

    def _validate_specifications(self):
        for  measurement_type in MeasurementType:
            count = sum(1 for spec in self.specifications if spec.measurement_type == measurement_type)
            if count == 0:
                raise ValueError(f"Specification for measurement type {measurement_type.value} is missing.")
            if count > 1:
                raise ValueError(f"Specification for measurement type {measurement_type.value} is duplicated.")
    
    def check_for_non_conformity(self, measurement:Measurement):
        for specification in self.specifications:
            if specification.measurement_type == measurement.measurement_type:
                if not specification.is_value_within_specification(measurement.value):
                    description = f"""Measurement {measurement.value} {measurement.measurement_unit.value if measurement.measurement_unit else ''} 
                    is out of specification range ({specification.min_value} - {specification.max_value} 
                    {specification.measurement_unit.value if specification.measurement_unit else ''})"""
                    non_conformity = NonConformity(
                        id_=len(self.non_conformities) + 1,
                        measurement=measurement,
                        specification=specification,
                        description=description
                    )
                    self.non_conformities.append(non_conformity)

    def add_measurement(self, measurement:Measurement):
        self.measurements.append(measurement)
        self.check_for_non_conformity(measurement)