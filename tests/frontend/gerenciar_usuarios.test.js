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
        // Garante Timers Reais por padrão
        jest.useRealTimers(); 
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
    // 3. SEUS TESTES ORIGINAIS (MANTIDOS INTACTOS)
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

        await window.abrirModalParaEditar(5);

        const passwordGroup = document.getElementById('password-group');
        expect(passwordGroup.style.display).toBe('none');
        expect(document.getElementById('user-nome').value).toBe('usuario_antigo');

        document.getElementById('user-nome').value = 'usuario_novo';
        document.getElementById('user-senha').value = 'senha_que_nao_deve_ir';
        
        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/users/5', expect.objectContaining({
                method: 'PUT'
            }));
            
            const call = mockFetch.mock.calls.find(call => call[1] && call[1].method === 'PUT');
            expect(call).toBeDefined(); 
            const body = JSON.parse(call[1].body);
            expect(body.username).toBe('usuario_novo');
            expect(body.password).toBeUndefined(); 
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

    // ==========================================================================
    // 4. NOVOS TESTES (COBERTURA FALTANTE)
    // ==========================================================================

    test('Notificação: Deve desaparecer após 5s (Mock Manual do setTimeout)', async () => {
        // Cobertura linhas 23-25
        const originalSetTimeout = global.setTimeout;
        let callbackRemocao = null;
        
        const mockSetTimeout = jest.fn((cb, delay) => {
            if (delay === 5000) callbackRemocao = cb;
            return 123;
        });
        global.setTimeout = mockSetTimeout;
        window.setTimeout = mockSetTimeout;

        try {
            // Gera erro para chamar showNotification
            document.getElementById('btn-add-user').click();
            document.getElementById('user-nome').value = 'test';
            document.getElementById('user-senha').value = '123'; // Inválido
            document.getElementById('form-user').dispatchEvent(new Event('submit'));

            await waitFor(() => {
                expect(document.getElementById('notification-area').children.length).toBeGreaterThan(0);
            });

            expect(mockSetTimeout).toHaveBeenCalledWith(expect.any(Function), 5000);

            if (callbackRemocao) {
                const notif = document.querySelector('.notification');
                callbackRemocao(); // Executa o timer
                expect(notif.style.opacity).toBe('0');
                notif.dispatchEvent(new Event('transitionend')); // Cobertura do addEventListener
                expect(document.getElementById('notification-area').children.length).toBe(0);
            }
        } finally {
            global.setTimeout = originalSetTimeout;
            window.setTimeout = originalSetTimeout;
        }
    });

    test('Inicialização: Deve exibir msg da SessionStorage se existir', async () => {
        // Cobertura linhas 38-40
        // Precisamos recarregar o script "do zero" com a session preenchida
        jest.resetModules();
        sessionStorage.setItem('notificationMessage', 'Mensagem da Sessão');
        sessionStorage.setItem('notificationType', 'warning');
        
        require('../../app/static/js/gerenciar_usuarios');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Mensagem da Sessão');
            expect(notif.querySelector('.warning')).toBeTruthy();
            // Deve limpar após mostrar
            expect(sessionStorage.getItem('notificationMessage')).toBeNull();
        });
    });

    test('Resiliência: Funções globais devem tratar DOM quebrado', async () => {
        // Cobertura linhas 44-47, 51-58 (guards)
        jest.resetModules();
        document.body.innerHTML = '<div>Nada aqui</div>'; // DOM sem modal
        require('../../app/static/js/gerenciar_usuarios');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        // Chama função global - não deve quebrar
        await window.abrirModalParaEditar(1);
        
        // Se chegou aqui sem erro, passou. Verifica que nada aconteceu.
        expect(mockFetch).not.toHaveBeenCalled();
    });

    test('Toggle Status: Cancelar no confirm', async () => {
        // Cobertura linha 104
        window.confirm.mockReturnValueOnce(false);
        await window.toggleUserStatus(1, true);
        expect(mockFetch).not.toHaveBeenCalled();
    });

    test('Resetar Senha: Erro na API (Catch Block)', async () => {
        // Cobertura linha 119
        setupRouterMock([{
            url: '/reset-password', method: 'POST',
            ok: false, status: 500, body: { detail: 'Erro Crítico' }
        }]);

        await window.resetarSenha(10);

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Erro ao redefinir senha');
        });
    });

    test('Click Overlay: Deve fechar modal', () => {
        // Cobertura linha 136-137
        const modal = document.getElementById('modal-user');
        modal.style.display = 'flex';
        
        // Clica no overlay
        modal.click();
        
        expect(modal.style.display).toBe('none');
    });

    test('Form Submit: Erro Genérico (Catch Block)', async () => {
        // Cobertura linha 181
        document.getElementById('btn-add-user').click();
        document.getElementById('user-nome').value = 'admin';
        document.getElementById('user-senha').value = '12345678';

        // Mock de erro de rede
        mockFetch.mockRejectedValue(new Error('Rede Indisponível'));

        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Rede Indisponível');
        });
    });
});