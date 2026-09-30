from datetime import datetime

from sqlalchemy import text

from LactoQC.adapters.repository import SqlAlchemyProductionBatchRepository
from LactoQC.domain.model import (
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
)


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
