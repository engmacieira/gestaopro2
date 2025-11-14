import pytest
from fastapi.testclient import TestClient
from datetime import date
from urllib.parse import unquote

# --- Testes de Rotas Públicas (Sem Login) ---

def test_get_login_page_sem_auth(test_client: TestClient):
    """Testa se a página de login /login carrega (200 OK)."""
    response = test_client.get("/login")
    assert response.status_code == 200
    assert "GestãoPRO" in response.text

def test_root_redirects_to_login(test_client: TestClient):
    """Testa se a raiz / redireciona para /login."""
    
    # 1. Faz a chamada (sem 'allow_redirects'). O TestClient seguirá o redirect.
    response = test_client.get("/") 
    
    # 2. O status final da página deve ser 200 (a página /login que carregou com sucesso)
    assert response.status_code == 200
    
    # 3. A "prova" do redirect está no histórico da resposta.
    assert len(response.history) == 1 # Prova que houve exatamente 1 redirecionamento.
    assert response.history[0].status_code == 302 # O primeiro passo foi um 302.
    assert response.history[0].headers["location"] == "/login" # E foi para /login.

def test_get_static_files(test_client: TestClient):
    """Testa se o CSS e JS (ficheiros estáticos) estão a ser servidos."""
    response_css = test_client.get("/static/style.css")
    assert response_css.status_code == 200
    assert "color-background" in response_css.text

    response_js = test_client.get("/static/js/index.js")
    assert response_js.status_code == 200
    assert "showNotification" in response_js.text

# --- Testes de Rotas Protegidas (Exigem Login) ---

def test_protected_routes_fail_sem_auth(test_client: TestClient):
    """Testa se as rotas protegidas falham com 401 (Unauthorized) se não estiver logado."""
    response_home = test_client.get("/home")
    assert response_home.status_code == 401

    response_categorias = test_client.get("/categorias-ui")
    assert response_categorias.status_code == 401

