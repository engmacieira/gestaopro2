/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

// Mock do window.open
const mockOpen = jest.fn();
delete window.open;
window.open = mockOpen;

// HTML Simulado
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
        
        // 1. Habilita controle total do tempo (Fake Timers)
        jest.useFakeTimers();

        // 2. Carrega o script
        jest.resetModules();
        require('../../app/static/js/relatorios');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        // 3. Limpa os timers para não afetar outros testes
        jest.useRealTimers();
    });

    // ==========================================================================
    // TESTES DE LÓGICA E VALIDAÇÃO
    // ==========================================================================

    test('Validação: Deve exigir seleção de ordenação', () => {
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        // Clica sem selecionar nada no select
        btn.click();

        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('selecione uma opção de ordenação');
        expect(mockOpen).not.toHaveBeenCalled();
    });

    test('Configuração: Deve tratar erro se o select não existir', () => {
        // Remove o select propositalmente para simular erro de HTML
        const select = document.getElementById('ordenacao-relatorio_contratos');
        select.remove();

        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        // Mock do console.error para não sujar o terminal
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

        // Chama diretamente a função global (útil para onlick="" no HTML legado)
        window.gerarRelatorio('relatorio_pedidos');

        expect(window.open).toHaveBeenCalledWith(
            expect.stringContaining('ordenacao=status'),
            '_blank'
        );
    });

    // ==========================================================================
    // TESTE DE COBERTURA DO TIMEOUT (Linhas 17-19)
    // ==========================================================================

    test('Notificação: Deve desaparecer do DOM após 5 segundos', () => {
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');
        
        // 1. Gera uma notificação
        btn.click(); // Erro de validação gera notificação

        const notifArea = document.getElementById('notification-area');
        const notification = notifArea.querySelector('.notification');
        
        expect(notification).toBeTruthy(); // Garante que existe
        expect(notification.style.opacity).toBe(''); // Opacidade inicial vazia ou padrão

        // 2. Avança o tempo em 5 segundos (Fake Timers)
        jest.advanceTimersByTime(5000);

        // 3. Verifica se a opacidade foi alterada (Lógica do setTimeout executou)
        expect(notification.style.opacity).toBe('0');

        // 4. Dispara manualmente o evento 'transitionend' (JSDOM não faz isso sozinho)
        // Isso cobre a arrow function do .addEventListener
        const event = new Event('transitionend');
        notification.dispatchEvent(event);

        // 5. Verifica se o elemento foi removido
        expect(notifArea.children.length).toBe(0);
    });
});