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




class MilkType(Enum):
    COW = "Cow"
    GOAT = "Goat"


class RawMaterialReceiptStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class TestResult(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class BatchStatus(Enum):
    OPEN = "Open"
    NON_CONFORMING = "Non Conforming"
    RELEASED = "Released"


class RawMaterialReceipt:
    """Simplified reference to the raw material receipt batch."""

    def __init__(self, id_: int, status: RawMaterialReceiptStatus):
        self.id_ = id_
        self.status = status

    @property
    def approved(self) -> bool:
        return self.status == RawMaterialReceiptStatus.APPROVED


class WeightSample:
    def __init__(self, id_: int, date_time: datetime, weight_kg: float):
        self.id_ = id_
        self.date_time = date_time
        self.weight_kg = weight_kg

        self._verify_weight()

    def _verify_weight(self):
        if self.weight_kg <= 0:
            raise ValueError("Sample weight must be greater than zero.")


class Lecithinization:
    def __init__(self, performed: bool, date_time: datetime | None = None, responsible: str | None = None):
        self.performed = performed
        self.date_time = date_time
        self.responsible = responsible


class BatchNonConformity:
    def __init__(self, id_: int, batch_id: int, description: str):
        self.id_ = id_
        self.batch_id = batch_id
        self.description = description


class ProductionBatch:

    WEIGHT_TOLERANCE = 0.05  # 5%

    def __init__(
        self, id_: int, batch_number: str, production_date: datetime,
        milk_type: MilkType, raw_material_receipt: RawMaterialReceipt,
        expected_weight: float,
        weight_samples: list[WeightSample] | None = None,
        lecithinization: Lecithinization | None = None,
        wettability_result: TestResult = TestResult.PENDING,
        status: BatchStatus = BatchStatus.OPEN,
        non_conformities: list[BatchNonConformity] | None = None,
        ):
        self.id_ = id_
        self.batch_number = batch_number
        self.production_date = production_date
        self.milk_type = milk_type
        self.raw_material_receipt = raw_material_receipt
        self.expected_weight = expected_weight
        self.weight_samples = weight_samples if weight_samples is not None else []
        self.lecithinization = lecithinization
        self.wettability_result = wettability_result
        self.status = status
        self.non_conformities = non_conformities if non_conformities is not None else []

        self._verify_raw_material_approved()
        self._verify_expected_weight()

    def _verify_raw_material_approved(self):
        if not self.raw_material_receipt.approved:
            raise ValueError(
                f"Raw material receipt {self.raw_material_receipt.id_} is not approved "
                f"(status: {self.raw_material_receipt.status.value})."
            )

    def _verify_expected_weight(self):
        if self.expected_weight <= 0:
            raise ValueError("Expected weight must be greater than zero.")

    def _register_non_conformity(self, description: str):
        non_conformity = BatchNonConformity(
            id_=len(self.non_conformities) + 1,
            batch_id=self.id_,
            description=description,
        )
        self.non_conformities.append(non_conformity)

    def check_sample_weight(self, weight_sample: WeightSample):
        lower_bound = self.expected_weight * (1 - self.WEIGHT_TOLERANCE)
        upper_bound = self.expected_weight * (1 + self.WEIGHT_TOLERANCE)
        if not (lower_bound <= weight_sample.weight_kg <= upper_bound):
            description = (
                f"Sample {weight_sample.id_} with weight {weight_sample.weight_kg}kg is out of the "
                f"{self.WEIGHT_TOLERANCE * 100:.0f}% tolerance range "
                f"({lower_bound:.2f}kg - {upper_bound:.2f}kg)."
            )
            self._register_non_conformity(description)

    def add_weight_sample(self, weight_sample: WeightSample):
        self.weight_samples.append(weight_sample)
        self.check_sample_weight(weight_sample)

    def register_lecithinization(self, lecithinization: Lecithinization):
        self.lecithinization = lecithinization

    def register_wettability_result(self, result: TestResult):
        self.wettability_result = result
        if result == TestResult.REJECTED:
            self._register_non_conformity("Wettability test rejected.")

    def check_mandatory_lecithinization(self):
        if self.milk_type == MilkType.GOAT and (self.lecithinization is None or not self.lecithinization.performed):
            self._register_non_conformity("Goat milk requires lecithinization, but it was not performed.")

    def check_milk_type_conflict(self, other_batches_of_the_day: list["ProductionBatch"]):
        for other_batch in other_batches_of_the_day:
            same_date = other_batch.production_date.date() == self.production_date.date()
            if other_batch.id_ != self.id_ and same_date and other_batch.milk_type != self.milk_type:
                self._register_non_conformity(
                    f"Milk type conflict: batch {other_batch.batch_number} ({other_batch.milk_type.value}) "
                    f"produced on the same date ({self.production_date.date()})."
                )

    def release(self, other_batches_of_the_day: list["ProductionBatch"] | None = None):
        other_batches_of_the_day = other_batches_of_the_day if other_batches_of_the_day is not None else []

        self.check_mandatory_lecithinization()
        self.check_milk_type_conflict(other_batches_of_the_day)

        if self.wettability_result != TestResult.APPROVED:
            self._register_non_conformity("Wettability test not approved.")

        self.status = BatchStatus.NON_CONFORMING if self.non_conformities else BatchStatus.RELEASED