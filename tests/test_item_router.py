import pytest
from fastapi.testclient import TestClient
from datetime import date

# O 'admin_auth_headers' é pego automaticamente do conftest.py

# --- Fixture de Preparação ---
@pytest.fixture
def setup_contrato(test_client: TestClient, admin_auth_headers: dict) -> dict:
    """
    Cria um Contrato "pai" no banco de teste e retorna o seu nome e ID.
    Isto é necessário para que possamos criar Itens.
    """
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


# --- Fixture de Dados (Payload do Item) ---
@pytest.fixture
def item_payload(setup_contrato: dict) -> dict:
    """
    Retorna um payload JSON válido para criar um Item,
    já usando o nome do contrato 'pai' que a fixture 'setup_contrato' criou.
    """
    return {
        "numero_item": 1,
        "marca": "Marca Teste",
        "unidade_medida": "UN",
        "quantidade": 100.50,
        "valor_unitario": 10.99,
        "contrato_nome": setup_contrato["nome"], # <-- Dependência chave
        "descricao": {
            "descricao": "Item de Teste 1"
        }
    }

# --- Testes do CRUD ---

def test_create_item(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    """Testa POST /api/itens/"""
    response = test_client.post(
        "/api/itens/", 
        json=item_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["descricao"]["descricao"] == "Item de Teste 1"
    assert data["id_contrato"] is not None # Prova que a associação funcionou

def test_get_item_by_id(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    """Testa GET /api/itens/{id}"""
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
    """Testa GET /api/itens?contrato_id=..."""
    # 1. Criar o item (ele já está associado ao 'setup_contrato')
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    id_contrato_pai = setup_contrato["id"]

    # 2. Buscar itens por esse ID de contrato
    response_get = test_client.get(
        f"/api/itens?contrato_id={id_contrato_pai}", 
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) == 1 # Deve retornar *apenas* 1 item
    assert data[0]["descricao"]["descricao"] == "Item de Teste 1"

def test_update_item(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    """Testa PUT /api/itens/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Atualizar (vamos mudar a descrição e a quantidade)
    # O payload de update é o mesmo do de create (ItemRequest)
    update_payload = item_payload.copy() # Copia o payload original
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
    assert float(data["quantidade"]) == 999.0 # Compara como float

def test_delete_item(test_client: TestClient, admin_auth_headers: dict, item_payload: dict):
    """Testa DELETE /api/itens/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/itens/",
        json=item_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Deletar
    response_delete = test_client.delete(
        f"/api/itens/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    # 3. Verificar (deve dar 404)
    response_get = test_client.get(
        f"/api/itens/{new_id}",
        headers=admin_auth_headers
    )
    # Como você fez a Tarefa 1, este teste deve passar
    assert response_get.status_code == 404