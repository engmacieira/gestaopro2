/**
 * @jest-environment jsdom
 */

// ==========================================================================
// 1. CONFIGURAÇÃO E UTILS
// ==========================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Função auxiliar para esperar elementos aparecerem na tela (assincronismo)
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

// HTML Simulado (Representa a estrutura da sua página real)
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
            
            <input id="aocs-unidade" value="Unidade Teste">
            <input id="aocs-justificativa" value="Justificativa Teste">
            <input id="aocs-orcamento" value="Verba X">
            <input id="aocs-local-entrega" value="Local Y">
            <input id="aocs-responsavel" value="Fulano">

            <button type="button" id="btn-cancelar-modal">Cancelar</button>
            <button type="button" id="btn-enviar-pedido">Confirmar e Enviar</button>
        </form>
        <button id="btn-fechar-modal">X</button>
    </div>
`;

describe('Testes Frontend - Novo Pedido', () => {
    
    // DADOS MOCKADOS: O Segredo está aqui.
    // id_contrato deve existir e bater com o esperado no JS.
    const itensMock = [
        {
            id: 101,
            numero_item: 1,
            descricao: { descricao: "Cimento CP-II" },
            numero_contrato: "123/2024",
            id_contrato: 55, // <--- ATENÇÃO: snake_case, igual ao Python
            saldo: 100.00,
            valor_unitario: 50.00
        },
        {
            id: 102,
            numero_item: 2,
            descricao: { descricao: "Areia Lavada" },
            numero_contrato: "124/2024",
            id_contrato: 56, // <--- ATENÇÃO: snake_case
            saldo: 50.00,
            valor_unitario: 100.00
        }
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = DOM_HTML;
        sessionStorage.clear();

        // Mock para propriedade innerText (compatibilidade JSDOM)
        Object.defineProperty(HTMLElement.prototype, 'innerText', {
            get() { return this.textContent; },
            set(value) { this.textContent = value; },
            configurable: true
        });

        // Variáveis Globais necessárias
        window.idCategoriaGlobal = 1; 
        window.redirectUrlPedidosGlobal = '/pedidos';
        
        // Mocks de Window
        window.confirm = jest.fn(() => true);
        window.alert = jest.fn();
        delete window.location;
        window.location = { href: '' };

        // Configuração Inicial do Fetch (Padrão: Retornar itens para a tabela)
        mockFetch.mockImplementation(async (url) => {
            // Se for chamada de itens (GET)
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
            return { ok: false }; // Default error
        });

        // Recarrega o script JS fresco para cada teste
        jest.resetModules();
        require('../../app/static/js/novo_pedido');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    // ==========================================================================
    // TESTES
    // ==========================================================================

    test('Inicialização: Deve buscar e renderizar itens na tabela', async () => {
        console.log('TESTE: Inicialização');
        await waitFor(() => {
            const linhas = document.querySelectorAll('#corpo-tabela-itens tr');
            // Se falhar aqui, o fetch inicial não funcionou
            expect(linhas.length).toBe(2);
            expect(document.body.textContent).toContain('Cimento CP-II');
        });
    });

    test('Carrinho: Adicionar item deve atualizar UI e Variável Global', async () => {
        console.log('TESTE: Carrinho Adicionar');
        await waitFor(() => document.querySelector('.small-input'));

        const input = document.querySelector('.small-input'); // Item 101
        
        // Simula usuário digitando "2"
        input.value = '2,00';
        input.dispatchEvent(new Event('change'));

        await waitFor(() => {
            const carrinhoTotal = document.getElementById('carrinho-total');
            // 2 * 50.00 = 100.00
            expect(carrinhoTotal.textContent).toContain('R$ 100,00'); // Espaço non-breaking
            
            const btnFinalizar = document.getElementById('btn-finalizar-pedido');
            expect(btnFinalizar.disabled).toBe(false);
        });
    });

    test('Validação: Quantidade > Saldo deve ser corrigida', async () => {
        console.log('TESTE: Validação Saldo');
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input'); // Saldo é 100
        
        // Tenta burlar com 200
        input.value = '200,00';
        input.dispatchEvent(new Event('change'));

        await waitFor(() => {
            // JavaScript deve corrigir para 100
            expect(input.value).toBe('100,00');
            const notif = document.getElementById('notification-area');
            expect(notif.textContent).toContain('Saldo insuficiente');
        });
    });

    test('Fluxo Completo: Finalizar pedido com sucesso (AOCS + Pedidos)', async () => {
        console.log('TESTE: Fluxo Completo - Inicio');
        
        // 1. Adicionar item ao carrinho
        await waitFor(() => document.querySelector('.small-input'));
        const input = document.querySelector('.small-input');
        input.value = '1,00';
        input.dispatchEvent(new Event('change'));

        // 2. Clicar em Finalizar (Abre Modal)
        const btnFinalizar = document.getElementById('btn-finalizar-pedido');
        btnFinalizar.click();
        
        const modal = document.getElementById('modal-finalizar-pedido');
        expect(modal.style.display).toBe('flex');

        // 3. Verificar se o input da AOCS foi gerado (depende do id_contrato estar certo)
        // O ID do contrato é 55 (conforme itensMock)
        const inputAocs = document.querySelector('#aocs-contrato-55');
        
        if (!inputAocs) {
            console.error('FALHA TESTE: Input de AOCS não encontrado! O agrupamento falhou.');
            // Isso força a falha do teste com mensagem clara
            expect(inputAocs).toBeTruthy(); 
        }
        
        inputAocs.value = 'AOCS-TESTE-01';

        // 4. Preparar Mock para o Envio (Roteamento de URLs)
        mockFetch.mockImplementation(async (url, options) => {
            const method = options ? options.method : 'GET';

            // Rota 1: Criar AOCS
            if (url === '/api/aocs' && method === 'POST') {
                console.log('MOCK FETCH: Criando AOCS...');
                return {
                    ok: true,
                    json: async () => ({ id: 999, numero: 'AOCS-TESTE-01' })
                };
            }
            
            // Rota 2: Criar Itens do Pedido (vinculados à AOCS 999)
            if (url.includes('/api/pedidos') && method === 'POST') {
                console.log('MOCK FETCH: Criando Item de Pedido...');
                return {
                    ok: true,
                    json: async () => ({ id: 888, status: 'sucesso' })
                };
            }

            // Default: Retorna lista de itens (para background fetchs)
            return {
                ok: true,
                json: async () => ({ 
                    itens: itensMock, 
                    total_paginas: 1, 
                    pagina_atual: 1 
                })
            };
        });

        // 5. Enviar
        const btnEnviar = document.getElementById('btn-enviar-pedido');
        btnEnviar.click();

        // 6. Aguardar redirecionamento
        await waitFor(() => {
            // Verifica se o redirecionamento ocorreu
            if (window.location.href !== '/pedidos') {
                // Se não redirecionou, o waitFor vai dar timeout, mas o console vai mostrar os logs do JS
                throw new Error('Ainda não redirecionou...');
            }
        });

        expect(window.location.href).toBe('/pedidos');
        console.log('TESTE: Fluxo Completo - Sucesso');
    });
});