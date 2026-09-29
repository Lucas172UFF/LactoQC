from abc import ABC, abstractmethod
from datetime import datetime

from LactoQC.adapters.orm import CollectionPointRow
from LactoQC.domain.models import (
    CollectionPoint,
    Measurement,
    MeasurementType,
    MeasurementUnit,
    Specification,
)


class AbstractCollectionPointRepository(ABC):
    @abstractmethod
    def add(self, collection_point: CollectionPoint) -> None:
        pass

    @abstractmethod
    def get(self, collection_point_id: int) -> CollectionPoint:
        pass

    @abstractmethod
    def list(self) -> list[CollectionPoint]:
        pass


class FakeCollectionPointRepository(AbstractCollectionPointRepository):
    def __init__(self):
        self.collection_points: dict[int, CollectionPoint] = {}

    def add(self, collection_point: CollectionPoint) -> None:
        self.collection_points[collection_point.id_] = collection_point

    def get(self, collection_point_id: int) -> CollectionPoint:
        try:
            return self.collection_points[collection_point_id]
        except KeyError as error:
            raise KeyError(
                f"Collection point {collection_point_id} was not found."
            ) from error

    def list(self) -> list[CollectionPoint]:
        return list(self.collection_points.values())


def _serialize_specification(specification: Specification) -> dict:
    return {
        "measurement_type": specification.measurement_type.name,
        "min_value": specification.min_value,
        "max_value": specification.max_value,
        "measurement_unit": (
            specification.measurement_unit.name
            if specification.measurement_unit is not None
            else None
        ),
    }


def _serialize_measurement(measurement: Measurement) -> dict:
    date = measurement.measurement_date
    if isinstance(date, datetime):
        date = date.isoformat()

    return {
        "id": measurement.id_,
        "measurement_date": date,
        "value": measurement.value,
        "measurement_type": measurement.measurement_type.name,
        "measurement_unit": (
            measurement.measurement_unit.name
            if measurement.measurement_unit is not None
            else None
        ),
    }


def _deserialize_collection_point(row: CollectionPointRow) -> CollectionPoint:
    specifications = [
        Specification(
            measurement_type=MeasurementType[item["measurement_type"]],
            min_value=item["min_value"],
            max_value=item["max_value"],
            measurement_unit=(
                MeasurementUnit[item["measurement_unit"]]
                if item["measurement_unit"] is not None
                else None
            ),
        )
        for item in row.payload["specifications"]
    ]

    point = CollectionPoint(
        id_=row.id,
        name=row.name,
        location=row.location,
        specifications=specifications,
    )

    for item in row.payload["measurements"]:
        date = datetime.fromisoformat(
            item["measurement_date"].replace("Z", "+00:00")
        )

        point.add_measurement(
            Measurement(
                id_=item["id"],
                measurement_date=date,
                value=item["value"],
                measurement_type=MeasurementType[item["measurement_type"]],
                measurement_unit=(
                    MeasurementUnit[item["measurement_unit"]]
                    if item["measurement_unit"] is not None
                    else None
                ),
            )
        )

    return point


class SqlAlchemyCollectionPointRepository(AbstractCollectionPointRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def add(self, collection_point: CollectionPoint) -> None:
        payload = {
            "specifications": [
                _serialize_specification(specification)
                for specification in collection_point.specifications
            ],
            "measurements": [
                _serialize_measurement(measurement)
                for measurement in collection_point.measurements
            ],
        }

        with self.session_factory() as session:
            row = session.get(CollectionPointRow, collection_point.id_)

            if row is None:
                session.add(
                    CollectionPointRow(
                        id=collection_point.id_,
                        name=collection_point.name,
                        location=collection_point.location,
                        payload=payload,
                    )
                )
            else:
                row.name = collection_point.name
                row.location = collection_point.location
                row.payload = payload

            session.commit()

    def get(self, collection_point_id: int) -> CollectionPoint:
        with self.session_factory() as session:
            row = session.get(CollectionPointRow, collection_point_id)

            if row is None:
                raise KeyError(
                    f"Collection point {collection_point_id} was not found."
                )

            return _deserialize_collection_point(row)

    def list(self) -> list[CollectionPoint]:
        with self.session_factory() as session:
            rows = (
                session.query(CollectionPointRow)
                .order_by(CollectionPointRow.id)
                .all()
            )

            return [_deserialize_collection_point(row) for row in rows]
