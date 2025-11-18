import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture
def setup_dependencias(test_client: TestClient, admin_auth_headers: dict):
    test_client.post("/api/categorias/", json={"nome": "Obras e Serviços"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Contrato de Teste"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Pregão Eletrônico"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "PE 123/2024"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL 456/2024"}, headers=admin_auth_headers)
    
    return {
        "categoria": "Obras e Serviços",
        "instrumento": "Contrato de Teste",
        "modalidade": "Pregão Eletrônico",
        "num_modalidade": "PE 123/2024",
        "processo": "PL 456/2024"
    }

@pytest.fixture
def contrato_payload(setup_dependencias: dict) -> dict:
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
        "categoria_nome": setup_dependencias["categoria"],
        "instrumento_nome": setup_dependencias["instrumento"],
        "modalidade_nome": setup_dependencias["modalidade"],
        "numero_modalidade_str": setup_dependencias["num_modalidade"],
        "processo_licitatorio_numero": setup_dependencias["processo"]
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
    assert data["id_categoria"] is not None 
    assert data["id_instrumento_contratual"] is not None

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
    assert data["numero_contrato"] == contrato_payload["numero_contrato"]

def test_get_all_contratos(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    test_client.post("/api/contratos/", json=contrato_payload, headers=admin_auth_headers)

    response_get = test_client.get("/api/contratos/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["numero_contrato"] == contrato_payload["numero_contrato"] for c in data)

def test_update_contrato(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    response_create = test_client.post(
        "/api/contratos/",
        json=contrato_payload,
        headers=admin_auth_headers
    )
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

def test_delete_contrato(test_client: TestClient, admin_auth_headers: dict, contrato_payload: dict):
    response_create = test_client.post(
        "/api/contratos/",
        json=contrato_payload,
        headers=admin_auth_headers
    )
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

def test_create_contrato_duplicado_409(
    test_client: TestClient, 
    admin_auth_headers: dict,
    contrato_payload: dict 
):
    payload_dup = contrato_payload.copy()
    payload_dup["numero_contrato"] = "CT-DUPLICADO-UNIQUE/2025"

    response_create1 = test_client.post("/api/contratos/", json=payload_dup, headers=admin_auth_headers)
    assert response_create1.status_code == 201

    response_create2 = test_client.post("/api/contratos/", json=payload_dup, headers=admin_auth_headers)
    
    assert response_create2.status_code == 409

def test_create_contrato_dependencia_invalida_400(
    test_client: TestClient, 
    admin_auth_headers: dict,
    setup_dependencias: dict 
):

    payload_invalido = {
        "numero_contrato": "CT-FALHA-FK/2025",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Forn", "cpf_cnpj": "00.000.000/0001-00"},
        
        "categoria_nome": "CATEGORIA_QUE_NAO_EXISTE_NO_BANCO", 
        
        "instrumento_nome": setup_dependencias["instrumento"],
        "modalidade_nome": setup_dependencias["modalidade"],
        "numero_modalidade_str": setup_dependencias["num_modalidade"],
        "processo_licitatorio_numero": setup_dependencias["processo"]
    }
    
    response = test_client.post("/api/contratos/", json=payload_invalido, headers=admin_auth_headers)
    
    assert response.status_code == 400

def test_get_contrato_by_id_not_found(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.get(f"/api/contratos/999999", headers=admin_auth_headers)
    assert response.status_code == 404

def test_update_contrato_not_found(test_client: TestClient, admin_auth_headers: dict):
    payload = {"fornecedor": {"nome": "Fantasma"}}
    response = test_client.put(f"/api/contratos/999999", json=payload, headers=admin_auth_headers)
    assert response.status_code == 404

def test_delete_contrato_not_found(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.delete(f"/api/contratos/999999", headers=admin_auth_headers)
    assert response.status_code == 404