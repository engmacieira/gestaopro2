/**
 * @jest-environment jsdom
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;
global.alert = jest.fn();
global.confirm = jest.fn(() => true);

// Simula a variável global injetada pelo template HTML
window.nomeContratoGlobal = 'CT-123/2024';

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
    </div>

    <button id="btn-toggle-form">Adicionar Novo Item</button>

    <div id="form-container-item" style="display: none;">
        <h2 id="form-item-titulo">Adicionar Novo Item</h2>
        <form id="form-item">
            <input type="number" name="numero_item" value="1">
            <input type="text" name="marca">
            <input type="text" name="unidade_medida">
            <input type="text" name="quantidade" id="quantidade">
            <input type="text" name="valor_unitario" id="valor_unitario">
            <textarea name="descricao"></textarea>
            <button type="submit">Salvar</button>
        </form>
    </div>

    <form id="form-upload-anexo-contrato" action="/api/anexos/upload">
        <select id="tipo_documento_select_anexo" name="tipo_documento">
            <option value="">Selecione</option>
            <option value="Contrato">Contrato</option>
            <option value="NOVO">Outro</option>
        </select>
        <input type="text" id="tipo_documento_novo_anexo" name="tipo_documento_novo" style="display: none;">
        <input type="file" id="anexo_file" name="file">
        <button type="submit">Enviar</button>
    </form>
`;

describe('Testes Frontend - Detalhe Contrato', () => {
    let reloadMock;

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;

        // Mock scrollIntoView para evitar erro no JSDOM
        Element.prototype.scrollIntoView = jest.fn();

        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };

        jest.resetModules();
        require('../../app/static/js/detalhe_contrato');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    test('UI: Botão toggle deve mostrar/esconder formulário', () => {
        const btn = document.getElementById('btn-toggle-form');
        const formContainer = document.getElementById('form-container-item');
        
        // Abrir
        btn.click();
        expect(formContainer.style.display).toBe('block');
        expect(document.getElementById('form-item-titulo').textContent).toBe('Adicionar Novo Item');

        // Fechar
        btn.click();
        expect(formContainer.style.display).toBe('none');
    });

    test('Salvar Item: Deve enviar dados formatados corretamente (PT-BR -> Float)', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ numero_item: 1 })
        });

        // Preencher form
        const form = document.getElementById('form-item');
        form.querySelector('[name="unidade_medida"]').value = 'cx';
        form.querySelector('[name="quantidade"]').value = '1.000,50'; // 1000.5
        form.querySelector('[name="valor_unitario"]').value = '200,00'; // 200.0

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/itens'),
                expect.objectContaining({
                    method: 'POST',
                    body: expect.stringContaining('"quantidade":1000.5') // JSON Number
                })
            );
            expect(mockFetch).toHaveBeenCalledWith(
                expect.anything(),
                expect.objectContaining({
                    body: expect.stringContaining('"valor_unitario":200') // JSON Number
                })
            );
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Salvar Item: Deve bloquear envio de valores inválidos', async () => {
        const form = document.getElementById('form-item');
        // Quantidade inválida
        form.querySelector('[name="quantidade"]').value = 'abc';
        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).not.toHaveBeenCalled();
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Quantidade e Valor Unitário devem ser números válidos');
        });
    });

    test('Salvar Item: Deve tratar erro da API (500)', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ erro: 'Erro no Banco de Dados' })
        });

        const form = document.getElementById('form-item');
        form.querySelector('[name="quantidade"]').value = '10';
        form.querySelector('[name="valor_unitario"]').value = '10';

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Erro no Banco de Dados');
            expect(document.querySelector('button[type="submit"]').disabled).toBe(false);
        });
    });

    test('Editar Item: Deve buscar dados e preencher (Sucesso)', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                id: 50,
                numero_item: 1,
                unidade_medida: 'Un',
                quantidade: 10.5,
                valor_unitario: 50.0,
                descricao: { descricao: 'Teste Desc' }
            })
        });

        await window.abrirFormParaEditarItem(50);

        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/itens/50')
        );

        await waitFor(() => {
             // Verificação principal: Dados foram carregados?
             const qtdVal = document.getElementById('quantidade').value;
             expect(qtdVal.replace('.', ',')).toContain('10,5');
        });
    });

    test('Editar Item: Deve exibir erro se falhar ao buscar', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 404,
            json: async () => ({})
        });

        await window.abrirFormParaEditarItem(999);

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Erro ao buscar dados');
        });
    });

    test('Status Item: Deve enviar PATCH corretamente', async () => {
        mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

        await window.toggleItemStatus(10, true);

        expect(global.confirm).toHaveBeenCalled();
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/itens/10/status?activate=false'),
            expect.objectContaining({ method: 'PATCH' })
        );
        expect(reloadMock).toHaveBeenCalled();
    });

    test('Anexos: UI - Mostrar/Esconder input "Novo Tipo"', () => {
        const select = document.getElementById('tipo_documento_select_anexo');
        const inputNovo = document.getElementById('tipo_documento_novo_anexo');

        // Seleciona NOVO
        select.value = 'NOVO';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('block');

        // Seleciona Outro
        select.value = 'Contrato';
        select.dispatchEvent(new Event('change'));
        expect(inputNovo.style.display).toBe('none');
    });

    test('Upload Anexo: Deve validar "Novo Tipo" vazio', async () => {
        const select = document.getElementById('tipo_documento_select_anexo');
        select.value = 'NOVO';
        select.dispatchEvent(new Event('change'));

        // Simula arquivo
        Object.defineProperty(document.getElementById('anexo_file'), 'files', {
            value: [new File(['content'], 'test.pdf', { type: 'application/pdf' })]
        });

        document.getElementById('form-upload-anexo-contrato').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(mockFetch).not.toHaveBeenCalled();
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent.toLowerCase()).toContain('informe o nome do novo tipo');
        });
    });

    test('Excluir Anexo: Deve tratar erro da API', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 403,
            json: async () => ({ detail: 'Arquivo protegido' })
        });

        await window.excluirAnexo(5, 'safe_name', 'Original.pdf');

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            // Agora o código lê o detail do erro
            expect(notif.textContent).toContain('Arquivo protegido');
            expect(reloadMock).not.toHaveBeenCalled();
        });
    });
});
