const mockFetch = jest.fn();
global.fetch = mockFetch;

function setupDOM() {
    document.body.innerHTML = `
        <div class="main-content">
            <div id="notification-area"></div>
        </div>
        <div id="modal-categoria" style="display: none;">
            <h2 id="modal-titulo"></h2>
            <form id="form-categoria">
                <input id="nome-categoria" value="" />
                <button type="submit"></button>
            </form>
            <button id="btn-fechar-modal"></button>
            <button id="btn-cancelar-modal"></button>
        </div>
        <button id="btn-abrir-modal"></button>
        <table>
            <tbody></tbody>
        </table>
    `;

    require('../../app/static/js/categorias');
}

describe('Testes de Funcionalidades do categorias.js', () => {

    beforeEach(() => {
        jest.clearAllMocks();
        setupDOM();

        delete window.location;
        window.location = { reload: jest.fn() };
        global.confirm = jest.fn(() => true);
    });

    test('Deve abrir e fechar o modal de cadastro', () => {
        const modal = document.getElementById('modal-categoria');
        const btnAbrir = document.getElementById('btn-abrir-modal');
        const btnFechar = document.getElementById('btn-fechar-modal');

        btnAbrir.click();
        expect(modal.style.display).toBe('flex');
        expect(document.getElementById('modal-titulo').innerText).toBe('Cadastrar Nova Categoria');

        btnFechar.click();
        expect(modal.style.display).toBe('none');
    });

    test('Deve enviar a requisição de criação de categoria com sucesso', async () => {
        const form = document.getElementById('form-categoria');
        const inputNome = document.getElementById('nome-categoria');

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 201,
            json: async () => ({ id: 10, nome: 'Nova Categoria Teste' }),
        });

        inputNome.value = 'Nova Categoria Teste';

        await form.dispatchEvent(new Event('submit', { cancelable: true }));

        expect(mockFetch).toHaveBeenCalledWith('/api/categorias', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: 'Nova Categoria Teste' }),
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('Categoria \'Nova Categoria Teste\' criada com sucesso!');
        expect(window.location.reload).toHaveBeenCalledTimes(1);
    });
    
    test('Deve enviar a requisição de edição de categoria com sucesso', async () => {
        const form = document.getElementById('form-categoria');
        const inputNome = document.getElementById('nome-categoria');
        const mockId = 5;

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: mockId, nome: 'Categoria Antiga' }),
        });

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ id: mockId, nome: 'Categoria Editada' }),
        });

        await window.abrirModalParaEditar(mockId);
        
        inputNome.value = 'Categoria Editada';

        await form.dispatchEvent(new Event('submit', { cancelable: true }));

        expect(mockFetch).toHaveBeenCalledTimes(2); // Uma para GET e outra para PUT
        
        expect(mockFetch).toHaveBeenLastCalledWith(`/api/categorias/${mockId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: 'Categoria Editada' }),
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('Categoria \'Categoria Editada\' atualizada com sucesso!');
        expect(window.location.reload).toHaveBeenCalledTimes(1);
    });

    test('Deve enviar a requisição de deleção de categoria e recarregar a página', async () => {
        const mockId = 99;

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => ({}), 
        });

        await window.excluirCategoria(mockId);

        expect(mockFetch).toHaveBeenCalledWith(`/api/categorias/${mockId}`, {
            method: 'DELETE',
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('Categoria excluída com sucesso!');
        expect(window.location.reload).toHaveBeenCalledTimes(1);
    });

    test('Deve enviar a requisição para ativar a categoria', async () => {
        const mockId = 7;

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ id: mockId, nome: 'Categoria Inativa' }),
        });

        await window.toggleStatusCategoria(mockId, false);

        expect(mockFetch).toHaveBeenCalledWith(`/api/categorias/${mockId}/status?activate=true`, {
            method: 'PATCH',
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('ativada com sucesso!');
    });
    
    test('Deve exibir notificação de erro se o nome estiver vazio', async () => {
        const form = document.getElementById('form-categoria');
        const inputNome = document.getElementById('nome-categoria');
        const notificationArea = document.getElementById('notification-area');

        inputNome.value = ' ';

        await form.dispatchEvent(new Event('submit', { cancelable: true }));

        expect(mockFetch).not.toHaveBeenCalled(); 
        expect(notificationArea.children.length).toBe(1);
        expect(notificationArea.textContent).toContain('O nome da categoria não pode estar vazio.');
    });

});