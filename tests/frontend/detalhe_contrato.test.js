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

// HTML Combinado (Base + Form Item + Seção Anexos)
const DOM_HTML_BASE = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>

    <div class="card-actions">
        <button id="btn-toggle-form">Adicionar Item</button>
    </div>

    <div id="form-container-item" style="display: none;">
        <form id="form-item">
            <h3 id="form-item-titulo">Adicionar Novo Item</h3>
            <input type="number" name="numero_item" id="numero_item" value="">
            <input type="text" name="descricao" id="descricao" value="">
            <input type="text" name="marca" id="marca" value="">
            <input type="text" name="unidade_medida" id="unidade_medida" value="">
            <input type="text" name="quantidade" id="quantidade" value="">
            <input type="text" name="valor_unitario" id="valor_unitario" value="">
            <button type="submit">Salvar</button>
        </form>
    </div>

    <form id="form-upload-anexo-contrato" action="/api/anexos/upload/" method="POST">
        <select name="tipo_documento" id="tipo_documento_select_anexo">
            <option value="" selected>Selecione...</option>
            <option value="Contrato">Contrato</option>
            <option value="NOVO">--- CRIAR NOVO TIPO ---</option>
        </select>
        <input type="text" name="tipo_documento_novo" id="tipo_documento_novo_anexo" style="display: none;">
        <input type="file" name="file" id="anexo_file">
        <button type="submit">Enviar</button>
    </form>
