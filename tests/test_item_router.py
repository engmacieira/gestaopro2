import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture
def setup_contrato(test_client: TestClient, admin_auth_headers: dict) -> dict:
    test_client.post("/api/categorias/", json={"nome": "Categoria Padrão de Itens"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Instrumento Padrão"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade Padrão"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "NumMod Padrão"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL Padrão"}, headers=admin_auth_headers)
    payload = {
        "numero_contrato": "CT-PAI-999/2025",
        "data_inicio": "2025-01-01",
        "data_fim": "2025-12-31",
        "fornecedor": {
            "nome": "Fornecedor Padrão de Itens",
            "cpf_cnpj": "00.000.000/0001-00" 
        },
        "categoria_nome": "Categoria Padrão de Itens",
        "instrumento_nome": "Instrumento Padrão",
        "modalidade_nome": "Modalidade Padrão",
        "numero_modalidade_str": "NumMod Padrão",
        "processo_licitatorio_numero": "PL Padrão"
    }
    response = test_client.post("/api/contratos/", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201, "Falha ao criar o Contrato 'pai' para o teste de item."
    data = response.json()
    return {"id": data["id"], "nome": data["numero_contrato"]}

@pytest.fixture
def item_payload(setup_contrato: dict) -> dict:
    return {
        "numero_item": 1,
        "marca": "Marca Teste",
        "unidade_medida": "UN",
        "quantidade": 100.50,
        "valor_unitario": 10.99,
        "contrato_nome": setup_contrato["nome"], 
        "descricao": {
            "descricao": "Item de Teste 1"
        }
    }

def test_create_item(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    response = test_client.post(
        "/api/itens/", 
        json=item_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["descricao"]["descricao"] == "Item de Teste 1"
    assert data["id_contrato"] is not None 

def test_get_item_by_id(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/itens/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["descricao"]["descricao"] == "Item de Teste 1"

def test_get_itens_por_contrato(test_client: TestClient, admin_auth_headers: dict, item_payload: dict, setup_contrato: dict):
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    id_contrato_pai = setup_contrato["id"]

    response_get = test_client.get(
        f"/api/itens?contrato_id={id_contrato_pai}", 
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) == 1 
    assert data[0]["descricao"]["descricao"] == "Item de Teste 1"

def test_update_item(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    update_payload = item_payload.copy() 
    update_payload["descricao"]["descricao"] = "Item ATUALIZADO"
    update_payload["quantidade"] = 999.0
    
    response_put = test_client.put(
        f"/api/itens/{new_id}",
        json=update_payload,
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["descricao"]["descricao"] == "Item ATUALIZADO"
    assert float(data["quantidade"]) == 999.0 

def test_delete_item(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/itens/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/itens/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 404