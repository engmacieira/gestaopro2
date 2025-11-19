/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

// Mock do Fetch API
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Função de espera (Wait For) robusta para aguardar Promises e re-renderizações
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
    <div id="modal-categoria" style="display: none;">
        <h2 id="modal-titulo"></h2>
        <form id="form-categoria">
            <input id="nome-categoria" value="" />
            <button type="submit">Salvar</button>
        </form>
        <button id="btn-fechar-modal"></button>
        <button id="btn-cancelar-modal"></button>
    </div>
    <button id="btn-abrir-modal"></button>
`;

describe('Testes Frontend - Categorias', () => {
    let reloadMock;
    
    // Espiões para rastrear event listeners criados pelo script
    let documentSpy;
    let windowSpy;

    // ==========================================================================
    // 2. SETUP (Antes de cada teste)
    // ==========================================================================
    beforeEach(() => {
        // 1. Limpa mocks e DOM
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // 2. CORREÇÃO DO ERRO DE TEXTO (JSDOM innerText Patch)
        // Isso ensina o JSDOM a tratar innerText igual a textContent,
        // permitindo testar textos em elementos ocultos (display: none).
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // 3. Prepara o Spy para rastrear eventos no document e window
        // Isso permite que o addEventListener funcione normalmente, mas anota quem foi adicionado
        documentSpy = jest.spyOn(document, 'addEventListener');
        windowSpy = jest.spyOn(window, 'addEventListener');

        // 4. Mock do window.location (Recarregamento)
        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };

        // 5. Mock do Confirm
        window.confirm = jest.fn(() => true);

        // 6. Reseta os módulos e Carrega o Script
        jest.resetModules();
        require('../../app/static/js/categorias');

        // 7. Dispara o início do script
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // 3. TEARDOWN (Depois de cada teste)
    // ==========================================================================
    afterEach(() => {
        // Remove APENAS os listeners criados neste teste para evitar duplicidade
        if (documentSpy) {
            documentSpy.mock.calls.forEach(call => {
                const [type, listener] = call;
                document.removeEventListener(type, listener);
            });
            documentSpy.mockRestore();
        }

        if (windowSpy) {
            windowSpy.mock.calls.forEach(call => {
                const [type, listener] = call;
                window.removeEventListener(type, listener);
            });
            windowSpy.mockRestore();
        }
    });

    // ==========================================================================
    // 4. TESTES
    // ==========================================================================

    test('Deve abrir o modal ao clicar no botão', () => {
        const btn = document.getElementById('btn-abrir-modal');
        btn.click();
        
        const modal = document.getElementById('modal-categoria');
        const titulo = document.getElementById('modal-titulo');

        expect(modal.style.display).toBe('flex');
        // Agora isso vai funcionar porque aplicamos o patch no innerText
        expect(titulo.textContent).toBe('Cadastrar Nova Categoria');
    });

    test('Criação (POST): Deve enviar dados e recarregar página', async () => {
        // Configura resposta da API
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 1, nome: 'Nova Cat' })
        });

        // Simula interação do usuário
        const input = document.getElementById('nome-categoria');
        input.value = 'Nova Cat';
        document.getElementById('form-categoria').dispatchEvent(new Event('submit'));

        // Aguarda o processamento assíncrono
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/categorias', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ nome: 'Nova Cat' })
            }));
            expect(reloadMock).toHaveBeenCalled();
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('criada com sucesso');
    });

    test('Edição (PUT): Deve carregar dados, salvar e recarregar', async () => {
        const mockId = 10;

        // Mock 1: GET (Carrega dados)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: mockId, nome: 'Antigo' })
        });

        // Mock 2: PUT (Salva dados)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ id: mockId, nome: 'Novo' })
        });

        // 1. Abre modal (GET)
        await window.abrirModalParaEditar(mockId);
        const input = document.getElementById('nome-categoria');
        expect(input.value).toBe('Antigo');

        // 2. Edita e Salva (PUT)
        input.value = 'Novo';
        document.getElementById('form-categoria').dispatchEvent(new Event('submit'));

        // 3. Verifica
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledTimes(2);
            expect(mockFetch).toHaveBeenLastCalledWith(`/api/categorias/${mockId}`, expect.objectContaining({
                method: 'PUT',
                body: JSON.stringify({ nome: 'Novo' })
            }));
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Exclusão (DELETE): Deve deletar e recarregar', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => ({})
        });

        await window.excluirCategoria(99);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/categorias/99', expect.objectContaining({
                method: 'DELETE'
            }));
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Ativação (PATCH): Deve alterar status e recarregar', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 50, nome: 'Cat', ativa: true })
        });

        await window.toggleStatusCategoria(50, false);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/status?activate=true'),
                expect.objectContaining({ method: 'PATCH' })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Validação: Não deve enviar se nome estiver vazio', async () => {
        const input = document.getElementById('nome-categoria');
        input.value = ''; // Vazio

        document.getElementById('form-categoria').dispatchEvent(new Event('submit'));

        // Pequeno delay para garantir que o fetch NÃO foi chamado
        await new Promise(r => setTimeout(r, 100));

        expect(mockFetch).not.toHaveBeenCalled();
        expect(reloadMock).not.toHaveBeenCalled();
        
        const msg = document.getElementById('notification-area').textContent;
        expect(msg).toContain('não pode estar vazio');
    });
});