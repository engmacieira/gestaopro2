import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token 
from app.models.user_model import User
from datetime import date
from psycopg2.extensions import connection 

from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.contrato_repository import ContratoRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.aocs_repository import AocsRepository
from app.repositories.pedido_repository import PedidoRepository

from app.schemas.categoria_schema import CategoriaRequest
from app.schemas.contrato_schema import ContratoCreateRequest
from app.schemas.item_schema import ItemRequest
from app.schemas.descricao_item_schema import DescricaoItemRequest
from app.schemas.aocs_schema import AocsCreateRequest
from app.schemas.pedido_schema import PedidoCreateRequest
from app.models.fornecedor_vo import Fornecedor

@pytest.fixture
def admin_auth_headers(db_session): 
    
    from app.repositories.user_repository import UserRepository
    from app.schemas.user_schema import UserCreateRequest

    repo = UserRepository(db_session)
    user_data = UserCreateRequest(
        username="test_admin_user",
        password="password123",
        nivel_acesso=1, 
        ativo=True
    )
    try:
        admin_user = repo.create(user_data)
    except Exception as e:
        db_session.rollback()
        admin_user = repo.get_by_username("test_admin_user")
    
    token = create_access_token(admin_user)
    
    return {"Authorization": f"Bearer {token}"}


