/**
 * @jest-environment jsdom
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;
global.alert = jest.fn();
global.confirm = jest.fn(() => true);

// Simulação de dados globais injetados pelo template
window.aocsDadosAtuais = {
    id: 100,
    unidade_requisitante: 'TI',
    justificativa: 'Precisa',
    info_orcamentaria: 'Verba X',
    local_entrega: 'Prédio A',
    agente_responsavel: 'João'
};
window.numeroAOCSGlobal = 'AOCS-2024';

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

const DOM_HTML = `
    <div class="main-content">
        <div id="notification-area"></div>
        <a class="back-link" href="/voltar">Voltar</a>
    </div>

    <!-- Inputs Inline -->
    <input id="numero-pedido-input" value="123">
    <input id="empenho-input" value="EMP-001">
    <input id="data_pedido_input" value="2024-01-01">

    <!-- Ação Excluir -->
    <button id="btn-excluir-aocs">Excluir AOCS</button>

    <!-- Modal Edição -->
    <button id="btn-abrir-modal-edicao">Editar AOCS</button>
    <div id="modal-edicao-aocs" style="display: none;">
        <form id="form-edicao-aocs">
            <select id="edit-aocs-unidade" name="unidade_requisitante"></select>
            <textarea name="justificativa"></textarea>
            <select id="edit-aocs-orcamento" name="info_orcamentaria"></select>
            <select id="edit-aocs-local-entrega" name="local_entrega"></select>
            <select id="edit-aocs-responsavel" name="agente_responsavel"></select>
            <button type="submit">Salvar Alterações</button>
        </form>
        <button class="close-button">X</button>
    </div>

    <!-- Modal Entrega -->
    <div id="modal-registrar-entrega" style="display: none;">
        <span id="entrega-item-descricao"></span>
        <span id="entrega-saldo-restante"></span>
        <form id="form-registrar-entrega">
            <input id="quantidade_entregue" name="quantidade_entregue">
            <input id="data_entrega" name="data_entrega" type="date">
            <input name="nota_fiscal" value="NF-123">
            <button type="submit">Confirmar</button>
        </form>
        <button class="close-button">X</button>
    </div>

    <!-- Form Anexos -->
    <form id="form-anexos" action="/api/anexos/upload">
        <select id="tipo_documento_select" name="tipo_documento">
            <option value="DOC">Doc</option>
            <option value="NOVO">Novo</option>
        </select>
        <input id="tipo_documento_novo" name="tipo_documento_novo" style="display: none;">
        <input id="file" type="file" name="file">
        <button type="submit">Enviar Anexo</button>
    </form>
`;

describe('Testes Frontend - Detalhe Pedido', () => {
    let reloadMock;

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        
        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock, href: '' };

        // Reinicia a variável global se tiver sido alterada
        window.aocsDadosAtuais = {
            id: 100,
            unidade_requisitante: 'TI',
            justificativa: 'Precisa',
            info_orcamentaria: 'Verba X',
            local_entrega: 'Prédio A',
            agente_responsavel: 'João'
        };

        jest.resetModules();
        require('../../app/static/js/detalhe_pedido');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    test('Resiliência: Elementos Ausentes não devem quebrar script', () => {
        document.body.innerHTML = ''; // Remove tudo
        document.dispatchEvent(new Event('DOMContentLoaded'));
        // Se não lançar exceção, passou.
        expect(true).toBe(true);
    });

    test('Edição AOCS: Sucesso - Carrega dados e Salva', async () => {
        // Mocks para as tabelas do dropdown
        mockFetch.mockResolvedValueOnce({ json: async () => [{ nome: 'TI' }] }); // Unidades
        mockFetch.mockResolvedValueOnce({ json: async () => [{ descricao: 'Prédio A' }] }); // Locais
        mockFetch.mockResolvedValueOnce({ json: async () => [{ nome: 'João' }] }); // Agentes
        mockFetch.mockResolvedValueOnce({ json: async () => [{ info_orcamentaria: 'Verba X' }] }); // Dotações

        // Clica para abrir modal
        document.getElementById('btn-abrir-modal-edicao').click();

        // Espera popular dropdowns e valores
        await waitFor(() => {
            const form = document.getElementById('form-edicao-aocs');
            expect(form.elements['unidade_requisitante'].value).toBe('TI');
            expect(form.elements['justificativa'].value).toBe('Precisa');
        });

        // Simula submit (Salvar)
        // Mock do PUT
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

        document.getElementById('form-edicao-aocs').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/aocs/100'),
                expect.objectContaining({ method: 'PUT' })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Edição AOCS: Erro se dados globais ausentes', async () => {
        window.aocsDadosAtuais = null;
        document.getElementById('btn-abrir-modal-edicao').click();
        
        // Mock dos fetches de lista (ainda são chamados)
        mockFetch.mockResolvedValue({ json: async () => [] });

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Dados da AOCS não carregados');
        });
    });

    test('Anexos: UI - Mostrar/Esconder input "Novo Tipo"', () => {
        const select = document.getElementById('tipo_documento_select');
        const novo = document.getElementById('tipo_documento_novo');

        select.value = 'NOVO';
        select.dispatchEvent(new Event('change'));
        expect(novo.style.display).toBe('block');
        expect(novo.required).toBe(true);

        select.value = 'DOC';
        select.dispatchEvent(new Event('change'));
        expect(novo.style.display).toBe('none');
    });

    test('Anexos: Validação - Arquivo ausente', async () => {
        // Sem arquivo selecionado
        document.getElementById('form-anexos').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).not.toHaveBeenCalled();
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Selecione um arquivo');
        });
    });

    test('Inline Updates: Alterar Inputs (Empenho/Data) dispara API', async () => {
        mockFetch.mockResolvedValue({ ok: true, json: async () => ({}) });

        const inputEmpenho = document.getElementById('empenho-input');
        inputEmpenho.value = 'NOVO-EMP';
        inputEmpenho.dispatchEvent(new Event('change'));

        const inputData = document.getElementById('data_pedido_input');
        inputData.value = '2024-12-31';
        inputData.dispatchEvent(new Event('change'));

        await waitFor(() => {
            // Verifica chamadas
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/aocs/100',
                expect.objectContaining({
                    method: 'PUT',
                    body: JSON.stringify({ empenho: 'NOVO-EMP' })
                })
            );
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/aocs/100',
                expect.objectContaining({
                    method: 'PUT',
                    body: JSON.stringify({ data_criacao: '2024-12-31' })
                })
            );
        });
    });

    test('Excluir AOCS: Fluxo de Sucesso', async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

        document.getElementById('btn-excluir-aocs').click();

        await waitFor(() => {
            expect(global.confirm).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalledWith('/api/aocs/100', { method: 'DELETE' });
            expect(window.location.href).toContain('/voltar'); // Redirecionamento
        });
    });

    test('Registrar Entrega: Sucesso', async () => {
        window.abrirModalEntrega(50, 'Item Teste', 100);
        
        const modal = document.getElementById('modal-registrar-entrega');
        expect(modal.style.display).toBe('flex');
        expect(document.getElementById('entrega-item-descricao').textContent).toBe('Item Teste');

        // Preenche form
        const form = document.getElementById('form-registrar-entrega');
        form.querySelector('[name="quantidade_entregue"]').value = '10,00';
        form.querySelector('[name="data_entrega"]').value = '2024-05-20';

        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                '/api/pedidos/50/registrar-entrega',
                expect.objectContaining({
                    method: 'PUT',
                    body: JSON.stringify({
                        quantidade: "10.00",
                        data_entrega: '2024-05-20',
                        nota_fiscal: 'NF-123'
                    })
                })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });
});
