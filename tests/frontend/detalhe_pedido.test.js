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

// HTML Simulado (Completo para satisfazer todas as dependências do script)
const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>
    
    <a href="/pedidos" class="back-link">Voltar</a>

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

        <button class="close-button" id="btn-fechar-modal">Fechar</button>
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
    let documentSpy;
    let windowSpy;

    // ==========================================================================
    // 2. SETUP
    // ==========================================================================
    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Patch de Compatibilidade (innerText)
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
        window.location = { 
            reload: reloadMock,
            href: 'http://localhost/pedidos/123' // Mock href para redirecionamentos
        };
        
        window.confirm = jest.fn(() => true);
        
        // Variável global
        window.numeroAOCSGlobal = 'AOCS-123';

        // Carrega o script
        jest.resetModules();
        require('../../app/static/js/detalhe_pedido');
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
        delete window.numeroAOCSGlobal;
    });

    // ==========================================================================
    // 4. TESTES - ENTREGAS
    // ==========================================================================

    test('Modal Entrega: Deve abrir com dados passados por argumento', () => {
        const modal = document.getElementById('modal-registrar-entrega');
        const descDisplay = document.getElementById('entrega-item-descricao');
        const inputQtd = document.getElementById('quantidade_entregue');

        // window.abrirModalEntrega(id, descricao, saldo)
        window.abrirModalEntrega(50, 'Cimento CP-II', 100.00);

        expect(modal.style.display).toBe('flex');
        expect(descDisplay.textContent).toBe('Cimento CP-II');
        expect(inputQtd.value).toBe('100,00'); // Verifica auto-preenchimento
    });

    test('Registrar Entrega: Deve validar saldo e enviar requisição correta', async () => {
        window.abrirModalEntrega(50, 'Item Teste', 10.00);

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 50, quantidade_entregue: 5 })
        });

        document.getElementById('quantidade_entregue').value = '5,50'; 
        document.getElementById('data_entrega').value = '2024-11-21';
        document.getElementById('nota_fiscal').value = 'NF-1234';

        const form = document.getElementById('form-registrar-entrega');
        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/pedidos/50/registrar-entrega', expect.objectContaining({
                method: 'PUT',
                body: expect.stringContaining('"quantidade":"5.50"')
            }));
            
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Registrar Entrega: Deve bloquear quantidade maior que o saldo', async () => {
        window.abrirModalEntrega(50, 'Item Teste', 10.00);
        document.getElementById('quantidade_entregue').value = '15,00'; // Maior que 10

        const form = document.getElementById('form-registrar-entrega');
        form.dispatchEvent(new Event('submit'));

        await new Promise(r => setTimeout(r, 100));

        expect(mockFetch).not.toHaveBeenCalled();
        expect(document.getElementById('notification-area').textContent).toContain('Quantidade inválida');
    });

    // ==========================================================================
    // 5. TESTES - ANEXOS
    // ==========================================================================

    test('Anexos: Interface de Novo Tipo funciona', () => {
        const select = document.getElementById('tipo_documento_select');
        const inputNovo = document.getElementById('tipo_documento_novo');

        select.value = 'NOVO';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('block');

        select.value = 'Outros';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('none');
    });

    test('Upload Anexo: Deve enviar FormData corretamente', async () => {
        const form = document.getElementById('form-anexos');
        const fileInput = document.getElementById('file');
        const select = document.getElementById('tipo_documento_select');

        // Configura arquivo mockado
        const file = new File(['conteudo'], 'teste.pdf', { type: 'application/pdf' });
        Object.defineProperty(fileInput, 'files', { value: [file] });
        
        select.value = 'Outros';

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ mensagem: 'Sucesso' })
        });

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            // Correção aqui: usamos stringContaining para ignorar o http://localhost
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/anexos/upload/'), 
                expect.objectContaining({
                    method: 'POST',
                    body: expect.any(FormData)
                })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Excluir Anexo: Deve deletar com sucesso', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => ({})
        });

        await window.excluirAnexo(10, 'arquivo.pdf');

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/anexos/10', { method: 'DELETE' });
            expect(reloadMock).toHaveBeenCalled();
        });
    });
});