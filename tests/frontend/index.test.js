/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Helper para espera assíncrona
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
    <button id="btn-iniciar-pedido-modal">Novo Pedido</button>
    <button id="btn-iniciar-pedido-shortcut">Atalho Pedido</button>
    <div id="modal-novo-pedido" style="display: none;">
        <select id="categoria-pedido-select">
            <option value="">Selecione...</option>
        </select>
        <button id="btn-continuar-pedido">Continuar</button>
        <button id="btn-fechar-modal-pedido">X</button>
        <button id="btn-cancelar-modal-pedido">Cancelar</button>
    </div>
`;

describe('Testes Frontend - Index (Fluxo Novo Pedido)', () => {
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

        // Patch de Compatibilidade
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // CRUCIAL: Restaurar ou Mockar Option de forma compatível com .add()
        // O JSDOM suporta new Option(), mas às vezes conflita se sobrescrito incorretamente.
        // Vamos garantir que o ambiente tenha a classe Option original do window.
        global.Option = window.Option;

        // Mocks Globais
        reloadMock = jest.fn();
        delete window.location;
        window.location = { href: '' };

        documentSpy = jest.spyOn(document, 'addEventListener');
        windowSpy = jest.spyOn(window, 'addEventListener');

        jest.resetModules();
        require('../../app/static/js/index');
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

    test('Abrir Modal: Deve buscar categorias e popular o select', async () => {
        const btn = document.getElementById('btn-iniciar-pedido-modal');
        const modal = document.getElementById('modal-novo-pedido');
        const select = document.getElementById('categoria-pedido-select');

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ([
                { id: 1, nome: 'Informática', ativo: true },
                { id: 2, nome: 'Limpeza', ativo: true },
                { id: 3, nome: 'Inativo', ativo: false }
            ])
        });

        btn.click();

        expect(modal.style.display).toBe('flex');
        expect(select.innerHTML).toContain('Carregando');

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/categorias?mostrar_inativos=false');
            
            // Verifica população: 1 Placeholder + 2 Ativos = 3
            expect(select.options.length).toBe(3); 
            expect(select.options[1].text).toBe('Informática');
            expect(select.options[2].text).toBe('Limpeza');
            
            expect(document.getElementById('btn-continuar-pedido').disabled).toBe(false);
        });
    });

    test('Fechar Modal: Deve esconder o modal ao clicar nos botões', () => {
        const modal = document.getElementById('modal-novo-pedido');
        const btnFechar = document.getElementById('btn-fechar-modal-pedido');
        const btnCancelar = document.getElementById('btn-cancelar-modal-pedido');

        modal.style.display = 'flex';

        btnFechar.click();
        expect(modal.style.display).toBe('none');

        modal.style.display = 'flex';

        btnCancelar.click();
        expect(modal.style.display).toBe('none');
    });

    test('Continuar Pedido: Deve redirecionar para a URL correta', () => {
        const btnContinuar = document.getElementById('btn-continuar-pedido');
        const select = document.getElementById('categoria-pedido-select');

        // Criação manual de option para garantir compatibilidade no teste síncrono
        const option = document.createElement('option');
        option.value = '10';
        option.text = 'Categoria Teste';
        select.add(option);
        select.value = '10';

        btnContinuar.click();
        expect(window.location.href).toBe('/categoria/10/novo-pedido');
    });

    test('Continuar sem Seleção: Deve mostrar notificação de erro', async () => {
        const btnContinuar = document.getElementById('btn-continuar-pedido');
        const select = document.getElementById('categoria-pedido-select');
        
        select.value = '';
        btnContinuar.click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('selecione uma categoria');
        });
        expect(window.location.href).toBe('');
    });

    test('Erro na API: Deve mostrar erro no select e na notificação', async () => {
        const btn = document.getElementById('btn-iniciar-pedido-modal');
        const select = document.getElementById('categoria-pedido-select');

        mockFetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ erro: 'Falha no servidor' })
        });

        btn.click();

        await waitFor(() => {
            expect(select.innerHTML).toContain('Erro ao carregar');
            
            const notif = document.getElementById('notification-area');
            // Ajustado para bater com a mensagem real do seu código:
            // `Erro ao carregar categorias: ${error.message}`
            expect(notif.textContent).toContain('Erro ao carregar categorias');
            expect(notif.textContent).toContain('Falha no servidor');
        });
    });

    test('Notificação da Sessão: Deve exibir mensagem salva no sessionStorage', () => {
        sessionStorage.setItem('notificationMessage', 'Pedido criado com sucesso');
        sessionStorage.setItem('notificationType', 'success');

        jest.resetModules();
        require('../../app/static/js/index');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('Pedido criado com sucesso');
        expect(sessionStorage.getItem('notificationMessage')).toBeNull();
    });
});