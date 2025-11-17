import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture
def setup_contrato_com_item(test_client: TestClient, admin_auth_headers: dict) -> dict:
    contrato_payload = {
        "numero_contrato": "CT-PEDIDO-111/2025",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Fornecedor de Pedidos", "cpf_cnpj": "11.111.111/0001-11"},
        "categoria_nome": "Categoria de Pedidos",
        "instrumento_nome": "Instrumento de Pedidos",
        "modalidade_nome": "Modalidade de Pedidos",
        "numero_modalidade_str": "NumMod Pedidos",
        "processo_licitatorio_numero": "PL Pedidos"
    }
    response_contrato = test_client.post("/api/contratos/", json=contrato_payload, headers=admin_auth_headers)
    assert response_contrato.status_code == 201
    contrato_data = response_contrato.json()
    
    item_payload = {
        "numero_item": 1, "unidade_medida": "UN",
        "quantidade": 1000, 
        "valor_unitario": 50.0,
        "contrato_nome": contrato_data["numero_contrato"],
        "descricao": {"descricao": "Item de Teste para Pedido"}
    }
    response_item = test_client.post("/api/itens/", json=item_payload, headers=admin_auth_headers)
    assert response_item.status_code == 201
    item_data = response_item.json()

    return {"id_contrato": contrato_data["id"], "id_item": item_data["id"]}

@pytest.fixture
def setup_aocs(test_client: TestClient, admin_auth_headers: dict) -> dict:
    aocs_payload = {
        "numero_aocs": "AOCS-PEDIDO-222/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "AOCS para teste de pedidos",
        "unidade_requisitante_nome": "Unidade (Pedido)",
        "local_entrega_descricao": "Local (Pedido)",
        "agente_responsavel_nome": "Agente (Pedido)",
        "dotacao_info_orcamentaria": "Dotação (Pedido)"
    }
    response_aocs = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert response_aocs.status_code == 201
    aocs_data = response_aocs.json()
    
    return {"id_aocs": aocs_data["id"]}

def test_create_pedido_sucesso(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item: dict, setup_aocs: dict):
    id_item_com_saldo = setup_contrato_com_item["id_item"]
    id_aocs_criada = setup_aocs["id_aocs"]
    
    pedido_payload = {
        "item_contrato_id": id_item_com_saldo,
        "quantidade_pedida": 10.5,
        "id_aocs": id_aocs_criada 
    }

    response = test_client.post(
        f"/api/pedidos/?id_aocs={id_aocs_criada}", 
        json=pedido_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id_aocs"] == id_aocs_criada
    assert data["id_item_contrato"] == id_item_com_saldo
    assert float(data["quantidade_pedida"]) == 10.5
    assert data["status_entrega"] == "Pendente"

def test_create_pedido_sem_saldo(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item: dict, setup_aocs: dict):
    id_item_com_saldo = setup_contrato_com_item["id_item"]
    id_aocs_criada = setup_aocs["id_aocs"]
    
    pedido_payload = {
        "item_contrato_id": id_item_com_saldo,
        "quantidade_pedida": 2000,
        "id_aocs": id_aocs_criada 
    }

    response = test_client.post(
        f"/api/pedidos/?id_aocs={id_aocs_criada}",
        json=pedido_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 400
    assert "excede o saldo disponível" in response.json()["detail"]

def test_get_and_delete_pedido(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item: dict, setup_aocs: dict):
    payload_pedido = {
        "item_contrato_id": setup_contrato_com_item['id_item'], 
        "quantidade_pedida": 5,
        "id_aocs": setup_aocs['id_aocs'] 
    }
    response_create = test_client.post(
        f"/api/pedidos/?id_aocs={setup_aocs['id_aocs']}",
        json=payload_pedido,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id_pedido = response_create.json()["id"]

    response_get = test_client.get(f"/api/pedidos/{new_id_pedido}", headers=admin_auth_headers)
    assert response_get.status_code == 200
    assert response_get.json()["id"] == new_id_pedido

    response_delete = test_client.delete(f"/api/pedidos/{new_id_pedido}", headers=admin_auth_headers)
    assert response_delete.status_code == 204

    response_get_deleted = test_client.get(f"/api/pedidos/{new_id_pedido}", headers=admin_auth_headers)
    assert response_get_deleted.status_code == 404