def test_protected_routes_pass_com_auth(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa (Smoke Test) se as páginas principais carregam (200 OK)
    quando estamos autenticados como admin.
    """
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

# --- Fixture de Preparação Complexa ---
@pytest.fixture
def setup_full_pedido_scenario(test_client: TestClient, admin_auth_headers: dict) -> dict:
    """
    Cria um cenário completo: Contrato -> Item -> AOCS -> Pedido.
    Retorna os nomes/números para verificação no HTML.
    """
    # 1. Criar Contrato
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
    
    # 2. Criar Item
    item_payload = {
        "numero_item": 1, "unidade_medida": "UN", "quantidade": 100, "valor_unitario": 10.0,
        "contrato_nome": "CT-UI-123/2025",
        "descricao": {"descricao": "Item Visível no Teste de UI"}
    }
    resp_item = test_client.post("/api/itens/", json=item_payload, headers=admin_auth_headers)
    assert resp_item.status_code == 201
    id_item = resp_item.json()["id"]

    # 3. Criar AOCS
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

    # 4. Criar Pedido (Ligar Item à AOCS)
    pedido_payload = {"item_contrato_id": id_item, "quantidade_pedida": 25}
    resp_pedido = test_client.post(f"/api/pedidos/?id_aocs={id_aocs}", json=pedido_payload, headers=admin_auth_headers)
    assert resp_pedido.status_code == 201

    # Retorna os dados que queremos procurar no HTML
    return {
        "numero_aocs": "AOCS-UI-789/2025",
        "nome_item": "Item Visível no Teste de UI",
        "nome_fornecedor": "Fornecedor Teste UI",
        "quantidade_pedida": "25" # O HTML vai formatar isto
    }

# --- Adicione este novo teste no final do ficheiro ---

def test_detalhe_pedido_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_full_pedido_scenario: dict):
    """
    Testa se a página /pedido/{numero_aocs} (detalhe_pedido)
    renderiza os dados corretos do banco de dados no HTML.
    """
    # Pega os dados criados pela fixture
    cenario = setup_full_pedido_scenario
    
    # 1. Agir: Carregar a página de UI
    response = test_client.get(
        f"/pedido/{cenario['numero_aocs']}",
        headers=admin_auth_headers
    )
    
    # 2. Verificar o Básico
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    # 3. Verificar o Conteúdo (A parte importante!)
    # Vamos verificar se os dados que criámos estão no HTML renderizado
    html = response.text
    assert cenario["numero_aocs"] in html
    assert cenario["nome_item"] in html
    assert cenario["nome_fornecedor"] in html
    
    # Verifica a quantidade pedida (pode ser formatada, ex: 25 ou 25,00)
    assert "25" in html

@pytest.fixture
def setup_contrato_com_item_para_ui(test_client: TestClient, admin_auth_headers: dict) -> dict:
    """
    Cria um Contrato e um Item para o teste de UI 'detalhe_contrato'.
    Retorna os dados que esperamos ver no HTML.
    """
    # 1. Criar Contrato
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

    # 2. Criar Item
    item_payload = {
        "numero_item": 1, "unidade_medida": "UN", "quantidade": 500, "valor_unitario": 10.0,
        "contrato_nome": "CT-UI-DETALHE-555/2025",
        "descricao": {"descricao": "Item Visível no Detalhe do Contrato"}
    }
    resp_item = test_client.post("/api/itens/", json=item_payload, headers=admin_auth_headers)
    assert resp_item.status_code == 201

    # Retorna os dados que queremos procurar no HTML
    return {
        "id_contrato": id_contrato,
        "numero_contrato": "CT-UI-DETALHE-555/2025",
        "nome_fornecedor": "Fornecedor Detalhe UI",
        "nome_item": "Item Visível no Detalhe do Contrato"
    }

# --- Adicione este novo teste no final do ficheiro ---

def test_detalhe_contrato_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item_para_ui: dict):
    """
    Testa se a página /contrato/{id} (detalhe_contrato)
    renderiza os dados corretos do banco de dados no HTML.
    """
    # Pega os dados criados pela fixture
    cenario = setup_contrato_com_item_para_ui
    id_contrato = cenario["id_contrato"]
    
    # 1. Agir: Carregar a página de UI
    response = test_client.get(
        f"/contrato/{id_contrato}",
        headers=admin_auth_headers
    )
    
    # 2. Verificar o Básico
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    # 3. Verificar o Conteúdo (A parte importante!)
    html = response.text
    assert cenario["numero_contrato"] in html
    assert cenario["nome_fornecedor"] in html
    assert cenario["nome_item"] in html
    
# (Não são precisos novos imports)

def test_contratos_por_categoria_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_contrato_com_item_para_ui: dict):
    """
    Testa se a página /categoria/{id}/contratos (contratos_por_categoria)
    renderiza os dados corretos do banco de dados no HTML.
    """
    # A fixture já criou um Contrato e um Item.
    # Precisamos de ir buscar o ID da Categoria a que esse Contrato pertence.
    
    # 1. Buscar o Contrato que a fixture criou para descobrir o ID da Categoria
    response_contrato = test_client.get(
        f"/api/contratos/{setup_contrato_com_item_para_ui['id_contrato']}", 
        headers=admin_auth_headers
    )
    assert response_contrato.status_code == 200
    id_categoria = response_contrato.json()["id_categoria"]
    
    # 2. Agir: Carregar a página da Categoria
    response = test_client.get(
        f"/categoria/{id_categoria}/contratos",
        headers=admin_auth_headers
    )
    
    # 3. Verificar o Básico
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    # 4. Verificar o Conteúdo
    html = response.text
    assert "Catálogo de Itens:" in html
    # Verifica se o item que criámos está a ser listado na tabela
    assert "Item Visível no Detalhe do Contrato" in html 
    # Verifica se o número do contrato do item está lá
    assert "CT-UI-DETALHE-555/2025" in html

@pytest.fixture
def setup_novo_pedido_deps(test_client: TestClient, admin_auth_headers: dict) -> int:
    """
    Cria as dependências de domínio (Categoria, Unidade, Local, Agente, Dotação)
    necessárias para a página 'novo_pedido'.
    Retorna o ID da Categoria principal.
    """
    # 1. Criar Categoria (o "pai" da rota)
    resp_cat = test_client.post("/api/categorias/", json={"nome": "Categoria Para Novo Pedido"}, headers=admin_auth_headers)
    assert resp_cat.status_code == 201
    id_categoria = resp_cat.json()["id"]

    # 2. Criar os dados que devem aparecer nos dropdowns
    test_client.post("/api/unidades/", json={"nome": "Unidade Dropdown Teste"}, headers=admin_auth_headers)
    test_client.post("/api/locais/", json={"descricao": "Local Dropdown Teste"}, headers=admin_auth_headers)
    test_client.post("/api/agentes/", json={"nome": "Agente Dropdown Teste"}, headers=admin_auth_headers)
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotacao Dropdown Teste"}, headers=admin_auth_headers)
    
    return id_categoria

# --- Adiciona este novo teste no final do ficheiro ---

def test_novo_pedido_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_novo_pedido_deps: int):
    """
    Testa se a página /categoria/{id}/novo-pedido (novo_pedido_pagina)
    renderiza os dados de domínio (dropdowns) corretamente no HTML.
    """
    id_categoria_teste = setup_novo_pedido_deps
    
    # 1. Agir: Carregar a página de UI
    response = test_client.get(
        f"/categoria/{id_categoria_teste}/novo-pedido",
        headers=admin_auth_headers
    )
    
    # 2. Verificar o Básico
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    # 3. Verificar o Conteúdo (A parte importante!)
    # Vamos verificar se os dados que criámos estão nos <option> do HTML
    html = response.text
    
    assert "Categoria Para Novo Pedido" in html # Verifica o título da página
    
    # Verifica os dropdowns
    assert "Unidade Dropdown Teste" in html
    assert "Local Dropdown Teste" in html
    assert "Agente Dropdown Teste" in html
    assert "Dotacao Dropdown Teste" in html
    
@pytest.fixture
def setup_nova_ci_deps(test_client: TestClient, admin_auth_headers: dict) -> dict:
    """
    Cria as dependências mínimas (AOCS, Agente, Unidade, Dotação)
    para carregar a página 'nova_ci_ui'.
    """
    # 1. Criar as dependências que o repositório de AOCS vai procurar (get_or_create)
    test_client.post("/api/unidades/", json={"nome": "Unidade Teste CI-UI"}, headers=admin_auth_headers)
    test_client.post("/api/locais/", json={"descricao": "Local Teste CI-UI"}, headers=admin_auth_headers)
    test_client.post("/api/agentes/", json={"nome": "Agente Teste CI-UI"}, headers=admin_auth_headers)
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotacao Teste CI-UI"}, headers=admin_auth_headers)

    # 2. Criar AOCS
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
    
    # Retorna o número da AOCS (que está na URL da UI)
    return "AOCS-CI-UI-444/2025"

# --- Adiciona este novo teste no final do ficheiro ---

def test_nova_ci_ui_loads_data(test_client: TestClient, admin_auth_headers: dict, setup_nova_ci_deps: str):
    """
    Testa se a página /pedido/{numero_aocs}/nova-ci (nova_ci_ui)
    renderiza os dados de domínio (dropdowns) corretamente no HTML.
    """
    numero_aocs_teste = setup_nova_ci_deps
    
    # 1. Agir: Carregar a página de UI
    response = test_client.get(
        f"/pedido/{numero_aocs_teste}/nova-ci",
        headers=admin_auth_headers
    )
    
    # 2. Verificar o Básico
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

    # 3. Verificar o Conteúdo
    html = response.text
    
    assert "Nova Comunicação Interna de Pagamento" in html
    assert numero_aocs_teste in html # Verifica se o número da AOCS está na página
    
    # Verifica se os dados que criámos estão nos <option> dos dropdowns
    assert "Unidade Teste CI-UI" in html
    assert "Agente Teste CI-UI" in html
    assert "Dotacao Teste CI-UI" in html

@pytest.mark.skip(reason="Implementação da geração real de PDF (WeasyPrint) em 'imprimir_aocs' está pendente.")
def test_imprimir_aocs(test_client: TestClient, admin_auth_headers: dict, setup_full_pedido_scenario: dict):
    """
    Testa se a rota de impressão da AOCS retorna um documento PDF.
    Rota: GET /pedido/{numero_aocs:path}/imprimir
    """
    cenario = setup_full_pedido_scenario
    numero_aocs_teste = cenario["numero_aocs"]
    
    response = test_client.get(
        f"/pedido/{numero_aocs_teste}/imprimir",
        headers=admin_auth_headers
    )
    
    # Verifica se a rota de impressão responde com sucesso (200)
    assert response.status_code == 200
    # Verifica se o tipo de conteúdo é PDF
    assert response.headers["content-type"] == "application/pdf"
    # Verifica se o conteúdo do PDF não está vazio
    assert len(response.content) > 1000 

@pytest.mark.skip(reason="Implementação da geração real de PDF (WeasyPrint) em 'imprimir_pendentes_aocs' está pendente.")
def test_imprimir_pendentes(test_client: TestClient, admin_auth_headers: dict, setup_full_pedido_scenario: dict):
    """
    Testa se a rota de impressão de Pendentes retorna um documento PDF.
    Rota: GET /pedido/{numero_aocs:path}/imprimir-pendentes
    """
    cenario = setup_full_pedido_scenario
    numero_aocs_teste = cenario["numero_aocs"]
    
    response = test_client.get(
        f"/pedido/{numero_aocs_teste}/imprimir-pendentes",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000
    
def test_importar_itens_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_contrato_com_item_para_ui: dict # Reutilizamos esta fixture
):
    """
    Testa se a página /contrato/{id}/importar-itens (importar_itens_ui)
    carrega corretamente.
    """
    # 1. Preparar: Pegar os dados da fixture
    cenario = setup_contrato_com_item_para_ui
    id_contrato = cenario["id_contrato"]
    numero_contrato = cenario["numero_contrato"]
    
    # 2. Agir: Carregar a página de UI
    response = test_client.get(
        f"/contrato/{id_contrato}/importar-itens",
        headers=admin_auth_headers
    )
    
    # 3. Verificar: Checar o status e o conteúdo
    assert response.status_code == 200, f"Esperava 200 OK, mas recebi {response.status_code}"
    assert "<!DOCTYPE html>" in response.text
    
    # Verifica se o número do contrato aparece na página
    assert numero_contrato in response.text
    # Verifica se o título da página está correto
    assert "Importar Itens" in response.text
    
# (No mesmo local, após test_get_static_files)

def test_login_post_fail_invalid_credentials(test_client: TestClient):
    """
    Testa se o POST /login com credenciais inválidas redireciona
    de volta para /login com uma mensagem de erro, sem definir um cookie.
    """
    # 1. Preparar:
    payload = {
        "username": "usuario_que_nao_existe",
        "password": "senha_errada"
    }

    # 2. Agir:
    original_follow_redirects = test_client.follow_redirects
    test_client.follow_redirects = False
    
    response = test_client.post("/login", data=payload)
    
    test_client.follow_redirects = original_follow_redirects

    # 3. Verificar:
    assert response.status_code == 302
    assert "access_token" not in response.cookies
    
    # --- AQUI ESTÁ A CORREÇÃO ---
    
    # 1. Pegar o cabeçalho 'location' bruto (URL-encoded)
    location_header = response.headers["location"]
    
    # 2. Decodificar a string da URL para texto legível
    decoded_location = unquote(location_header)
    
    # 3. Fazer as asserções na string decodificada (legível)
    assert "login" in decoded_location
    assert "Usuário ou senha inválidos" in decoded_location
    assert "category=error" in decoded_location

# (Precisamos do 'unquote' que já adicionámos)

def test_logout_redirects_and_clears_cookie(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa se o GET /logout redireciona para /login com a mensagem
    correta e limpa o cookie 'access_token'.
    """
    # 1. Preparar:
    # Estamos a usar 'admin_auth_headers', por isso esta chamada é
    # feita por um utilizador autenticado.
    
    # 2. Agir:
    # Desativar o 'follow_redirects' para apanhar o 302
    original_follow_redirects = test_client.follow_redirects
    test_client.follow_redirects = False
    
    response = test_client.get("/logout", headers=admin_auth_headers)
    
    test_client.follow_redirects = original_follow_redirects

    # 3. Verificar:
    assert response.status_code == 302
    
    # Verifica a URL de redirecionamento (decodificada)
    decoded_location = unquote(response.headers["location"])
    assert "login" in decoded_location
    assert "Você foi desconectado com sucesso" in decoded_location
    assert "category=success" in decoded_location
    
    # A verificação mais importante:
    # O servidor DEVE ter-nos dito para apagar o cookie.
    # Procuramos por 'access_token=""' e 'max-age=0'.
    assert "access_token" in response.headers["set-cookie"]
    assert 'Max-Age=0' in response.headers["set-cookie"]
    
@pytest.fixture
def setup_categoria_para_ui(test_client: TestClient, admin_auth_headers: dict) -> str:
    """
    Cria uma categoria de teste via API e retorna o seu nome.
    """
    nome_categoria = "Categoria Visível na UI 123"
    response = test_client.post(
        "/api/categorias/", 
        json={"nome": nome_categoria}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    return nome_categoria

def test_categorias_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_categoria_para_ui: str # Usa a fixture
):
    """
    Testa se a página /categorias-ui (categorias_ui)
    renderiza os dados do banco de dados (a categoria) no HTML.
    """
    # 1. Preparar:
    # A fixture 'setup_categoria_para_ui' já foi executada
    # e criou a categoria. 'nome_categoria' contém o nome.
    nome_categoria = setup_categoria_para_ui
    
    # 2. Agir: Carregar a página de UI
    response = test_client.get("/categorias-ui", headers=admin_auth_headers)
    
    # 3. Verificar:
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    # Verifica o conteúdo estático (título da página)
    assert "Gerenciar Categorias" in response.text
    
    # A verificação mais importante:
    # O nome da categoria que acabámos de criar está no HTML?
    assert nome_categoria in response.text
    
# (Não são necessários novos imports)

def test_contratos_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_contrato_com_item_para_ui: dict # Reutilizamos esta fixture
):
    """
    Testa se a página /contratos-ui (contratos_ui)
    renderiza os dados do banco de dados (o contrato) no HTML.
    """
    # 1. Preparar:
    # A fixture já criou o contrato.
    cenario = setup_contrato_com_item_para_ui
    nome_contrato = cenario["numero_contrato"]
    nome_fornecedor = cenario["nome_fornecedor"]
    
    # 2. Agir: Carregar a página de UI
    response = test_client.get("/contratos-ui", headers=admin_auth_headers)
    
    # 3. Verificar:
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    # Verifica o título estático
    assert "Gerenciar Contratos" in response.text
    
    # A verificação importante:
    # Os dados dinâmicos estão no HTML?
    assert nome_contrato in response.text
    assert nome_fornecedor in response.text
    
