from datetime import datetime
from sqlalchemy import text
from LactoQC.domain.model import (
    CollectionPoint,
    Measurement,
    MeasurementType,
    MeasurementUnit,
    Specification,
    BatchStatus,
    Lecithinization,
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
    TestResult,
    WeightSample,
)

def make_specifications():
    return [
        Specification(MeasurementType.CHLORINE, 0.2, 0.5, MeasurementUnit.MG_L),
        Specification(MeasurementType.PH, 6.5, 7.5, None),
        Specification(MeasurementType.TEMPERATURE, 0.0, 100.0, MeasurementUnit.CELSIUS),
    ]

def test_orm_saves_collection_point_with_specifications(session):
    collection_point = CollectionPoint(1, "Collection Point 1", "Location 1", specifications=make_specifications())

    session.add(collection_point)
    session.commit()

    assert list(
        session.execute(
            text(
                "SELECT id, name, location FROM collection_points"
                )
            )
        ) == [
        (1, "Collection Point 1", "Location 1")
    ]
    assert list(
        session.execute(
            text(
                "SELECT collection_point_id, measurement_type, measurement_unit FROM specifications ORDER BY id"
                )
            )
        ) == [
        (1, "CHLORINE", "MG_L"),
        (1, "PH", None),
        (1, "TEMPERATURE", "CELSIUS"),
    ]

def test_orm_loads_collection_point_with_specifications(session):
    session.execute(
        text(
            "INSERT INTO collection_points (id, name, location) VALUES (1, 'Collection Point 1', 'Location 1')"
            )
        )
    session.execute(
        text(
        "INSERT INTO specifications "
        "(collection_point_id, measurement_type, min_value, max_value, measurement_unit) VALUES "
        "(1, 'CHLORINE', 0.2, 0.5, 'MG_L'), "
        "(1, 'PH', 6.5, 7.5, NULL), "
        "(1, 'TEMPERATURE', 0.0, 100.0, 'CELSIUS')"
        )
    )

    collection_point = session.query(CollectionPoint).one()

    assert collection_point.id_ == 1
    assert collection_point.name == "Collection Point 1"
    assert [s.measurement_type for s in collection_point.specifications] == [
        MeasurementType.CHLORINE, MeasurementType.PH, MeasurementType.TEMPERATURE,
    ]
    assert collection_point.specifications[1].measurement_unit is None


def test_orm_saves_non_conformity_linked_to_measurement(session):
    collection_point = CollectionPoint(1, "Collection Point 1", "Location 1", specifications=make_specifications())
    collection_point.add_measurement(
        Measurement(10, datetime(2026, 9, 28, 8, 0), 0.1, MeasurementUnit.MG_L, MeasurementType.CHLORINE)
    )

    session.add(collection_point)
    session.commit()

    assert list(session.execute(text(
        "SELECT number, measurement_id FROM non_conformities"
    ))) == [(1, 10)]

def make_batch_for_orm(session, id_=1, batch_number="PB-001"):
    receipt = RawMaterialReceipt(id_=id_, status=RawMaterialReceiptStatus.APPROVED)
    session.add(receipt)
    session.flush()

    batch = ProductionBatch(
        id_=id_,
        batch_number=batch_number,
        production_date=datetime(2026, 9, 25),
        milk_type=MilkType.COW,
        raw_material_receipt=receipt,
        expected_weight=100.0,
    )
    return batch


def test_can_save_a_production_batch(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    batch = make_batch_for_orm(session)

    session.add(batch)
    session.commit()

    rows = list(session.execute(
        text("SELECT id_, batch_number, milk_type, status FROM production_batches")
    ))
    assert rows == [(1, "PB-001", "COW", "OPEN")]


def test_can_load_a_production_batch_with_weight_samples(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    batch = make_batch_for_orm(session)
    batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=98.0))
    batch.add_weight_sample(WeightSample(id_=2, date_time=datetime.now(), weight_kg=101.0))

    session.add(batch)
    session.commit()
    session.expunge_all()

    loaded_batch = session.query(ProductionBatch).filter_by(batch_number="PB-001").one()
    assert len(loaded_batch.weight_samples) == 2
    assert {s.weight_kg for s in loaded_batch.weight_samples} == {98.0, 101.0}


def test_can_load_a_production_batch_with_lecithinization(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    batch = make_batch_for_orm(session, id_=2, batch_number="PB-002")
    batch.register_lecithinization(Lecithinization(performed=True, responsible="Maria"))

    session.add(batch)
    session.commit()
    session.expunge_all()

    loaded_batch = session.query(ProductionBatch).filter_by(batch_number="PB-002").one()
    assert loaded_batch.lecithinization.performed is True
    assert loaded_batch.lecithinization.responsible == "Maria"


def test_can_load_a_production_batch_with_non_conformities(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    batch = make_batch_for_orm(session, id_=3, batch_number="PB-003")
    batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=50.0))
    batch.register_wettability_result(TestResult.REJECTED)

    session.add(batch)
    session.commit()
    session.expunge_all()

    loaded_batch = session.query(ProductionBatch).filter_by(batch_number="PB-003").one()
    assert len(loaded_batch.non_conformities) == 2


def test_release_status_is_persisted(sqlite_session_production_batch):
    session = sqlite_session_production_batch
    batch = make_batch_for_orm(session, id_=4, batch_number="PB-004")
    batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
    batch.register_wettability_result(TestResult.APPROVED)
    batch.release()

    session.add(batch)
    session.commit()
    session.expunge_all()

    loaded_batch = session.query(ProductionBatch).filter_by(batch_number="PB-004").one()
    assert loaded_batch.status == BatchStatus.RELEASED
