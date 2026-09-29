from datetime import datetime

import pytest

from LactoQC.domain.models import (
    BatchNonConformity,
    BatchStatus,
    Lecithinization,
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
    TestResult,
    WeightSample,
)




def make_approved_receipt(id_: int = 1) -> RawMaterialReceipt:
    return RawMaterialReceipt(id_=id_, status=RawMaterialReceiptStatus.APPROVED)


def make_batch(
    id_: int = 1,
    batch_number: str = "PB-001",
    production_date: datetime = datetime(2026, 9, 25),
    milk_type: MilkType = MilkType.COW,
    receipt: RawMaterialReceipt | None = None,
    expected_weight: float = 100.0,
) -> ProductionBatch:
    return ProductionBatch(
        id_=id_,
        batch_number=batch_number,
        production_date=production_date,
        milk_type=milk_type,
        raw_material_receipt=receipt or make_approved_receipt(id_),
        expected_weight=expected_weight,
    )


class TestRawMaterialReceipt:

    def test_approved_status_returns_true(self):
        receipt = RawMaterialReceipt(id_=1, status=RawMaterialReceiptStatus.APPROVED)
        assert receipt.approved is True

    def test_pending_status_returns_false(self):
        receipt = RawMaterialReceipt(id_=1, status=RawMaterialReceiptStatus.PENDING)
        assert receipt.approved is False

    def test_rejected_status_returns_false(self):
        receipt = RawMaterialReceipt(id_=1, status=RawMaterialReceiptStatus.REJECTED)
        assert receipt.approved is False




class TestWeightSample:

    def test_creates_valid_sample(self):
        sample = WeightSample(id_=1, date_time=datetime.now(), weight_kg=98.0)
        assert sample.weight_kg == 98.0

    def test_rejects_zero_weight(self):
        with pytest.raises(ValueError):
            WeightSample(id_=1, date_time=datetime.now(), weight_kg=0)

    def test_rejects_negative_weight(self):
        with pytest.raises(ValueError):
            WeightSample(id_=1, date_time=datetime.now(), weight_kg=-10)



class TestLecithinization:

    def test_creates_performed_lecithinization(self):
        lecithinization = Lecithinization(performed=True, responsible="Maria")
        assert lecithinization.performed is True
        assert lecithinization.responsible == "Maria"

    def test_creates_non_performed_lecithinization(self):
        lecithinization = Lecithinization(performed=False)
        assert lecithinization.performed is False



class TestProductionBatchCreation:

    def test_creates_batch_with_approved_raw_material(self):
        batch = make_batch()
        assert batch.status == BatchStatus.OPEN

    def test_rejects_creation_with_rejected_raw_material(self):
        receipt = RawMaterialReceipt(id_=1, status=RawMaterialReceiptStatus.REJECTED)
        with pytest.raises(ValueError):
            make_batch(receipt=receipt)

    def test_rejects_creation_with_pending_raw_material(self):
        receipt = RawMaterialReceipt(id_=1, status=RawMaterialReceiptStatus.PENDING)
        with pytest.raises(ValueError):
            make_batch(receipt=receipt)

    def test_rejects_zero_expected_weight(self):
        with pytest.raises(ValueError):
            make_batch(expected_weight=0)

    def test_rejects_negative_expected_weight(self):
        with pytest.raises(ValueError):
            make_batch(expected_weight=-50)

    def test_default_status_is_open(self):
        batch = make_batch()
        assert batch.status == BatchStatus.OPEN

    def test_default_wettability_result_is_pending(self):
        batch = make_batch()
        assert batch.wettability_result == TestResult.PENDING

    def test_default_collections_start_empty(self):
        batch = make_batch()
        assert batch.weight_samples == []
        assert batch.non_conformities == []
        assert batch.lecithinization is None



class TestWeightTolerance:

    def test_sample_within_tolerance_generates_no_non_conformity(self):
        batch = make_batch(expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=98.0))
        assert batch.non_conformities == []

    def test_sample_above_upper_bound_generates_non_conformity(self):
        batch = make_batch(expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=106.0))
        assert len(batch.non_conformities) == 1

    def test_sample_below_lower_bound_generates_non_conformity(self):
        batch = make_batch(expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=94.0))
        assert len(batch.non_conformities) == 1

    def test_sample_exactly_at_upper_bound_is_valid(self):
        batch = make_batch(expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=105.0))
        assert batch.non_conformities == []

    def test_sample_exactly_at_lower_bound_is_valid(self):
        batch = make_batch(expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=95.0))
        assert batch.non_conformities == []

    def test_multiple_samples_are_evaluated_individually(self):
        batch = make_batch(expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=98.0))
        batch.add_weight_sample(WeightSample(id_=2, date_time=datetime.now(), weight_kg=120.0))
        assert len(batch.non_conformities) == 1
        assert len(batch.weight_samples) == 2


class TestMandatoryLecithinization:

    def test_goat_milk_without_lecithinization_generates_non_conformity(self):
        batch = make_batch(milk_type=MilkType.GOAT)
        batch.check_mandatory_lecithinization()
        assert len(batch.non_conformities) == 1

    def test_goat_milk_with_lecithinization_performed_is_valid(self):
        batch = make_batch(milk_type=MilkType.GOAT)
        batch.register_lecithinization(Lecithinization(performed=True))
        batch.check_mandatory_lecithinization()
        assert batch.non_conformities == []

    def test_goat_milk_with_lecithinization_not_performed_generates_non_conformity(self):
        batch = make_batch(milk_type=MilkType.GOAT)
        batch.register_lecithinization(Lecithinization(performed=False))
        batch.check_mandatory_lecithinization()
        assert len(batch.non_conformities) == 1

    def test_cow_milk_without_lecithinization_is_valid(self):
        batch = make_batch(milk_type=MilkType.COW)
        batch.check_mandatory_lecithinization()
        assert batch.non_conformities == []



