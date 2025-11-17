import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture
def contrato_payload() -> dict:
    return {
        "numero_contrato": "CT-001/2025-TESTE",
        "data_inicio": "2025-01-01",
        "data_fim": "2025-12-31",
        "fornecedor": {
            "nome": "Fornecedor de Teste LTDA",
            "cpf_cnpj": "12.345.678/0001-99",
            "email": "teste@fornecedor.com",
            "telefone": "31999998888"
        },
        "categoria_nome": "Obras e Serviços",
        "instrumento_nome": "Contrato de Teste",
        "modalidade_nome": "Pregão Eletrônico",
        "numero_modalidade_str": "PE 123/2024",
        "processo_licitatorio_numero": "PL 456/2024"
    }

def test_create_contrato(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    response = test_client.post(
        "/api/contratos/", 
        json=contrato_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["numero_contrato"] == "CT-001/2025-TESTE"
    assert data["fornecedor"]["nome"] == "Fornecedor de Teste LTDA"
    assert data["id_categoria"] is not None 

def test_get_contrato_by_id(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    response_create = test_client.post(
        "/api/contratos/",
        json=contrato_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/contratos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["numero_contrato"] == "CT-001/2025-TESTE"

def test_get_all_contratos(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    test_client.post("/api/contratos/", json=contrato_payload, headers=admin_auth_headers)

    response_get = test_client.get("/api/contratos/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["numero_contrato"] == "CT-001/2025-TESTE"

def test_update_contrato(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    response_create = test_client.post(
        "/api/contratos/",
        json=contrato_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    update_payload = {
        "data_fim": "2026-01-31",
        "fornecedor": { "nome": "Fornecedor ATUALIZADO" }
    }
    response_put = test_client.put(
        f"/api/contratos/{new_id}",
        json=update_payload,
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["data_fim"] == "2026-01-31" 
    assert data["fornecedor"]["nome"] == "Fornecedor ATUALIZADO"
    assert data["numero_contrato"] == "CT-001/2025-TESTE"

def test_delete_contrato(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    response_create = test_client.post(
        "/api/contratos/",
        json=contrato_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/contratos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/contratos/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404