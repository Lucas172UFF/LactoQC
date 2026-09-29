from datetime import datetime

from LactoQC.domain.models import (
    CollectionPoint,
    Measurement,
    MeasurementType,
    MeasurementUnit,
    Specification,
)


def create_collection_point(
    repository,
    collection_point_id: int,
    name: str,
    location: str,
    specifications: list[dict],
) -> CollectionPoint:
    point = CollectionPoint(
        id_=collection_point_id,
        name=name,
        location=location,
        specifications=[
            Specification(
                measurement_type=MeasurementType[item["measurement_type"]],
                min_value=float(item["min_value"]),
                max_value=float(item["max_value"]),
                measurement_unit=(
                    MeasurementUnit[item["measurement_unit"]]
                    if item.get("measurement_unit") is not None
                    else None
                ),
            )
            for item in specifications
        ],
    )

    repository.add(point)
    return point


def list_collection_points(repository) -> list[CollectionPoint]:
    return repository.list()


def get_collection_point(repository, collection_point_id: int) -> CollectionPoint:
    return repository.get(collection_point_id)


def register_measurement(
    repository,
    collection_point_id: int,
    measurement_id: int,
    measurement_date: str,
    value: float,
    measurement_type: str,
    measurement_unit: str | None,
) -> CollectionPoint:
    point = repository.get(collection_point_id)

    point.add_measurement(
        Measurement(
            id_=measurement_id,
            measurement_date=datetime.fromisoformat(
                measurement_date.replace("Z", "+00:00")
            ),
            value=float(value),
            measurement_type=MeasurementType[measurement_type],
            measurement_unit=(
                MeasurementUnit[measurement_unit]
                if measurement_unit is not None
                else None
            ),
        )
    )

    repository.add(point)
    return point


def list_measurements(repository, collection_point_id: int) -> list[Measurement]:
    return repository.get(collection_point_id).measurements


def list_non_conformities(repository, collection_point_id: int):
    return repository.get(collection_point_id).non_conformities
