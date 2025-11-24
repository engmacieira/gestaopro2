/**
 * @jest-environment jsdom
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;

const waitFor = async (callback, timeout = 2000) => {
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
            <button type="button" id="btn-salvar-contratos">Salvar Contratos</button>
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
            <button type="button" id="btn-salvar-itens">Salvar Itens</button>
        </div>
    </div>
`;

describe('Testes Frontend - Importação', () => {
    let documentSpy;

    const setupRouterMock = (routes = []) => {
        mockFetch.mockImplementation(async (url, options) => {
            const method = options ? options.method : 'GET';
            const match = routes.find(r => url.includes(r.url) && (r.method || 'GET') === method);
            
            if (match) {
                return {
                    ok: match.ok !== false,
                    status: match.status || 200,
                    json: async () => match.body || {}
                };
            }
            return { ok: true, json: async () => [] };
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        documentSpy = jest.spyOn(document, 'addEventListener');

        window.redirectUrlContratos = '/contratos';
        window.redirectUrlItens = '/itens';

        delete window.location;
        window.location = { href: '' };

        jest.resetModules();
        require('../../app/static/js/importar');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        if (documentSpy) {
            documentSpy.mock.calls.forEach(call => document.removeEventListener(call[0], call[1]));
            documentSpy.mockRestore();
        }
        delete window.redirectUrlContratos;
        delete window.redirectUrlItens;
    });

    test('Inicialização: Deve exibir notificação via sessionStorage', () => {
        sessionStorage.setItem('notificationMessage', 'Upload realizado');
        sessionStorage.setItem('notificationType', 'success');
        
        documentSpy.mock.calls.forEach(call => document.removeEventListener(call[0], call[1]));
        document.body.innerHTML = DOM_HTML;
        
        jest.resetModules();
        require('../../app/static/js/importar');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        const notif = document.querySelector('.notification.success');
        expect(notif).toBeTruthy();
        expect(notif.textContent).toBe('Upload realizado');
    });

    test('Abas: Deve alternar visibilidade entre Contratos e Itens', () => {
        const linkContratos = document.getElementById('link-contratos');
        const linkItens = document.getElementById('link-itens');
        const tabContratos = document.getElementById('tab-contratos');
        const tabItens = document.getElementById('tab-itens');

        expect(tabContratos.classList.contains('active')).toBe(true);

        linkItens.click();
        expect(tabContratos.classList.contains('active')).toBe(false);
        expect(tabItens.classList.contains('active')).toBe(true);

        linkContratos.click();
        expect(tabContratos.classList.contains('active')).toBe(true);
    });

    test('Preview Contratos: Deve formatar dados e escapar HTML (Segurança)', async () => {
        const maliciousData = [{ 
            numero_contrato: '<b>Negrito</b>', 
            fornecedor: '<script>alert(1)</script>',
            valor_unitario: 2500.50,
            data_inicio: '2024-12-31'
        }];

        setupRouterMock([{
            url: '/api/importar/contratos/preview',
            method: 'POST',
            body: maliciousData
        }]);

        document.getElementById('form-upload-contratos').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const table = document.getElementById('preview-table-contratos');
            expect(table.innerHTML).toContain('&lt;b&gt;Negrito&lt;/b&gt;');
            expect(table.innerHTML).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
            expect(table.textContent).toMatch(/2[\.,]500[\.,]50/);
            expect(document.getElementById('preview-container-contratos').style.display).toBe('flex');
        });
    });

    test('Salvar Contratos: Deve enviar dados e redirecionar', async () => {
        const dadosParaSalvar = [{ id: 1, nome: 'Teste' }];

        setupRouterMock([
            { url: '/api/importar/contratos/preview', method: 'POST', body: dadosParaSalvar },
            { url: '/api/importar/contratos/salvar', method: 'POST', body: { mensagem: 'Sucesso' } }
        ]);

        const form = document.getElementById('form-upload-contratos');
        form.dispatchEvent(new Event('submit'));
        
        await waitFor(() => {
             const container = document.getElementById('preview-container-contratos');
             if(container.style.display !== 'flex') throw new Error('Preview não abriu');
        });

        const btnSalvar = document.getElementById('btn-salvar-contratos');
        btnSalvar.click();

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/importar/contratos/salvar', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(dadosParaSalvar)
            }));
            expect(window.location.href).toBe('/contratos');
        });
    });

    test('Preview Erro: Deve exibir mensagem na div de erro', async () => {
        setupRouterMock([{
            url: '/api/importar/itens/global/preview',
            method: 'POST',
            ok: false,
            status: 400,
            body: { erro: 'Arquivo inválido' }
        }]);

        document.getElementById('form-upload-itens').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const errorDiv = document.getElementById('error-message-itens');
            expect(errorDiv.textContent).toContain('Arquivo inválido');
            expect(document.getElementById('preview-container-itens').style.display).toBe('none');
        });
    });

    test('Salvar Erro: Deve exibir notificação e reabilitar botão', async () => {
        const dadosMock = [{ id: 1, item: 'Teste' }];
        const container = document.getElementById('preview-container-itens');
        
        container.dataset.cacheData = JSON.stringify(dadosMock);

        setupRouterMock([
            { 
                url: '/api/importar/itens/global/salvar', 
                method: 'POST', 
                ok: false, 
                status: 500, 
                body: { erro: 'Erro no Banco' } 
            }
        ]);

        const btnSalvar = document.getElementById('btn-salvar-itens');

        btnSalvar.click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Erro no Banco');
            expect(btnSalvar.disabled).toBe(false);
        });
    });

    test('Validação: Não deve salvar sem preview prévio', async () => {
        const btnSalvar = document.getElementById('btn-salvar-contratos');
        btnSalvar.click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Não há dados pré-visualizados');
            expect(mockFetch).not.toHaveBeenCalledWith(expect.stringContaining('salvar'), expect.anything());
        });
    });
});