/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

// HTML Simulado (Representa a Home)
const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>
    
    <button id="btn-iniciar-pedido-modal">Novo Pedido</button>
    <button id="btn-iniciar-pedido-shortcut">Atalho Pedido</button>

    <div id="modal-novo-pedido" style="display: none;">
        <div class="modal-content"> <select id="categoria-pedido-select">
                <option value="">Selecione...</option>
            </select>
            <button id="btn-continuar-pedido" disabled>Continuar</button>
            <button id="btn-fechar-modal-pedido">X</button>
            <button id="btn-cancelar-modal-pedido">Cancelar</button>
        </div>
    </div>
`;

// Helper para espera assíncrona (Funciona apenas com Real Timers!)
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

describe('Testes Frontend - Index (Home)', () => {
    let reloadMock;

    beforeEach(() => {
        jest.clearAllMocks();
        // IMPORTANTE: Garante timers reais por padrão para o waitFor funcionar
        jest.useRealTimers(); 
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Mock de Location
        delete window.location;
        window.location = { href: '' };

        // Mock da classe Option (para compatibilidade JSDOM)
        global.Option = window.Option;

        // Resetar módulos para recarregar os event listeners
        jest.resetModules();
        require('../../app/static/js/index');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // 1. TESTES DE INTERFACE E INTERAÇÃO
    // ==========================================================================

    test('Modal: Deve abrir ao clicar no botão principal', async () => {
        mockFetch.mockResolvedValue({ ok: true, json: async () => [] });
        
        document.getElementById('btn-iniciar-pedido-modal').click();
        
        const modal = document.getElementById('modal-novo-pedido');
        expect(modal.style.display).toBe('flex');
        expect(mockFetch).toHaveBeenCalled();
    });

    test('Modal: Deve abrir ao clicar no botão de atalho', async () => {
        mockFetch.mockResolvedValue({ ok: true, json: async () => [] });

        document.getElementById('btn-iniciar-pedido-shortcut').click();
        
        const modal = document.getElementById('modal-novo-pedido');
        expect(modal.style.display).toBe('flex');
    });

    test('Fechar Modal: Deve fechar apenas ao clicar FORA (overlay), não dentro', () => {
        const modal = document.getElementById('modal-novo-pedido');
        const modalContent = modal.querySelector('.modal-content');
        modal.style.display = 'flex';

        // 1. Clicar dentro do conteúdo (não deve fechar)
        modalContent.click();
        expect(modal.style.display).toBe('flex');

        // 2. Clicar no overlay (deve fechar)
        modal.click();
        expect(modal.style.display).toBe('none');
    });

    // ==========================================================================
    // 2. TESTES DE LÓGICA E DADOS (O 80/20)
    // ==========================================================================

    test('Categorias: Sucesso - Deve popular select e habilitar botão', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ([
                { id: 1, nome: 'TI', ativo: true },
                { id: 2, nome: 'Limpeza', ativo: true }
            ])
        });

        document.getElementById('btn-iniciar-pedido-modal').click();
        
        await waitFor(() => {
            const select = document.getElementById('categoria-pedido-select');
            const btnContinuar = document.getElementById('btn-continuar-pedido');
            
            expect(select.disabled).toBe(false);
            expect(select.options.length).toBe(3); // 1 Placeholder + 2 Opções
            expect(btnContinuar.disabled).toBe(false);
        });
    });

    test('Categorias: Vazio ou Inativo - Deve mostrar mensagem e manter bloqueado', async () => {
        // Cenário: Retorna 1 categoria, mas ela está INATIVA
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ([{ id: 99, nome: 'Antiga', ativo: false }])
        });

        document.getElementById('btn-iniciar-pedido-modal').click();

        await waitFor(() => {
            const select = document.getElementById('categoria-pedido-select');
            const btnContinuar = document.getElementById('btn-continuar-pedido');

            // Não deve ter adicionado a opção inativa
            expect(select.innerHTML).toContain('Nenhuma categoria ativa');
            expect(btnContinuar.disabled).toBe(true); // Continua travado
        });
    });

    test('Redirecionamento: Deve ir para URL correta ao continuar', () => {
        const select = document.getElementById('categoria-pedido-select');
        const btn = document.getElementById('btn-continuar-pedido');
        
        // 1. Criação manual da opção
        const opt = document.createElement('option');
        opt.value = '50';
        opt.text = 'Obras';
        select.appendChild(opt);
        
        // 2. Força a seleção e dispara evento de mudança (Crucial para JSDOM)
        select.value = '50';
        select.dispatchEvent(new Event('change'));

        // 3. IMPORTANTE: Habilitar o botão manualmente, pois ele começa disabled no HTML
        btn.disabled = false;

        // 4. Clica
        btn.click();

        expect(window.location.href).toBe('/categoria/50/novo-pedido');
    });

    // ==========================================================================
    // 3. TESTES DE ERRO E NOTIFICAÇÃO
    // ==========================================================================

    test('Erro API (Network Crash): Deve tratar exceção do fetch', async () => {
        // Simula queda de internet (Promise reject)
        mockFetch.mockRejectedValue(new Error('Falha de conexão'));

        document.getElementById('btn-iniciar-pedido-modal').click();

        await waitFor(() => {
            const select = document.getElementById('categoria-pedido-select');
            const notif = document.getElementById('notification-area');
            
            expect(select.innerHTML).toContain('Erro ao carregar');
            expect(notif.textContent).toContain('Falha de conexão');
        });
    });

    test('Erro API (500): Deve ler mensagem de erro do backend', async () => {
        mockFetch.mockResolvedValue({
            ok: false,
            json: async () => ({ detail: 'Banco de dados fora do ar' })
        });

        document.getElementById('btn-iniciar-pedido-modal').click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Banco de dados fora do ar');
        });
    });

    test('Validação: Tentar continuar sem selecionar nada', () => {
        const btnContinuar = document.getElementById('btn-continuar-pedido');
        const select = document.getElementById('categoria-pedido-select');
        
        // Garante que está vazio
        select.value = '';
        
        // Força o botão a estar habilitado (simulando bug de UI ou hack via console)
        btnContinuar.disabled = false;
        btnContinuar.click();

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('selecione uma categoria');
        expect(window.location.href).toBe(''); // Não redirecionou
    });

    test('Notificação: Deve desaparecer automaticamente após 5s', () => {
        // Usar Spy e Fake Timers
        jest.useFakeTimers(); 
        const setTimeoutSpy = jest.spyOn(global, 'setTimeout');

        // Dispara uma notificação qualquer
        const btn = document.getElementById('btn-continuar-pedido');
        btn.disabled = false;
        document.getElementById('categoria-pedido-select').value = '';
        btn.click();

        const notifArea = document.getElementById('notification-area');
        expect(notifArea.children.length).toBeGreaterThan(0);
        const notification = notifArea.querySelector('.notification');

        // Verifica se o timer foi agendado
        expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 5000);

        // Avança o tempo
        jest.advanceTimersByTime(5000);
        
        // Dispara o evento 'transitionend' manualmente (JSDOM não faz isso sozinho)
        const event = new Event('transitionend');
        notification.dispatchEvent(event);

        // Agora verificamos se foi removido do DOM
        expect(notifArea.children.length).toBe(0);
        
        jest.useRealTimers();
    });
});