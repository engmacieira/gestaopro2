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

// HTML Simulado (Baseado em _importar_itens_steps.html)
const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>

    <form id="form-upload-itens">
        <input type="file" name="arquivo_excel" id="arquivo_excel">
        <button type="submit">Carregar</button>
    </form>

    <div id="error-message"></div>

    <div id="preview-container" style="display: none;">
        <table id="preview-table">
            <thead></thead>
            <tbody></tbody>
        </table>
        <button id="btn-salvar-dados">Salvar Itens</button>
    </div>
`;

describe('Testes Frontend - Importar Itens (Contrato Específico)', () => {
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

        // Variáveis globais esperadas pelo script
        window.idContratoGlobal = 500;
        window.redirectUrlGlobal = '/contrato/500';

        // Mock Location
        delete window.location;
        window.location = { href: '' };

        // Carrega o script
        jest.resetModules();
        require('../../app/static/js/importar_itens');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // 3. TEARDOWN
    // ==========================================================================
    afterEach(() => {
        delete window.idContratoGlobal;
        delete window.redirectUrlGlobal;
    });

    // ==========================================================================
    // 4. TESTES
    // ==========================================================================

    test('Preview: Deve enviar arquivo e exibir tabela formatada', async () => {
        const mockData = [
            { 
                descricao: 'Item A', 
                quantidade: 10.5,      // Deve formatar para 10,50
                valor_unitario: 100.0  // Deve formatar para 100,00
            }
        ];

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockData
        });

        const form = document.getElementById('form-upload-itens');
        const container = document.getElementById('preview-container');
        const table = document.getElementById('preview-table');

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            // 1. Verifica URL com ID do contrato
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/importar/itens/500/preview', 
                expect.objectContaining({ method: 'POST' })
            );

            // 2. Verifica exibição
            expect(container.style.display).toBe('flex');
            
            // 3. Verifica conteúdo e formatação
            expect(table.innerHTML).toContain('Item A');
            // Verificamos se os valores numéricos aparecem (a formatação exata depende do suporte i18n do Node)
            // Mas garantimos que o script tentou renderizar
            expect(table.innerHTML).toMatch(/10,50|10.50/); 
        });
    });

    test('Erro no Preview: Deve mostrar mensagem na div de erro', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({ erro: 'Arquivo inválido' })
        });

        const errorDiv = document.getElementById('error-message');
        document.getElementById('form-upload-itens').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(errorDiv.textContent).toContain('Arquivo inválido');
            expect(document.getElementById('preview-container').style.display).toBe('none');
        });
    });

    test('Salvar: Deve enviar dados e redirecionar para o contrato', async () => {
        const mockData = [{ item: 1 }];

        // --- PASSO 1: Preview (para popular dadosParaSalvar) ---
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockData });
        document.getElementById('form-upload-itens').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(document.getElementById('preview-container').style.display).toBe('flex'));

        // --- PASSO 2: Salvar ---
        mockFetch.mockResolvedValueOnce({ // Mock resposta do Save
            ok: true,
            json: async () => ({ mensagem: 'Sucesso' })
        });

        const btnSalvar = document.getElementById('btn-salvar-dados');
        btnSalvar.click();

        await waitFor(() => {
            // Verifica URL de salvamento
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/importar/itens/500/salvar', 
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify(mockData)
                })
            );

            // Verifica redirecionamento
            expect(window.location.href).toBe('/contrato/500');
            expect(sessionStorage.getItem('notificationMessage')).toContain('Sucesso');
        });
    });

    test('Salvar Vazio: Não deve permitir salvar sem preview', async () => {
        const btnSalvar = document.getElementById('btn-salvar-dados');
        btnSalvar.click(); // Clica direto sem fazer upload antes

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Não há dados');
            expect(mockFetch).not.toHaveBeenCalled();
        });
    });
});