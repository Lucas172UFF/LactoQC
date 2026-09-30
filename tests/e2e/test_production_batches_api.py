def create_batch(
    client,
    batch_number="LOTE-001",
    milk_type="COW",
    expected_weight=1000,
    receipt_id=1,
):
    response = client.post(
        "/production-batches",
        json={
            "batch_number": batch_number,
            "production_date": "2026-09-30T08:00:00",
            "milk_type": milk_type,
            "raw_material_receipt": {
                "id": receipt_id,
                "status": "APPROVED",
            },
            "expected_weight": expected_weight,
        },
    )

    assert response.status_code == 201, response.get_json()

    return response


def test_cria_lote_de_producao(client):
    response = create_batch(client)

    data = response.get_json()

    assert data["batch_number"] == "LOTE-001"
    assert data["milk_type"] == "COW"
    assert data["expected_weight"] == 1000
    assert data["status"] == "OPEN"


def test_lista_lotes_de_producao(client):
    create_batch(client, "LOTE-001")
    create_batch(client, "LOTE-002", receipt_id=2)

    response = client.get("/production-batches")

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2
    assert data[0]["batch_number"] == "LOTE-001"
    assert data[1]["batch_number"] == "LOTE-002"


def test_busca_lote_de_producao(client):
    create_batch(client)

    response = client.get("/production-batches/LOTE-001")

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch_number"] == "LOTE-001"
    assert data["milk_type"] == "COW"
    assert data["expected_weight"] == 1000


def test_lote_inexistente_retorna_404(client):
    response = client.get("/production-batches/LOTE-999")

    assert response.status_code == 404


def test_criar_lote_com_materia_prima_reprovada_retorna_422(client):
    response = client.post(
        "/production-batches",
        json={
            "batch_number": "LOTE-001",
            "production_date": "2026-09-30T08:00:00",
            "milk_type": "COW",
            "raw_material_receipt": {
                "id": 1,
                "status": "REJECTED",
            },
            "expected_weight": 1000,
        },
    )

    assert response.status_code == 422


def test_criar_lote_sem_campos_obrigatorios_retorna_400(client):
    response = client.post(
        "/production-batches",
        json={
            "batch_number": "LOTE-001",
        },
    )

    assert response.status_code == 400


def test_criar_lote_com_peso_esperado_invalido_retorna_422(client):
    response = client.post(
        "/production-batches",
        json={
            "batch_number": "LOTE-001",
            "production_date": "2026-09-30T08:00:00",
            "milk_type": "COW",
            "raw_material_receipt": {
                "id": 1,
                "status": "APPROVED",
            },
            "expected_weight": 0,
        },
    )

    assert response.status_code == 422


def test_registra_amostra_de_peso_dentro_da_tolerancia(client):
    create_batch(client)

    response = client.post(
        "/production-batches/LOTE-001/weight-samples",
        json={
            "weight_kg": 1020,
            "date_time": "2026-09-30T09:00:00",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["weight_sample"]["weight_kg"] == 1020
    assert data["non_conformities"] == []


def test_peso_fora_da_tolerancia_gera_nao_conformidade(client):
    create_batch(client)

    response = client.post(
        "/production-batches/LOTE-001/weight-samples",
        json={
            "weight_kg": 1100,
            "date_time": "2026-09-30T09:00:00",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert len(data["non_conformities"]) == 1
    assert "tolerance range" in data["non_conformities"][0]["description"]


def test_amostra_de_peso_invalida_retorna_422(client):
    create_batch(client)

    response = client.post(
        "/production-batches/LOTE-001/weight-samples",
        json={
            "weight_kg": 0,
        },
    )

    assert response.status_code == 422


def test_registra_lecitinizacao(client):
    create_batch(client, milk_type="GOAT")

    response = client.post(
        "/production-batches/LOTE-001/lecithinization",
        json={
            "performed": True,
            "date_time": "2026-09-30T10:00:00",
            "responsible": "Aloysio",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["lecithinization"]["performed"] is True
    assert data["lecithinization"]["responsible"] == "Aloysio"


def test_lecitinizacao_com_valor_invalido_retorna_400(client):
    create_batch(client)

    response = client.post(
        "/production-batches/LOTE-001/lecithinization",
        json={
            "performed": "true",
        },
    )

    assert response.status_code == 400


def test_registra_wettability_aprovado(client):
    create_batch(client)

    response = client.post(
        "/production-batches/LOTE-001/wettability",
        json={
            "result": "APPROVED",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["result"] == "APPROVED"
    assert data["non_conformities"] == []


def test_wettability_reprovado_gera_nao_conformidade(client):
    create_batch(client)

    response = client.post(
        "/production-batches/LOTE-001/wettability",
        json={
            "result": "REJECTED",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["result"] == "REJECTED"
    assert len(data["non_conformities"]) == 1
    assert "Wettability test rejected" in data["non_conformities"][0]["description"]


def test_libera_lote_de_leite_de_vaca(client):
    create_batch(client, milk_type="COW")

    client.post(
        "/production-batches/LOTE-001/weight-samples",
        json={
            "weight_kg": 1000,
        },
    )

    client.post(
        "/production-batches/LOTE-001/wettability",
        json={
            "result": "APPROVED",
        },
    )

    response = client.post(
        "/production-batches/LOTE-001/release"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch"]["status"] == "RELEASED"
    assert data["non_conformities"] == []


def test_lote_de_cabra_sem_lecitinizacao_nao_e_liberado(client):
    create_batch(client, milk_type="GOAT")

    client.post(
        "/production-batches/LOTE-001/weight-samples",
        json={
            "weight_kg": 1000,
        },
    )

    client.post(
        "/production-batches/LOTE-001/wettability",
        json={
            "result": "APPROVED",
        },
    )

    response = client.post(
        "/production-batches/LOTE-001/release"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch"]["status"] == "NON_CONFORMING"
    assert len(data["non_conformities"]) == 1
    assert "lecithinization" in data["non_conformities"][0]["description"]


def test_lote_sem_wettability_aprovado_nao_e_liberado(client):
    create_batch(client)

    client.post(
        "/production-batches/LOTE-001/weight-samples",
        json={
            "weight_kg": 1000,
        },
    )

    response = client.post(
        "/production-batches/LOTE-001/release"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch"]["status"] == "NON_CONFORMING"
    assert any(
        "Wettability test not approved"
        in nc["description"]
        for nc in data["non_conformities"]
    )


def test_lotes_de_tipos_diferentes_no_mesmo_dia_geram_nao_conformidade(client):
    create_batch(
        client,
        batch_number="LOTE-001",
        milk_type="COW",
        receipt_id=1,
    )

    create_batch(
        client,
        batch_number="LOTE-002",
        milk_type="GOAT",
        receipt_id=2,
    )

    client.post(
        "/production-batches/LOTE-002/lecithinization",
        json={
            "performed": True,
        },
    )

    client.post(
        "/production-batches/LOTE-002/wettability",
        json={
            "result": "APPROVED",
        },
    )

    response = client.post(
        "/production-batches/LOTE-002/release"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch"]["status"] == "NON_CONFORMING"

    assert any(
        "Milk type conflict" in nc["description"]
        for nc in data["non_conformities"]
    )