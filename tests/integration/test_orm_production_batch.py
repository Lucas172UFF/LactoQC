from datetime import datetime

from sqlalchemy import text

from LactoQC.domain.model import (
    BatchStatus,
    Lecithinization,
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
    TestResult,
    WeightSample,
)


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
