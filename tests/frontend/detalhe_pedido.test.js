/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

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

// HTML Simulado
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
    let reloadMock;
    let currentHref = 'http://localhost/pedidos/current';

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Mock de Location com getter/setter para href
        currentHref = 'http://localhost/pedidos/current';
        delete window.location;
        window.location = { reload: jest.fn() };
        Object.defineProperty(window.location, 'href', {
            get: () => currentHref,
            set: (val) => { currentHref = val; },
            configurable: true
        });

        // Mock de Confirm
        window.confirm = jest.fn(() => true);
        
        // Variável Global Essencial
        window.numeroAOCSGlobal = 'AOCS-123';

        // Mock Fetch Genérico (Default)
        mockFetch.mockResolvedValue({ ok: true, json: async () => ({}) });

        // Carrega Script
        jest.resetModules();
        require('../../app/static/js/detalhe_pedido');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        delete window.numeroAOCSGlobal;
    });

    // --- CONFIGURAÇÃO DO MOCK INTELIGENTE ---
    // Esta função ajuda a configurar respostas baseadas na URL
    const setupSmartMock = (responses) => {
        mockFetch.mockImplementation(async (url, options) => {
            const method = options ? options.method : 'GET';
            
            // Procura uma resposta configurada que bata com a URL e Método
            const match = responses.find(r => url.includes(r.url) && (r.method || 'GET') === method);
            
            if (match) {
                return {
                    ok: match.ok !== false,
                    status: match.status || 200,
                    json: async () => match.body || {}
                };
            }
            
            // Fallback para debugging
            console.log(`Unmocked request: ${method} ${url}`);
            return { ok: true, json: async () => ({}) };
        });
    };

    // ==========================================================================
    // TESTES QUE ESTAVAM FALHANDO (Agora com Smart Mock)
    // ==========================================================================

    test('Edição AOCS: Deve abrir modal, carregar dados e salvar', async () => {
        setupSmartMock([
            { 
                url: '/api/aocs/numero/AOCS-123', 
                method: 'GET', 
                body: { 
                    id: 10, 
                    unidade_requisitante_nome: 'TI', // Importante: nome do campo que o JS espera
                    justificativa: 'Teste' 
                } 
            },
            { 
                url: '/api/aocs/10', 
                method: 'PUT', 
                body: { numero_aocs: 'AOCS-123' } 
            }
        ]);

        // 1. Abrir Modal
        document.getElementById('btn-abrir-modal-edicao').click();

        // Aguarda fetch e população do campo
        await waitFor(() => {
            const input = document.querySelector('input[name="unidade_requisitante"]');
            expect(input.value).toBe('TI');
        });

        // 2. Salvar
        document.querySelector('input[name="justificativa"]').value = 'Nova Justificativa';
        document.getElementById('form-edicao-aocs').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            // Verifica se chamou o PUT no ID correto (10)
            expect(mockFetch).toHaveBeenCalledWith('/api/aocs/10', expect.objectContaining({
                method: 'PUT',
                body: expect.stringContaining('Nova Justificativa')
            }));
            expect(window.location.reload).toHaveBeenCalled(); // Verifica reload
        });
    });

    test('Excluir AOCS: Deve confirmar, buscar ID e deletar', async () => {
        setupSmartMock([
            { 
                url: '/api/aocs/numero/AOCS-123', 
                method: 'GET', 
                body: { id: 55 } 
            },
            { 
                url: '/api/aocs/55', 
                method: 'DELETE', 
                status: 204 // No Content
            }
        ]);

        document.getElementById('btn-excluir-aocs').click();

        await waitFor(() => {
            expect(window.confirm).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalledWith('/api/aocs/55', { method: 'DELETE' });
            
            // Verifica redirecionamento
            expect(window.location.href).toBe('http://localhost/pedidos');
        });
    });

    // ==========================================================================
    // OUTROS TESTES (Mantidos e adaptados)
    // ==========================================================================

    test('Entrega: Sucesso com reload', async () => {
        window.abrirModalEntrega(50, 'Item', 100);
        
        setupSmartMock([{
            url: '/api/pedidos/50/registrar-entrega',
            method: 'PUT',
            body: { quantidade_entregue: 10 }
        }]);

        document.getElementById('quantidade_entregue').value = '10,00';
        document.getElementById('data_entrega').value = '2024-01-01';
        document.getElementById('nota_fiscal').value = 'NF-001';

        document.getElementById('form-registrar-entrega').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/pedidos/50'), 
                expect.anything()
            );
            expect(window.location.reload).toHaveBeenCalled();
        });
    });

    test('Anexo: Deve tratar resposta 204', async () => {
        const file = new File(['a'], 'b.pdf', { type: 'application/pdf' });
        Object.defineProperty(document.getElementById('file'), 'files', { value: [file] });
        document.getElementById('tipo_documento_select').value = 'Outros';

        setupSmartMock([{
            url: '/api/anexos/upload/',
            method: 'POST',
            status: 204
        }]);

        document.getElementById('form-anexos').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(window.location.reload).toHaveBeenCalled();
            expect(sessionStorage.getItem('notificationMessage')).toContain('Anexo enviado');
        });
    });

    test('Inline: Alterar campos dispara PUT', async () => {
        setupSmartMock([{ url: '/api/aocs/AOCS-123', method: 'PUT' }]);

        const input = document.getElementById('numero-pedido-input');
        input.value = 'PED-999';
        input.dispatchEvent(new Event('change'));

        await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    });
});