import pytest
from fastapi.testclient import TestClient

# Não precisamos importar o 'admin_auth_headers' ou as dependências dele aqui.
# O Pytest vai encontrá-lo automaticamente no 'conftest.py'.

# --- Testes do CRUD de Agentes ---

def test_create_agente(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa a criação de um novo agente.
    Endpoint: POST /api/agentes/
    """
    response = test_client.post(
        "/api/agentes/", # URL do agente_router (com a barra)
        json={"nome": "Agente de Teste 1"}, # Payload do AgenteRequest
        headers=admin_auth_headers
    )
    
    # Verificações
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Agente de Teste 1"
    assert data["id"] is not None

def test_get_agente_by_id(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa a busca de um agente por ID.
    Endpoint: GET /api/agentes/{id}
    """
    # 1. Criar um agente
    response_create = test_client.post(
        "/api/agentes/",
        json={"nome": "Agente de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Buscar o agente
    response_get = test_client.get(
        f"/api/agentes/{new_id}",
        headers=admin_auth_headers
    )
    
    # Verificações
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Agente de Teste 2"
    assert data["id"] == new_id

def test_get_all_agentes(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa a listagem de todos os agentes.
    Endpoint: GET /api/agentes/
    """
    # 1. Criar alguns agentes para garantir que a lista não esteja vazia
    response1 = test_client.post("/api/agentes/", json={"nome": "Agente A"}, headers=admin_auth_headers)
    response2 = test_client.post("/api/agentes/", json={"nome": "Agente B"}, headers=admin_auth_headers)
    assert response1.status_code == 201
    assert response2.status_code == 201

    # 2. Buscar a lista
    response_get = test_client.get("/api/agentes/", headers=admin_auth_headers)
    
    # Verificações
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list) # Deve ser uma lista
    assert len(data) >= 2 # Deve ter pelo menos os 2 que criamos
    assert "Agente A" in [item["nome"] for item in data]
    assert "Agente B" in [item["nome"] for item in data]

def test_update_agente(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa a atualização de um agente.
    Endpoint: PUT /api/agentes/{id}
    """
    # 1. Criar
    response_create = test_client.post(
        "/api/agentes/",
        json={"nome": "Agente Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Atualizar
    response_put = test_client.put(
        f"/api/agentes/{new_id}",
        json={"nome": "Agente Atualizado"}, # Payload do AgenteRequest
        headers=admin_auth_headers
    )
    
    # Verificações
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Agente Atualizado"
    assert data["id"] == new_id

def test_delete_agente(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa a deleção de um agente.
    Endpoint: DELETE /api/agentes/{id}
    """
    # 1. Criar
    response_create = test_client.post(
        "/api/agentes/",
        json={"nome": "Agente Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Deletar
    response_delete = test_client.delete(
        f"/api/agentes/{new_id}",
        headers=admin_auth_headers
    )
    
    # Verificação 1: Resposta 204 (No Content)
    assert response_delete.status_code == 204 

    # 3. Tentar buscar (deve falhar com 404)
    response_get = test_client.get(
        f"/api/agentes/{new_id}",
        headers=admin_auth_headers
    )
    
    # Verificação 2: Resposta 404 (Not Found)
    assert response_get.status_code == 404