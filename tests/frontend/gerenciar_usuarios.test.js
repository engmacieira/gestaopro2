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

// HTML Simulado (IDs e Names corrigidos conforme gerenciar_usuarios.js)
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

        // Spies
        documentSpy = jest.spyOn(document, 'addEventListener');
        windowSpy = jest.spyOn(window, 'addEventListener');

        // Mocks Globais
        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };
        
        window.confirm = jest.fn(() => true);
        window.alert = jest.fn(); // Mock do alert para o reset de senha

        // Carrega Script
        jest.resetModules();
        require('../../app/static/js/gerenciar_usuarios');
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

    test('Interface Novo Usuário: Deve abrir modal e exigir senha', () => {
        const btnAdd = document.getElementById('btn-add-user');
        const modal = document.getElementById('modal-user');
        const senhaGroup = document.getElementById('password-group');
        const inputSenha = document.getElementById('user-senha');
        const titulo = document.getElementById('modal-user-title');

        btnAdd.click();

        expect(modal.style.display).toBe('flex');
        expect(titulo.textContent).toContain('Adicionar');
        
        // Senha deve estar visível e obrigatória na criação
        expect(senhaGroup.style.display).toBe('block');
        expect(inputSenha.hasAttribute('required')).toBe(true);
    });

    test('Criar Usuário (POST): Deve enviar dados incluindo senha', async () => {
        // Mock sucesso criação
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 1, username: 'admin_novo' })
        });

        // Abre modal e preenche
        document.getElementById('btn-add-user').click();
        
        document.getElementById('user-nome').value = 'admin_novo';
        document.getElementById('user-nivel').value = '1';
        document.getElementById('user-senha').value = '12345678'; // > 8 chars

        // Submit
        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/users/', expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('"password":"12345678"')
            }));
            expect(reloadMock).toHaveBeenCalled();
        });

        expect(sessionStorage.getItem('notificationMessage')).toContain('criado com sucesso');
    });

    test('Interface Editar Usuário: Deve esconder campo de senha', async () => {
        // Mock dados do usuário
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                id: 5,
                username: 'usuario_existente',
                nivel_acesso: 2
            })
        });

        // Nome da função corrigida: abrirModalParaEditar
        await window.abrirModalParaEditar(5);

        const modal = document.getElementById('modal-user');
        const senhaGroup = document.getElementById('password-group');
        const inputSenha = document.getElementById('user-senha');
        const titulo = document.getElementById('modal-user-title');

        expect(mockFetch).toHaveBeenCalledWith('/api/users/5');
        expect(modal.style.display).toBe('flex');
        expect(titulo.textContent).toContain('Editar');
        
        // Senha deve estar OCULTA e NÃO obrigatória na edição
        expect(senhaGroup.style.display).toBe('none');
        expect(inputSenha.required).toBe(false);
        
        // Verifica preenchimento
        expect(document.getElementById('user-nome').value).toBe('usuario_existente');
    });

    test('Atualizar Usuário (PUT): Deve enviar dados SEM a senha', async () => {
        // 1. Carrega dados (GET)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 5, username: 'antigo', nivel_acesso: 2 })
        });
        await window.abrirModalParaEditar(5);

        // 2. Altera dados
        document.getElementById('user-nome').value = 'editado';
        // Preenche senha só para garantir que o código ignora (embora esteja oculta)
        document.getElementById('user-senha').value = 'senha_ignorada';

        // 3. Mock Salvar (PUT)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 5, username: 'editado' })
        });

        document.getElementById('form-user').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenLastCalledWith('/api/users/5', expect.objectContaining({
                method: 'PUT'
            }));

            // Verifica payload
            const callArgs = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
            const body = JSON.parse(callArgs[1].body);
            
            expect(body.username).toBe('editado');
            expect(body.password).toBeUndefined(); // Garante que senha não foi enviada
        });
    });

    test('Resetar Senha: Deve confirmar e exibir Alert', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ new_password: 'nova_senha_temp' })
        });

        await window.resetarSenha(10);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/users/10/reset-password', {
                method: 'POST'
            });
            // O código usa alert(), não notificação na tela
            expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('nova_senha_temp'));
        });
    });

    test('Alternar Status: Deve confirmar e enviar PATCH', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 10, username: 'teste', ativo: false })
        });

        // Nome da função corrigida: toggleUserStatus
        await window.toggleUserStatus(10, true);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/users/10', 
                expect.objectContaining({
                    method: 'PATCH',
                    body: JSON.stringify({ ativo: false })
                })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });
});