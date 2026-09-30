"""Casos de uso do Ponto de Coleta. Recebem repositório e sessão; o commit é feito aqui."""
from __future__ import annotations

from datetime import datetime, date
from typing import Any

from sqlalchemy.orm import Session

from LactoQC.adapters.repository import AbstractCollectionPointRepository , AbstractProductionBatchRepository
from LactoQC.domain.model import (
    EXPECTED_UNITS,
    CollectionPoint,
    Measurement,
    MeasurementType,
    NonConformity,
    Specification,
    DailyClosure,
    ProductionBatch,
    WeightSample,
    Lecithinization,
    BatchNonConformity,
    MilkType,
    RawMaterialReceipt,
    TestResult,
)

def parse_measurement_type(raw: Any) -> MeasurementType:
    """Aceita o nome do enum ('CHLORINE') ou o rótulo ('Cloro'), sem diferenciar maiúsculas."""
    if isinstance(raw, str):
        text = raw.strip()
        if text.upper() in MeasurementType.__members__:
            return MeasurementType[text.upper()]
        for measurement_type in MeasurementType:
            if measurement_type.value.lower() == text.lower():
                return measurement_type
    valid = ", ".join(MeasurementType.__members__)
    raise ValueError(f"Invalid measurement type {raw!r}. Valid types: {valid}.")


def _to_float(raw: Any, field: str) -> float:
    if isinstance(raw, bool):
        raise ValueError(f"'{field}' must be a number.")
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' must be a number.")


def create_collection_point(
    repo: AbstractCollectionPointRepository, session: Session,
    name: str, location: str, specifications: list[dict],
) -> CollectionPoint:
    """Cria o ponto com as 3 especificações obrigatórias (o domínio valida)."""
    specs = []
    for spec in specifications:
        measurement_type = parse_measurement_type(spec.get("measurement_type"))
        specs.append(
            Specification(
                measurement_type=measurement_type,
                min_value=_to_float(spec.get("min_value"), "min_value"),
                max_value=_to_float(spec.get("max_value"), "max_value"),
                measurement_unit=EXPECTED_UNITS[measurement_type],
            )
        )
    collection_point = CollectionPoint(id_=None, name=name, location=location, specifications=specs)
    repo.add(collection_point)
    session.commit()
    return collection_point


def get_collection_point(repo: AbstractCollectionPointRepository, collection_point_id: int) -> CollectionPoint:
    collection_point = repo.get(collection_point_id)
    if collection_point is None:
        raise LookupError(f"Collection point {collection_point_id} not found.")
    return collection_point


def register_measurement(
    repo: AbstractCollectionPointRepository, session: Session, collection_point_id: int,
    measurement_type: Any, value: Any, measurement_date: datetime | None = None,
) -> tuple[Measurement, list[NonConformity]]:
    """Registra a medição; o domínio gera a não conformidade se estiver fora da faixa.

    A unidade é derivada do tipo (EXPECTED_UNITS), então a API não precisa recebê-la.
    """
    collection_point = get_collection_point(repo, collection_point_id)
    parsed_type = parse_measurement_type(measurement_type)
    measurement = Measurement(
        id_=None,
        measurement_date=measurement_date or datetime.now(),
        value=_to_float(value, "value"),
        measurement_unit=EXPECTED_UNITS[parsed_type],
        measurement_type=parsed_type,
    )
    before = len(collection_point.non_conformities)
    collection_point.add_measurement(measurement)
    new_non_conformities = collection_point.non_conformities[before:]
    session.commit()
    return measurement, new_non_conformities


def list_non_conformities(
    repo: AbstractCollectionPointRepository,
    start: datetime | None = None, end: datetime | None = None,
    collection_point_id: int | None = None,) -> list[NonConformity]:
        collection_points = repo.list()
        if collection_point_id is not None:
            collection_points = [cp for cp in collection_points if cp.id_ == collection_point_id]
        return [
            nc
            for cp in collection_points
            for nc in cp.non_conformities
            if (start is None or nc.measurement.measurement_date >= start)
            and (end is None or nc.measurement.measurement_date <= end)
        ]

def close_daily_record(repo: AbstractCollectionPointRepository, session:Session, collection_point_id: int, day: date):
    collection_point = get_collection_point(repo, collection_point_id)
    collection_point.close_day(day)
    session.commit()
    return collection_point.daily_closures[-1]
