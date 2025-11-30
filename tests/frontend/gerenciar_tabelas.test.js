/**
 * @jest-environment jsdom
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock para window.alert e window.confirm
global.alert = jest.fn();
// Default confirm true
global.confirm = jest.fn(() => true);

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
    <h1 id="pageTitle">Gerenciar</h1>

    <div class="nav-buttons">
        <button class="nav-btn" data-target="unidades" data-coluna="nome">Unidades</button>
        <button class="nav-btn" data-target="categorias" data-coluna="nome">Categorias</button>
    </div>

    <div id="empty-state" style="display: none;">Selecione uma tabela</div>

    <div id="tabela-container" style="display: none;">
        <button id="btnNovoItem">Novo Item</button>
        <table>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <!-- Modal -->
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

    const setupRouterMock = (routes = []) => {
        mockFetch.mockImplementation(async (url, options) => {
            const method = options ? options.method : 'GET';
            // Simples verificação de includes para URL
            const match = routes.find(r => url.includes(r.url) && (r.method || 'GET') === method);
            
            if (match) {
                return {
                    ok: match.ok !== false,
                    status: match.status || 200,
                    json: async () => match.body !== undefined ? match.body : []
                };
            }
            // Default 404 se não achar rota mockada
            return { ok: false, status: 404, json: async () => ({}) };
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;

        // Reload mock
        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };

        // Reinicia módulos para re-bindar eventos no novo DOM
        jest.resetModules();
        require('../../app/static/js/gerenciar_tabelas');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    test('Carregar Tabela: Sucesso com dados', async () => {
        setupRouterMock([
            { 
                url: '/api/tabelas-sistema/unidades', 
                body: [{ id: 1, nome: 'Metro' }, { id: 2, nome: 'Quilo' }] 
            }
        ]);

        const btn = document.querySelector('.nav-btn[data-target="unidades"]');
        btn.click();

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/unidades');
            expect(document.getElementById('pageTitle').textContent).toContain('Unidades');
            // Verifica se renderizou no tbody
            const body = document.getElementById('tableBody');
            expect(body.innerHTML).toContain('Metro');
            expect(body.innerHTML).toContain('Quilo');
        });
    });

    test('Carregar Tabela: Vazio (Nenhum registro)', async () => {
        setupRouterMock([
            { 
                url: '/api/tabelas-sistema/categorias', 
                body: [] 
            }
        ]);

        const btn = document.querySelector('.nav-btn[data-target="categorias"]');
        btn.click();

        await waitFor(() => {
            const body = document.getElementById('tableBody');
            expect(body.textContent).toContain('Nenhum registro encontrado');
        });
    });

    test('Carregar Tabela: Erro na API', async () => {
        setupRouterMock([
            { 
                url: '/api/tabelas-sistema/unidades', 
                ok: false,
                status: 500
            }
        ]);

        const btn = document.querySelector('.nav-btn[data-target="unidades"]');
        btn.click();

        await waitFor(() => {
            const body = document.getElementById('tableBody');
            expect(body.textContent).toContain('Erro ao carregar dados');
        });
    });

    test('Adicionar Item: Fluxo completo de Sucesso', async () => {
        // Mock GET inicial (vazio) e POST
        setupRouterMock([
            { url: '/api/tabelas-sistema/categorias', method: 'GET', body: [] },
            { url: '/api/tabelas-sistema/categorias', method: 'POST', body: { id: 10, nome: 'Nova Cat' } }
        ]);

        // Seleciona categoria primeiro para setar currentTabela
        document.querySelector('.nav-btn[data-target="categorias"]').click();

        // Abre modal
        const btnNovo = document.getElementById('btnNovoItem');
        btnNovo.click();

        const modal = document.getElementById('modal-item');
        // Verifica se modal abriu (pela classe ou display, dependendo da impl. O JS usa style.display = 'flex')
        await waitFor(() => expect(modal.style.display).toBe('flex'));

        // Preenche form
        document.getElementById('item-nome').value = 'Nova Cat';

        // Submit
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            // Verifica POST
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/tabelas-sistema/categorias'),
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({ nome: 'Nova Cat' })
                })
            );
            // Verifica alert de sucesso
            expect(global.alert).toHaveBeenCalledWith('Salvo com sucesso!');
            // Verifica se modal fechou
            expect(modal.style.display).toBe('none');
        });
    });

    test('Adicionar Item: Erro de Validação (Campo vazio)', async () => {
        document.querySelector('.nav-btn[data-target="categorias"]').click();

        // Abre modal e submete vazio
        document.getElementById('btnNovoItem').click();
        document.getElementById('item-nome').value = '';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith('Campo obrigatório.');
            expect(mockFetch).not.toHaveBeenCalledWith(
                expect.anything(),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    test('Excluir Item: Deve confirmar e fazer DELETE', async () => {
        setupRouterMock([
            { url: '/api/tabelas-sistema/categorias', method: 'GET', body: [] }, // Reload após delete
            { url: '/api/tabelas-sistema/categorias/99', method: 'DELETE', status: 200 }
        ]);

        // Precisamos selecionar a tabela primeiro para setar currentTabela
        document.querySelector('.nav-btn[data-target="categorias"]').click();

        // JS define window.deletarItem. Chamamos direto.
        await window.deletarItem(99);

        expect(global.confirm).toHaveBeenCalled();
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/tabelas-sistema/categorias/99'),
            expect.objectContaining({ method: 'DELETE' })
        );
    });
});
