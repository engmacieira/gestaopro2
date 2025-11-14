import pytest
from fastapi.testclient import TestClient
from datetime import date

# O 'admin_auth_headers' é pego automaticamente do conftest.py

# --- Fixture de Preparação ---
@pytest.fixture
def setup_ci_dependencies(test_client: TestClient, admin_auth_headers: dict) -> dict:
    """
    Cria todas as entidades necessárias (AOCS, Agente, Unidade, Dotação)
    para que uma CI possa ser criada, pois o repositório NÃO usa get_or_create.
    """
    # 1. Criar Agente (Solicitante)
    resp_agente = test_client.post("/api/agentes/", json={"nome": "Solicitante Teste CI"}, headers=admin_auth_headers)
    assert resp_agente.status_code == 201
    
    # 2. Criar Unidade (Secretaria)
    resp_unidade = test_client.post("/api/unidades/", json={"nome": "Secretaria Teste CI"}, headers=admin_auth_headers)
    assert resp_unidade.status_code == 201
    
    # 3. Criar Dotação
    resp_dotacao = test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotacao Teste CI"}, headers=admin_auth_headers)
    assert resp_dotacao.status_code == 201

    # 4. Criar AOCS (que usa get_or_create, mas vamos criar as dependências acima primeiro)
    aocs_payload = {
        "numero_aocs": "AOCS-CI-TESTE-333/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "AOCS para teste de CI",
        "unidade_requisitante_nome": "Secretaria Teste CI",
        "local_entrega_descricao": "Local Teste CI", # Esta pode ser criada automaticamente
        "agente_responsavel_nome": "Solicitante Teste CI",
        "dotacao_info_orcamentaria": "Dotacao Teste CI"
    }
    resp_aocs = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert resp_aocs.status_code == 201
    
    # Retorna os nomes exatos que o create_ci espera
    return {
        "aocs_numero": "AOCS-CI-TESTE-333/2025",
        "solicitante_nome": "Solicitante Teste CI",
        "secretaria_nome": "Secretaria Teste CI",
        "dotacao_info_orcamentaria": "Dotacao Teste CI"
    }

# --- Fixture de Dados (Payload da CI) ---
@pytest.fixture
def ci_payload(setup_ci_dependencies: dict) -> dict:
    """
    Retorna um payload JSON válido para criar uma CI,
    usando os nomes das dependências criadas na fixture anterior.
    """
    payload = {
        "numero_ci": "CI-999/2025",
        "data_ci": "2025-11-14",
        "numero_nota_fiscal": "NF-12345",
        "data_nota_fiscal": "2025-11-10",
        "valor_nota_fiscal": 1500.75
    }
    # Junta o payload base com as dependências
    payload.update(setup_ci_dependencies)
    return payload

# --- Testes do CRUD ---

def test_create_ci_pagamento(test_client: TestClient, admin_auth_headers: dict, ci_payload: dict):
    """Testa POST /api/ci-pagamento/"""
    response = test_client.post(
        "/api/ci-pagamento/", 
        json=ci_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["numero_ci"] == "CI-999/2025"
    assert data["id_solicitante"] is not None # Prova que a FK foi resolvida
    assert data["id_aocs"] is not None # Prova que a FK foi resolvida

def test_get_ci_pagamento_by_id(test_client: TestClient, admin_auth_headers: dict, ci_payload: dict):
    """Testa GET /api/ci-pagamento/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/ci-pagamento/",
        json=ci_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Buscar por ID
    response_get = test_client.get(
        f"/api/ci-pagamento/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["numero_ci"] == "CI-999/2025"

def test_delete_ci_pagamento(test_client: TestClient, admin_auth_headers: dict, ci_payload: dict):
    """Testa DELETE /api/ci-pagamento/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/ci-pagamento/",
        json=ci_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Deletar
    response_delete = test_client.delete(
        f"/api/ci-pagamento/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    # 3. Verificar (deve dar 404)
    response_get = test_client.get(
        f"/api/ci-pagamento/{new_id}",
        headers=admin_auth_headers
    )
    # Graças à Tarefa 1, este assert deve passar
    assert response_get.status_code == 404