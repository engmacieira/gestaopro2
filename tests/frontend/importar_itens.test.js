/**
 * @jest-environment jsdom
 */

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

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        window.idContratoGlobal = 500;
        window.redirectUrlGlobal = '/contrato/500';

        delete window.location;
        window.location = { href: '' };

        jest.resetModules();
        require('../../app/static/js/importar_itens');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        delete window.idContratoGlobal;
        delete window.redirectUrlGlobal;
    });

    test('Preview: Deve enviar arquivo e exibir tabela formatada', async () => {
        const mockData = [
            { 
                descricao: 'Item A', 
                quantidade: 10.5,      
                valor_unitario: 100.0  
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
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/importar/itens/500/preview', 
                expect.objectContaining({ method: 'POST' })
            );

            expect(container.style.display).toBe('flex');
            
            expect(table.innerHTML).toContain('Item A');
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

        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockData });
        document.getElementById('form-upload-itens').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(document.getElementById('preview-container').style.display).toBe('flex'));

        mockFetch.mockResolvedValueOnce({ 
            ok: true,
            json: async () => ({ mensagem: 'Sucesso' })
        });

        const btnSalvar = document.getElementById('btn-salvar-dados');
        btnSalvar.click();

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/importar/itens/500/salvar', 
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify(mockData)
                })
            );

            expect(window.location.href).toBe('/contrato/500');
            expect(sessionStorage.getItem('notificationMessage')).toContain('Sucesso');
        });
    });

    test('Salvar Vazio: Não deve permitir salvar sem preview', async () => {
        const btnSalvar = document.getElementById('btn-salvar-dados');
        btnSalvar.click(); 

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Não há dados');
            expect(mockFetch).not.toHaveBeenCalled();
        });
    });
});