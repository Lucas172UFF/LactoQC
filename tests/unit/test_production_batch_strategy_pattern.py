from datetime import datetime

from LactoQC.domain.model import (
    BatchStatus,
    MilkType,
    ProductionBatch,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
    SampleWeightRule,
    TestResult,
    WeightSample,
    WeightToleranceRule,
    WettabilityRule,
)


def make_batch(milk_type=MilkType.COW, expected_weight=100.0, **rule_kwargs):
    receipt = RawMaterialReceipt(id_=1, status=RawMaterialReceiptStatus.APPROVED)
    return ProductionBatch(
        id_=1,
        batch_number="PB-001",
        production_date=datetime(2026, 9, 25),
        milk_type=milk_type,
        raw_material_receipt=receipt,
        expected_weight=expected_weight,
        **rule_kwargs,
    )


class AlwaysApprovedWettabilityRule(WettabilityRule):
    def check(self, batch):
        return None


class StrictWeightToleranceRule(SampleWeightRule):
    """Estratégia alternativa: tolerância de 1% em vez dos 5% padrão."""

    def check(self, batch, sample):
        lower = batch.expected_weight * 0.99
        upper = batch.expected_weight * 1.01
        if lower <= sample.weight_kg <= upper:
            return None
        return f"Sample {sample.id_} outside the strict 1% tolerance."


class TestStrategyPatternDefaultBehavior:

    def test_batch_uses_default_rule_when_none_is_injected(self):
        batch = make_batch()
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=104.0))
        # 104kg esta dentro dos 5% padrao (95-105kg) -> sem nao conformidade
        assert batch.non_conformities == []

    def test_default_rule_instance_is_a_weight_tolerance_rule(self):
        batch = make_batch()
        assert isinstance(batch.weight_rule, WeightToleranceRule)


class TestStrategyPatternCanBeSwappedWithoutModifyingProductionBatch:

    def test_injecting_a_stricter_weight_rule_changes_behavior(self):
        lenient_batch = make_batch()
        lenient_batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=104.0))
        assert lenient_batch.non_conformities == []  # 5% padrao: 104kg passa

        strict_batch = make_batch(weight_rule=StrictWeightToleranceRule())
        strict_batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=104.0))
        assert len(strict_batch.non_conformities) == 1  # 1% customizado: 104kg nao passa

    def test_injecting_a_permissive_wettability_rule_allows_release(self):
        batch = make_batch()
        batch._wettability_rule = AlwaysApprovedWettabilityRule()
        batch.add_weight_sample(WeightSample(id_=1, date_time=datetime.now(), weight_kg=99.0))
        # wettability_result fica PENDING: com a regra padrao isso reprovaria o lote

        batch.release()

        assert batch.status == BatchStatus.RELEASED

    def test_same_batch_class_supports_two_different_strategies_simultaneously(self):
        batch_a = make_batch(weight_rule=WeightToleranceRule(tolerance=0.05))
        batch_b = make_batch(weight_rule=StrictWeightToleranceRule())

        sample = WeightSample(id_=1, date_time=datetime.now(), weight_kg=104.0)
        batch_a.add_weight_sample(sample)
        batch_b.add_weight_sample(sample)

        assert batch_a.non_conformities == []
        assert len(batch_b.non_conformities) == 1