`;

describe('Testes Frontend - Detalhe Contrato', () => {
    let reloadMock;
    let documentSpy;
    let windowSpy;

    // ==========================================================================
    // 2. SETUP
    // ==========================================================================
    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML_BASE;
        sessionStorage.clear();

        // Patch de Compatibilidade
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
        window.location = { reload: reloadMock };
        
        window.confirm = jest.fn(() => true);
        window.nomeContratoGlobal = 'CT-123/2024';
        
        // Scroll Mock
        Element.prototype.scrollIntoView = jest.fn();

        // Carrega Script
        jest.resetModules();
        require('../../app/static/js/detalhe_contrato');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        if (documentSpy) documentSpy.mockRestore();
        if (windowSpy) windowSpy.mockRestore();
        delete window.nomeContratoGlobal;
    });

    // ==========================================================================
    // 3. TESTES - INICIALIZAÇÃO E UI
    // ==========================================================================

    test('Inicialização: Deve exibir notificação do SessionStorage se existir', () => {
        sessionStorage.setItem('notificationMessage', 'Item salvo');
        sessionStorage.setItem('notificationType', 'success');
        
        document.body.innerHTML = DOM_HTML_BASE;
        jest.resetModules();
        require('../../app/static/js/detalhe_contrato');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        const notif = document.querySelector('.notification.success');
        expect(notif).toBeTruthy();
        expect(notif.textContent).toBe('Item salvo');
        expect(sessionStorage.getItem('notificationMessage')).toBeNull();
    });

    test('Formulário UI: Deve alternar visibilidade ao clicar no botão', () => {
        const btn = document.getElementById('btn-toggle-form');
        const container = document.getElementById('form-container-item');
        
        btn.click();
        expect(container.style.display).toBe('block');
        expect(Element.prototype.scrollIntoView).toHaveBeenCalled();

        btn.click();
        expect(container.style.display).toBe('none');
    });

    // ==========================================================================
    // 4. TESTES - CRUD DE ITENS
    // ==========================================================================

    test('Salvar Item: Deve enviar dados formatados corretamente (PT-BR -> Float)', async () => {
        // Preenche formulário com formato brasileiro
        document.getElementById('quantidade').value = '1.000,50'; // Mil e cinquenta
        document.getElementById('valor_unitario').value = '200,00';
        document.getElementById('numero_item').value = '1';

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ numero_item: 1 })
        });

        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/itens', expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('"quantidade":"1000.50"') // Verifica conversão
            }));
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Salvar Item: Deve bloquear envio de valores inválidos', async () => {
        document.getElementById('quantidade').value = 'texto_invalido';
        
        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).not.toHaveBeenCalled();
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Quantidade e Valor Unitário devem ser números válidos');
        });
    });

    test('Salvar Item: Deve tratar erro da API (500)', async () => {
        document.getElementById('quantidade').value = '10,00';
        document.getElementById('valor_unitario').value = '10,00';

        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ erro: 'Erro no Banco de Dados' })
        });

        document.getElementById('form-item').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Erro no Banco de Dados');
            // Botão deve ser reabilitado
            expect(document.querySelector('button[type="submit"]').disabled).toBe(false);
        });
    });

    test('Editar Item: Deve buscar dados e preencher (Sucesso)', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                id: 50,
                numero_item: 1,
                descricao: { descricao: 'Item Teste' },
                quantidade: 10.5,
                valor_unitario: 100
            })
        });

        await window.abrirFormParaEditarItem(50);

        expect(mockFetch).toHaveBeenCalledWith('/api/itens/50');
        // Verifica formatação de volta para PT-BR no input
        expect(document.getElementById('quantidade').value).toContain('10,50');
        expect(document.getElementById('form-item-titulo').textContent).toBe('Editar Item');
    });

    test('Editar Item: Deve exibir erro se falhar ao buscar', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ detail: 'Item não encontrado' })
        });

        await window.abrirFormParaEditarItem(999);

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Item não encontrado');
        });
    });

    test('Excluir Item: Deve cancelar ação se usuário negar confirmação', async () => {
        window.confirm.mockReturnValue(false);
        await window.excluirItem(10);
        expect(mockFetch).not.toHaveBeenCalled();
    });

    test('Status Item: Deve enviar PATCH corretamente', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ numero_item: 1 })
        });

        await window.toggleItemStatus(5, true);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('activate=false'), { method: 'PATCH' });
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    // ==========================================================================
    // 5. TESTES - ANEXOS
    // ==========================================================================

    test('Upload Anexo: Deve enviar com sucesso', async () => {
        const form = document.getElementById('form-upload-anexo-contrato');
        
        // Simula seleção de arquivo
        const file = new File(['dummy'], 'teste.pdf', { type: 'application/pdf' });
        const fileInput = document.getElementById('anexo_file');
        Object.defineProperty(fileInput, 'files', { value: [file] });

        // Seleciona tipo
        document.getElementById('tipo_documento_select_anexo').value = 'Contrato';

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ mensagem: 'Sucesso' })
        });

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/anexos/upload/'),
                expect.objectContaining({ method: 'POST', body: expect.any(FormData) })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Upload Anexo: Deve validar "Novo Tipo" vazio', async () => {
        const form = document.getElementById('form-upload-anexo-contrato');
        
        // Arquivo selecionado
        const file = new File(['dummy'], 't.pdf', { type: 'application/pdf' });
        Object.defineProperty(document.getElementById('anexo_file'), 'files', { value: [file] });

        // Seleciona NOVO mas deixa input vazio
        const select = document.getElementById('tipo_documento_select_anexo');
        select.value = 'NOVO';
        select.dispatchEvent(new Event('change')); // Dispara lógica de mostrar input
        
        // Submit
        form.dispatchEvent(new Event('submit'));
        await new Promise(r => setTimeout(r, 100));

        expect(mockFetch).not.toHaveBeenCalled();
        const notif = document.querySelector('.notification.error');
        expect(notif.textContent).toContain('informe o nome do novo tipo');
    });

    test('Excluir Anexo: Deve tratar erro da API', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ detail: 'Arquivo protegido' })
        });

        await window.excluirAnexo(1, 'arq.pdf', 'arq.pdf');

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Arquivo protegido');
            expect(reloadMock).not.toHaveBeenCalled();
        });
    });
});