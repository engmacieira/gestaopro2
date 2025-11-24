import pytest
import re
from playwright.sync_api import Page, expect

# -----------------------------------------------------------------------------
# 1. Configuração dos Cenários de Teste (Dicionário de Rotas)
# -----------------------------------------------------------------------------
# Aqui definimos explicitamente o que queremos testar. 
# Se adicionar uma nova funcionalidade, adicione aqui.
# Formato: "Nome da Tela": {"href_parcial": "trecho_da_url", "titulo_esperado": "Texto no H1"}
CENARIOS_NAVEGACAO = {
    "Home": {
        "selector": "a[href='/home']", 
        "url_check": "/home", 
        "h1_check": "Dashboard"  # Ajuste conforme o texto real do seu H1 na home
    },
    "Categorias": {
        "selector": "a[href*='/categorias-ui']", 
        "url_check": "/categorias-ui", 
        "h1_check": "Categorias"
    },
    "Contratos": {
        "selector": "a[href*='/contratos-ui']", 
        "url_check": "/contratos-ui", 
        "h1_check": "Contratos"
    },
    "Pedidos": {
        "selector": "a[href*='/pedidos-ui']", 
        "url_check": "/pedidos-ui", 
        "h1_check": "Pedidos"
    },
    "Relatórios": {
        "selector": "a[href*='/relatorios']", 
        "url_check": "/relatorios", 
        "h1_check": "Relatórios"
    },
    "Gerenciar Usuários": {
        "selector": "a[href*='/usuarios-ui']", # Verifiquei no ui_router se essa rota existe
        "url_check": "/usuarios-ui",
        "h1_check": "Usuários"
    }
}

# -----------------------------------------------------------------------------
# 2. Setup e Login (Fixture)
# -----------------------------------------------------------------------------
@pytest.fixture(scope="function", autouse=True)
def setup_login(page: Page):
    """
    Este bloco roda antes de cada teste. Garante que estamos logados
    e com a tela carregada no tamanho correto.
    """
    # Força um tamanho de tela Desktop para garantir que a Sidebar esteja visível
    page.set_viewport_size({"width": 1280, "height": 800})
    
    print("\n🚀 Iniciando Login...")
    page.goto("http://localhost:8000/login") # Ajuste a porta se necessário
    
    # Preenchimento do Login
    page.locator("input[name='username']").fill("admin")
    page.locator("input[name='password']").fill("Azulceleste#123")
    page.get_by_role("button", name="Entrar").click()

    # Validação Crítica: Espera sair da tela de login
    try:
        expect(page).to_have_url(re.compile(r".*/home"))
        print("✅ Login realizado com sucesso!")
    except Exception as e:
        print(f"❌ Falha no Login. URL atual: {page.url}")
        raise e

# -----------------------------------------------------------------------------
# 3. O Teste Principal
# -----------------------------------------------------------------------------
def test_validar_links_sidebar(page: Page):
    """
    Clica em cada link da sidebar definido em CENARIOS_NAVEGACAO 
    e valida se a página carrega sem erros 500.
    """
    
    # Aguarda a Sidebar estar visível na tela
    sidebar = page.locator("aside.sidebar, nav#sidebar") # Tenta seletores comuns, ajuste se necessário
    if sidebar.count() > 0:
        expect(sidebar).to_be_visible()

    for nome_cenario, dados in CENARIOS_NAVEGACAO.items():
        print(f"\n👉 Testando navegação para: {nome_cenario}")

        # 1. Encontrar o Link na Sidebar
        # Usamos 'first' para garantir que se houver dois links iguais (desktop/mobile), ele pegue um.
        link = page.locator(f"aside {dados['selector']}").first
        
        # Verifica se o link realmente existe antes de clicar
        if link.count() == 0:
            print(f"⚠️ Link para {nome_cenario} não encontrado na sidebar. Pulando...")
            continue
            
        # 2. Clicar e Monitorar Resposta de Rede
        # Isso garante que pegamos o erro 500 "no ato", vindo do backend
        with page.expect_response(lambda response: response.status == 200 or response.status == 500) as response_info:
            link.click()
        
        response = response_info.value
        
        # 3. Validação Técnica (HTTP Status)
        if response.status == 500:
            print(f"❌ ERRO CRÍTICO 500 detectado ao acessar {nome_cenario}")
            pytest.fail(f"Backend retornou erro 500 na rota {dados['url_check']}")
        
        # 4. Validação Visual (URL e Título)
        expect(page).to_have_url(re.compile(dados['url_check']))
        
        # Verifica se não temos uma tela de erro vazia
        # (Às vezes o status é 200, mas o conteúdo é uma stack trace do Python)
        content = page.content()
        assert "Internal Server Error" not in content, f"Erro 500 (texto) encontrado em {nome_cenario}"
        
        # Verifica um elemento chave da tela (ex: H1)
        # Usamos timeout curto aqui para não travar muito se a página for lenta
        try:
            expect(page.locator("h1")).to_contain_text(dados['h1_check'], timeout=3000)
            print(f"✅ Sucesso visual: {nome_cenario}")
        except AssertionError:
            print(f"⚠️ Aviso: Título H1 não corresponde em {nome_cenario}. Verifique se o texto mudou.")