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

// HTML Simulado (Sidebar + Área de Conteúdo + Template + Modal)
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

    // ==========================================================================
    // 2. SETUP
    // ==========================================================================
    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Patch de Compatibilidade (innerText)
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // Spies
        documentSpy = jest.spyOn(document, 'addEventListener');
        windowSpy = jest.spyOn(window, 'addEventListener');

        // Mocks Globais
        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };
        
        window.confirm = jest.fn(() => true);

        // Carrega o script
        jest.resetModules();
        require('../../app/static/js/gerenciar_tabelas');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // 3. TEARDOWN
    // ==========================================================================
    afterEach(() => {
        if (documentSpy) {
            documentSpy.mock.calls.forEach(c => document.removeEventListener(c[0], c[1]));
            documentSpy.mockRestore();
        }
        if (windowSpy) {
            windowSpy.mock.calls.forEach(c => window.removeEventListener(c[0], c[1]));
            windowSpy.mockRestore();
        }
    });

    // ==========================================================================
    // 4. TESTES
    // ==========================================================================

    test('Carregar Tabela: Deve clonar template e buscar dados ao clicar no link', async () => {
        // Mock dados da tabela 'unidades'
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ([
                { id: 1, nome: 'Metro' },
                { id: 2, nome: 'Quilo' }
            ])
        });

        // Clica no link "Unidades"
        const linkUnidades = document.querySelector('.management-link[data-tabela="unidades"]');
        linkUnidades.click();

        // Verifica se o template foi inserido
        const contentArea = document.getElementById('content-area');
        
        // Aguarda fetch e renderização
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/unidades');
            
            // Verifica título inserido dinamicamente
            const titulo = document.getElementById('table-title');
            expect(titulo).toBeTruthy();
            expect(titulo.textContent).toContain('Unidades');

            // Verifica linhas da tabela
            const tbody = document.getElementById('table-body');
            expect(tbody.innerHTML).toContain('Metro');
            expect(tbody.innerHTML).toContain('Quilo');
        });
    });

    test('Adicionar Item: Deve abrir modal e fazer POST na tabela ativa', async () => {
        // 1. Carrega a tabela 'categorias' primeiro
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [] // Tabela vazia inicialmente
        });
        document.querySelector('.management-link[data-tabela="categorias"]').click();
        
        await waitFor(() => expect(document.getElementById('btn-add-new-item')).toBeTruthy());

        // 2. Clica em "Adicionar Novo"
        document.getElementById('btn-add-new-item').click();
        const modal = document.getElementById('modal-item');
        expect(modal.style.display).toBe('flex');
        expect(document.getElementById('modal-titulo').textContent).toContain('Adicionar Novo');

        // 3. Preenche e Salva
        mockFetch.mockResolvedValueOnce({ // Mock da resposta do POST
            ok: true,
            json: async () => ({ id: 10, nome: 'Nova Categoria' })
        });
        
        // Mock do reload da tabela após salvar
        mockFetch.mockResolvedValueOnce({ 
            ok: true, 
            json: async () => ([{ id: 10, nome: 'Nova Categoria' }]) 
        });

        document.getElementById('item-nome').value = 'Nova Categoria';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            // Verifica se fez POST na URL correta da tabela ativa
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/categorias', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ nome: 'Nova Categoria' })
            }));
            
            // Verifica notificação
            expect(document.getElementById('notification-area').textContent).toContain('criado com sucesso');
        });
    });

    test('Editar Item: Deve abrir modal com dados e fazer PUT', async () => {
        // 1. Carrega tabela
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ([{ id: 5, nome: 'Item Antigo' }])
        });
        document.querySelector('.management-link[data-tabela="unidades"]').click();
        await waitFor(() => expect(document.getElementById('table-body').textContent).toContain('Item Antigo'));

        // 2. Abre modal de edição via função global (simulando clique no botão da tabela)
        window.abrirModalParaEditar(5, 'Item Antigo');

        const modal = document.getElementById('modal-item');
        const inputNome = document.getElementById('item-nome');
        
        expect(modal.style.display).toBe('flex');
        expect(inputNome.value).toBe('Item Antigo'); // Verifica preenchimento

        // 3. Edita e Salva
        mockFetch.mockResolvedValueOnce({ // Mock PUT
            ok: true,
            json: async () => ({ id: 5, nome: 'Item Editado' })
        });
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] }); // Mock reload

        inputNome.value = 'Item Editado';
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/unidades/5', expect.objectContaining({
                method: 'PUT',
                body: JSON.stringify({ nome: 'Item Editado' })
            }));
            expect(document.getElementById('notification-area').textContent).toContain('atualizado com sucesso');
        });
    });

    test('Excluir Item: Deve confirmar e fazer DELETE', async () => {
        // 1. Carrega tabela (precisa ter tabela ativa para excluir)
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
        document.querySelector('.management-link[data-tabela="categorias"]').click();
        await waitFor(() => expect(document.getElementById('table-title')).toBeTruthy());

        // 2. Chama exclusão
        mockFetch.mockResolvedValueOnce({ // Mock DELETE
            ok: true,
            status: 204,
            json: async () => ({})
        });
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] }); // Mock reload

        await window.excluirItem(99);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/tabelas-sistema/categorias/99', {
                method: 'DELETE'
            });
            expect(document.getElementById('notification-area').textContent).toContain('Item excluído');
        });
    });

    test('Validação: Não deve salvar sem nome ou tabela ativa', async () => {
        // Tenta salvar sem carregar tabela e sem nome
        const form = document.getElementById('form-item');
        form.dispatchEvent(new Event('submit'));

        await new Promise(r => setTimeout(r, 100));

        expect(mockFetch).not.toHaveBeenCalled();
        expect(document.getElementById('notification-area').textContent).toContain('Nome é obrigatório');
    });
});