import pytest
from playwright.sync_api import Page, expect

# Constantes para seletores facilitam a manutenção (DRY)
SELECTOR_SIDEBAR_LINKS = "aside.sidebar a[href]"
SELECTOR_HEADER_TITLE = "h1"

def realizar_login(page: Page):
    """
    Realiza o login padrão para os testes.
    Dica de Sênior: Em projetos maiores, moveríamos isso para um 'fixture' do Pytest no conftest.py
    para não repetir código, mas por enquanto vamos manter aqui para clareza.
    """
    page.goto("/login")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "Azulceleste#123")
    page.get_by_role("button", name="Entrar").click()
    
    # Aguarda chegar na home para garantir que o login funcionou
    expect(page).to_have_url("/home")
    page.wait_for_load_state("networkidle")

def test_verificar_links_sidebar(page: Page):
    """
    Este teste varre dinamicamente a sidebar e verifica se todos os links
    retornam status 200 (OK) e não quebram a aplicação.
    """
    # 1. Login
    realizar_login(page)

    # 2. Coletar todos os links da sidebar
    # O 'evaluate_all' executa um JS no navegador para pegar os atributos href
    links_hrefs = page.locator(SELECTOR_SIDEBAR_LINKS).evaluate_all("elements => elements.map(e => e.href)")
    
    print(f"\n🔍 Encontrados {len(links_hrefs)} links na sidebar para testar.")

    # 3. Iterar sobre cada link encontrado
    for href in links_hrefs:
        # Ignora links de logout ou links vazios/javascript:void
        if "logout" in href or "#" in href:
            continue

        print(f"👉 Testando navegação para: {href}")

        # A Mágica do Playwright: RunAndWait
        # Nós dizemos: "Playwright, clica no link E fique monitorando a resposta da rede"
        with page.expect_response(lambda response: response.url == href and response.status == 200) as response_info:
            # Temos que usar o seletor específico do href para clicar no elemento certo
            # Usamos CSS selector matching attribute
            page.locator(f"aside.sidebar a[href='{href.split('/')[-1]}']").click()

        # Se o código acima passar, significa que recebemos um 200.
        # Se recebermos um 500, o 'expect_response' vai dar timeout e falhar o teste (o que queremos!).
        
        # Validação extra de UI: Verifica se não existe texto de erro explícito na tela
        # Isso ajuda caso o backend retorne 200 mas mostre uma stack trace no HTML (acontece!)
        conteudo_pagina = page.content()
        assert "Internal Server Error" not in conteudo_pagina, f"❌ Erro 500 detectado visualmente em {href}"
        assert "404 Not Found" not in conteudo_pagina, f"❌ Erro 404 detectado visualmente em {href}"
        
        # Opcional: Verifica se tem um título H1 (garante que a página renderizou o básico do layout)
        expect(page.locator(SELECTOR_HEADER_TITLE)).toBeVisible()
        
        print(f"✅ Sucesso: {href}")