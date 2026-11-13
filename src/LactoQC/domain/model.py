from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

class MeasurementType(Enum):
    CHLORINE = "Cloro"
    PH = "pH"
    TEMPERATURE = "Temperatura"


class MeasurementUnit(Enum):
    MG_L = "mg/L"
    CELSIUS = "°C"

EXPECTED_UNITS = {
    MeasurementType.CHLORINE: MeasurementUnit.MG_L,
    MeasurementType.PH: None,
    MeasurementType.TEMPERATURE: MeasurementUnit.CELSIUS,
}

# Quais tipos de medição são obrigatórios para todo CollectionPoint (fecham o dia).
# Um tipo novo entra em MeasurementType + EXPECTED_UNITS sem mexer aqui;
# só entra aqui se a regra de negócio for "este tipo também é obrigatório".
MANDATORY_MEASUREMENT_TYPES = frozenset(
    {MeasurementType.CHLORINE, MeasurementType.PH, MeasurementType.TEMPERATURE}
)

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


class DailyClosure:
    def __init__(self, day:date):
        self.day = day


class NonConformityObserver(ABC):
    """Observer: alguém fora do agregado que precisa saber quando uma não
    conformidade é registrada (auditoria, alerta ao supervisor etc.),
    sem que o CollectionPoint conheça esse "alguém"."""

    @abstractmethod
    def notify(self, collection_point: "CollectionPoint", non_conformity: "NonConformity") -> None:
        ...


class CollectionPoint:
    def __init__(
        self, id_:int, name:str, location:str,
        measurements:list[Measurement] | None = None, specifications:list[Specification] | None = None, 
        non_conformities:list[NonConformity] | None = None, daily_closures:list[DailyClosure] | None=None, 
        ):
        self.id_ = id_
        self.name = name
        self.location = location
        self.measurements = measurements if measurements is not None else []
        self.specifications = specifications if specifications is not None else []
        self.non_conformities = non_conformities if non_conformities is not None else []
        self.daily_closures = daily_closures if daily_closures is not None else []

        self._validate_specifications()

    def _validate_specifications(self):
        for measurement_type in MANDATORY_MEASUREMENT_TYPES:
            count = sum(1 for spec in self.specifications if spec.measurement_type == measurement_type)
            if count == 0:
                raise ValueError(f"Specification for measurement type {measurement_type.value} is missing.")
            if count > 1:
                raise ValueError(f"Specification for measurement type {measurement_type.value} is duplicated.")

    def is_day_closed(self, day: date) -> bool:
        return any(closure.day == day for closure in self.daily_closures)

    def _verify_day_is_open(self, day: date):
        if self.is_day_closed(day):
            raise ValueError(f"Day {day} is already closed.")
    
    def _verify_all_measurement_types_on(self, day: date):
        measured_types = {
            measurement.measurement_type for measurement in self.measurements if measurement.measurement_date.date() == day
        }
        for measurement_type in MANDATORY_MEASUREMENT_TYPES:
            if measurement_type not in measured_types:
                raise ValueError(
                    f"Cannot close day {day}: missing {measurement_type.value} measurement."
                )

    def register_observer(self, observer: NonConformityObserver) -> None:
        # getattr: instâncias recarregadas do banco pelo SQLAlchemy nunca rodam
        # __init__ (R-02 em docs/arquitetura.md), então _observers pode não existir ainda.
        self._observers = getattr(self, "_observers", [])
        self._observers.append(observer)

    def _notify_observers(self, non_conformity: "NonConformity") -> None:
        for observer in getattr(self, "_observers", []):
            observer.notify(self, non_conformity)

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
                    self._notify_observers(non_conformity)

    def close_day(self, day:date):
        self._verify_day_is_open(day)
        self._verify_all_measurement_types_on(day)
        self.daily_closures.append(DailyClosure(day))

    def add_measurement(self, measurement: Measurement):
        self._verify_day_is_open(measurement.measurement_date.date())
        self.measurements.append(measurement)
        self.check_for_non_conformity(measurement)




from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Optional


class MilkType(Enum):
    COW = "Cow"
    GOAT = "Goat"


class RawMaterialReceiptStatus(Enum):
    PENDING = "Pending"
    QUARANTINED = "Quarantined"
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


