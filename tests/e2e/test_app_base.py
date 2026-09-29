def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_rota_inexistente_retorna_404_em_json(client):
    resp = client.get("/rota-que-nao-existe")
    assert resp.status_code == 404
    assert "erro" in resp.get_json()
