/**
 * @jest-environment jsdom
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;

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
        
        <input type="text" id="campo-busca" value="">
        
        <table>
            <thead>
                <tr>
                    <th class="sortable" data-sort="descricao">Descrição <i></i></th>
                    <th class="sortable" data-sort="saldo">Saldo <i></i></th>
                    </tr>
            </thead>
            <tbody id="corpo-tabela-itens">
                </tbody>
        </table>
        <div id="pagination-container"></div>

        <div id="carrinho-itens"></div>
        <div id="carrinho-total">
            Total: <strong>R$ 0,00</strong>
        </div>
        <button id="btn-limpar-carrinho">Limpar</button>
        <button id="btn-finalizar-pedido" disabled>Finalizar Pedido</button>
    </div>

    <div id="modal-finalizar-pedido" style="display: none;">
        <form id="form-finalizar-pedido">
            <div id="aocs-por-contrato-container"></div>
            
            <input id="aocs-unidade" value="Unidade Teste" required>
            <input id="aocs-justificativa" value="Justificativa Teste" required>
            <input id="aocs-orcamento" value="Verba X" required>
            <input id="aocs-local-entrega" value="Local Y" required>
            <input id="aocs-responsavel" value="Fulano" required>

            <button type="button" id="btn-cancelar-modal">Cancelar</button>
            <button type="button" id="btn-enviar-pedido">Confirmar e Enviar</button>
        </form>
        <button id="btn-fechar-modal">X</button>
    </div>
`;

describe('Testes Frontend - Novo Pedido', () => {
    
    const itensMock = [
        {
            id: 101,
            numero_item: 1,
            descricao: { descricao: "Cimento CP-II" },
            numero_contrato: "123/2024",
            id_contrato: 55,
            saldo: 100.00,
            valor_unitario: 50.00
        },
        {
            id: 102,
            numero_item: 2,
            descricao: { descricao: "Areia Lavada" },
            numero_contrato: "124/2024",
            id_contrato: 56,
            saldo: 50.00,
            valor_unitario: 100.00
        }
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        window.idCategoriaGlobal = 1; 
        window.redirectUrlPedidosGlobal = '/pedidos';
        
        window.confirm = jest.fn(() => true);
        window.alert = jest.fn();
        delete window.location;
        window.location = { href: '' };

        mockFetch.mockImplementation(async (url) => {
            if (url.includes('/itens')) {
                return {
                    ok: true,
                    json: async () => ({ 
                        itens: itensMock,
                        total_paginas: 1,
                        pagina_atual: 1
                    })
                };
            }
            return { ok: false }; 
        });

        let domCallback = null;
        const originalAddEventListener = document.addEventListener;
        
        document.addEventListener = jest.fn((event, callback) => {
            if (event === 'DOMContentLoaded') {
                domCallback = callback;
            } else {
                originalAddEventListener.call(document, event, callback);
            }
        });

        jest.resetModules();
        require('../../app/static/js/novo_pedido');
        
        document.addEventListener = originalAddEventListener;

        if (domCallback) domCallback();
    });

    test('Inicialização: Deve buscar e renderizar itens na tabela', async () => {
        await waitFor(() => {
            const linhas = document.querySelectorAll('#corpo-tabela-itens tr');
            expect(linhas.length).toBe(2);
            expect(document.body.textContent).toContain('Cimento CP-II');
        });
    });

    test('Carrinho: Adicionar item deve atualizar UI e Variável Global', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input'); 
        input.value = '2,00';
        input.dispatchEvent(new Event('change'));

        await waitFor(() => {
            const carrinhoTotal = document.getElementById('carrinho-total');
            expect(carrinhoTotal.textContent).toContain('R$ 100,00');
            const btnFinalizar = document.getElementById('btn-finalizar-pedido');
            expect(btnFinalizar.disabled).toBe(false);
        });
    });

    test('Validação: Quantidade > Saldo deve ser corrigida', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input'); 
        input.value = '200,00';
        input.dispatchEvent(new Event('change'));

        await waitFor(() => {
            expect(input.value).toBe('100,00');
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Saldo insuficiente');
        });
    });

    test('Fluxo Completo: Finalizar pedido com sucesso', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input');
        input.value = '1,00';
        input.dispatchEvent(new Event('change'));

        document.getElementById('btn-finalizar-pedido').click();
        
        const modal = document.getElementById('modal-finalizar-pedido');
        expect(modal.style.display).toBe('flex');

        const inputAocs = document.querySelector('#aocs-contrato-55');
        inputAocs.value = 'AOCS-TESTE-01';

        mockFetch.mockImplementation(async (url, options) => {
            const method = options ? options.method : 'GET';
            if (url === '/api/aocs' && method === 'POST') {
                return { ok: true, json: async () => ({ id: 999, numero: 'AOCS-TESTE-01' }) };
            }
            if (url.includes('/api/pedidos') && method === 'POST') {
                return { ok: true, json: async () => ({ id: 888, status: 'sucesso' }) };
            }
            return { ok: true, json: async () => ({ itens: itensMock, total_paginas: 1, pagina_atual: 1 }) };
        });

        document.getElementById('btn-enviar-pedido').click();

        await waitFor(() => {
            if (window.location.href !== '/pedidos') throw new Error('Ainda não redirecionou...');
        });
        expect(window.location.href).toBe('/pedidos');
    });

    test('Busca: Enter no input dispara fetch com termo', async () => {
        const input = document.getElementById('campo-busca');
        input.value = 'cimento';
        input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter' }));

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('busca=cimento'));
        });
    });

    test('Carrinho: Limpar (Cancelar e Confirmar)', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input');
        input.value = '1,00';
        input.dispatchEvent(new Event('change'));
        
        const btnLimpar = document.getElementById('btn-limpar-carrinho');
        
        const mockConfirm = jest.fn();
        
        window.confirm = mockConfirm;
        global.confirm = mockConfirm;

        mockConfirm.mockReturnValueOnce(false).mockReturnValueOnce(true);

        btnLimpar.click();
        
        expect(mockConfirm).toHaveBeenCalledTimes(1);
        expect(input.value).toBe('1,00'); 

        btnLimpar.click();
        
        await waitFor(() => {
            expect(input.value).toBe(''); 
            const total = document.getElementById('carrinho-total');
            expect(total.textContent).toContain('0,00');
        });
    });

    test('Ordenação: Clique no cabeçalho altera parâmetros', async () => {
        const thDescricao = document.querySelector('th[data-sort="descricao"]');
        thDescricao.click(); 
        await waitFor(() => expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('order=desc')));

        thDescricao.click(); 
        await waitFor(() => expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('order=asc')));
    });

    test('Paginação: Clique na página carrega novos itens', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ({ itens: itensMock, total_paginas: 2, pagina_atual: 1 })
        });

        if(document.querySelector('#campo-busca')) {
             document.getElementById('campo-busca').dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter' }));
        }

        let linkPag2;
        await waitFor(() => {
            linkPag2 = document.querySelector('.page-link[data-page="2"]');
            expect(linkPag2).toBeTruthy();
        });
        
        linkPag2.click();

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('page=2'));
        });
    });

    test('Modal UI: Fechar via botões e overlay', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input');
        input.value = '1,00';
        input.dispatchEvent(new Event('change'));
        document.getElementById('btn-finalizar-pedido').click();

        const modal = document.getElementById('modal-finalizar-pedido');
        expect(modal.style.display).toBe('flex');

        document.getElementById('btn-fechar-modal').click();
        expect(modal.style.display).toBe('none');

        document.getElementById('btn-finalizar-pedido').click();
        document.getElementById('btn-cancelar-modal').click();
        expect(modal.style.display).toBe('none');

        document.getElementById('btn-finalizar-pedido').click();
        modal.click();
        expect(modal.style.display).toBe('none');
    });

    test('Finalizar: Erro de Validação (AOCS Vazio)', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input');
        input.value = '1,00';
        input.dispatchEvent(new Event('change'));
        document.getElementById('btn-finalizar-pedido').click();

        const inputAocs = document.querySelector('.aocs-input');
        inputAocs.value = ''; 

        document.getElementById('btn-enviar-pedido').click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toMatch(/Por favor, preencha|Preencha o número/);
        });
    });

    test('Finalizar: Erro de API ao Enviar', async () => {
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input');
        input.value = '1,00';
        input.dispatchEvent(new Event('change'));
        document.getElementById('btn-finalizar-pedido').click();
        document.querySelector('.aocs-input').value = 'AOCS-ERRO';

        mockFetch.mockImplementation(async (url, opts) => {
            if (url === '/api/aocs' && opts.method === 'POST') {
                return { 
                    ok: false, status: 500,
                    json: async () => ({ erro: 'Erro Interno no Banco' })
                };
            }
            return { ok: true, json: async () => ({ itens: itensMock }) };
        });

        document.getElementById('btn-enviar-pedido').click();

        await waitFor(() => {
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Erro ao enviar pedido');
            expect(notif.textContent).toContain('Erro Interno no Banco');
        });
    });
});