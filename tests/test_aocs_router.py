import pytest
from fastapi.testclient import TestClient
from datetime import date

# O 'admin_auth_headers' é pego automaticamente do conftest.py

# --- Fixture de Dados (Payload) ---
@pytest.fixture
def aocs_payload() -> dict:
    """Retorna um payload JSON válido para criar uma AOCS."""
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

# --- Testes do CRUD ---

def test_create_aocs(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    """Testa POST /api/aocs/"""
    response = test_client.post(
        "/api/aocs/", 
        json=aocs_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["numero_aocs"] == "AOCS-001/2025-TESTE"
    assert data["justificativa"] == "Teste de criação de AOCS"
    assert data["id_unidade_requisitante"] is not None # Prova que o get_or_create funcionou

def test_get_aocs_by_id(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    """Testa GET /api/aocs/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Buscar por ID
    response_get = test_client.get(
        f"/api/aocs/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["numero_aocs"] == "AOCS-001/2025-TESTE"

def test_get_aocs_by_numero(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    """Testa GET /api/aocs/numero/{numero_aocs}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    numero_aocs = response_create.json()["numero_aocs"]

    # 2. Buscar por Número
    response_get = test_client.get(
        f"/api/aocs/numero/{numero_aocs}", # A rota usa /numero/
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["numero_aocs"] == numero_aocs

def test_update_aocs(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    """Testa PUT /api/aocs/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Atualizar (vamos mudar a justificativa e o empenho)
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
    # Verifica se o campo original (não enviado no update) permaneceu
    assert data["numero_aocs"] == "AOCS-001/2025-TESTE"

def test_delete_aocs(test_client: TestClient, admin_auth_headers: dict, aocs_payload: dict):
    """Testa DELETE /api/aocs/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/aocs/",
        json=aocs_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Deletar
    response_delete = test_client.delete(
        f"/api/aocs/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    # 3. Verificar (deve dar 404)
    response_get = test_client.get(
        f"/api/aocs/{new_id}",
        headers=admin_auth_headers
    )
    # Como você fez a Tarefa 1, este teste deve passar
    assert response_get.status_code == 404