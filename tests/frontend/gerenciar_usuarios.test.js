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

// HTML Simulado
const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>

    <button id="btn-add-user">Adicionar Usuário</button>

    <div id="modal-user" style="display: none;">
        <h2 id="modal-user-title">Adicionar Usuário</h2>
        <form id="form-user">
            <input type="text" id="user-nome" name="username">
            <select id="user-nivel" name="nivel_acesso">
                <option value="1">Admin</option>
                <option value="2">User</option>
            </select>
            
            <div id="password-group">
                <input type="password" id="user-senha" name="password">
            </div>

            <button type="submit">Salvar</button>
            <button type="button" class="close-button">X</button>
        </form>
    </div>
`;

describe('Testes Frontend - Gerenciar Usuários', () => {
    let reloadMock;
    let documentSpy;
    let windowSpy;

    // Helper de Roteamento (Smart Mock)
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
            return { ok: true, json: async () => ({}) };
        });
    };

    // ==========================================================================
    // 2. SETUP
    // ==========================================================================
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
        window.alert = jest.fn(); 

        jest.resetModules();
        require('../../app/static/js/gerenciar_usuarios');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        if (documentSpy) documentSpy.mockRestore();
        if (windowSpy) windowSpy.mockRestore();
    });

    // ==========================================================================
    // 3. TESTES - CRIAÇÃO (POST)
    // ==========================================================================

    test('Interface: Botão Adicionar deve mostrar campo de senha', () => {
        document.getElementById('btn-add-user').click();
        
        const passwordGroup = document.getElementById('password-group');
        const inputSenha = document.getElementById('user-senha');
        
        expect(passwordGroup.style.display).toBe('block');
        expect(inputSenha.required).toBe(true);
    });

    test('Criar Usuário: Sucesso com senha válida', async () => {
        setupRouterMock([{
            url: '/api/users/',
            method: 'POST',
            body: { id: 1, username: 'novo_admin' }
        }]);

        document.getElementById('btn-add-user').click();
        
        document.getElementById('user-nome').value = 'novo_admin';
        document.getElementById('user-nivel').value = '1';
        document.getElementById('user-senha').value = '12345678'; 

        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/users/', expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('"password":"12345678"')
            }));
            expect(sessionStorage.getItem('notificationMessage')).toContain('criado com sucesso');
        });
    });

    test('Criar Usuário: Deve bloquear senha curta (< 8 chars)', async () => {
        document.getElementById('btn-add-user').click();
        
        document.getElementById('user-nome').value = 'teste';
        document.getElementById('user-nivel').value = '1';
        document.getElementById('user-senha').value = '123'; 

        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('mínimo 8 caracteres');
            expect(mockFetch).not.toHaveBeenCalled(); 
        });
    });

    // ==========================================================================
    // 4. TESTES - EDIÇÃO (PUT)
    // ==========================================================================

    test('Editar Usuário: Fluxo Completo (Carregar -> Esconder Senha -> Salvar Sem Senha)', async () => {
        setupRouterMock([
            { 
                url: '/api/users/5', 
                method: 'GET', 
                body: { id: 5, username: 'usuario_antigo', nivel_acesso: 2 } 
            },
            { 
                url: '/api/users/5', 
                method: 'PUT', 
                body: { id: 5, username: 'usuario_novo' } 
            }
        ]);

        // 1. Abre Modal de Edição
        await window.abrirModalParaEditar(5);

        // Verifica se carregou dados
        const passwordGroup = document.getElementById('password-group');
        expect(passwordGroup.style.display).toBe('none');
        expect(document.getElementById('user-nome').value).toBe('usuario_antigo');

        // 2. Altera e Salva
        document.getElementById('user-nome').value = 'usuario_novo';
        document.getElementById('user-senha').value = 'senha_que_nao_deve_ir';
        
        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/users/5', expect.objectContaining({
                method: 'PUT'
            }));
            
            // CORREÇÃO AQUI: Verifica se call[1] existe antes de checar o método
            const call = mockFetch.mock.calls.find(call => call[1] && call[1].method === 'PUT');
            
            expect(call).toBeDefined(); // Garante que achou a chamada
            const body = JSON.parse(call[1].body);
            expect(body.username).toBe('usuario_novo');
            expect(body.password).toBeUndefined(); // PROVA DA BLINDAGEM
        });
    });

    test('Editar Usuário: Tratamento de erro ao carregar (404)', async () => {
        setupRouterMock([{
            url: '/api/users/99',
            method: 'GET',
            ok: false,
            status: 404,
            body: { detail: 'Usuário não encontrado' }
        }]);

        await window.abrirModalParaEditar(99);

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Usuário não encontrado');
            expect(document.getElementById('modal-user').style.display).not.toBe('flex');
        });
    });

    // ==========================================================================
    // 5. TESTES - AÇÕES ESPECIAIS
    // ==========================================================================

    test('Resetar Senha: Deve exibir nova senha no Alert', async () => {
        setupRouterMock([{
            url: '/api/users/10/reset-password',
            method: 'POST',
            body: { new_password: 'SENHA_TEMPORARIA_123' }
        }]);

        await window.resetarSenha(10);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/reset-password'), 
                { method: 'POST' }
            );
            expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('SENHA_TEMPORARIA_123'));
        });
    });

    test('Alternar Status: Deve enviar PATCH', async () => {
        setupRouterMock([{
            url: '/api/users/10',
            method: 'PATCH',
            body: { ativo: false }
        }]);

        await window.toggleUserStatus(10, true);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/users/10', 
                expect.objectContaining({
                    method: 'PATCH',
                    body: JSON.stringify({ ativo: false })
                })
            );
            expect(sessionStorage.getItem('notificationMessage')).toContain('inativado com sucesso');
        });
    });
});