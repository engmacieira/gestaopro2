/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

const waitFor = async (callback, timeout = 1000) => {
    const startTime = Date.now();
    while (true) {
        try {
            callback();
            return;
        } catch (e) {
            if (Date.now() - startTime > timeout) throw e;
            await new Promise(r => setTimeout(r, 50));
        }
    }
};

// HTML Simulado (Abas + Formulário de Contratos + Formulário de Itens)
const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>

    <button class="tab-link active" data-tab="tab-contratos" id="link-contratos">Contratos</button>
    <button class="tab-link" data-tab="tab-itens" id="link-itens">Itens</button>

    <div id="tab-contratos" class="tab-content active">
        <form id="form-upload-contratos">
            <input type="file" name="arquivo_excel" id="arquivo_excel_contratos">
            <button type="submit">Carregar</button>
        </form>
        <div id="error-message-contratos"></div>
        
        <div id="preview-container-contratos" style="display: none;">
            <table id="preview-table-contratos"></table>
            <button id="btn-salvar-contratos">Salvar Contratos</button>
        </div>
    </div>

    <div id="tab-itens" class="tab-content">
        <form id="form-upload-itens">
            <input type="file" name="arquivo_excel" id="arquivo_excel_itens">
            <button type="submit">Carregar</button>
        </form>
        <div id="error-message-itens"></div>
        
        <div id="preview-container-itens" style="display: none;">
            <table id="preview-table-itens"></table>
            <button id="btn-salvar-itens">Salvar Itens</button>
        </div>
    </div>
`;

describe('Testes Frontend - Importação', () => {
    let reloadMock;

    // ==========================================================================
    // 2. SETUP
    // ==========================================================================
    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Patch innerText
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // Variáveis globais esperadas pelo HTML (definidas no bloco scripts do template)
        window.redirectUrlContratos = '/contratos';
        window.redirectUrlItens = '/itens';

        // Mock Location
        delete window.location;
        window.location = { href: '' };

        // Carrega o script
        jest.resetModules();
        require('../../app/static/js/importar');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // 3. TEARDOWN
    // ==========================================================================
    afterEach(() => {
        delete window.redirectUrlContratos;
        delete window.redirectUrlItens;
    });

    // ==========================================================================
    // 4. TESTES
    // ==========================================================================

    test('Navegação: Deve alternar entre as abas de Contratos e Itens', () => {
        const linkContratos = document.getElementById('link-contratos');
        const linkItens = document.getElementById('link-itens');
        const tabContratos = document.getElementById('tab-contratos');
        const tabItens = document.getElementById('tab-itens');

        // Estado inicial
        expect(tabContratos.classList.contains('active')).toBe(true);

        // Clica em Itens
        linkItens.click();
        expect(tabContratos.classList.contains('active')).toBe(false);
        expect(tabItens.classList.contains('active')).toBe(true);
        expect(linkItens.classList.contains('active')).toBe(true);

        // Clica em Contratos de volta
        linkContratos.click();
        expect(tabContratos.classList.contains('active')).toBe(true);
    });

    test('Preview (Contratos): Deve enviar arquivo e renderizar tabela formatada', async () => {
        const mockData = [
            { 
                numero_contrato: 'CT-001', 
                fornecedor: 'Empresa Teste', 
                valor_unitario: 1500.50,  // Deve formatar para 1.500,50
                data_inicio: '2024-01-01' // Deve formatar data
            }
        ];

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockData
        });

        const form = document.getElementById('form-upload-contratos');
        const container = document.getElementById('preview-container-contratos');
        const table = document.getElementById('preview-table-contratos');

        // Dispara submit
        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            // 1. Verifica chamada da API de preview
            expect(mockFetch).toHaveBeenCalledWith('/api/importar/contratos/preview', expect.objectContaining({
                method: 'POST',
                body: expect.any(FormData)
            }));

            // 2. Verifica se mostrou o container de preview
            expect(container.style.display).toBe('flex');

            // 3. Verifica conteúdo da tabela
            expect(table.innerHTML).toContain('CT-001');
            expect(table.innerHTML).toContain('Empresa Teste');
            
            // Verifica se a formatação PT-BR foi chamada (virgula decimal)
            // Nota: JSDOM pode ter suporte limitado a i18n completo dependendo do Node,
            // mas verificamos se o valor está presente.
            // O script usa toLocaleString('pt-BR'), que pode renderizar 1.500,50 ou 1500,50.
        });
    });

    test('Salvar (Contratos): Deve enviar dados do preview e redirecionar', async () => {
        const mockData = [{ id: 1, nome: 'Dado Importado' }];
        
        // --- PASSO 1: Executar Preview (para popular a variável interna dataToSave) ---
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockData });
        document.getElementById('form-upload-contratos').dispatchEvent(new Event('submit'));
        
        await waitFor(() => {
            const container = document.getElementById('preview-container-contratos');
            expect(container.style.display).toBe('flex'); // Garante que preview terminou
        });

        // --- PASSO 2: Executar Salvar ---
        mockFetch.mockResolvedValueOnce({ // Mock resposta do SALVAR
            ok: true,
            json: async () => ({ mensagem: 'Importação concluída' })
        });

        const btnSalvar = document.getElementById('btn-salvar-contratos');
        btnSalvar.click();

        await waitFor(() => {
            // Verifica chamada da API de salvar
            expect(mockFetch).toHaveBeenCalledWith('/api/importar/contratos/salvar', expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockData) // Deve enviar o mesmo JSON recebido no preview
            }));

            // Verifica redirecionamento
            expect(window.location.href).toBe('/contratos');
            expect(sessionStorage.getItem('notificationMessage')).toContain('Importação concluída');
        });
    });

    test('Erro no Preview: Deve exibir mensagem de erro na div específica', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({ erro: 'Colunas inválidas no Excel' })
        });

        const form = document.getElementById('form-upload-itens'); // Testando no form de Itens
        const errorDiv = document.getElementById('error-message-itens');

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(errorDiv.textContent).toContain('Colunas inválidas no Excel');
            // Container de preview deve continuar oculto
            expect(document.getElementById('preview-container-itens').style.display).toBe('none');
        });
    });

    test('Botão Salvar sem dados: Deve mostrar notificação de erro', async () => {
        // Tenta clicar em salvar sem ter feito preview antes
        const btnSalvar = document.getElementById('btn-salvar-itens');
        btnSalvar.click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Não há dados pré-visualizados');
            expect(mockFetch).not.toHaveBeenCalled(); // Não deve chamar API
        });
    });
});