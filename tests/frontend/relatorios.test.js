/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

// Mock do window.open (função principal deste script)
const mockOpen = jest.fn();
delete window.open;
window.open = mockOpen;

// Helper para espera assíncrona (caso precise, embora esse script seja síncrono)
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

// HTML Simulado (Baseado em _relatorio_item.html e relatorios.html)
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
            <button class="btn-print" data-relatorio-btn="relatorio_contratos">
                Gerar PDF
            </button>
        </div>

        <div class="report-item">
            <h3>Relatório de Pedidos</h3>
            <select id="ordenacao-relatorio_pedidos" class="form-control">
                <option value="">Selecione...</option>
                <option value="data">Por Data</option>
            </select>
            <button class="btn-print" data-relatorio-btn="relatorio_pedidos">
                Gerar PDF
            </button>
        </div>
    </div>
`;

describe('Testes Frontend - Relatórios', () => {
    let documentSpy;

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

        // Espião para garantir limpeza
        documentSpy = jest.spyOn(document, 'addEventListener');

        // Carrega o script
        jest.resetModules();
        require('../../app/static/js/relatorios');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        if (documentSpy) {
            documentSpy.mock.calls.forEach(c => document.removeEventListener(c[0], c[1]));
            documentSpy.mockRestore();
        }
    });

    // ==========================================================================
    // 3. TESTES
    // ==========================================================================

    test('Gerar Relatório: Deve abrir nova aba com URL correta quando opção selecionada', () => {
        const select = document.getElementById('ordenacao-relatorio_contratos');
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');

        // 1. Seleciona ordenação
        select.value = 'data_inicio';
        // O script lê o valor no momento do clique, não precisa disparar 'change'

        // 2. Clica no botão
        btn.click();

        // 3. Verifica window.open
        // URL esperada: /api/relatorios/relatorio_contratos?ordenacao=data_inicio
        expect(mockOpen).toHaveBeenCalledWith(
            '/api/relatorios/relatorio_contratos?ordenacao=data_inicio', 
            '_blank'
        );

        // 4. Verifica notificação de sucesso
        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain("Relatório 'relatorio_contratos' solicitado");
    });

    test('Validação: Deve exigir seleção de ordenação', () => {
        const select = document.getElementById('ordenacao-relatorio_contratos');
        const btn = document.querySelector('[data-relatorio-btn="relatorio_contratos"]');

        // 1. Garante que está vazio
        select.value = '';

        // 2. Clica
        btn.click();

        // 3. Verifica bloqueio
        expect(mockOpen).not.toHaveBeenCalled();
        
        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('selecione uma opção de ordenação');
    });

    test('Erro de Configuração: Deve tratar falta do elemento select', () => {
        // Remove o select do DOM propositalmente para simular erro
        const select = document.getElementById('ordenacao-relatorio_pedidos');
        select.remove();

        const btn = document.querySelector('[data-relatorio-btn="relatorio_pedidos"]');
        
        // Espiona console.error para evitar poluição no output do teste
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        btn.click();

        expect(mockOpen).not.toHaveBeenCalled();
        
        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('Não foi possível encontrar as opções');

        consoleSpy.mockRestore();
    });

    test('Função Global: Deve ser possível chamar window.gerarRelatorio diretamente', () => {
        const select = document.getElementById('ordenacao-relatorio_pedidos');
        select.value = 'data';

        // Chama a função exposta no window
        window.gerarRelatorio('relatorio_pedidos');

        expect(mockOpen).toHaveBeenCalledWith(
            '/api/relatorios/relatorio_pedidos?ordenacao=data', 
            '_blank'
        );
    });
});