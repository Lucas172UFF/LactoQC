from datetime import datetime

from LactoQC.adapters.repository import FakeProductionBatchRepository
from LactoQC.domain.model import (
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
)


def make_batch(id_=1, batch_number="PB-001"):
    receipt = RawMaterialReceipt(id_=id_, status=RawMaterialReceiptStatus.APPROVED)
    return ProductionBatch(
        id_=id_,
        batch_number=batch_number,
        production_date=datetime(2026, 9, 25),
        milk_type=MilkType.COW,
        raw_material_receipt=receipt,
        expected_weight=100.0,
    )


class TestFakeProductionBatchRepository:

    def test_starts_empty(self):
        repository = FakeProductionBatchRepository()
        assert repository.list() == []

    def test_add_and_get_a_batch(self):
        repository = FakeProductionBatchRepository()
        batch = make_batch()

        repository.add(batch)

        assert repository.get("PB-001") is batch

    def test_get_returns_none_for_unknown_batch(self):
        repository = FakeProductionBatchRepository()
        assert repository.get("PB-DOES-NOT-EXIST") is None

    def test_list_returns_all_added_batches(self):
        repository = FakeProductionBatchRepository()
        batch_a = make_batch(id_=1, batch_number="PB-001")
        batch_b = make_batch(id_=2, batch_number="PB-002")

        repository.add(batch_a)
        repository.add(batch_b)

        assert set(repository.list()) == {batch_a, batch_b}

    def test_can_be_initialized_with_existing_batches(self):
        batch = make_batch()
        repository = FakeProductionBatchRepository(batches=[batch])

        assert repository.list() == [batch]
