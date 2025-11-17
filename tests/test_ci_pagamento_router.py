import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture
def setup_ci_dependencies(test_client: TestClient, admin_auth_headers: dict) -> dict:
    resp_agente = test_client.post("/api/agentes/", json={"nome": "Solicitante Teste CI"}, headers=admin_auth_headers)
    assert resp_agente.status_code == 201
    
    resp_unidade = test_client.post("/api/unidades/", json={"nome": "Secretaria Teste CI"}, headers=admin_auth_headers)
    assert resp_unidade.status_code == 201
    
    resp_dotacao = test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotacao Teste CI"}, headers=admin_auth_headers)
    assert resp_dotacao.status_code == 201

    aocs_payload = {
        "numero_aocs": "AOCS-CI-TESTE-333/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "AOCS para teste de CI",
        "unidade_requisitante_nome": "Secretaria Teste CI",
        "local_entrega_descricao": "Local Teste CI", 
        "agente_responsavel_nome": "Solicitante Teste CI",
        "dotacao_info_orcamentaria": "Dotacao Teste CI"
    }
    resp_aocs = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert resp_aocs.status_code == 201
    
    return {
        "aocs_numero": "AOCS-CI-TESTE-333/2025",
        "solicitante_nome": "Solicitante Teste CI",
        "secretaria_nome": "Secretaria Teste CI",
        "dotacao_info_orcamentaria": "Dotacao Teste CI"
    }

@pytest.fixture
def ci_payload(setup_ci_dependencies: dict) -> dict:
    payload = {
        "numero_ci": "CI-999/2025",
        "data_ci": "2025-11-14",
        "numero_nota_fiscal": "NF-12345",
        "data_nota_fiscal": "2025-11-10",
        "valor_nota_fiscal": 1500.75
    }
    payload.update(setup_ci_dependencies)
    return payload

def test_create_ci_pagamento(test_client: TestClient, admin_auth_headers: dict, ci_payload: dict):
    response = test_client.post(
        "/api/ci-pagamento/", 
        json=ci_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["numero_ci"] == "CI-999/2025"
    assert data["id_solicitante"] is not None 
    assert data["id_aocs"] is not None 

def test_get_ci_pagamento_by_id(test_client: TestClient, admin_auth_headers: dict, ci_payload: dict):
    response_create = test_client.post(
        "/api/ci-pagamento/",
        json=ci_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/ci-pagamento/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["numero_ci"] == "CI-999/2025"

def test_delete_ci_pagamento(test_client: TestClient, admin_auth_headers: dict, ci_payload: dict):
    response_create = test_client.post(
        "/api/ci-pagamento/",
        json=ci_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/ci-pagamento/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/ci-pagamento/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404