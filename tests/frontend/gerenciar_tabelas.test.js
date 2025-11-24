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

    <nav>
        <a href="#" class="management-link" data-tabela="unidades" data-nome-exibicao="Unidades">Unidades</a>
        <a href="#" class="management-link" data-tabela="categorias" data-nome-exibicao="Categorias">Categorias</a>
    </nav>

    <div id="content-area"></div>

    <template id="table-template">
        <h2 id="table-title"></h2>
        <button id="btn-add-new-item">Adicionar Novo</button>
        <div class="table-wrapper">
            <table class="data-table">
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </template>

    <div id="modal-item" style="display: none;">
        <h2 id="modal-titulo"></h2>
        <form id="form-item">
            <input type="text" id="item-nome" name="nome">
            <button type="submit">Salvar</button>
            <button id="btn-cancelar-modal" type="button">Cancelar</button>
        </form>
        <button id="btn-fechar-modal">X</button>
    </div>
`;

describe('Testes Frontend - Gerenciar Tabelas', () => {
    let reloadMock;
    let documentSpy;
    let windowSpy;

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
        windowSpy = jest.spyOn(window, 'addEventListener');

        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };
        window.confirm = jest.fn(() => true);

        jest.resetModules();
        require('../../app/static/js/gerenciar_tabelas');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        if (documentSpy) documentSpy.mockRestore();
        if (windowSpy) windowSpy.mockRestore();
    });

    test('Carregar Tabela: Sucesso com dados', async () => {
        setupRouterMock([
            { 
                url: '/api/tabelas-sistema/unidades', 
                body: [{ id: 1, nome: 'Metro' }, { id: 2, nome: 'Quilo' }] 
            }
        ]);

        const link = document.querySelector('.management-link[data-tabela="unidades"]');
        link.click();

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/unidades');
            expect(document.getElementById('table-title').textContent).toContain('Unidades');
            expect(document.getElementById('table-body').innerHTML).toContain('Metro');
        });
    });

    test('Carregar Tabela: Deve exibir mensagem de "Vazio" se não houver itens', async () => {
        setupRouterMock([
            { 
                url: '/api/tabelas-sistema/categorias', 
                body: [] 
            }
        ]);

        document.querySelector('.management-link[data-tabela="categorias"]').click();

        await waitFor(() => {
            const body = document.getElementById('table-body');
            expect(body.innerHTML).toContain('empty-state');
            expect(body.textContent).toContain('Nenhum item cadastrado');
        });
    });

    test('Carregar Tabela: Deve tratar erro da API (500)', async () => {
        setupRouterMock([
            { 
                url: '/api/tabelas-sistema/unidades', 
                ok: false,
                status: 500,
                body: { erro: 'Falha no Servidor' }
            }
        ]);

        document.querySelector('.management-link[data-tabela="unidades"]').click();

        await waitFor(() => {
            const body = document.getElementById('table-body');
            expect(body.innerHTML).toContain('notification error');
            expect(body.textContent).toContain('Falha no Servidor');
        });
    });

    test('Adicionar Item: Fluxo completo de Sucesso', async () => {
        setupRouterMock([
            { url: '/api/tabelas-sistema/categorias', method: 'GET', body: [] },
            { url: '/api/tabelas-sistema/categorias', method: 'POST', body: { id: 10, nome: 'Nova Cat' } }
        ]);

        document.querySelector('.management-link[data-tabela="categorias"]').click();
        await waitFor(() => expect(document.getElementById('btn-add-new-item')).toBeTruthy());

        document.getElementById('btn-add-new-item').click();
        const modal = document.getElementById('modal-item');
        expect(modal.style.display).toBe('flex');

        document.getElementById('item-nome').value = 'Nova Cat';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/categorias', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ nome: 'Nova Cat' })
            }));
            expect(document.getElementById('notification-area').textContent).toContain('criado com sucesso');
        });
    });

    test('Editar Item: Fluxo completo de Sucesso', async () => {
        setupRouterMock([
            { url: '/api/tabelas-sistema/unidades', method: 'GET', body: [{ id: 5, nome: 'Kg' }] },
            { url: '/api/tabelas-sistema/unidades/5', method: 'PUT', body: { id: 5, nome: 'Kilograma' } }
        ]);

        document.querySelector('.management-link[data-tabela="unidades"]').click();
        await waitFor(() => document.getElementById('table-title'));

        window.abrirModalParaEditar(5, 'Kg');
        expect(document.getElementById('item-nome').value).toBe('Kg');

        document.getElementById('item-nome').value = 'Kilograma';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/tabelas-sistema/unidades/5'), expect.objectContaining({
                method: 'PUT'
            }));
            expect(document.getElementById('notification-area').textContent).toContain('atualizado com sucesso');
        });
    });

    test('Excluir Item: Deve confirmar e fazer DELETE', async () => {
        setupRouterMock([
            { url: '/api/tabelas-sistema/categorias', method: 'GET', body: [] },
            { url: '/api/tabelas-sistema/categorias/99', method: 'DELETE', status: 204 }
        ]);

        document.querySelector('.management-link[data-tabela="categorias"]').click();
        await waitFor(() => document.getElementById('table-title'));

        await window.excluirItem(99);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/categorias/99', {
                method: 'DELETE'
            });
            expect(document.getElementById('notification-area').textContent).toContain('Item excluído');
        });
    });

    test('Salvar (Erro API): Deve exibir erro e NÃO fechar modal', async () => {
        setupRouterMock([
            { url: '/api/tabelas-sistema/categorias', method: 'GET', body: [] },
            { 
                url: '/api/tabelas-sistema/categorias', 
                method: 'POST', 
                ok: false, 
                status: 400, 
                body: { erro: 'Nome duplicado' } 
            }
        ]);

        document.querySelector('.management-link[data-tabela="categorias"]').click();
        await waitFor(() => document.getElementById('btn-add-new-item').click());

        document.getElementById('item-nome').value = 'Duplicado';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Nome duplicado');
            
            const modal = document.getElementById('modal-item');
            expect(modal.style.display).toBe('flex');
        });
    });

    test('Validação: Salvar sem tabela ativa', async () => {
        document.getElementById('item-nome').value = 'Orfão';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(document.getElementById('notification-area').textContent).toContain('Nenhuma tabela ativa');
            expect(mockFetch).not.toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ method: 'POST' }));
        });
    });
});