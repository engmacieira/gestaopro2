import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture
def aocs_payload() -> dict:
    return {
        "numero_aocs": "AOCS-001/2025-TESTE",
        "data_criacao": date.today().isoformat(),
        "justificativa": "Teste de criação de AOCS",
        "numero_pedido": "NP-123",
        "empenho": "E-456",
        "unidade_requisitante_nome": "Unidade de Teste (AOCS)",
        "local_entrega_descricao": "Local de Teste (AOCS)",
        "agente_responsavel_nome": "Agente de Teste (AOCS)",
        "dotacao_info_orcamentaria": "Dotação de Teste (AOCS)"
    }

def test_create_aocs(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    response = test_client.post(
        "/api/aocs/", 
        json=aocs_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["numero_aocs"] == "AOCS-001/2025-TESTE"
    assert data["justificativa"] == "Teste de criação de AOCS"
    assert data["id_unidade_requisitante"] is not None 

def test_get_aocs_by_id(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/aocs/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["numero_aocs"] == "AOCS-001/2025-TESTE"

def test_get_aocs_by_numero(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    numero_aocs = response_create.json()["numero_aocs"]

    response_get = test_client.get(
        f"/api/aocs/numero/{numero_aocs}", 
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["numero_aocs"] == numero_aocs

def test_update_aocs(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    update_payload = {
        "justificativa": "Justificativa ATUALIZADA",
        "empenho": "E-789-UPDATED"
    }
    response_put = test_client.put(
        f"/api/aocs/{new_id}",
        json=update_payload,
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["justificativa"] == "Justificativa ATUALIZADA"
    assert data["empenho"] == "E-789-UPDATED"
    assert data["numero_aocs"] == "AOCS-001/2025-TESTE"

def test_delete_aocs(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/aocs/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/aocs/{new_id}",
        headers=admin_auth_headers
    )
   
    assert response_get.status_code == 404