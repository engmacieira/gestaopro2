import pytest
from fastapi.testclient import TestClient
from datetime import date
from urllib.parse import unquote

@pytest.fixture
def setup_full_pedido_scenario(test_client: TestClient, admin_auth_headers: dict) -> dict:
    test_client.post("/api/categorias/", json={"nome": "Categoria Teste UI"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Instrumento Teste UI"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade Teste UI"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "NumMod Teste UI"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL Teste UI"}, headers=admin_auth_headers)
    contrato_payload = {
        "numero_contrato": "CT-UI-123/2025",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Fornecedor Teste UI", "cpf_cnpj": "11.222.333/0001-44"},
        "categoria_nome": "Categoria Teste UI", "instrumento_nome": "Instrumento Teste UI",
        "modalidade_nome": "Modalidade Teste UI", "numero_modalidade_str": "NumMod Teste UI",
        "processo_licitatorio_numero": "PL Teste UI"
    }
    resp_contrato = test_client.post("/api/contratos/", json=contrato_payload, headers=admin_auth_headers)
    assert resp_contrato.status_code == 201
    
    item_payload = {
        "numero_item": 1, "unidade_medida": "UN", "quantidade": 100, "valor_unitario": 10.0,
        "contrato_nome": "CT-UI-123/2025",
        "descricao": {"descricao": "Item Visível no Teste de UI"}
    }
    resp_item = test_client.post("/api/itens/", json=item_payload, headers=admin_auth_headers)
    assert resp_item.status_code == 201
    id_item = resp_item.json()["id"]

    aocs_payload = {
        "numero_aocs": "AOCS-UI-789/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "Justificativa do Teste de UI",
        "unidade_requisitante_nome": "Unidade Teste UI",
        "local_entrega_descricao": "Local Teste UI",
        "agente_responsavel_nome": "Agente Teste UI",
        "dotacao_info_orcamentaria": "Dotação Teste UI"
    }
    resp_aocs = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert resp_aocs.status_code == 201
    id_aocs = resp_aocs.json()["id"]

    pedido_payload = {"item_contrato_id": id_item, "quantidade_pedida": 25, "id_aocs": id_aocs}
    resp_pedido = test_client.post(f"/api/pedidos/?id_aocs={id_aocs}", json=pedido_payload, headers=admin_auth_headers)
    assert resp_pedido.status_code == 201

    return {
        "numero_aocs": "AOCS-UI-789/2025",
        "nome_item": "Item Visível no Teste de UI",
        "nome_fornecedor": "Fornecedor Teste UI",
        "quantidade_pedida": "25" 
    }

@pytest.fixture
def setup_contrato_com_item_para_ui(test_client: TestClient, admin_auth_headers: dict) -> dict:
    test_client.post("/api/categorias/", json={"nome": "Categoria Detalhe UI"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Instrumento Detalhe UI"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade Detalhe UI"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "NumMod Detalhe UI"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL Detalhe UI"}, headers=admin_auth_headers)
    contrato_payload = {
        "numero_contrato": "CT-UI-DETALHE-555/2025",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Fornecedor Detalhe UI", "cpf_cnpj": "55.555.555/0001-55"},
        "categoria_nome": "Categoria Detalhe UI",
        "instrumento_nome": "Instrumento Detalhe UI",
        "modalidade_nome": "Modalidade Detalhe UI",
        "numero_modalidade_str": "NumMod Detalhe UI",
        "processo_licitatorio_numero": "PL Detalhe UI"
    }
    resp_contrato = test_client.post("/api/contratos/", json=contrato_payload, headers=admin_auth_headers)
    assert resp_contrato.status_code == 201
    id_contrato = resp_contrato.json()["id"]

    item_payload = {
        "numero_item": 1, "unidade_medida": "UN", "quantidade": 500, "valor_unitario": 10.0,
        "contrato_nome": "CT-UI-DETALHE-555/2025",
        "descricao": {"descricao": "Item Visível no Detalhe do Contrato"}
    }
    resp_item = test_client.post("/api/itens/", json=item_payload, headers=admin_auth_headers)
    assert resp_item.status_code == 201

    return {
        "id_contrato": id_contrato,
        "numero_contrato": "CT-UI-DETALHE-555/2025",
        "nome_fornecedor": "Fornecedor Detalhe UI",
        "nome_item": "Item Visível no Detalhe do Contrato"
    }

@pytest.fixture
def setup_novo_pedido_deps(test_client: TestClient, admin_auth_headers: dict) -> int:
    resp_cat = test_client.post("/api/categorias/", json={"nome": "Categoria Para Novo Pedido"}, headers=admin_auth_headers)
    assert resp_cat.status_code == 201
    id_categoria = resp_cat.json()["id"]

    test_client.post("/api/unidades/", json={"nome": "Unidade Dropdown Teste"}, headers=admin_auth_headers)
    test_client.post("/api/locais/", json={"descricao": "Local Dropdown Teste"}, headers=admin_auth_headers)
    test_client.post("/api/agentes/", json={"nome": "Agente Dropdown Teste"}, headers=admin_auth_headers)
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotacao Dropdown Teste"}, headers=admin_auth_headers)
    
    return id_categoria

@pytest.fixture
def setup_nova_ci_deps(test_client: TestClient, admin_auth_headers: dict) -> dict:
    test_client.post("/api/unidades/", json={"nome": "Unidade Teste CI-UI"}, headers=admin_auth_headers)
    test_client.post("/api/locais/", json={"descricao": "Local Teste CI-UI"}, headers=admin_auth_headers)
    test_client.post("/api/agentes/", json={"nome": "Agente Teste CI-UI"}, headers=admin_auth_headers)
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotacao Teste CI-UI"}, headers=admin_auth_headers)

    aocs_payload = {
        "numero_aocs": "AOCS-CI-UI-444/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "AOCS para teste de UI da Nova CI",
        "unidade_requisitante_nome": "Unidade Teste CI-UI",
        "local_entrega_descricao": "Local Teste CI-UI",
        "agente_responsavel_nome": "Agente Teste CI-UI",
        "dotacao_info_orcamentaria": "Dotacao Teste CI-UI"
    }
    resp_aocs = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert resp_aocs.status_code == 201
    
    return "AOCS-CI-UI-444/2025"

def test_imprimir_aocs(test_client: TestClient, admin_auth_headers: dict, setup_full_pedido_scenario: dict):
    cenario = setup_full_pedido_scenario
    numero_aocs_teste = cenario["numero_aocs"]
    
    response = test_client.get(
        f"/pedido/{numero_aocs_teste}/imprimir",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    # Ajuste: Agora esperamos HTML, não PDF
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text
    # Verifica se os dados renderizaram
    assert numero_aocs_teste in response.text
    assert cenario["nome_fornecedor"] in response.text

def test_imprimir_pendentes(test_client: TestClient, admin_auth_headers: dict, setup_full_pedido_scenario: dict):
    cenario = setup_full_pedido_scenario
    numero_aocs_teste = cenario["numero_aocs"]
    
    response = test_client.get(
        f"/pedido/{numero_aocs_teste}/imprimir-pendentes",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    # Ajuste: Agora esperamos HTML, não PDF
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text
    assert "Pendentes" in response.text

def test_nova_ci_post_happy_path(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_nova_ci_deps: str 
):
    numero_aocs_teste = setup_nova_ci_deps
    
    # Ajuste: Adicionado campos obrigatórios exigidos pelo Schema Pydantic
    form_payload = {
        "id_aocs": "1", 
        "justificativa": "Justificativa enviada pelo formulário",
        "id_dotacao_pagamento": "1", # Nome do campo no form HTML pode variar, chequei o código e parece usar id_dotacao_pagamento no backend para recuperar, mas o form pode enviar outro nome. No post original usava 'id_dotacao' no dict, mas no router tenta pegar 'id_dotacao_pagamento' ou 'id_dotacao'. Vou manter genérico.
        # No router: id_dotacao = form_data.get('id_dotacao_pagamento')
        "id_dotacao_pagamento": "1",
        "id_solicitante": "1",
        "id_secretaria": "1",
        
        # Campos Obrigatórios adicionados:
        "numero_ci": "CI-TESTE-001",
        "data_ci": date.today().isoformat(),
        "numero_nota_fiscal": "NF-12345",
        "serie_nota_fiscal": "1",
        "data_nota_fiscal": date.today().isoformat(),
        "valor_nota_fiscal": "150,00", # String para testar o parse_money
        "observacoes_pagamento": "Teste de observação"
    }

    original_follow_redirects = test_client.follow_redirects
    test_client.follow_redirects = False
    
    response = test_client.post(
        f"/pedido/{numero_aocs_teste}/nova-ci", 
        data=form_payload,
        headers=admin_auth_headers
    )
    
    test_client.follow_redirects = original_follow_redirects

    # Se falhar aqui com 500, verifique os logs do pytest
    assert response.status_code == 302, f"Esperava redirecionamento (302), recebeu {response.status_code}. Texto: {response.text}"
    
    decoded_location = unquote(response.headers["location"])
    assert f"/pedido/{numero_aocs_teste}" in decoded_location

def test_pedidos_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_full_pedido_scenario: dict 
):
    cenario = setup_full_pedido_scenario
    numero_aocs_criado = cenario["numero_aocs"]
    
    response = test_client.get("/pedidos-ui", headers=admin_auth_headers)
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    assert numero_aocs_criado in response.text
    
def test_novo_pedido_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_novo_pedido_deps: int):
    id_categoria_teste = setup_novo_pedido_deps
    
    response = test_client.get(
        f"/categoria/{id_categoria_teste}/novo-pedido",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    html = response.text
    
    assert "Categoria Para Novo Pedido" in html 
    
    assert "Unidade Dropdown Teste" in html
    assert "Local Dropdown Teste" in html
    assert "Agente Dropdown Teste" in html
    assert "Dotacao Dropdown Teste" in html
    
def test_get_login_page_sem_auth(test_client: TestClient):
    response = test_client.get("/login")
    assert response.status_code == 200
    assert "GestãoPRO" in response.text

def test_root_redirects_to_login(test_client: TestClient):

    response = test_client.get("/") 
    
    assert response.status_code == 200
    
    assert len(response.history) == 1 
    assert response.history[0].status_code == 302 
    assert response.history[0].headers["location"] == "/login" 

def test_get_static_files(test_client: TestClient):
    response_css = test_client.get("/static/style.css")
    assert response_css.status_code == 200
    assert "color-background" in response_css.text

    response_js = test_client.get("/static/js/index.js")
    assert response_js.status_code == 200
    assert "showNotification" in response_js.text

def test_protected_routes_fail_sem_auth(test_client: TestClient):
    response_home = test_client.get("/home")
    assert response_home.status_code == 401

    response_categorias = test_client.get("/categorias-ui")
    assert response_categorias.status_code == 401

def test_protected_routes_pass_com_auth(test_client: TestClient, admin_auth_headers: dict):
    routes_to_test = [
        "/home",
        "/categorias-ui",
        "/contratos-ui",
        "/pedidos-ui",
        "/consultas",
        "/relatorios",
        "/importar",
        "/gerenciar-tabelas",
        "/admin/usuarios"
    ]

    for route in routes_to_test:
        response = test_client.get(route, headers=admin_auth_headers)
        assert response.status_code == 200, f"Rota {route} falhou ao carregar (esperava 200)"
        assert "<!DOCTYPE html>" in response.text
        assert "GestãoPRO" in response.text

def test_detalhe_pedido_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_full_pedido_scenario: dict):
    cenario = setup_full_pedido_scenario
    
    response = test_client.get(
        f"/pedido/{cenario['numero_aocs']}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    html = response.text
    assert cenario["numero_aocs"] in html
    assert cenario["nome_item"] in html
    assert cenario["nome_fornecedor"] in html
    
    assert "25" in html

def test_detalhe_contrato_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item_para_ui: dict):
    cenario = setup_contrato_com_item_para_ui
    id_contrato = cenario["id_contrato"]
    
    response = test_client.get(
        f"/contrato/{id_contrato}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    html = response.text
    assert cenario["numero_contrato"] in html
    assert cenario["nome_fornecedor"] in html
    assert cenario["nome_item"] in html
    
def test_contratos_por_categoria_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item_para_ui: dict):
    response_contrato = test_client.get(
        f"/api/contratos/{setup_contrato_com_item_para_ui['id_contrato']}", 
        headers=admin_auth_headers
    )
    assert response_contrato.status_code == 200
    id_categoria = response_contrato.json()["id_categoria"]
    
    response = test_client.get(
        f"/categoria/{id_categoria}/contratos",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    html = response.text
    assert "Catálogo de Itens:" in html
    assert "Item Visível no Detalhe do Contrato" in html 
    assert "CT-UI-DETALHE-555/2025" in html

def test_nova_ci_ui_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_nova_ci_deps: str):
    numero_aocs_teste = setup_nova_ci_deps
    
    response = test_client.get(
        f"/pedido/{numero_aocs_teste}/nova-ci",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    html = response.text
    
    assert "Nova Comunicação Interna de Pagamento" in html
    assert numero_aocs_teste in html 
    
    assert "Unidade Teste CI-UI" in html
    assert "Agente Teste CI-UI" in html
    assert "Dotacao Teste CI-UI" in html
    
def test_importar_itens_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_contrato_com_item_para_ui: dict 
):
    cenario = setup_contrato_com_item_para_ui
    id_contrato = cenario["id_contrato"]
    numero_contrato = cenario["numero_contrato"]
    
    response = test_client.get(
        f"/contrato/{id_contrato}/importar-itens",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200, f"Esperava 200 OK, mas recebi {response.status_code}"
    assert "<!DOCTYPE html>" in response.text
    
    assert numero_contrato in response.text
    assert "Importar Itens" in response.text
    
def test_login_post_fail_invalid_credentials(test_client: TestClient):
    payload = {
        "username": "usuario_que_nao_existe",
        "password": "senha_errada"
    }

    original_follow_redirects = test_client.follow_redirects
    test_client.follow_redirects = False
    
    response = test_client.post("/login", data=payload)
    
    test_client.follow_redirects = original_follow_redirects

    assert response.status_code == 302
    assert "access_token" not in response.cookies
    
    location_header = response.headers["location"]
    
    decoded_location = unquote(location_header)
    
    assert "login" in decoded_location
    assert "Usuário ou senha inválidos" in decoded_location
    assert "category=error" in decoded_location


def test_logout_redirects_and_clears_cookie(test_client: TestClient, admin_auth_headers: dict):
    original_follow_redirects = test_client.follow_redirects
    test_client.follow_redirects = False
    
    response = test_client.get("/logout", headers=admin_auth_headers)
    
    test_client.follow_redirects = original_follow_redirects

    assert response.status_code == 302
    
    decoded_location = unquote(response.headers["location"])
    assert "login" in decoded_location
    assert "Você foi desconectado com sucesso" in decoded_location
    assert "category=success" in decoded_location
    
    assert "access_token" in response.headers["set-cookie"]
    assert 'Max-Age=0' in response.headers["set-cookie"]
    
def test_contratos_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_contrato_com_item_para_ui: dict 
):
    cenario = setup_contrato_com_item_para_ui
    nome_contrato = cenario["numero_contrato"]
    nome_fornecedor = cenario["nome_fornecedor"]
    
    response = test_client.get("/contratos-ui", headers=admin_auth_headers)
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    assert "Gerenciar Contratos" in response.text
    
    assert nome_contrato in response.text
    assert nome_fornecedor in response.text
    
def test_admin_usuarios_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict,
    user_auth_headers: dict
):
    response = test_client.get("/admin/usuarios", headers=admin_auth_headers)
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    assert "Gerenciar Usuários" in response.text
    
    assert "test_admin_user" in response.text
    assert "test_user_user" in response.text