# (Não são necessários novos imports)

@pytest.mark.skip(reason="Implementação da lógica de DB no router 'pedidos_ui'está pendente.")
def test_pedidos_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    setup_full_pedido_scenario: dict # Reutilizamos esta fixture complexa
):
    """
    Testa se a página /pedidos-ui (pedidos_ui)
    renderiza os dados do banco de dados (o pedido/AOCS) no HTML.
    """
    # 1. Preparar:
    # A fixture já criou o cenário completo.
    cenario = setup_full_pedido_scenario
    numero_aocs_criado = cenario["numero_aocs"]
    
    # 2. Agir: Carregar a página de UI de listagem
    response = test_client.get("/pedidos-ui", headers=admin_auth_headers)
    
    # 3. Verificar:
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    # A verificação importante:
    # O número da AOCS que acabámos de criar está na tabela?
    assert numero_aocs_criado in response.text

# (Não são necessários novos imports)

def test_admin_usuarios_ui_loads_data(
    test_client: TestClient, 
    admin_auth_headers: dict,
    user_auth_headers: dict
):
    """
    Testa se a página /admin/usuarios (gerenciar_usuarios_ui)
    renderiza os utilizadores do banco de dados (ex: o próprio admin) no HTML.
    """
    # 1. Preparar:
    # As fixtures (em conftest.py) já criaram os utilizadores
    # 'test_admin_user' e 'test_user_user'.
    
    # 2. Agir: Carregar a página de UI
    response = test_client.get("/admin/usuarios", headers=admin_auth_headers)
    
    # 3. Verificar:
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    
    # Verifica o título estático (Ajuste se este falhar)
    assert "Gerenciar Usuários" in response.text
    
    # A verificação importante:
    # Os nomes dos nossos utilizadores de teste estão na tabela?
    assert "test_admin_user" in response.text
    assert "test_user_user" in response.text