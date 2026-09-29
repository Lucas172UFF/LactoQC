"""Casos de uso do Ponto de Coleta. Recebem repositório e sessão; o commit é feito aqui."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from LactoQC.adapters.repository import AbstractCollectionPointRepository
from LactoQC.domain.model import (
    EXPECTED_UNITS,
    CollectionPoint,
    Measurement,
    MeasurementType,
    NonConformity,
    Specification,
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