class RawMaterialReceiptState(ABC):
    """State of a receipt and the transitions allowed from that state."""

    @property
    @abstractmethod
    def status(self) -> RawMaterialReceiptStatus:
        raise NotImplementedError

    def approve(self) -> RawMaterialReceiptStatus:
        raise ValueError(f"A receipt in state {self.status.value} cannot be approved.")

    def reject(self) -> RawMaterialReceiptStatus:
        raise ValueError(f"A receipt in state {self.status.value} cannot be rejected.")

    def quarantine(self) -> RawMaterialReceiptStatus:
        raise ValueError(f"A receipt in state {self.status.value} cannot be quarantined.")


class PendingReceiptState(RawMaterialReceiptState):
    @property
    def status(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.PENDING

    def approve(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.APPROVED

    def reject(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.REJECTED

    def quarantine(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.QUARANTINED


class QuarantinedReceiptState(RawMaterialReceiptState):
    @property
    def status(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.QUARANTINED

    def approve(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.APPROVED

    def reject(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.REJECTED


class ApprovedReceiptState(RawMaterialReceiptState):
    @property
    def status(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.APPROVED


class RejectedReceiptState(RawMaterialReceiptState):
    @property
    def status(self) -> RawMaterialReceiptStatus:
        return RawMaterialReceiptStatus.REJECTED


_RECEIPT_STATES: dict[RawMaterialReceiptStatus, RawMaterialReceiptState] = {
    RawMaterialReceiptStatus.PENDING: PendingReceiptState(),
    RawMaterialReceiptStatus.QUARANTINED: QuarantinedReceiptState(),
    RawMaterialReceiptStatus.APPROVED: ApprovedReceiptState(),
    RawMaterialReceiptStatus.REJECTED: RejectedReceiptState(),
}


class RawMaterialReceipt:
    def __init__(self, id_: int, status: RawMaterialReceiptStatus):
        self.id_ = id_
        # Keep the enum as the persisted representation; the State object is
        # resolved from it so SQLAlchemy can reconstruct receipts without
        # invoking __init__.
        self._status = status

    @property
    def status(self) -> RawMaterialReceiptStatus:
        return self._status

    @property
    def state(self) -> RawMaterialReceiptState:
        return _RECEIPT_STATES[self._status]

    @property
    def approved(self) -> bool:
        return self.state.status == RawMaterialReceiptStatus.APPROVED

    def approve(self) -> None:
        self._status = self.state.approve()

    def reject(self) -> None:
        self._status = self.state.reject()

    def quarantine(self) -> None:
        self._status = self.state.quarantine()


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
    def __init__(self, performed: bool, date_time: Optional[datetime] = None, responsible: Optional[str] = None):
        self.performed = performed
        self.date_time = date_time
        self.responsible = responsible


class BatchNonConformity:
    def __init__(self, id_: int, batch_id: int, description: str):
        self.id_ = id_
        self.batch_id = batch_id
        self.description = description




class SampleWeightRule(ABC):
    @abstractmethod
    def check(self, batch: "ProductionBatch", sample: WeightSample) -> Optional[str]:
        raise NotImplementedError


class WeightToleranceRule(SampleWeightRule):
    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance

    def check(self, batch: "ProductionBatch", sample: WeightSample) -> Optional[str]:
        lower_bound = batch.expected_weight * (1 - self.tolerance)
        upper_bound = batch.expected_weight * (1 + self.tolerance)
        if lower_bound <= sample.weight_kg <= upper_bound:
            return None
        return (
            f"Sample {sample.id_} with weight {sample.weight_kg}kg is out of the "
            f"{self.tolerance * 100:.0f}% tolerance range "
            f"({lower_bound:.2f}kg - {upper_bound:.2f}kg)."
        )


class LecithinizationRule(ABC):
    @abstractmethod
    def check(self, batch: "ProductionBatch") -> Optional[str]:
        raise NotImplementedError


class MandatoryLecithinizationForGoatMilkRule(LecithinizationRule):
    def check(self, batch: "ProductionBatch") -> Optional[str]:
        requires_lecithinization = batch.milk_type == MilkType.GOAT
        was_performed = batch.lecithinization is not None and batch.lecithinization.performed
        if requires_lecithinization and not was_performed:
            return "Goat milk requires lecithinization, but it was not performed."
        return None


class MilkTypeConflictRule(ABC):
    @abstractmethod
    def check(self, batch: "ProductionBatch", other_batches_of_the_day: List["ProductionBatch"]) -> List[str]:
        raise NotImplementedError


class SameDayDifferentMilkTypeRule(MilkTypeConflictRule):
    def check(self, batch: "ProductionBatch", other_batches_of_the_day: List["ProductionBatch"]) -> List[str]:
        violations = []
        for other_batch in other_batches_of_the_day:
            same_date = other_batch.production_date.date() == batch.production_date.date()
            different_milk = other_batch.milk_type != batch.milk_type
            if other_batch.id_ != batch.id_ and same_date and different_milk:
                violations.append(
                    f"Milk type conflict: batch {other_batch.batch_number} "
                    f"({other_batch.milk_type.value}) produced on the same date "
                    f"({batch.production_date.date()})."
                )
        return violations


class WettabilityRule(ABC):
    @abstractmethod
    def check(self, batch: "ProductionBatch") -> Optional[str]:
        raise NotImplementedError


class WettabilityMustBeApprovedRule(WettabilityRule):
    def check(self, batch: "ProductionBatch") -> Optional[str]:
        if batch.wettability_result != TestResult.APPROVED:
            return "Wettability test not approved."
        return None


class ProductionBatch:

    _default_weight_rule = WeightToleranceRule()
    _default_lecithinization_rule = MandatoryLecithinizationForGoatMilkRule()
    _default_milk_type_conflict_rule = SameDayDifferentMilkTypeRule()
    _default_wettability_rule = WettabilityMustBeApprovedRule()

    def __init__(
        self, id_: int, batch_number: str, production_date: datetime,
        milk_type: MilkType, raw_material_receipt: RawMaterialReceipt,
        expected_weight: float,
        weight_samples: Optional[List[WeightSample]] = None,
        lecithinization: Optional[Lecithinization] = None,
        wettability_result: TestResult = TestResult.PENDING,
        status: BatchStatus = BatchStatus.OPEN,
        non_conformities: Optional[List[BatchNonConformity]] = None,
        weight_rule: Optional[SampleWeightRule] = None,
        lecithinization_rule: Optional[LecithinizationRule] = None,
        milk_type_conflict_rule: Optional[MilkTypeConflictRule] = None,
        wettability_rule: Optional[WettabilityRule] = None,
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

        if weight_rule is not None:
            self._weight_rule = weight_rule
        if lecithinization_rule is not None:
            self._lecithinization_rule = lecithinization_rule
        if milk_type_conflict_rule is not None:
            self._milk_type_conflict_rule = milk_type_conflict_rule
        if wettability_rule is not None:
            self._wettability_rule = wettability_rule

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

    @property
    def weight_rule(self) -> SampleWeightRule:
        return getattr(self, "_weight_rule", self._default_weight_rule)

    @property
    def lecithinization_rule(self) -> LecithinizationRule:
        return getattr(self, "_lecithinization_rule", self._default_lecithinization_rule)

    @property
    def milk_type_conflict_rule(self) -> MilkTypeConflictRule:
        return getattr(self, "_milk_type_conflict_rule", self._default_milk_type_conflict_rule)

    @property
    def wettability_rule(self) -> WettabilityRule:
        return getattr(self, "_wettability_rule", self._default_wettability_rule)

    def _register_non_conformity(self, description: str):
        self.non_conformities.append(
            BatchNonConformity(
                id_=len(self.non_conformities) + 1,
                batch_id=self.id_,
                description=description,
            )
        )

    def add_weight_sample(self, weight_sample: WeightSample):
        self.weight_samples.append(weight_sample)
        violation = self.weight_rule.check(self, weight_sample)
        if violation:
            self._register_non_conformity(violation)

    def register_lecithinization(self, lecithinization: Lecithinization):
        self.lecithinization = lecithinization

    def register_wettability_result(self, result: TestResult):
        self.wettability_result = result
        if result == TestResult.REJECTED:
            self._register_non_conformity("Wettability test rejected.")

    def check_mandatory_lecithinization(self):
        violation = self.lecithinization_rule.check(self)
        if violation:
            self._register_non_conformity(violation)

    def check_milk_type_conflict(self, other_batches_of_the_day: List["ProductionBatch"]):
        for violation in self.milk_type_conflict_rule.check(self, other_batches_of_the_day):
            self._register_non_conformity(violation)

    def release(self, other_batches_of_the_day: Optional[List["ProductionBatch"]] = None):
        other_batches_of_the_day = other_batches_of_the_day if other_batches_of_the_day is not None else []

        self.check_mandatory_lecithinization()
        self.check_milk_type_conflict(other_batches_of_the_day)

        violation = self.wettability_rule.check(self)
        if violation:
            self._register_non_conformity(violation)

        self.status = BatchStatus.NON_CONFORMING if self.non_conformities else BatchStatus.RELEASED
