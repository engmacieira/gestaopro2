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

const DOM_HTML = `
    <div class="card full-width">
        <form id="form-consulta">
            <div class="form-group">
                <select id="tipo-consulta">
                    <option value="" disabled selected>Selecione...</option>
                    <option value="processo_licitatorio">Processo Licitatório</option>
                    <option value="unidade_requisitante">Unidade Requisitante</option>
                    <option value="tipo_sem_config">Tipo Quebrado</option>
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
    let consoleSpy;
    
    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        window.configEntidades = {
            'processo_licitatorio': { label: 'Selecionar Processo' },
            'unidade_requisitante': { label: 'Selecionar Unidade' }
        };

        documentSpy = jest.spyOn(document, 'addEventListener');
        consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        jest.resetModules();
        require('../../app/static/js/consultas'); 
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    afterEach(() => {
        if (documentSpy) documentSpy.mockRestore();
        consoleSpy.mockRestore();
        delete window.configEntidades;
    });

    test('Select Tipo: Deve carregar opções e mostrar container corretamente', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ([
                { id: 1, texto: 'Opção A' },
                { id: 2, texto: 'Opção B' }
            ])
        });

        const tipoSelect = document.getElementById('tipo-consulta');
        const valorContainer = document.getElementById('container-valor-consulta');
        const valorSelect = document.getElementById('valor-consulta');

        tipoSelect.value = 'processo_licitatorio';
        tipoSelect.dispatchEvent(new Event('change'));

        expect(valorContainer.style.display).toBe('block');
        expect(document.getElementById('label-valor-consulta').textContent).toBe('Selecionar Processo');
        expect(valorSelect.disabled).toBe(true); 

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/consultas/entidades/processo_licitatorio');
            expect(valorSelect.options.length).toBeGreaterThan(1); 
            expect(valorSelect.options[1].text).toBe('Opção A');
            expect(valorSelect.disabled).toBe(false); 
        });
    });

    test('Select Tipo: Deve lidar com erro de carregamento da API', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ erro: 'Falha ao carregar lista' })
        });

        const tipoSelect = document.getElementById('tipo-consulta');
        const valorSelect = document.getElementById('valor-consulta');

        tipoSelect.value = 'processo_licitatorio';
        tipoSelect.dispatchEvent(new Event('change'));

        await waitFor(() => {
            expect(valorSelect.innerHTML).toContain('Erro ao carregar');
            expect(consoleSpy).toHaveBeenCalled(); 
        });
    });

    test('Select Tipo: Deve ocultar container se configuração não existir', () => {
        const tipoSelect = document.getElementById('tipo-consulta');
        const valorContainer = document.getElementById('container-valor-consulta');

        tipoSelect.value = 'tipo_sem_config';
        tipoSelect.dispatchEvent(new Event('change'));

        expect(valorContainer.style.display).toBe('none');
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Configuração não encontrada'));
    });

    test('Busca (Processo): Deve renderizar tabela com link e boolean formatado', async () => {
        const areaResultados = document.getElementById('area-resultados');
        
        document.getElementById('tipo-consulta').value = 'processo_licitatorio';
        const sel = document.getElementById('valor-consulta');
        sel.innerHTML = '<option value="10" selected>Teste</option>';

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                titulo: 'Resultados',
                tipo: 'processo_licitatorio',
                resultados: [{ 
                    numero_contrato: '123/2024', 
                    fornecedor: 'Empresa X', 
                    nome_categoria: 'Obras', 
                    ativo: true, 
                    id: 99 
                }]
            })
        });

        document.getElementById('form-consulta').dispatchEvent(new Event('submit'));

        expect(areaResultados.innerHTML).toContain('Buscando...');

        await waitFor(() => {
            const table = areaResultados.querySelector('table');
            expect(table).toBeTruthy();
            
            expect(table.innerHTML).toContain('href="/contrato/99"');
            expect(table.textContent).toContain('123/2024');
            expect(table.innerHTML).toContain('status-badge green');
            expect(table.textContent).toContain('Ativo');
        });
    });

    test('Busca (Unidade): Deve renderizar badges coloridas de status (Condicional)', async () => {
        const areaResultados = document.getElementById('area-resultados');
        
        document.getElementById('tipo-consulta').value = 'unidade_requisitante';
        document.getElementById('valor-consulta').innerHTML = '<option value="5" selected>Unidade</option>';

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                titulo: 'Pedidos da Unidade',
                tipo: 'unidade_requisitante',
                resultados: [
                    { numero_aocs: 'AOCS-01', status_entrega: 'Entregue', id: 101 },
                    { numero_aocs: 'AOCS-02', status_entrega: 'Entrega Parcial', id: 102 },
                    { numero_aocs: 'AOCS-03', status_entrega: 'Pendente', id: 103 }
                ]
            })
        });

        document.getElementById('form-consulta').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const html = areaResultados.innerHTML;
            expect(html).toContain('status-badge green');  
            expect(html).toContain('status-badge orange'); 
            expect(html).toContain('status-badge gray');   
        });
    });

    test('Busca Vazia: Deve exibir mensagem de nenhum resultado', async () => {
        document.getElementById('tipo-consulta').value = 'processo_licitatorio';
        document.getElementById('valor-consulta').innerHTML = '<option value="1" selected>Vazio</option>';

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ tipo: 'processo_licitatorio', resultados: [] })
        });

        document.getElementById('form-consulta').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            expect(document.getElementById('area-resultados').textContent).toContain('Nenhum resultado encontrado');
        });
    });

    test('Erro API: Deve exibir notificação de erro na área de resultados', async () => {
        document.getElementById('tipo-consulta').value = 'processo_licitatorio';
        document.getElementById('valor-consulta').innerHTML = '<option value="1" selected>Erro</option>';

        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ erro: 'Erro Crítico no Servidor' })
        });

        document.getElementById('form-consulta').dispatchEvent(new Event('submit'));

        await waitFor(() => {
            const area = document.getElementById('area-resultados');
            expect(area.innerHTML).toContain('notification error');
            expect(area.textContent).toContain('Erro Crítico no Servidor');
        });
    });
});