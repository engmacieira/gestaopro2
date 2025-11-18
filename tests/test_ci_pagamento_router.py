import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal
from psycopg2.extensions import connection 

from app.schemas.pedido_schema import PedidoCreateRequest
from app.schemas.contrato_schema import ContratoCreateRequest
from app.schemas.item_schema import ItemRequest
from app.schemas.descricao_item_schema import DescricaoItemRequest
from app.schemas.ci_pagamento_schema import CiPagamentoCreateRequest, CiPagamentoUpdateRequest

@pytest.fixture
def setup_pedido_pronto(
    db_session: connection, 
    test_client: TestClient, 
    admin_auth_headers: dict
) -> dict:
    
    resp_agente = test_client.post("/api/agentes/", json={"nome": "Solicitante Teste CI"}, headers=admin_auth_headers)
    assert resp_agente.status_code == 201
    
    resp_unidade = test_client.post("/api/unidades/", json={"nome": "Secretaria Teste CI"}, headers=admin_auth_headers)
    assert resp_unidade.status_code == 201
    
    resp_dotacao = test_client.post(
        "/api/dotacoes/", 
        json={"info_orcamentaria": "Dotacao Teste CI"},  
        headers=admin_auth_headers
    )
    assert resp_dotacao.status_code == 201

    resp_local = test_client.post("/api/locais/", json={"descricao": "Local Teste CI"}, headers=admin_auth_headers)
    assert resp_local.status_code == 201

    test_client.post("/api/categorias/", json={"nome": "Categoria Teste CI"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Instrumento Teste CI"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade Teste CI"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "NumMod Teste CI"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL Teste CI"}, headers=admin_auth_headers)

    contrato_payload = ContratoCreateRequest(
        numero_contrato="CT-TESTE-CI-123",
        data_inicio=date(2025, 1, 1),
        data_fim=date(2025, 12, 31),
        fornecedor={"nome": "Fornecedor Teste CI", "cpf_cnpj": "12.345.678/0001-99"},
        categoria_nome="Categoria Teste CI",
        instrumento_nome="Instrumento Teste CI",
        modalidade_nome="Modalidade Teste CI",
        numero_modalidade_str="NumMod Teste CI",
        processo_licitatorio_numero="PL Teste CI"
    )
    resp_contrato = test_client.post("/api/contratos/", json=contrato_payload.model_dump(mode="json"), headers=admin_auth_headers)
    assert resp_contrato.status_code == 201
    contrato = resp_contrato.json()

    item_payload = ItemRequest(
        numero_item=1,
        unidade_medida="UN",
        quantidade=1000,
        valor_unitario=Decimal("10.0"),
        contrato_nome="CT-TESTE-CI-123",
        descricao=DescricaoItemRequest(descricao="Item para Teste CI")
    )
    resp_item = test_client.post("/api/itens/", json=item_payload.model_dump(mode="json"), headers=admin_auth_headers)
    assert resp_item.status_code == 201
    item = resp_item.json()

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
    aocs = resp_aocs.json()

    pedido_req = PedidoCreateRequest(
        item_contrato_id=item["id"],
        quantidade_pedida=Decimal("50.0"),
        id_aocs=aocs["id"]
    )
    pedido_payload_json = pedido_req.model_dump(mode="json")
    
    resp_pedido = test_client.post(
        f"/api/pedidos/?id_aocs={aocs['id']}", 
        json=pedido_payload_json,
        headers=admin_auth_headers
    )
    assert resp_pedido.status_code == 201, f"Falha ao criar Pedido no setup: {resp_pedido.json()}"
    novo_pedido = resp_pedido.json()

    return {
        "id_pedido": novo_pedido["id"], 
        "id_aocs": aocs["id"],
        "aocs_data": aocs_payload
    }


@pytest.fixture
def setup_ci_pronta(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_pedido_pronto: dict
) -> dict:

    id_pedido = setup_pedido_pronto["id_pedido"]
    aocs_data = setup_pedido_pronto["aocs_data"]
    
    ci_data_payload = {
        "numero_ci": "CI-TESTE-123",
        "data_ci": date.today().isoformat(),
        "valor": "100.50",
        "observacao": "Observação de teste",
        "numero_nota_fiscal": "NF-12345",
        "data_nota_fiscal": (date.today() - timedelta(days=5)).isoformat(),
        "valor_nota_fiscal": "100.50",
        "aocs_numero": aocs_data["numero_aocs"],
        "solicitante_nome": aocs_data["agente_responsavel_nome"],
        "secretaria_nome": aocs_data["unidade_requisitante_nome"],
        "dotacao_info_orcamentaria": aocs_data["dotacao_info_orcamentaria"]
    }
    
    response = test_client.post(
        f"/api/ci-pagamento/?id_pedido={id_pedido}",
        json=ci_data_payload,  
        headers=admin_auth_headers
    )
    assert response.status_code == 201, f"Falha ao criar CI na fixture 'setup_ci_pronta': {response.json()}"
    ci_criada = response.json()
    
    return {
        "id_ci": ci_criada["id"],
        "id_pedido": id_pedido
    }

def test_create_ci_pagamento_sucesso(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_pedido_pronto: dict 
):
    id_pedido = setup_pedido_pronto["id_pedido"]
    aocs_data = setup_pedido_pronto["aocs_data"]

    ci_payload = CiPagamentoCreateRequest(
        numero_ci="CI-TESTE-999",
        data_ci=date.today(),
        valor=Decimal("999.99"),
        observacao="Teste de criação sucesso",
        
        numero_nota_fiscal="NF-999",
        data_nota_fiscal=date.today(),
        valor_nota_fiscal=Decimal("999.99"),
        
        aocs_numero=aocs_data["numero_aocs"],
        solicitante_nome=aocs_data["agente_responsavel_nome"],
        secretaria_nome=aocs_data["unidade_requisitante_nome"],
        dotacao_info_orcamentaria=aocs_data["dotacao_info_orcamentaria"]
    )
    
    response = test_client.post(
        f"/api/ci-pagamento/?id_pedido={id_pedido}",
        json=ci_payload.model_dump(mode="json"), 
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["numero_ci"] == "CI-TESTE-999"
    assert data["id_pedido"] == id_pedido

def test_create_ci_pagamento_duplicado(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_ci_pronta: dict, 
    setup_pedido_pronto: dict 
):
    id_pedido = setup_ci_pronta["id_pedido"] 
    
    aocs_data = setup_pedido_pronto["aocs_data"]

    ci_payload_duplicado = CiPagamentoCreateRequest(
        numero_ci="CI-TESTE-123", 
        
        data_ci=date.today(),
        valor=Decimal("50.00"),
        observacao="Tentativa de duplicar",
        numero_nota_fiscal="NF-DUP-VALIDA", 
        data_nota_fiscal=date.today(),
        valor_nota_fiscal=Decimal("50.00"),
        
        aocs_numero=aocs_data["numero_aocs"],
        solicitante_nome=aocs_data["agente_responsavel_nome"],
        secretaria_nome=aocs_data["unidade_requisitante_nome"],
        dotacao_info_orcamentaria=aocs_data["dotacao_info_orcamentaria"]
    )
    
    response = test_client.post(
        f"/api/ci-pagamento/?id_pedido={id_pedido}",
        json=ci_payload_duplicado.model_dump(mode="json"), 
        headers=admin_auth_headers
    )
    
    assert response.status_code == 409

def test_get_all_ci_pagamentos(
    test_client: TestClient, 
    admin_auth_headers: dict,
    setup_ci_pronta: dict 
):
    response = test_client.get("/api/ci-pagamento/", headers=admin_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(item["numero_ci"] == "CI-TESTE-123" for item in data)

def test_get_ci_by_id(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_ci_pronta: dict
):
    id_ci_criada = setup_ci_pronta["id_ci"]
    
    response = test_client.get(
        f"/api/ci-pagamento/{id_ci_criada}", 
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == id_ci_criada
    assert data["numero_ci"] == "CI-TESTE-123"
    assert data["valor_nota_fiscal"] == "100.50"

def test_get_ci_by_pedido_id(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_ci_pronta: dict
):
    id_pedido = setup_ci_pronta["id_pedido"]
    
    response = test_client.get(
        f"/api/ci-pagamento/por-pedido/{id_pedido}", 
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id_pedido"] == id_pedido
    assert data["numero_ci"] == "CI-TESTE-123"

def test_update_ci_pagamento(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_ci_pronta: dict
):
    id_ci_criada = setup_ci_pronta["id_ci"]
    
    update_payload = CiPagamentoUpdateRequest(
        numero_ci="CI-TESTE-ATUALIZADA",
        valor_nota_fiscal=Decimal("200.00"),
        observacao="CI foi atualizada"
    )
    
    response = test_client.put(
        f"/api/ci-pagamento/{id_ci_criada}",
        json=update_payload.model_dump(mode="json"),
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == id_ci_criada
    assert data["numero_ci"] == "CI-TESTE-ATUALIZADA"
    assert data["valor_nota_fiscal"] == "200.00" 

def test_delete_ci_pagamento(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_ci_pronta: dict
):
    id_ci_criada = setup_ci_pronta["id_ci"]
    
    response_delete = test_client.delete(
        f"/api/ci-pagamento/{id_ci_criada}", 
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204
    
    response_get = test_client.get(
        f"/api/ci-pagamento/{id_ci_criada}", 
        headers=admin_auth_headers
    )
    assert response_get.status_code == 404