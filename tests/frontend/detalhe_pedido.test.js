/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Helper para espera assíncrona (Funciona com Real Timers)
const waitFor = async (callback, timeout = 2000) => {
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

// HTML Simulado Completo
const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>
    
    <a href="http://localhost/pedidos" class="back-link">Voltar</a>

    <input type="text" id="numero-pedido-input" data-campo="numero_pedido">
    <input type="text" id="empenho-input" data-campo="empenho">
    <input type="date" id="data_pedido_input">

    <button id="btn-excluir-aocs">Excluir AOCS</button>

    <div id="modal-registrar-entrega" style="display: none;">
        <form id="form-registrar-entrega">
            <input type="hidden" name="item_pedido_id" id="entrega-item-id">
            <input type="text" name="quantidade_entregue" id="quantidade_entregue" placeholder="0,00">
            <input type="date" name="data_entrega" id="data_entrega">
            <input type="text" name="nota_fiscal" id="nota_fiscal">
            <button type="submit">Confirmar Entrega</button>
        </form>
        <span id="entrega-item-descricao"></span>
        <span id="entrega-saldo-restante"></span>
        <button class="close-button" id="btn-fechar-modal-entrega">Fechar</button>
    </div>

    <button id="btn-abrir-modal-edicao">Editar AOCS</button>
    <div id="modal-edicao-aocs" style="display: none;">
        <form id="form-edicao-aocs">
            <input name="unidade_requisitante">
            <input name="justificativa">
            <input name="info_orcamentaria">
            <input name="local_entrega">
            <input name="agente_responsavel">
            <button type="submit">Salvar</button>
        </form>
        <button class="close-button">Fechar</button>
    </div>

    <form id="form-anexos" action="/api/anexos/upload/" method="POST">
        <select name="tipo_documento" id="tipo_documento_select">
            <option value="Outros">Outros</option>
            <option value="NOVO">--- CRIAR NOVO TIPO ---</option>
        </select>
        <input type="text" name="tipo_documento_novo" id="tipo_documento_novo" style="display: none;">
        <input type="file" name="file" id="file">
        <button type="submit">Enviar Anexo</button>
    </form>
`;

describe('Testes Frontend - Detalhe Pedido', () => {
    let currentHref = 'http://localhost/pedidos/current';

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useRealTimers();
        
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Mock de Location
        currentHref = 'http://localhost/pedidos/current';
        delete window.location;
        window.location = { reload: jest.fn() };
        Object.defineProperty(window.location, 'href', {
            get: () => currentHref,
            set: (val) => { currentHref = val; },
            configurable: true
        });

        window.confirm = jest.fn(() => true);
        window.numeroAOCSGlobal = 'AOCS-123';

        mockFetch.mockResolvedValue({ ok: true, json: async () => ({}) });

        // ==========================================================================
        // CORREÇÃO DO STACKING DE LISTENERS (Erro das 32 chamadas)
        // ==========================================================================
        
        // Interceptamos o addEventListener para capturar o callback do DOMContentLoaded
        // e executá-lo manualmente apenas UMA vez, evitando acumular listeners no document.
        let domCallback = null;
        const originalAddEventListener = document.addEventListener;
        
        document.addEventListener = jest.fn((event, callback) => {
            if (event === 'DOMContentLoaded') {
                domCallback = callback;
            } else {
                originalAddEventListener.call(document, event, callback);
            }
        });

        jest.resetModules();
        require('../../app/static/js/detalhe_pedido');
        
        // Restaura o original imediatamente
        document.addEventListener = originalAddEventListener;

        // Executa a inicialização do script explicitamente para este teste
        if (domCallback) domCallback();
    });

    afterEach(() => {
        delete window.numeroAOCSGlobal;
    });

    const setupSmartMock = (responses) => {
        mockFetch.mockImplementation(async (url, options) => {
            const method = (options && options.method) ? options.method : 'GET';
            const match = responses.find(r => url.includes(r.url) && (r.method || 'GET') === method);
            
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
    // 1. RESILIÊNCIA E UI (Corrigido)
    // ==========================================================================

    test('Resiliência: Elementos Ausentes (Ex: Modal deletado)', () => {
        // 1. Remove elemento ANTES de carregar o script
        const modal = document.getElementById('modal-registrar-entrega');
        modal.remove();

        // 2. Recarrega o script "do zero" para ele perceber que o elemento sumiu
        // Precisamos repetir a lógica de interceptação aqui
        let localCallback = null;
        const originalAdd = document.addEventListener;
        document.addEventListener = jest.fn((ev, cb) => { if (ev === 'DOMContentLoaded') localCallback = cb; });
        
        jest.resetModules();
        require('../../app/static/js/detalhe_pedido');
        document.addEventListener = originalAdd;
        if (localCallback) localCallback();

        // 3. Agora a variável interna 'modalEntrega' deve ser null
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        
        window.abrirModalEntrega(1, 'Teste', 10);
        
        expect(consoleSpy).toHaveBeenCalled();
        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('Erro ao abrir modal');
        
        consoleSpy.mockRestore();
    });

    test('Notificação: Deve desaparecer após 5s (Mock Manual do setTimeout)', async () => {
        const originalSetTimeout = global.setTimeout;
        let callbackRemocao = null;
        const mockSetTimeout = jest.fn((cb, delay) => {
            if (delay === 5000) callbackRemocao = cb;
            return 123;
        });
        global.setTimeout = mockSetTimeout;
        window.setTimeout = mockSetTimeout;

        try {
            const formAnexos = document.getElementById('form-anexos');
            formAnexos.dispatchEvent(new Event('submit'));

            const notifArea = document.getElementById('notification-area');
            await waitFor(() => expect(notifArea.children.length).toBeGreaterThan(0));

            expect(mockSetTimeout).toHaveBeenCalledWith(expect.any(Function), 5000);
            
            if (callbackRemocao) {
                const notification = notifArea.querySelector('.notification');
                callbackRemocao(); 
                expect(notification.style.opacity).toBe('0');
                notification.dispatchEvent(new Event('transitionend'));
                expect(notifArea.children.length).toBe(0);
            }
        } finally {
            global.setTimeout = originalSetTimeout;
            window.setTimeout = originalSetTimeout;
        }
    });

    // ==========================================================================
    // 2. TESTES DE EDIÇÃO AOCS
    // ==========================================================================

    test('Edição AOCS: Sucesso - Carrega dados e Salva', async () => {
        setupSmartMock([
            { url: '/api/aocs/numero', method: 'GET', body: { id: 10, unidade_requisitante_nome: 'TI' } },
            { url: '/api/aocs/10', method: 'PUT', body: { numero_aocs: 'AOCS-123' } }
        ]);

        document.getElementById('btn-abrir-modal-edicao').click();
        await waitFor(() => expect(document.querySelector('input[name="unidade_requisitante"]').value).toBe('TI'));

        document.getElementById('form-edicao-aocs').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(window.location.reload).toHaveBeenCalled());
    });

    test('Edição AOCS: Erro ao Carregar Dados (GET falha)', async () => {
        setupSmartMock([{ url: '/api/aocs/numero', method: 'GET', ok: false, status: 404, body: { erro: 'Não achou' } }]);
        document.getElementById('btn-abrir-modal-edicao').click();
        await waitFor(() => expect(document.getElementById('notification-area').textContent).toContain('Não achou'));
    });

    test('Edição AOCS: Erro ao Salvar (Falha ao obter ID para PUT)', async () => {
        mockFetch.mockImplementation(async (url, opts) => {
            if (url.includes('numero') && !opts) return { ok: true, json: async () => ({ id: 10 }) };
            if (url.includes('numero') && opts) { 
                 return { ok: false, status: 500, json: async () => ({ erro: 'Erro interno simulado' }) };
            }
            return { ok: true, json: async () => ({}) };
        });

        document.getElementById('btn-abrir-modal-edicao').click();
        await waitFor(() => {});
        
        mockFetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({ detail: 'AOCS não encontrada' }) });

        document.getElementById('form-edicao-aocs').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(document.getElementById('notification-area').textContent).toContain('AOCS não encontrada'));
    });

    // ==========================================================================
    // 3. TESTES DE ANEXOS
    // ==========================================================================

    test('Anexos: UI - Mostrar/Esconder input "Novo Tipo"', () => {
        const select = document.getElementById('tipo_documento_select');
        const inputNovo = document.getElementById('tipo_documento_novo');
        select.value = 'NOVO';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('block');
        select.value = 'Outros';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('none');
    });

    test('Anexos: Validação - Arquivo vazio', async () => {
        document.getElementById('form-anexos').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(document.getElementById('notification-area').textContent).toContain('Selecione um arquivo'));
    });

    test('Anexos: Validação - Tipo NOVO sem nome', async () => {
        const file = new File(['dummy'], 'test.txt', { type: 'text/plain' });
        Object.defineProperty(document.getElementById('file'), 'files', { value: [file] });
        document.getElementById('tipo_documento_select').value = 'NOVO';
        document.getElementById('form-anexos').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(document.getElementById('notification-area').textContent).toContain('Informe o nome do novo tipo'));
    });

    test('Anexos: Sucesso - Upload Completo', async () => {
        const file = new File(['dummy'], 'test.txt');
        Object.defineProperty(document.getElementById('file'), 'files', { value: [file] });
        document.getElementById('tipo_documento_select').value = 'Outros';
        setupSmartMock([{ url: '/api/anexos/upload/', method: 'POST', status: 204 }]);
        document.getElementById('form-anexos').dispatchEvent(new Event('submit'));
        await waitFor(() => expect(window.location.reload).toHaveBeenCalled());
    });

    // ==========================================================================
    // 4. EXCLUSÃO E OUTROS
    // ==========================================================================

    test('Excluir Anexo: Cancelar e Sucesso', async () => {
        window.confirm.mockReturnValueOnce(false);
        await window.excluirAnexo(1, 'doc.pdf');
        expect(mockFetch).not.toHaveBeenCalled();

        window.confirm.mockReturnValueOnce(true);
        setupSmartMock([{ url: '/api/anexos/1', method: 'DELETE', status: 204 }]);
        await window.excluirAnexo(1, 'doc.pdf');
        expect(window.location.reload).toHaveBeenCalled();
    });

    test('Excluir AOCS: Fluxo Completo (Busca ID -> Deleta)', async () => {
        setupSmartMock([
            { url: '/api/aocs/numero', method: 'GET', body: { id: 99 } },
            { url: '/api/aocs/99', method: 'DELETE', status: 204 }
        ]);
        await document.getElementById('btn-excluir-aocs').click();
        await waitFor(() => expect(window.location.href).toContain('pedidos'));
    });

    test('Parsers: Float Brasileiro', () => {
        window.abrirModalEntrega(1, 'Item', 1000.50);
        const input = document.getElementById('quantidade_entregue');
        input.value = '-10,00';
        document.getElementById('form-registrar-entrega').dispatchEvent(new Event('submit'));
    });

    test('Click Outside: Fecha Modais', () => {
        const modalE = document.getElementById('modal-registrar-entrega');
        modalE.style.display = 'flex';
        modalE.click();
        expect(modalE.style.display).toBe('none');
    });

    // ==========================================================================
    // 5. NOVOS CENÁRIOS (Corrigidos)
    // ==========================================================================

    test('Entrega: Caminho Feliz (Registrar Entrega com Sucesso)', async () => {
        window.abrirModalEntrega(50, 'Cimento', 100.00);
        document.getElementById('quantidade_entregue').value = '10,00';
        document.getElementById('data_entrega').value = '2024-01-01';
        document.getElementById('nota_fiscal').value = 'NF-123';

        setupSmartMock([{
            url: '/api/pedidos/50/registrar-entrega', method: 'PUT',
            body: { quantidade_entregue: 10.0, id: 50 }
        }]);

        document.getElementById('form-registrar-entrega').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/pedidos/50/registrar-entrega'),
                expect.objectContaining({ method: 'PUT' })
            );
            expect(window.location.reload).toHaveBeenCalled();
        });
    });

    test('Entrega: Erro de Rede no Fetch', async () => {
        window.abrirModalEntrega(50, 'Cimento', 100.00);
        document.getElementById('quantidade_entregue').value = '10,00';
        document.getElementById('data_entrega').value = '2024-01-01';
        document.getElementById('nota_fiscal').value = 'NF-123';

        mockFetch.mockRejectedValue(new Error('Falha de conexão na entrega'));

        document.getElementById('form-registrar-entrega').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(document.getElementById('notification-area').textContent).toContain('Falha de conexão na entrega');
        });
    });

    test('Inline Updates: Alterar Inputs (Empenho/Data) dispara API', async () => {
        const inputEmpenho = document.getElementById('empenho-input');
        const inputData = document.getElementById('data_pedido_input');

        setupSmartMock([
            { url: '/dados-gerais', method: 'PUT', body: { ok: true } },
            { url: '/data', method: 'PUT', body: { ok: true } }
        ]);

        inputEmpenho.value = '2024NE001';
        inputEmpenho.dispatchEvent(new Event('change'));
        
        inputData.value = '2024-12-31';
        inputData.dispatchEvent(new Event('change'));

        await waitFor(() => {
            // Agora deve ser exatamente 2, pois limpamos os listeners duplicados no beforeEach
            expect(mockFetch).toHaveBeenCalledTimes(2);
        });
    });

    test('Excluir AOCS: Falha ao buscar ID (Etapa 1 - 404)', async () => {
        setupSmartMock([{ url: '/api/aocs/numero', method: 'GET', ok: false, status: 404 }]);

        document.getElementById('btn-excluir-aocs').click();

        await waitFor(() => {
            expect(document.getElementById('notification-area').textContent).toContain('AOCS não encontrada');
        });
    });
});