class TestMilkTypeConflict:

    def test_same_date_different_milk_type_generates_non_conformity(self):
        cow_batch = make_batch(id_=1, milk_type=MilkType.COW, production_date=datetime(2026, 9, 25))
        goat_batch = make_batch(id_=2, milk_type=MilkType.GOAT, production_date=datetime(2026, 9, 25))

        cow_batch.check_milk_type_conflict([goat_batch])
        assert len(cow_batch.non_conformities) == 1

    def test_same_date_same_milk_type_is_valid(self):
        batch_a = make_batch(id_=1, milk_type=MilkType.COW, production_date=datetime(2026, 9, 25))
        batch_b = make_batch(id_=2, milk_type=MilkType.COW, production_date=datetime(2026, 9, 25))

        batch_a.check_milk_type_conflict([batch_b])
        assert batch_a.non_conformities == []

    def test_different_dates_different_milk_type_is_valid(self):
        cow_batch = make_batch(id_=1, milk_type=MilkType.COW, production_date=datetime(2026, 9, 25))
        goat_batch = make_batch(id_=2, milk_type=MilkType.GOAT, production_date=datetime(2026, 9, 26))

        cow_batch.check_milk_type_conflict([goat_batch])
        assert cow_batch.non_conformities == []

    def test_empty_list_of_other_batches_is_valid(self):
        batch = make_batch()
        batch.check_milk_type_conflict([])
        assert batch.non_conformities == []

    def test_batch_does_not_conflict_with_itself(self):
        batch = make_batch(id_=1, milk_type=MilkType.COW)
        batch.check_milk_type_conflict([batch])
        assert batch.non_conformities == []



class TestWettabilityResult:

    def test_approved_result_generates_no_non_conformity(self):
        batch = make_batch()
        batch.register_wettability_result(TestResult.APPROVED)
        assert batch.non_conformities == []

    def test_rejected_result_generates_non_conformity(self):
        batch = make_batch()
        batch.register_wettability_result(TestResult.REJECTED)
        assert len(batch.non_conformities) == 1

    def test_pending_result_does_not_generate_non_conformity_on_registration(self):
        batch = make_batch()
        batch.register_wettability_result(TestResult.PENDING)
        assert batch.non_conformities == []



class TestRelease:

    def test_batch_is_released_when_all_rules_pass(self):
        batch = make_batch(milk_type=MilkType.COW, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
        batch.register_wettability_result(TestResult.APPROVED)

        batch.release()

        assert batch.status == BatchStatus.RELEASED
        assert batch.non_conformities == []

    def test_batch_with_weight_out_of_tolerance_is_non_conforming(self):
        batch = make_batch(milk_type=MilkType.COW, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=80.0))
        batch.register_wettability_result(TestResult.APPROVED)

        batch.release()

        assert batch.status == BatchStatus.NON_CONFORMING

    def test_goat_batch_without_lecithinization_is_non_conforming(self):
        batch = make_batch(milk_type=MilkType.GOAT, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
        batch.register_wettability_result(TestResult.APPROVED)

        batch.release()

        assert batch.status == BatchStatus.NON_CONFORMING

    def test_batch_with_milk_type_conflict_is_non_conforming(self):
        cow_batch = make_batch(id_=1, milk_type=MilkType.COW, production_date=datetime(2026, 9, 25))
        goat_batch = make_batch(id_=2, milk_type=MilkType.GOAT, production_date=datetime(2026, 9, 25))
        cow_batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
        cow_batch.register_wettability_result(TestResult.APPROVED)

        cow_batch.release(other_batches_of_the_day=[goat_batch])

        assert cow_batch.status == BatchStatus.NON_CONFORMING

    def test_batch_with_rejected_wettability_is_non_conforming(self):
        batch = make_batch(milk_type=MilkType.COW, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
        batch.register_wettability_result(TestResult.REJECTED)

        batch.release()

        assert batch.status == BatchStatus.NON_CONFORMING

    def test_batch_with_pending_wettability_is_non_conforming_on_release(self):
        batch = make_batch(milk_type=MilkType.COW, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
        # wettability_result left as PENDING

        batch.release()

        assert batch.status == BatchStatus.NON_CONFORMING

    def test_batch_with_multiple_violations_registers_all_non_conformities(self):
        batch = make_batch(milk_type=MilkType.GOAT, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=50.0))
        # no lecithinization registered, wettability left PENDING

        batch.release()

        assert batch.status == BatchStatus.NON_CONFORMING
        assert len(batch.non_conformities) == 3  # weight + lecithinization + wettability


# ---------------------------------------------------------------------------
# BatchNonConformity
# ---------------------------------------------------------------------------

class TestBatchNonConformity:

    def test_creates_non_conformity_with_batch_reference(self):
        non_conformity = BatchNonConformity(id_=1, batch_id=10, description="Some issue")
        assert non_conformity.batch_id == 10
        assert non_conformity.description == "Some issue"

    def test_non_conformity_ids_increment_within_batch(self):
        batch = make_batch(milk_type=MilkType.GOAT, expected_weight=100.0)
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=50.0))
        batch.check_mandatory_lecithinization()

        ids = [nc.id_ for nc in batch.non_conformities]
        assert ids == [1, 2]