def parse_milk_type(raw: Any) -> MilkType:
    if isinstance(raw, MilkType):
        return raw

    if isinstance(raw, str):
        text = raw.strip()

        if text.upper() in MilkType.__members__:
            return MilkType[text.upper()]

        for milk_type in MilkType:
            if milk_type.value.lower() == text.lower():
                return milk_type

    valid = ", ".join(MilkType.__members__)
    raise ValueError(
        f"Invalid milk type {raw!r}. Valid types: {valid}."
    )


def parse_test_result(raw: Any) -> TestResult:
    if isinstance(raw, TestResult):
        return raw

    if isinstance(raw, str):
        text = raw.strip()

        if text.upper() in TestResult.__members__:
            return TestResult[text.upper()]

        for result in TestResult:
            if result.value.lower() == text.lower():
                return result

    valid = ", ".join(TestResult.__members__)
    raise ValueError(
        f"Invalid test result {raw!r}. Valid results: {valid}."
    )


def get_production_batch(
    repo: AbstractProductionBatchRepository,
    batch_number: str,
) -> ProductionBatch:
    batch = repo.get(batch_number)

    if batch is None:
        raise LookupError(
            f"Production batch {batch_number!r} not found."
        )

    return batch


def list_production_batches(
    repo: AbstractProductionBatchRepository,
) -> list[ProductionBatch]:
    return repo.list()


def create_production_batch(
    repo: AbstractProductionBatchRepository,
    session: Session,
    batch_number: str,
    production_date: datetime,
    milk_type: Any,
    raw_material_receipt: RawMaterialReceipt,
    expected_weight: Any,
) -> ProductionBatch:

    if repo.get(batch_number) is not None:
        raise ValueError(
            f"Production batch {batch_number!r} already exists."
        )

    parsed_milk_type = parse_milk_type(milk_type)

    expected_weight = _to_float(
        expected_weight,
        "expected_weight",
    )

    existing_batches = repo.list()

    next_id = max(
        (batch.id_ or 0 for batch in existing_batches),
        default=0,
    ) + 1

    batch = ProductionBatch(
        id_=next_id,
        batch_number=batch_number,
        production_date=production_date,
        milk_type=parsed_milk_type,
        raw_material_receipt=raw_material_receipt,
        expected_weight=expected_weight,
    )

    repo.add(batch)
    session.commit()

    return batch


def register_weight_sample(
    repo: AbstractProductionBatchRepository,
    session: Session,
    batch_number: str,
    weight_kg: Any,
    date_time: datetime | None = None,
) -> tuple[WeightSample, list[BatchNonConformity]]:

    batch = get_production_batch(repo, batch_number)

    weight_kg = _to_float(weight_kg, "weight_kg")

    next_id = max(
        (sample.id_ or 0 for sample in batch.weight_samples),
        default=0,
    ) + 1

    sample = WeightSample(
        id_=next_id,
        date_time=date_time or datetime.now(),
        weight_kg=weight_kg,
    )

    before = len(batch.non_conformities)

    batch.add_weight_sample(sample)

    new_non_conformities = batch.non_conformities[before:]

    session.commit()

    return sample, new_non_conformities


def register_lecithinization(
    repo: AbstractProductionBatchRepository,
    session: Session,
    batch_number: str,
    performed: bool,
    date_time: datetime | None = None,
    responsible: str | None = None,
) -> Lecithinization:

    batch = get_production_batch(repo, batch_number)

    if not isinstance(performed, bool):
        raise ValueError("'performed' must be a boolean.")

    lecithinization = Lecithinization(
        performed=performed,
        date_time=date_time or datetime.now(),
        responsible=responsible,
    )

    batch.register_lecithinization(lecithinization)

    session.commit()

    return lecithinization


def register_wettability_result(
    repo: AbstractProductionBatchRepository,
    session: Session,
    batch_number: str,
    result: Any,
) -> tuple[TestResult, list[BatchNonConformity]]:

    batch = get_production_batch(repo, batch_number)

    parsed_result = parse_test_result(result)

    before = len(batch.non_conformities)

    batch.register_wettability_result(parsed_result)

    new_non_conformities = batch.non_conformities[before:]

    session.commit()

    return parsed_result, new_non_conformities


def release_production_batch(
    repo: AbstractProductionBatchRepository,
    session: Session,
    batch_number: str,
) -> tuple[ProductionBatch, list[BatchNonConformity]]:

    batch = get_production_batch(repo, batch_number)

    other_batches = repo.list()

    before = len(batch.non_conformities)

    batch.release(other_batches)

    new_non_conformities = batch.non_conformities[before:]

    session.commit()

    return batch, new_non_conformities
