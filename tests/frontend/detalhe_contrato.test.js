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
const DOM_HTML = `
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
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Patch de Compatibilidade (innerText -> textContent)
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // Spies de Eventos
        documentSpy = jest.spyOn(document, 'addEventListener');
        windowSpy = jest.spyOn(window, 'addEventListener');

        // Mocks Globais
        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };
        
        window.confirm = jest.fn(() => true);
        
        // Variável global esperada pelo script
        window.nomeContratoGlobal = 'CT-123/2024';
        
        // Scroll Mock (evita erro "scrollIntoView is not a function")
        Element.prototype.scrollIntoView = jest.fn();

        // Carrega Script
        jest.resetModules();
        require('../../app/static/js/detalhe_contrato');
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
        delete window.nomeContratoGlobal;
    });

    // ==========================================================================
    // 4. TESTES - ITENS DO CONTRATO
    // ==========================================================================

    test('Deve alternar visibilidade do formulário de item ao clicar no botão', () => {
        const btn = document.getElementById('btn-toggle-form');
        const container = document.getElementById('form-container-item');
        const titulo = document.getElementById('form-item-titulo');

        // 1. Abrir
        btn.click();
        expect(container.style.display).toBe('block');
        expect(titulo.textContent).toBe('Adicionar Novo Item');

        // 2. Fechar
        btn.click();
        expect(container.style.display).toBe('none');
    });

    test('Edição de Item: Deve buscar dados da API e preencher o formulário', async () => {
        // Mock dos dados do item
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                id: 50,
                numero_item: 1,
                descricao: { descricao: 'Cadeira de Escritório' },
                marca: 'Marca X',
                unidade_medida: 'UN',
                quantidade: 10.50,
                valor_unitario: 150.00
            })
        });

        // Chama função global exposta pelo script
        await window.abrirFormParaEditarItem(50);

        const container = document.getElementById('form-container-item');
        const form = document.getElementById('form-item');

        expect(mockFetch).toHaveBeenCalledWith('/api/itens/50');
        expect(container.style.display).toBe('block');
        expect(document.getElementById('form-item-titulo').textContent).toBe('Editar Item');
        
        // Verifica preenchimento (nota: o script formata numeros para PT-BR)
        expect(document.getElementById('descricao').value).toBe('Cadeira de Escritório');
        expect(document.getElementById('quantidade').value).toContain('10,50'); // Formatação BR
    });

    test('Salvar Item (POST): Deve enviar dados formatados corretamente', async () => {
        // Preenche formulário
        document.getElementById('numero_item').value = '2';
        document.getElementById('descricao').value = 'Mesa';
        document.getElementById('unidade_medida').value = 'UN';
        document.getElementById('quantidade').value = '5,00'; // Input BR
        document.getElementById('valor_unitario').value = '200,00';

        // Mock resposta sucesso
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ numero_item: 2 })
        });

        // Dispara submit
        const form = document.getElementById('form-item');
        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/itens', expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('"quantidade":"5.00"') // Verifica conversão para float ponto
            }));
            expect(reloadMock).toHaveBeenCalled();
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('cadastrado com sucesso');
    });

    test('Excluir Item: Deve confirmar e enviar DELETE', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => ({})
        });

        await window.excluirItem(99);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/itens/99', { method: 'DELETE' });
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Status Item: Deve enviar PATCH para alternar status', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ numero_item: 1, ativo: false })
        });

        // Status atual true, espera enviar false
        await window.toggleItemStatus(10, true);

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/status?activate=false'), 
                { method: 'PATCH' }
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    // ==========================================================================
    // 5. TESTES - ANEXOS
    // ==========================================================================

    test('Interface Anexo: Deve mostrar input "Novo Tipo" quando selecionado', () => {
        const select = document.getElementById('tipo_documento_select_anexo');
        const inputNovo = document.getElementById('tipo_documento_novo_anexo');

        // Seleciona opção normal
        select.value = 'Contrato';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('none');

        // Seleciona opção NOVO
        select.value = 'NOVO';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('block');
    });

    test('Upload Anexo: Deve bloquear envio sem arquivo', async () => {
        const form = document.getElementById('form-upload-anexo-contrato');
        // Não selecionamos arquivo

        form.dispatchEvent(new Event('submit'));
        await new Promise(r => setTimeout(r, 100)); // Espera

        expect(mockFetch).not.toHaveBeenCalled();
        const notif = document.getElementById('notification-area');
        expect(notif.textContent).toContain('selecione um arquivo');
    });

    test('Excluir Anexo: Deve confirmar e enviar DELETE', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => ({})
        });

        await window.excluirAnexo(55, 'seguro.pdf', 'original.pdf');

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/anexos/55', { method: 'DELETE' });
            expect(reloadMock).toHaveBeenCalled();
        });
    });
});