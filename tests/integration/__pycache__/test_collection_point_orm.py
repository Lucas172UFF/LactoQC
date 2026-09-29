"""Ida e volta do ORM: salva, fecha a sessão, lê numa sessão nova."""
from datetime import datetime

from LactoQC.adapters.repository import CollectionPointRepository
from LactoQC.domain.models import (
    CollectionPoint, Measurement, MeasurementType, MeasurementUnit, Specification,
)


def make_collection_point(name="Sala de envase"):
    return CollectionPoint(
        id_=None, name=name, location="Bloco A",
        specifications=[
            Specification(MeasurementType.CHLORINE, 0.5, 5.0, MeasurementUnit.MG_L),
            Specification(MeasurementType.PH, 6.0, 9.5, None),
            Specification(MeasurementType.TEMPERATURE, 18.0, 25.0, MeasurementUnit.CELSIUS),
        ],
    )


def measurement(value, mtype, unit, date):
    return Measurement(None, date, value, unit, mtype)


def test_round_trip_com_medicoes_e_nao_conformidade(session_factory):
    s1 = session_factory()
    cp = make_collection_point()
    cp.add_measurement(measurement(2.0, MeasurementType.CHLORINE, MeasurementUnit.MG_L, datetime(2026, 9, 29, 8)))
    cp.add_measurement(measurement(0.1, MeasurementType.CHLORINE, MeasurementUnit.MG_L, datetime(2026, 9, 29, 9)))
    cp.add_measurement(measurement(7.0, MeasurementType.PH, None, datetime(2026, 9, 29, 9, 30)))
    s1.add(cp)
    s1.commit()
    cp_id = cp.id_
    s1.close()

    s2 = session_factory()
    loaded = s2.get(CollectionPoint, cp_id)
    assert loaded.name == "Sala de envase"
    assert len(loaded.specifications) == 3
    assert len(loaded.measurements) == 3
    assert len(loaded.non_conformities) == 1

    nc = loaded.non_conformities[0]
    assert nc.id_ == 1
    assert nc.measurement.value == 0.1
    assert nc.measurement in loaded.measurements
    assert nc.specification.measurement_type == MeasurementType.CHLORINE
    ph = [m for m in loaded.measurements if m.measurement_type == MeasurementType.PH][0]
    assert ph.measurement_unit is None
    s2.close()


def test_numeracao_da_nao_conformidade_e_por_ponto(session_factory):
    session = session_factory()
    a, b = make_collection_point("A"), make_collection_point("B")
    for cp in (a, b):
        cp.add_measurement(measurement(0.1, MeasurementType.CHLORINE, MeasurementUnit.MG_L, datetime(2026, 9, 29, 8)))
        session.add(cp)
    session.commit()
    assert a.non_conformities[0].id_ == 1
    assert b.non_conformities[0].id_ == 1


def test_repositorio_lista_nao_conformidades_por_periodo_e_origem(session_factory):
    session = session_factory()
    a, b = make_collection_point("A"), make_collection_point("B")
    a.add_measurement(measurement(0.1, MeasurementType.CHLORINE, MeasurementUnit.MG_L, datetime(2026, 9, 1, 8)))
    a.add_measurement(measurement(30.0, MeasurementType.TEMPERATURE, MeasurementUnit.CELSIUS, datetime(2026, 9, 20, 8)))
    b.add_measurement(measurement(10.0, MeasurementType.PH, None, datetime(2026, 9, 10, 8)))
    session.add_all([a, b])
    session.commit()

    repo = CollectionPointRepository(session)
    assert len(repo.list_non_conformities()) == 3
    assert len(repo.list_non_conformities(collection_point_id=a.id_)) == 2
    assert len(repo.list_non_conformities(start=datetime(2026, 9, 5), end=datetime(2026, 9, 15))) == 1
    assert len(repo.list_non_conformities(start=datetime(2026, 9, 5), collection_point_id=a.id_)) == 1
