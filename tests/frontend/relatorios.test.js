/**
 * @jest-environment jsdom
 */

const mockOpen = jest.fn();
delete window.open;
window.open = mockOpen;

const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>

    <div class="card">
        <div class="report-item">
            <h3>Relatório de Contratos</h3>
            <select id="ordenacao-relatorio_contratos" class="form-control">
                <option value="">Selecione a ordenação...</option>
                <option value="numero">Por Número</option>
                <option value="data_inicio">Por Data de Início</option>
            </select>
            <button class="btn-action" data-relatorio-btn="relatorio_contratos">
                <i class="fa-solid fa-file-pdf"></i> Gerar PDF
            </button>
        </div>

        <div class="report-item">
            <h3>Relatório de Pedidos</h3>
             <select id="ordenacao-relatorio_pedidos" class="form-control">
                <option value="">Selecione a ordenação...</option>
                <option value="data">Por Data</option>
                <option value="status">Por Status</option>
            </select>
            <button class="btn-action" data-relatorio-btn="relatorio_pedidos">
                <i class="fa-solid fa-file-pdf"></i> Gerar PDF
            </button>
        </div>
    </div>
`;

describe('Testes Frontend - Relatórios', () => {
    
    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        
        jest.useFakeTimers();

        jest.resetModules();
        require('../../app/static/js/relatorios');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    test('Validação: Deve exigir seleção de ordenação', () => {
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        btn.click();

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('selecione uma opção de ordenação');
        expect(mockOpen).not.toHaveBeenCalled();
    });

    test('Configuração: Deve tratar erro se o select não existir', () => {
        const select = document.getElementById('ordenacao-relatorio_contratos');
        select.remove();

        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        btn.click();

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('Não foi possível encontrar as opções');
        
        consoleSpy.mockRestore();
    });

    test('Sucesso: Deve abrir nova aba com a URL correta', () => {
        const select = document.getElementById('ordenacao-relatorio_contratos');
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        select.value = 'numero';
        btn.click();

        expect(window.open).toHaveBeenCalledWith(
            '/api/relatorios/relatorio_contratos?ordenacao=numero', 
            '_blank'
        );

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('solicitado');
    });

    test('Função Global: Deve funcionar via window.gerarRelatorio', () => {
        const select = document.getElementById('ordenacao-relatorio_pedidos');
        select.value = 'status';

        window.gerarRelatorio('relatorio_pedidos');

        expect(window.open).toHaveBeenCalledWith(
            expect.stringContaining('ordenacao=status'),
            '_blank'
        );
    });

    test('Notificação: Deve desaparecer do DOM após 5 segundos', () => {
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        btn.click(); 

        const notifArea = document.getElementById('notification-area');
        const notification = notifArea.querySelector('.notification');
        
        expect(notification).toBeTruthy(); 
        expect(notification.style.opacity).toBe(''); 

        jest.advanceTimersByTime(5000);

        expect(notification.style.opacity).toBe('0');

        const event = new Event('transitionend');
        notification.dispatchEvent(event);

        expect(notifArea.children.length).toBe(0);
    });
});