from playwright.sync_api import Page, expect
import time

# --- Função Auxiliar de Login ---
def realizar_login(page: Page):
    """Helper para pular a tela de login em testes que precisam de autenticação"""
    page.goto("/login")
    
    # Ajuste as credenciais aqui se o seu banco tiver outro usuário
    page.fill("input[name='username']", "admin")   
    page.fill("input[name='password']", "Azulceleste#123") 
    
    page.get_by_role("button", name="Entrar").click()
    
    # CORREÇÃO AQUI: O sistema redireciona para /home, não para /
    expect(page).to_have_url("/home") 

# --- O Teste do Fluxo ---
def test_fluxo_criar_novo_pedido(page: Page):
    # 1. Login (agora corrigido)
    realizar_login(page)

    # 2. Interação no Dashboard
    # Clica no botão "Iniciar Novo Pedido"
    page.click("#btn-iniciar-pedido-modal") 
    
    # Verifica se o modal abriu
    modal = page.locator("#modal-novo-pedido")
    expect(modal).to_be_visible()

    # 3. Seleção de Categoria
    select_categoria = page.locator("#categoria-pedido-select")
    
    # Seleciona a segunda opção (índice 1), assumindo que a 0 é "Selecione..."
    # Se falhar, verifique se você tem categorias cadastradas no banco!
    select_categoria.select_option(index=1) 

    # Clica em continuar
    page.click("#btn-continuar-pedido")

    # 4. Tela de Novo Pedido
    # Verifica se carregou a página certa e se o título contém "Novo Pedido"
    expect(page.locator("h1")).to_contain_text("Novo Pedido")

    # Adiciona um item ao carrinho
    # Pega o primeiro input de quantidade visível na tabela
    input_qtd = page.locator(".small-input").first
    input_qtd.fill("10,00")
    
    # Dispara o blur (sair do campo) para acionar o cálculo do JS
    input_qtd.blur() 

    # Verifica se o botão "Finalizar" habilitou
    btn_finalizar = page.locator("#btn-finalizar-pedido")
    expect(btn_finalizar).to_be_enabled()

    # Verifica se o total mudou de R$ 0,00
    total = page.locator("#carrinho-total strong")
    expect(total).not_to_contain_text("R$ 0,00")

    # 5. Finalização (Preenchimento da AOCS)
    btn_finalizar.click()
    
    # Preenche os campos obrigatórios do modal
    page.select_option("#aocs-unidade", index=1)
    page.fill("#aocs-justificativa", "Teste E2E Automatizado")
    page.select_option("#aocs-orcamento", index=1)
    page.select_option("#aocs-local-entrega", index=1)
    page.select_option("#aocs-responsavel", index=1)

    # Preenche os números das AOCS gerados dinamicamente
    inputs_aocs = page.locator(".aocs-input")
    count = inputs_aocs.count()
    
    for i in range(count):
        inputs_aocs.nth(i).fill(f"AOCS-AUT-{i}")

    # Nota: Não clicamos no botão final de envio para não poluir seu banco de dados a cada teste.
    # Se quiser testar o envio real, descomente a linha abaixo:
    # page.click("#btn-enviar-pedido")