import pytest
from datetime import datetime

from LactoQC.domain.model import (
    Lecithinization,
    MilkType,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
    TestResult,
)
from LactoQC.service_layer import services


def create_receipt(receipt_id=1):
    return RawMaterialReceipt(
        id_=receipt_id,
        status=RawMaterialReceiptStatus.APPROVED,
    )


def create_batch(
    repo,
    session,
    batch_number="LOTE-001",
    milk_type=MilkType.COW,
    expected_weight=1000,
    receipt_id=1,
):
    return services.create_production_batch(
        repo,
        session,
        batch_number=batch_number,
        production_date=datetime(2026, 9, 30, 8, 0),
        milk_type=milk_type,
        raw_material_receipt=create_receipt(receipt_id),
        expected_weight=expected_weight,
    )


def test_create_production_batch(
    production_batch_repo,
    session,
):
    batch = create_batch(
        production_batch_repo,
        session,
    )

    assert batch.batch_number == "LOTE-001"
    assert batch.milk_type == MilkType.COW
    assert batch.expected_weight == 1000
    assert production_batch_repo.get("LOTE-001") == batch


def test_create_production_batch_with_string_milk_type(
    production_batch_repo,
    session,
):
    batch = services.create_production_batch(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        production_date=datetime(2026, 9, 30, 8, 0),
        milk_type="GOAT",
        raw_material_receipt=create_receipt(),
        expected_weight=1000,
    )

    assert batch.milk_type == MilkType.GOAT


def test_create_production_batch_rejects_duplicate(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    with pytest.raises(ValueError, match="already exists"):
        create_batch(
            production_batch_repo,
            session,
        )


def test_create_production_batch_rejects_invalid_milk_type(
    production_batch_repo,
    session,
):
    with pytest.raises(ValueError, match="Invalid milk type"):
        create_batch(
            production_batch_repo,
            session,
            milk_type="INVALID",
        )


def test_create_production_batch_rejects_invalid_expected_weight(
    production_batch_repo,
    session,
):
    with pytest.raises(ValueError):
        create_batch(
            production_batch_repo,
            session,
            expected_weight="invalid",
        )


def test_get_production_batch(
    production_batch_repo,
    session,
):
    batch = create_batch(
        production_batch_repo,
        session,
    )

    result = services.get_production_batch(
        production_batch_repo,
        "LOTE-001",
    )

    assert result == batch


def test_get_production_batch_not_found(
    production_batch_repo,
    session,
):
    with pytest.raises(
        LookupError,
        match="not found",
    ):
        services.get_production_batch(
            production_batch_repo,
            "LOTE-999",
        )


def test_list_production_batches(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        receipt_id=1,
    )

    create_batch(
        production_batch_repo,
        session,
        batch_number="LOTE-002",
        receipt_id=2,
    )

    result = services.list_production_batches(
        production_batch_repo,
    )

    assert len(result) == 2

    batch_numbers = {
        batch.batch_number
        for batch in result
    }

    assert batch_numbers == {
        "LOTE-001",
        "LOTE-002",
    }
    
def test_register_weight_sample_within_tolerance(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    sample, non_conformities = services.register_weight_sample(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        weight_kg=1020,
        date_time=datetime(2026, 9, 30, 9, 0),
    )

    assert sample.weight_kg == 1020
    assert sample.date_time == datetime(2026, 9, 30, 9, 0)
    assert non_conformities == []


def test_register_weight_sample_outside_tolerance(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    sample, non_conformities = services.register_weight_sample(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        weight_kg=1100,
    )

    assert sample.weight_kg == 1100
    assert len(non_conformities) == 1


def test_register_weight_sample_invalid_weight(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    with pytest.raises(ValueError):
        services.register_weight_sample(
            production_batch_repo,
            session,
            batch_number="LOTE-001",
            weight_kg=0,
        )


def test_register_lecithinization(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
        milk_type=MilkType.GOAT,
    )

    lecithinization = services.register_lecithinization(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        performed=True,
        date_time=datetime(2026, 9, 30, 10, 0),
        responsible="Aloysio",
    )

    assert isinstance(
        lecithinization,
        Lecithinization,
    )
    assert lecithinization.performed is True
    assert lecithinization.responsible == "Aloysio"


def test_register_lecithinization_requires_boolean(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    with pytest.raises(
        ValueError,
        match="performed",
    ):
        services.register_lecithinization(
            production_batch_repo,
            session,
            batch_number="LOTE-001",
            performed="true",
        )


def test_register_wettability_approved(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    result, non_conformities = (
        services.register_wettability_result(
            production_batch_repo,
            session,
            batch_number="LOTE-001",
            result="APPROVED",
        )
    )

    assert result == TestResult.APPROVED
    assert non_conformities == []


def test_register_wettability_rejected(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    result, non_conformities = (
        services.register_wettability_result(
            production_batch_repo,
            session,
            batch_number="LOTE-001",
            result="REJECTED",
        )
    )

    assert result == TestResult.REJECTED
    assert len(non_conformities) == 1


def test_register_wettability_invalid_result(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    with pytest.raises(
        ValueError,
        match="Invalid test result",
    ):
        services.register_wettability_result(
            production_batch_repo,
            session,
            batch_number="LOTE-001",
            result="INVALID",
        )


def test_release_cow_production_batch(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
        milk_type=MilkType.COW,
    )

    services.register_weight_sample(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        weight_kg=1000,
    )

    services.register_wettability_result(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        result="APPROVED",
    )

    batch, non_conformities = (
        services.release_production_batch(
            production_batch_repo,
            session,
            "LOTE-001",
        )
    )

    assert batch.status.name == "RELEASED"
    assert non_conformities == []


def test_release_goat_batch_without_lecithinization(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
        milk_type=MilkType.GOAT,
    )

    services.register_weight_sample(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        weight_kg=1000,
    )

    services.register_wettability_result(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        result="APPROVED",
    )

    batch, non_conformities = (
        services.release_production_batch(
            production_batch_repo,
            session,
            "LOTE-001",
        )
    )

    assert batch.status.name == "NON_CONFORMING"
    assert len(non_conformities) == 1


def test_release_batch_without_approved_wettability(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
    )

    services.register_weight_sample(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        weight_kg=1000,
    )

    batch, non_conformities = (
        services.release_production_batch(
            production_batch_repo,
            session,
            "LOTE-001",
        )
    )

    assert batch.status.name == "NON_CONFORMING"
    assert len(non_conformities) >= 1


def test_release_goat_batch_with_lecithinization(
    production_batch_repo,
    session,
):
    create_batch(
        production_batch_repo,
        session,
        milk_type=MilkType.GOAT,
    )

    services.register_weight_sample(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        weight_kg=1000,
    )

    services.register_lecithinization(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        performed=True,
    )

    services.register_wettability_result(
        production_batch_repo,
        session,
        batch_number="LOTE-001",
        result="APPROVED",
    )

    batch, non_conformities = (
        services.release_production_batch(
            production_batch_repo,
            session,
            "LOTE-001",
        )
    )

    assert batch.status.name == "RELEASED"
    assert non_conformities == []