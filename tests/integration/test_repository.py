import pytest
from datetime import datetime, date

from LactoQC.adapters.repository import SqlAlchemyCollectionPointRepository
from LactoQC.domain.model import (
    CollectionPoint,
    Measurement,
    MeasurementType,
    MeasurementUnit,
    Specification,
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
)


def make_specifications():
    return [
        Specification(MeasurementType.CHLORINE, 0.2, 0.5, MeasurementUnit.MG_L),
        Specification(MeasurementType.PH, 6.5, 7.5, None),
        Specification(MeasurementType.TEMPERATURE, 0.0, 100.0, MeasurementUnit.CELSIUS),
    ]


def make_collection_point(id_=1, name="Collection Point 1"):
    return CollectionPoint(id_, name, "Location 1", specifications=make_specifications())


def test_repository_can_retrieve_saved_collection_point(session_factory):
    collection_point = make_collection_point()
    collection_point.add_measurement(
        Measurement(10, datetime(2026, 9, 28, 8, 0), 0.9, MeasurementUnit.MG_L, MeasurementType.CHLORINE)
    )
    with session_factory() as session:
        SqlAlchemyCollectionPointRepository(session).add(collection_point)
        session.commit()

    with session_factory() as session:
        retrieved = SqlAlchemyCollectionPointRepository(session).get(1)

        assert retrieved.name == "Collection Point 1"
        assert len(retrieved.specifications) == 3
        assert [m.id_ for m in retrieved.measurements] == [10]
        assert retrieved.non_conformities[0].measurement is retrieved.measurements[0]


def test_repository_get_returns_none_for_unknown_id(session):
    assert SqlAlchemyCollectionPointRepository(session).get(999) is None


def test_repository_lists_collection_points(session):
    repo = SqlAlchemyCollectionPointRepository(session)
    repo.add(make_collection_point(2, "Collection Point 2"))
    repo.add(make_collection_point(1, "Collection Point 1"))
    session.commit()

    assert [cp.name for cp in repo.list()] == ["Collection Point 1", "Collection Point 2"]

def test_repository_persists_daily_closure(session_factory):
    collection_point = make_collection_point()
    day = date(2026, 9, 29)
    collection_point.add_measurement(Measurement(1, datetime(2026, 9, 29, 8, 0), 0.3, MeasurementUnit.MG_L, MeasurementType.CHLORINE))
    collection_point.add_measurement(Measurement(2, datetime(2026, 9, 29, 8, 0), 7.0, None, MeasurementType.PH))
    collection_point.add_measurement(Measurement(3, datetime(2026, 9, 29, 8, 0), 25.0, MeasurementUnit.CELSIUS, MeasurementType.TEMPERATURE))
    collection_point.close_day(day)
    with session_factory() as session:
        SqlAlchemyCollectionPointRepository(session).add(collection_point)
        session.commit()

    with session_factory() as session:
        retrieved = SqlAlchemyCollectionPointRepository(session).get(1)

        assert retrieved.is_day_closed(day)
        assert [closure.day for closure in retrieved.daily_closures] == [day]

def test_repository_loaded_collection_point_rejects_measurement_on_closed_day(session_factory):
    collection_point = make_collection_point()
    collection_point.add_measurement(Measurement(1, datetime(2026, 9, 29, 8, 0), 0.3, MeasurementUnit.MG_L, MeasurementType.CHLORINE))
    collection_point.add_measurement(Measurement(2, datetime(2026, 9, 29, 8, 0), 7.0, None, MeasurementType.PH))
    collection_point.add_measurement(Measurement(3, datetime(2026, 9, 29, 8, 0), 25.0, MeasurementUnit.CELSIUS, MeasurementType.TEMPERATURE))
    collection_point.close_day(date(2026, 9, 29))
    with session_factory() as session:
        SqlAlchemyCollectionPointRepository(session).add(collection_point)
        session.commit()

    with session_factory() as session:
        retrieved = SqlAlchemyCollectionPointRepository(session).get(1)

        with pytest.raises(ValueError, match="already closed"):
            retrieved.add_measurement(Measurement(4, datetime(2026, 9, 29, 9, 0), 7.0, None, MeasurementType.PH))

def make_batch(session, id_=1, batch_number="PB-001"):
    receipt = RawMaterialReceipt(id_=id_, status=RawMaterialReceiptStatus.APPROVED)
    session.add(receipt)
    session.flush()

    return ProductionBatch(
        id_=id_,
        batch_number=batch_number,
        production_date=datetime(2026, 9, 25),
        milk_type=MilkType.COW,
        raw_material_receipt=receipt,
        expected_weight=100.0,
    )


def test_repository_can_save_a_batch(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    repository = SqlAlchemyProductionBatchRepository(session)

    batch = make_batch(session)
    repository.add(batch)
    session.commit()

    rows = list(session.execute(text("SELECT batch_number FROM production_batches")))
    assert rows == [("PB-001",)]


def test_repository_can_retrieve_a_batch_by_batch_number(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    repository = SqlAlchemyProductionBatchRepository(session)

    batch = make_batch(session, id_=1, batch_number="PB-001")
    repository.add(batch)
    session.commit()

    retrieved = repository.get("PB-001")
    assert retrieved is not None
    assert retrieved.batch_number == "PB-001"
    assert retrieved.milk_type == MilkType.COW


def test_repository_get_returns_none_for_unknown_batch(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    repository = SqlAlchemyProductionBatchRepository(session)

    assert repository.get("PB-DOES-NOT-EXIST") is None


def test_repository_lists_all_batches(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    repository = SqlAlchemyProductionBatchRepository(session)

    repository.add(make_batch(session, id_=1, batch_number="PB-001"))
    repository.add(make_batch(session, id_=2, batch_number="PB-002"))
    session.commit()

    batch_numbers = {batch.batch_number for batch in repository.list()}
    assert batch_numbers == {"PB-001", "PB-002"}