def test_create_categoria(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria de Teste 1"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201 
    data = response.json()
    assert data["nome"] == "Categoria de Teste 1"
    assert data["id"] is not None
    assert data["ativo"] is True

def test_get_categoria_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/categorias/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Categoria de Teste 2"
    assert data["id"] == new_id

def test_update_categoria(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria Original"},
        headers=admin_auth_headers
    )
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/categorias/{new_id}",
        json={"nome": "Categoria Atualizada"},
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Categoria Atualizada"
    assert data["id"] == new_id

def test_delete_categoria(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria Para Deletar"},
        headers=admin_auth_headers
    )
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/categorias/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/categorias/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 404 
    
def test_update_categoria(test_client: TestClient, admin_auth_headers: dict):
    payload_criar = {"nome": "Categoria Antiga para Update"}
    response_criar = test_client.post(
        "/api/categorias/", 
        json=payload_criar, 
        headers=admin_auth_headers
    )
    assert response_criar.status_code == 201
    id_da_categoria_criada = response_criar.json()["id"]
    
    payload_atualizar = {"nome": "Categoria ATUALIZADA"}
    response_atualizar = test_client.put(
        f"/api/categorias/{id_da_categoria_criada}",
        json=payload_atualizar,
        headers=admin_auth_headers
    )
    
    assert response_atualizar.status_code == 200
    assert response_atualizar.json()["nome"] == "Categoria ATUALIZADA"
    
    response_get = test_client.get(
        f"/api/categorias/{id_da_categoria_criada}", 
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    assert response_get.json()["nome"] == "Categoria ATUALIZADA"
    
@pytest.fixture
def categoria_para_testes(test_client: TestClient, admin_auth_headers: dict) -> dict:
    payload = {"nome": "Categoria para Testes (PUT, PATCH, DELETE)"}
    response = test_client.post("/api/categorias/", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
def categoria_com_dependencia(test_client: TestClient, admin_auth_headers: dict) -> int:
    nome_categoria = "Categoria Com Dependência"
    resp_cat = test_client.post("/api/categorias/", json={"nome": nome_categoria}, headers=admin_auth_headers)
    assert resp_cat.status_code == 201
    id_categoria = resp_cat.json()["id"]

    test_client.post("/api/instrumentos/", json={"nome": "Instrumento (Dep)"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade (Dep)"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "NumMod (Dep)"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL (Dep)"}, headers=admin_auth_headers)
    
    payload_contrato = {
        "numero_contrato": "CT-DEP-999/2025",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Fornecedor (Dep)", "cpf_cnpj": "99.999.999/0001-99"},
        "categoria_nome": nome_categoria, 
        "instrumento_nome": "Instrumento (Dep)",
        "modalidade_nome": "Modalidade (Dep)",
        "numero_modalidade_str": "NumMod (Dep)",
        "processo_licitatorio_numero": "PL (Dep)"
    }
    resp_contrato = test_client.post("/api/contratos/", json=payload_contrato, headers=admin_auth_headers)
    assert resp_contrato.status_code == 201
    
    return id_categoria

def test_update_categoria_happy_path(test_client: TestClient, admin_auth_headers: dict, categoria_para_testes: dict):
    id_categoria = categoria_para_testes["id"]
    payload_atualizar = {"nome": "Categoria Nome ATUALIZADO"}

    response = test_client.put(
        f"/api/categorias/{id_categoria}",
        json=payload_atualizar,
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["nome"] == "Categoria Nome ATUALIZADO"
    assert response.json()["id"] == id_categoria

def test_update_categoria_not_found(test_client: TestClient, admin_auth_headers: dict):
    payload_atualizar = {"nome": "Atualização Fantasma"}
    response = test_client.put(
        "/api/categorias/999999", 
        json=payload_atualizar,
        headers=admin_auth_headers
    )
    assert response.status_code == 404

def test_update_categoria_conflict(test_client: TestClient, admin_auth_headers: dict, categoria_para_testes: dict):
    payload_outra = {"nome": "Nome Único Existente"}
    resp_outra = test_client.post("/api/categorias/", json=payload_outra, headers=admin_auth_headers)
    assert resp_outra.status_code == 201

    id_categoria_original = categoria_para_testes["id"]

    payload_conflito = {"nome": "Nome Único Existente"}
    response = test_client.put(
        f"/api/categorias/{id_categoria_original}",
        json=payload_conflito,
        headers=admin_auth_headers
    )

    assert response.status_code == 409

def test_patch_status_categoria(test_client: TestClient, admin_auth_headers: dict, categoria_para_testes: dict):
    id_categoria = categoria_para_testes["id"]
    assert categoria_para_testes["ativo"] is True 

    response_desativar = test_client.patch(
        f"/api/categorias/status/{id_categoria}?ativo=false",
        headers=admin_auth_headers
    )
    assert response_desativar.status_code == 200
    assert response_desativar.json()["ativo"] is False

    response_ativar = test_client.patch(
        f"/api/categorias/status/{id_categoria}?ativo=true",
        headers=admin_auth_headers
    )
    assert response_ativar.status_code == 200
    assert response_ativar.json()["ativo"] is True

def test_patch_status_categoria_not_found(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.patch(
        "/api/categorias/status/999999?ativo=false",
        headers=admin_auth_headers
    )
    assert response.status_code == 404

def test_delete_categoria_happy_path(test_client: TestClient, admin_auth_headers: dict, categoria_para_testes: dict):
    id_categoria = categoria_para_testes["id"]
    
    response_delete = test_client.delete(
        f"/api/categorias/{id_categoria}", 
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/categorias/{id_categoria}", 
        headers=admin_auth_headers
    )
    assert response_get.status_code == 404 

def test_delete_categoria_not_found(test_client: TestClient, admin_auth_headers: dict):
    response_delete = test_client.delete(
        "/api/categorias/999999", 
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 404

def test_delete_categoria_conflict(test_client: TestClient, admin_auth_headers: dict, categoria_com_dependencia: int):
    id_categoria = categoria_com_dependencia 

    response_delete = test_client.delete(
        f"/api/categorias/{id_categoria}", 
        headers=admin_auth_headers
    )
    
    assert response_delete.status_code == 409
    
@pytest.fixture
def setup_scenario_saldo_item(db_session: connection) -> int:
    categoria_repo = CategoriaRepository(db_session)
    contrato_repo = ContratoRepository(db_session)
    item_repo = ItemRepository(db_session)
    aocs_repo = AocsRepository(db_session)
    pedido_repo = PedidoRepository(db_session)

    categoria = categoria_repo.get_or_create("Categoria Teste Saldo")
    
    contrato_repo.instrumento_repo.get_or_create("Instrumento (Saldo)")
    contrato_repo.modalidade_repo.get_or_create("Modalidade (Saldo)")
    contrato_repo.numeromodalidade_repo.get_or_create("NumMod (Saldo)")
    contrato_repo.processolicitatorio_repo.get_or_create("PL (Saldo)")
    
    contrato_req = ContratoCreateRequest(
        numero_contrato="CT-SALDO-100", data_inicio=date(2025,1,1), data_fim=date(2025,12,31),
        fornecedor={"nome": "Fornecedor (Saldo)", "cpf_cnpj": "10.100.100/0001-10"}, 
        categoria_nome="Categoria Teste Saldo",
        instrumento_nome="Instrumento (Saldo)", modalidade_nome="Modalidade (Saldo)",
        numero_modalidade_str="NumMod (Saldo)", processo_licitatorio_numero="PL (Saldo)"
    )
    contrato = contrato_repo.create(contrato_req)

    item_descricao = DescricaoItemRequest(descricao="Item para Cálculo de Saldo")
    item_req = ItemRequest(
        numero_item=1, unidade_medida="UN", quantidade=100, valor_unitario=10.0,
        contrato_nome="CT-SALDO-100",
        descricao=item_descricao 
    )
    item = item_repo.create(item_req)

    aocs_repo.unidade_repo.get_or_create("Unidade (Saldo)")
    aocs_repo.local_repo.get_or_create("Local (Saldo)")
    aocs_repo.agente_repo.get_or_create("Agente (Saldo)")
    aocs_repo.dotacao_repo.get_or_create("Dotacao (Saldo)")
    
    aocs_req = AocsCreateRequest(
        numero_aocs="AOCS-SALDO-10", data_criacao=date.today(), justificativa="Teste de saldo",
        unidade_requisitante_nome="Unidade (Saldo)", local_entrega_descricao="Local (Saldo)",
        agente_responsavel_nome="Agente (Saldo)", dotacao_info_orcamentaria="Dotacao (Saldo)"
    )
    aocs = aocs_repo.create(aocs_req)

    pedido_req = PedidoCreateRequest(
        item_contrato_id=item.id, 
        quantidade_pedida=10,
        id_aocs=aocs.id 
    )
    
    pedido = pedido_repo.create(id_aocs=aocs.id, pedido_create_req=pedido_req)

    return categoria.id 


def test_get_itens_com_saldo_por_categoria(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_scenario_saldo_item: int, 
    db_session: connection 
):

    id_categoria = setup_scenario_saldo_item

    response = test_client.get(
        f"/api/categorias/{id_categoria}/itens",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    
    assert "itens" in data
    assert "total_paginas" in data
    assert data["total_paginas"] == 1
    assert len(data["itens"]) == 1

    item_na_lista = data["itens"][0]
    assert item_na_lista["descricao"]["descricao"] == "Item para Cálculo de Saldo"
    assert item_na_lista["quantidade"] == "100.000" 
    assert item_na_lista["total_pedido"] == "10.000"
    assert item_na_lista["saldo"] == "90.000"