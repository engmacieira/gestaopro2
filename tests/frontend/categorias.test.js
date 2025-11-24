/**
 * @jest-environment jsdom
 */

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

// HTML Padrão
const DOM_HTML_BASE = `
    <div class="main-content">
        <div id="notification-area"></div>
    </div>
    <div id="modal-categoria" style="display: none;">
        <h2 id="modal-titulo"></h2>
        <form id="form-categoria">
            <input id="nome-categoria" value="" />
            <button type="submit">Salvar</button>
        </form>
        <button id="btn-fechar-modal"></button>
        <button id="btn-cancelar-modal"></button>
    </div>
    <button id="btn-abrir-modal"></button>
`;

describe('Testes Frontend - Categorias', () => {
    let reloadMock;
    let documentSpy;
    let consoleSpy;

    beforeEach(() => {
        jest.useRealTimers();
        
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML_BASE;
        sessionStorage.clear();

        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        documentSpy = jest.spyOn(document, 'addEventListener');
        consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); 

        reloadMock = jest.fn();
        delete window.location;
        window.location = { reload: reloadMock };
        window.confirm = jest.fn(() => true);

        jest.resetModules();
        require('../../app/static/js/categorias');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        consoleSpy.mockRestore();
        if (documentSpy) documentSpy.mockRestore();
        jest.useRealTimers();
    });

    test('Inicialização: Deve exibir notificação se houver mensagem no sessionStorage', () => {
        sessionStorage.setItem('notificationMessage', 'Teste de Sessão');
        sessionStorage.setItem('notificationType', 'success');
        document.body.innerHTML = DOM_HTML_BASE; 

        jest.resetModules();
        require('../../app/static/js/categorias');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        const notif = document.querySelector('.notification.success');
        expect(notif).toBeTruthy();
        expect(notif.textContent).toBe('Teste de Sessão');
        expect(sessionStorage.getItem('notificationMessage')).toBeNull();
    });

    test('Inicialização: Deve logar erro se botão de abrir modal não existir', () => {
        document.body.innerHTML = DOM_HTML_BASE.replace('<button id="btn-abrir-modal"></button>', '');

        jest.resetModules();
        require('../../app/static/js/categorias');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        expect(consoleSpy).toHaveBeenCalledWith("Botão 'btn-abrir-modal' não encontrado.");
    });

    test('Modal: Deve abrir e limpar campos', () => {
        const btn = document.getElementById('btn-abrir-modal');
        btn.click();
        
        const modal = document.getElementById('modal-categoria');
        expect(modal.style.display).toBe('flex');
        expect(document.getElementById('modal-titulo').textContent).toBe('Cadastrar Nova Categoria');
    });

    test('Modal: Deve fechar ao clicar no botão fechar ou fora', () => {
        const modal = document.getElementById('modal-categoria');
        modal.style.display = 'flex';

        document.getElementById('btn-fechar-modal').click();
        expect(modal.style.display).toBe('none');

        modal.style.display = 'flex';
        modal.click(); 
        expect(modal.style.display).toBe('none');
    });

    test('Salvar (Erro 500): Deve exibir erro e reabilitar botão', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ erro: 'Falha interna' })
        });

        const input = document.getElementById('nome-categoria');
        input.value = 'Erro Teste';
        const form = document.getElementById('form-categoria');
        const btnSubmit = form.querySelector('button[type="submit"]');
        
        form.dispatchEvent(new Event('submit'));
        expect(btnSubmit.disabled).toBe(true); 

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif).toBeTruthy();
            expect(notif.textContent).toContain('Falha interna');
            expect(btnSubmit.disabled).toBe(false); 
        });
    });

    test('Editar (Erro ao carregar): Deve exibir notificação se ID não existe', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ detail: 'Categoria 404' })
        });

        await window.abrirModalParaEditar(999);

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Categoria 404');
            const input = document.getElementById('nome-categoria');
            expect(input.value).toBe(''); 
        });
    });

    test('Excluir: Deve cancelar se usuário negar confirmação', async () => {
        window.confirm.mockReturnValue(false); 

        await window.excluirCategoria(10);

        expect(mockFetch).not.toHaveBeenCalled(); 
        expect(reloadMock).not.toHaveBeenCalled();
    });

    test('Excluir (Erro API): Deve exibir erro se falhar', async () => {
        window.confirm.mockReturnValue(true);
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({ detail: 'Não pode excluir pois tem vinculos' })
        });

        await window.excluirCategoria(10);

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Não pode excluir pois tem vinculos');
            expect(reloadMock).not.toHaveBeenCalled();
        });
    });

    test('Toggle Status: Deve funcionar corretamente', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 5, nome: 'Cat Teste', ativa: false })
        });

        await window.toggleStatusCategoria(5, true); 

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/status?activate=false'),
                expect.objectContaining({ method: 'PATCH' })
            );
            expect(sessionStorage.getItem('notificationMessage')).toContain("Categoria 'Cat Teste' inativada");
            expect(reloadMock).toHaveBeenCalled();
        });
    });

    test('Toggle Status: Deve tratar erro da API', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ erro: 'Erro servidor' })
        });

        await window.toggleStatusCategoria(5, true);

        await waitFor(() => {
            const notif = document.querySelector('.notification.error');
            expect(notif.textContent).toContain('Erro servidor');
        });
    });

    test('Notificação: Deve desaparecer automaticamente após 5 segundos', () => {
        jest.useFakeTimers();

        const input = document.getElementById('nome-categoria');
        input.value = ''; 
        document.getElementById('form-categoria').dispatchEvent(new Event('submit'));

        let notif = document.querySelector('.notification.error');
        expect(notif).toBeTruthy();

        jest.advanceTimersByTime(5000);

        notif.dispatchEvent(new Event('transitionend'));

        notif = document.querySelector('.notification.error');
        expect(notif).toBeNull();
    });
});