SPECS = [
    {"measurement_type": "CHLORINE", "min_value": 0.5, "max_value": 5.0},
    {"measurement_type": "PH", "min_value": 6.0, "max_value": 9.5},
    {"measurement_type": "TEMPERATURE", "min_value": 18.0, "max_value": 25.0},
]

def create_point(client, name="Sala de envase", specs=None):
    resp = client.post(
        "/collection-points",
        json={"name": name, "location": "Bloco A", "specifications": SPECS if specs is None else specs},
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["id"]

def post_measurement(client, cp_id, mtype, value, date=None):
    body = {"measurement_type": mtype, "value": value}
    if date:
        body["measurement_date"] = date
    return client.post(f"/collection-points/{cp_id}/measurements", json=body)

def test_cria_ponto_de_coleta(client):
    resp = client.post("/collection-points", json={"name": "Sala 1", "location": "A", "specifications": SPECS})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["id"] is not None
    assert len(data["specifications"]) == 3

def test_ponto_sem_todas_as_especificacoes_retorna_422(client):
    resp = client.post("/collection-points", json={"name": "Sala 1", "location": "A", "specifications": SPECS[:2]})
    assert resp.status_code == 422

def test_ponto_com_faixa_invertida_retorna_422(client):
    bad = [dict(SPECS[0], min_value=9.0, max_value=1.0)] + SPECS[1:]
    resp = client.post("/collection-points", json={"name": "Sala 1", "location": "A", "specifications": bad})
    assert resp.status_code == 422

def test_criar_ponto_sem_campos_retorna_400(client):
    assert client.post("/collection-points", json={"name": "Sala 1"}).status_code == 400
    assert client.post("/collection-points", data="nao e json").status_code == 400

def test_medicao_dentro_da_faixa_nao_gera_nao_conformidade(client):
    cp_id = create_point(client)
    resp = post_measurement(client, cp_id, "CHLORINE", 2.0)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["measurement"]["measurement_unit"] == "mg/L"
    assert data["non_conformities"] == []

def test_medicao_fora_da_faixa_gera_nao_conformidade(client):
    cp_id = create_point(client)
    resp = post_measurement(client, cp_id, "CHLORINE", 0.1)
    assert resp.status_code == 201
    ncs = resp.get_json()["non_conformities"]
    assert len(ncs) == 1
    assert ncs[0]["number"] == 1
    assert ncs[0]["collection_point_id"] == cp_id
    assert "out of specification" in ncs[0]["description"]

    detail = client.get(f"/collection-points/{cp_id}").get_json()
    assert len(detail["measurements"]) == 1
    assert len(detail["non_conformities"]) == 1

def test_ph_nao_tem_unidade(client):
    cp_id = create_point(client)
    resp = post_measurement(client, cp_id, "PH", 7.0)
    assert resp.status_code == 201
    assert resp.get_json()["measurement"]["measurement_unit"] is None

def test_aceita_rotulo_do_tipo_de_medicao(client):
    cp_id = create_point(client)
    assert post_measurement(client, cp_id, "Temperatura", 20).status_code == 201

def test_tipo_de_medicao_invalido_retorna_422(client):
    cp_id = create_point(client)
    assert post_measurement(client, cp_id, "DENSIDADE", 1.0).status_code == 422

def test_valor_nao_numerico_retorna_422(client):
    cp_id = create_point(client)
    assert post_measurement(client, cp_id, "PH", "abc").status_code == 422

def test_data_invalida_retorna_422(client):
    cp_id = create_point(client)
    assert post_measurement(client, cp_id, "PH", 7.0, date="ontem").status_code == 422

def test_medicao_sem_campos_retorna_400(client):
    cp_id = create_point(client)
    resp = client.post(f"/collection-points/{cp_id}/measurements", json={"value": 7.0})
    assert resp.status_code == 400

def test_ponto_inexistente_retorna_404(client):
    assert client.get("/collection-points/999").status_code == 404
    assert post_measurement(client, 999, "PH", 7.0).status_code == 404

def test_lista_nao_conformidades_por_periodo_e_origem(client):
    a = create_point(client, "A")
    b = create_point(client, "B")
    post_measurement(client, a, "CHLORINE", 0.1, "2026-09-01T08:00:00")
    post_measurement(client, a, "TEMPERATURE", 30, "2026-09-20T08:00:00")
    post_measurement(client, b, "PH", 10, "2026-09-10T08:00:00")
    post_measurement(client, b, "PH", 7, "2026-09-11T08:00:00")  # conforme

    assert len(client.get("/non-conformities").get_json()) == 3
    assert len(client.get(f"/non-conformities?collection_point_id={a}").get_json()) == 2
    periodo = client.get("/non-conformities?start=2026-09-05T00:00:00&end=2026-09-15T00:00:00").get_json()
    assert len(periodo) == 1
    assert periodo[0]["collection_point_id"] == b

def test_filtros_invalidos_retornam_422(client):
    assert client.get("/non-conformities?start=abc").status_code == 422
    assert client.get("/non-conformities?collection_point_id=x").status_code == 422

def register_full_day(client, cp_id, day):
    assert post_measurement(client, cp_id, "CHLORINE", 2.0, f"{day}T08:00:00").status_code == 201
    assert post_measurement(client, cp_id, "PH", 7.0, f"{day}T08:00:00").status_code == 201
    assert post_measurement(client, cp_id, "TEMPERATURE", 20.0, f"{day}T08:00:00").status_code == 201

def close_day(client, cp_id, day):
    return client.post(f"/collection-points/{cp_id}/daily-closures", json={"date": day})

def test_fecha_registro_diario_completo(client):
    cp_id = create_point(client)
    register_full_day(client, cp_id, "2026-09-29")

    resp = close_day(client, cp_id, "2026-09-29")

    assert resp.status_code == 201
    assert resp.get_json() == {"collection_point_id": cp_id, "date": "2026-09-29"}

def test_detalhe_do_ponto_mostra_dias_fechados(client):
    cp_id = create_point(client)
    register_full_day(client, cp_id, "2026-09-29")
    close_day(client, cp_id, "2026-09-29")

    detail = client.get(f"/collection-points/{cp_id}").get_json()

    assert detail["daily_closures"] == ["2026-09-29"]

def test_fechar_dia_incompleto_retorna_422(client):
    cp_id = create_point(client)
    post_measurement(client, cp_id, "CHLORINE", 2.0, "2026-09-29T08:00:00")
    post_measurement(client, cp_id, "PH", 7.0, "2026-09-29T08:00:00")

    resp = close_day(client, cp_id, "2026-09-29")

    assert resp.status_code == 422
    assert "Temperatura" in resp.get_json()["detalhe"]

def test_fechar_dia_duas_vezes_retorna_422(client):
    cp_id = create_point(client)
    register_full_day(client, cp_id, "2026-09-29")
    close_day(client, cp_id, "2026-09-29")

    resp = close_day(client, cp_id, "2026-09-29")

    assert resp.status_code == 422

def test_medicao_em_dia_fechado_retorna_422(client):
    cp_id = create_point(client)
    register_full_day(client, cp_id, "2026-09-29")
    close_day(client, cp_id, "2026-09-29")

    resp = post_measurement(client, cp_id, "PH", 7.0, "2026-09-29T09:00:00")

    assert resp.status_code == 422
    assert post_measurement(client, cp_id, "PH", 7.0, "2026-09-30T08:00:00").status_code == 201

def test_fechar_dia_com_data_invalida_retorna_422(client):
    cp_id = create_point(client)

    assert close_day(client, cp_id, "29/09/2026").status_code == 422
    assert close_day(client, cp_id, "2026-09-29T08:00:00").status_code == 422

def test_fechar_dia_sem_data_retorna_400(client):
    cp_id = create_point(client)

    resp = client.post(f"/collection-points/{cp_id}/daily-closures", json={})

    assert resp.status_code == 400

def test_fechar_dia_de_ponto_inexistente_retorna_404(client):
    assert close_day(client, 999, "2026-09-29").status_code == 404