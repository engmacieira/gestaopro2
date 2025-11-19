// Simula a função fetch global do navegador (API de rede)
const mockFetch = jest.fn();
global.fetch = mockFetch;

// 💡 Salva a referência original de window.location para restauração
const originalLocation = window.location; 
let reloadMock; // O mock de reload que usaremos

// Funções auxiliares para simular eventos do navegador
function dispatchDOMContentLoaded() {
    // Inicializa o categorias.js
    document.dispatchEvent(new Event('DOMContentLoaded', {
        bubbles: true,
        cancelable: true
    }));
}

// Função auxiliar para configurar o ambiente DOM
function setupDOM() {
    // Estrutura HTML Mínima necessária para o categorias.js
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

    // Carrega o script que queremos testar. 
    require('../../app/static/js/categorias'); //
}

describe('Testes de Funcionalidades do categorias.js', () => {
    
    // Configura o Mock de window.location.reload UMA ÚNICA VEZ (Corrigindo o problema do JSDOM)
    beforeAll(() => {
        reloadMock = jest.fn();

        // 💡 Solução definitiva: Deleta a propriedade 'location' e a recria com nosso mock.
        delete window.location;
        window.location = { reload: reloadMock };

        // Mock para simular a confirmação de exclusão/status
        global.confirm = jest.fn(() => true);
    });
    
    afterAll(() => {
        // Restaura o objeto original de location.
        window.location = originalLocation;
    });

    beforeEach(() => {
        // Limpa mocks e DOM antes de cada teste.
        jest.clearAllMocks();
        reloadMock.mockClear(); // Limpa as chamadas do mock
        setupDOM(); 
        dispatchDOMContentLoaded(); 
    });

    // 1. Testando a Abertura e Fechamento do Modal
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

    // 2. Testando o Cadastro de Nova Categoria (POST)
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

        // 💡 CORREÇÃO DE TIMING: Força a resolução de Promessas internas (fetch e json)
        await Promise.resolve(); 
        await Promise.resolve(); 

        expect(mockFetch).toHaveBeenCalledWith('/api/categorias', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: 'Nova Categoria Teste' }),
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('Categoria \'Nova Categoria Teste\' criada com sucesso!');
        expect(reloadMock).toHaveBeenCalledTimes(1); 
    });
    
    // 3. Testando Edição de Categoria (PUT)
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

        // 💡 CORREÇÃO DE TIMING
        await Promise.resolve();
        await Promise.resolve(); 

        expect(mockFetch).toHaveBeenCalledTimes(2); 
        
        expect(mockFetch).toHaveBeenLastCalledWith(`/api/categorias/${mockId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: 'Categoria Editada' }),
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('Categoria \'Categoria Editada\' atualizada com sucesso!');
        expect(reloadMock).toHaveBeenCalledTimes(1);
    });

    // 4. Testando Deleção de Categoria (DELETE)
    test('Deve enviar a requisição de deleção de categoria e recarregar a página', async () => {
        const mockId = 99;

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => ({}), 
        });

        await window.excluirCategoria(mockId);
        
        // 💡 CORREÇÃO DE TIMING
        await Promise.resolve();
        await Promise.resolve(); 

        expect(mockFetch).toHaveBeenCalledWith(`/api/categorias/${mockId}`, {
            method: 'DELETE',
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('Categoria excluída com sucesso!');
        expect(reloadMock).toHaveBeenCalledTimes(1); 
    });

    // 5. Testando Alternância de Status (PATCH)
    test('Deve enviar a requisição para ativar a categoria', async () => {
        const mockId = 7;

        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ id: mockId, nome: 'Categoria Inativa' }),
        });

        await window.toggleStatusCategoria(mockId, false);
        
        // 💡 CORREÇÃO DE TIMING
        await Promise.resolve();
        await Promise.resolve(); 

        expect(mockFetch).toHaveBeenCalledWith(`/api/categorias/${mockId}/status?activate=true`, {
            method: 'PATCH',
        });
        
        expect(sessionStorage.getItem('notificationMessage')).toContain('ativada com sucesso!');
        expect(reloadMock).toHaveBeenCalledTimes(1);
    });
    
    // 6. Testando Erro de Validação
    test('Deve exibir notificação de erro se o nome estiver vazio', async () => {
        const form = document.getElementById('form-categoria');
        const inputNome = document.getElementById('nome-categoria');
        const notificationArea = document.getElementById('notification-area');

        inputNome.value = ' ';

        // Código síncrono, não precisa de await Promise.resolve()
        await form.dispatchEvent(new Event('submit', { cancelable: true })); 

        expect(mockFetch).not.toHaveBeenCalled(); 
        expect(notificationArea.children.length).toBe(1);
        expect(notificationArea.textContent).toContain('O nome da categoria não pode estar vazio.');
        expect(reloadMock).not.toHaveBeenCalled(); 
    });

});