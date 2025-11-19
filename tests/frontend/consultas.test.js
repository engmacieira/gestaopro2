/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Função de espera robusta
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

// HTML Base simulando a estrutura do template _consultas_form.html e consultas.html
const DOM_HTML = `
    <div class="card full-width">
        <form id="form-consulta">
            <div class="form-group">
                <select id="tipo-consulta">
                    <option value="" disabled selected>Selecione...</option>
                    <option value="processo_licitatorio">Processo Licitatório</option>
                    <option value="unidade_requisitante">Unidade Requisitante</option>
                </select>
            </div>

            <div id="container-valor-consulta" style="display: none;">
                <label id="label-valor-consulta">Selecione o Valor</label>
                <select id="valor-consulta"></select>
            </div>

            <button type="submit" id="btn-consultar">Consultar</button>
        </form>
    </div>
    
    <div id="area-resultados">
        <div class="empty-state">Aguardando...</div>
    </div>
`;

describe('Testes Frontend - Consultas', () => {
    let documentSpy;
    
    // ==========================================================================
    // 2. SETUP
    // ==========================================================================
    beforeEach(() => {
        // A. Limpeza
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // B. Patch de compatibilidade (innerText -> textContent)
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // C. Mock da Variável Global configEntidades
        // O script consultas.js espera que isso exista no window
        window.configEntidades = {
            'processo_licitatorio': { label: 'Selecionar Processo' },
            'unidade_requisitante': { label: 'Selecionar Unidade' }
        };

        // D. Espião de Eventos (para limpeza posterior)
        documentSpy = jest.spyOn(document, 'addEventListener');
        // Nota: O script adiciona listeners em elementos específicos (select, form), 
        // não no window, então focar no document e elementos é suficiente.

        // E. Carrega o Script Isolado
        jest.resetModules();
        require('../../app/static/js/consultas'); // Ajuste o caminho se necessário

        // F. Inicia o Script
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // 3. TEARDOWN
    // ==========================================================================
    afterEach(() => {
        // Remove listeners globais do document se houverem
        if (documentSpy) {
            documentSpy.mock.calls.forEach(call => {
                const [type, listener] = call;
                document.removeEventListener(type, listener);
            });
            documentSpy.mockRestore();
        }
        
        // Limpa variável global mockada
        delete window.configEntidades;
    });

    // ==========================================================================
    // 4. TESTES
    // ==========================================================================

    test('Deve carregar opções ao selecionar um tipo de consulta (processo_licitatorio)', async () => {
        // Mock da resposta do backend para as opções do select
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ([
                { id: 1, texto: 'Processo 001/2024' },
                { id: 2, texto: 'Processo 002/2024' }
            ])
        });

        const tipoSelect = document.getElementById('tipo-consulta');
        const valorContainer = document.getElementById('container-valor-consulta');
        const valorSelect = document.getElementById('valor-consulta');

        // 1. Seleciona o tipo
        tipoSelect.value = 'processo_licitatorio';
        tipoSelect.dispatchEvent(new Event('change'));

        // 2. Verifica se mostrou o container
        expect(valorContainer.style.display).toBe('block');
        expect(document.getElementById('label-valor-consulta').textContent).toBe('Selecionar Processo');

        // 3. Aguarda o fetch e o preenchimento do select
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/consultas/entidades/processo_licitatorio');
            expect(valorSelect.options.length).toBeGreaterThan(1); // Placeholder + Opções
            expect(valorSelect.options[1].text).toBe('Processo 001/2024');
        });
    });

    test('Deve realizar a busca e renderizar tabela de resultados com sucesso', async () => {
        const tipoSelect = document.getElementById('tipo-consulta');
        const valorSelect = document.getElementById('valor-consulta');
        const form = document.getElementById('form-consulta');
        const areaResultados = document.getElementById('area-resultados');

        // 1. Configura estado inicial (simula que o usuário já selecionou as opções)
        tipoSelect.value = 'processo_licitatorio';
        
        // Adiciona uma opção manualmente ao select de valor para poder selecioná-la
        const option = document.createElement('option');
        option.value = '10';
        option.text = 'Processo Teste';
        valorSelect.add(option);
        valorSelect.value = '10';

        // 2. Mock da resposta da busca (Resultados)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                titulo: 'Resultados Teste',
                tipo: 'processo_licitatorio', // Importante: deve bater com o colunasMap no JS
                resultados: [
                    { 
                        numero_contrato: '123/2024', 
                        fornecedor: 'Empresa X', 
                        nome_categoria: 'Obras', 
                        ativo: true,
                        id: 99
                    }
                ]
            })
        });

        // 3. Submete o formulário
        form.dispatchEvent(new Event('submit'));

        // 4. Verifica feedback de carregamento
        expect(areaResultados.innerHTML).toContain('Buscando...');

        // 5. Aguarda renderização da tabela
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/consultas?tipo=processo_licitatorio&valor=10');
            
            // Verifica se a tabela foi criada
            const tabela = areaResultados.querySelector('table');
            expect(tabela).toBeTruthy();
            
            // Verifica conteúdo da linha
            expect(tabela.textContent).toContain('123/2024');
            expect(tabela.textContent).toContain('Empresa X');
            expect(tabela.textContent).toContain('Ativo');
        });
    });

    test('Deve exibir mensagem quando nenhum resultado for encontrado', async () => {
        const tipoSelect = document.getElementById('tipo-consulta');
        const valorSelect = document.getElementById('valor-consulta');
        const form = document.getElementById('form-consulta');
        const areaResultados = document.getElementById('area-resultados');

        tipoSelect.value = 'unidade_requisitante';
        
        const option = document.createElement('option');
        option.value = '5';
        valorSelect.add(option);
        valorSelect.value = '5';

        // Mock resposta vazia
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                titulo: 'Resultados',
                tipo: 'unidade_requisitante',
                resultados: [] // Lista vazia
            })
        });

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(areaResultados.textContent).toContain('Nenhum resultado encontrado');
            expect(areaResultados.querySelector('table')).toBeNull();
        });
    });

    test('Deve tratar erro na busca (API Error)', async () => {
        const tipoSelect = document.getElementById('tipo-consulta');
        const valorSelect = document.getElementById('valor-consulta');
        const form = document.getElementById('form-consulta');
        const areaResultados = document.getElementById('area-resultados');

        tipoSelect.value = 'processo_licitatorio';
        const option = document.createElement('option');
        option.value = '1';
        valorSelect.add(option);
        valorSelect.value = '1';

        // Mock Erro 500
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ erro: 'Erro interno no servidor' })
        });

        form.dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(areaResultados.querySelector('.notification.error')).toBeTruthy();
            expect(areaResultados.textContent).toContain('Erro interno no servidor');
        });
    });

    test('Não deve submeter se os campos estiverem vazios', async () => {
        const form = document.getElementById('form-consulta');
        
        // Campos vazios por padrão no HTML mockado
        form.dispatchEvent(new Event('submit'));

        await new Promise(r => setTimeout(r, 100)); // Pequena espera

        expect(mockFetch).not.toHaveBeenCalled();
    });
});