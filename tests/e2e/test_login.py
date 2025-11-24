from playwright.sync_api import Page, expect

def test_deve_carregar_pagina_de_login(page: Page):
    # 1. Acessar a página inicial (o pytest.ini completa com localhost:8000)
    page.goto("/login")

    # 2. Verificar se o título da aba está correto
    # Isso confirma que o HTML base foi carregado
    expect(page).to_have_title("Login - GestãoPRO")

    # 3. Verificar se os elementos principais estão visíveis
    # Isso confirma que o CSS e o HTML do formulário renderizaram
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.get_by_role("button", name="Entrar")).to_be_visible()

def test_deve_exibir_erro_login_invalido(page: Page):
    # 1. Acessar
    page.goto("/login")

    # 2. Preencher com dados errados
    page.fill("input[name='username']", "usuario_inexistente")
    page.fill("input[name='password']", "senha_errada")

    # 3. Clicar em Entrar
    page.get_by_role("button", name="Entrar").click()

    # 4. Verificar se a notificação de erro aparece
    # Baseado no seu base.html, as mensagens aparecem em #notification-area
    notification = page.locator(".notification.error")
    
    # Espera que a notificação apareça
    expect(notification).to_be_visible()
    # (Opcional) Verifica o texto se você souber a mensagem exata do backend
    # expect(notification).to_contain_text("incorretos")