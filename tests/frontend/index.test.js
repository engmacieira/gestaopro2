/**
 * @jest-environment jsdom
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;

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
        jest.useRealTimers(); 
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        delete window.location;
        window.location = { href: '' };

        global.Option = window.Option;

        jest.resetModules();
        require('../../app/static/js/index');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

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

        modalContent.click();
        expect(modal.style.display).toBe('flex');

        modal.click();
        expect(modal.style.display).toBe('none');
    });

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
            expect(select.options.length).toBe(3); 
            expect(btnContinuar.disabled).toBe(false);
        });
    });

    test('Categorias: Vazio ou Inativo - Deve mostrar mensagem e manter bloqueado', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ([{ id: 99, nome: 'Antiga', ativo: false }])
        });

        document.getElementById('btn-iniciar-pedido-modal').click();

        await waitFor(() => {
            const select = document.getElementById('categoria-pedido-select');
            const btnContinuar = document.getElementById('btn-continuar-pedido');

            expect(select.innerHTML).toContain('Nenhuma categoria ativa');
            expect(btnContinuar.disabled).toBe(true); 
        });
    });

    test('Redirecionamento: Deve ir para URL correta ao continuar', () => {
        const select = document.getElementById('categoria-pedido-select');
        const btn = document.getElementById('btn-continuar-pedido');
        
        const opt = document.createElement('option');
        opt.value = '50';
        opt.text = 'Obras';
        select.appendChild(opt);
        
        select.value = '50';
        select.dispatchEvent(new Event('change'));

        btn.disabled = false;

        btn.click();

        expect(window.location.href).toBe('/categoria/50/novo-pedido');
    });

    test('Erro API (Network Crash): Deve tratar exceção do fetch', async () => {
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
        
        select.value = '';
        
        btnContinuar.disabled = false;
        btnContinuar.click();

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('selecione uma categoria');
        expect(window.location.href).toBe(''); 
    });

    test('Notificação: Deve desaparecer automaticamente após 5s', () => {
        jest.useFakeTimers(); 
        const setTimeoutSpy = jest.spyOn(global, 'setTimeout');

        const btn = document.getElementById('btn-continuar-pedido');
        btn.disabled = false;
        document.getElementById('categoria-pedido-select').value = '';
        btn.click();

        const notifArea = document.getElementById('notification-area');
        expect(notifArea.children.length).toBeGreaterThan(0);
        const notification = notifArea.querySelector('.notification');

        expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 5000);

        jest.advanceTimersByTime(5000);
        
        const event = new Event('transitionend');
        notification.dispatchEvent(event);

        expect(notifArea.children.length).toBe(0);
        
        jest.useRealTimers();
    });
});