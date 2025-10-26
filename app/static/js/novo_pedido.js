document.addEventListener('DOMContentLoaded', function() {

    let carrinho = [];
    // idCategoriaGlobal e redirectUrlPedidosGlobal são definidos no HTML
    let sortColumn = 'descricao';
    let sortDirection = 'asc';

    // Referências a elementos DOM
    const corpoTabelaItens = document.getElementById('corpo-tabela-itens');
    const divItensCarrinho = document.getElementById('carrinho-itens');
    const divTotalCarrinho = document.getElementById('carrinho-total');
    const campoBusca = document.getElementById('campo-busca');
    const btnLimparCarrinho = document.getElementById('btn-limpar-carrinho');
    const btnFinalizarPedido = document.getElementById('btn-finalizar-pedido');
    const modal = document.getElementById('modal-finalizar-pedido');
    const formFinalizar = document.getElementById('form-finalizar-pedido');
    const btnFecharModal = document.getElementById('btn-fechar-modal');
    const btnCancelarModal = document.getElementById('btn-cancelar-modal');
    const btnEnviarPedido = document.getElementById('btn-enviar-pedido');
    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');
    const paginationContainer = document.getElementById('pagination-container');
    const containerAOCSInputs = document.getElementById('aocs-por-contrato-container'); // Container para inputs de AOCS no modal

    // --- FUNÇÕES ---

    function showNotification(message, type = 'error') {
        if (!notificationArea) return;
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();
        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if(existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationArea.prepend(notification); // Usa prepend
        setTimeout(() => {
            if(notification) {
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    // Função ajustada para usar o endpoint da API refatorada
    async function fetchItens(page = 1, busca = '') {
        if (!corpoTabelaItens) return; // Segurança
        corpoTabelaItens.innerHTML = '<tr><td colspan="5">Carregando itens...</td></tr>';
        try {
            // Chamada ao Router/Controller de Categoria/Itens
            // Endpoint API: /api/categorias/{id_categoria}/itens
            const url = `/api/categorias/${idCategoriaGlobal}/itens?page=${page}&busca=${encodeURIComponent(busca)}&sort_by=${sortColumn}&order=${sortDirection}`;
            const response = await fetch(url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || data.erro || 'Falha ao carregar dados.');

            renderizarTabelaItens(data.itens);
            renderizarPaginacao(data.total_paginas, data.pagina_atual);
            updateSortIcons();

        } catch (error) {
            console.error('Erro ao buscar itens:', error);
            corpoTabelaItens.innerHTML = `<tr><td colspan="5"><div class="notification error mini">Erro: ${error.message}</div></td></tr>`;
            showNotification(error.message);
        }
    }

    function updateSortIcons() {
        document.querySelectorAll('th.sortable i').forEach(icon => icon.className = 'fa-solid fa-sort');
        const activeTh = document.querySelector(`th[data-sort="${sortColumn}"]`);
        if (activeTh) {
            const activeIcon = activeTh.querySelector('i');
            if (activeIcon) {
                activeIcon.className = sortDirection === 'asc' ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down';
            }
        }
    }

    function handleSort(coluna) {
        if (sortColumn === coluna) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortColumn = coluna;
            sortDirection = 'asc'; // Padrão é asc ao mudar coluna
        }
        fetchItens(1, campoBusca.value); // Volta para página 1 ao reordenar
    }

    function renderizarTabelaItens(itens) {
        if (!corpoTabelaItens) return;
        corpoTabelaItens.innerHTML = '';
        if (!itens || itens.length === 0) {
            corpoTabelaItens.innerHTML = '<tr><td colspan="5"><div class="empty-state mini"><p>Nenhum item encontrado.</p></div></td></tr>';
            return;
        }
        itens.forEach(item => {
            const itemNoCarrinho = carrinho.find(c => c.id === item.id);
            const quantidadeNoCarrinho = itemNoCarrinho ? itemNoCarrinho.quantidade : '';
            const linha = document.createElement('tr');
            linha.className = itemNoCarrinho ? 'item-in-cart' : '';

            // Formata valores numéricos para exibição
            const saldoFormatado = item.saldo.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const valorUnitFormatado = parseFloat(item.valor_unitario).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

            linha.innerHTML = `
                <td>${item.numero_item}</td>
                <td><strong>${item.descricao.descricao}</strong><br><small>Contrato: ${item.numero_contrato}</small></td>
                <td class="text-center" style="font-weight: 600;">${saldoFormatado}</td>
                <td class="text-center">${valorUnitFormatado}</td>
                <td class="text-center">
                    <input type="number" class="form-control small-input" min="0" max="${item.saldo}" step="0.01"  {# step para decimais #}
                           data-item-id="${item.id}" data-item-full='${JSON.stringify(item)}'
                           value="${quantidadeNoCarrinho}" placeholder="0,00"
                           style="width: 100px; min-width: 80px;">
                </td>
            `;
            const inputQtd = linha.querySelector('input[type="number"]');
            inputQtd.addEventListener('change', (e) => handleQuantidadeChange(e.target));
            corpoTabelaItens.appendChild(linha);
        });
    }

    function renderizarPaginacao(total_paginas, pagina_atual) {
        if (!paginationContainer) return;
        paginationContainer.innerHTML = ''; // Limpa antes de renderizar
        if (total_paginas <= 1) return;

        let paginationHtml = '<nav class="pagination-nav"><ul class="pagination">';
        const maxPagesToShow = 5;
        let startPage = Math.max(1, pagina_atual - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(total_paginas, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        // Botão Primeira e Anterior
        if (pagina_atual > 1) {
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="1" aria-label="Primeira"><i class="fa-solid fa-backward-fast"></i></a></li>`;
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagina_atual - 1}" aria-label="Anterior"><i class="fa-solid fa-backward-step"></i></a></li>`;
        } else {
             paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Primeira"><i class="fa-solid fa-backward-fast"></i></span></li>`;
             paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Anterior"><i class="fa-solid fa-backward-step"></i></span></li>`;
        }


        // Números das Páginas
        for (let i = startPage; i <= endPage; i++) {
             paginationHtml += `<li class="page-item ${i === pagina_atual ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }

        // Botão Próxima e Última
        if (pagina_atual < total_paginas) {
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagina_atual + 1}" aria-label="Próxima"><i class="fa-solid fa-forward-step"></i></a></li>`;
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${total_paginas}" aria-label="Última"><i class="fa-solid fa-forward-fast"></i></a></li>`;
        } else {
              paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Próxima"><i class="fa-solid fa-forward-step"></i></span></li>`;
              paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Última"><i class="fa-solid fa-forward-fast"></i></span></li>`;
        }


        paginationHtml += '</ul></nav>';
        paginationContainer.innerHTML = paginationHtml;

        // Adiciona listeners aos links criados
        paginationContainer.querySelectorAll('.page-link').forEach(link => {
            if (link.closest('.page-item.disabled')) return; // Não adiciona listener a links desabilitados
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.closest('a').dataset.page);
                fetchItens(page, campoBusca.value);
            });
        });
    }

    function renderizarCarrinho() {
        if (!divItensCarrinho || !divTotalCarrinho || !btnFinalizarPedido) return;

        let totalGeral = carrinho.reduce((acc, item) => acc + item.subtotal, 0);

        if (carrinho.length === 0) {
            divItensCarrinho.innerHTML = '<div class="empty-state mini"><i class="fa-solid fa-dolly"></i><p>Seu carrinho está vazio.</p></div>';
            btnFinalizarPedido.disabled = true;
            divTotalCarrinho.querySelector('strong').innerText = `R$ 0,00`;
            return;
        }

        divItensCarrinho.innerHTML = ''; // Limpa carrinho
        carrinho.forEach(item => {
            const precoFormatado = item.preco.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            const subtotalFormatado = item.subtotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            divItensCarrinho.innerHTML += `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <span class="cart-item-name">${item.nome}</span>
                        <span class="cart-item-price">${item.quantidade.toLocaleString('pt-BR')} x ${precoFormatado}</span>
                    </div>
                    <strong class="cart-item-subtotal">${subtotalFormatado}</strong>
                </div>`;
        });

        btnFinalizarPedido.disabled = false;
        divTotalCarrinho.querySelector('strong').innerText = totalGeral.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function handleQuantidadeChange(input) {
        const itemId = parseInt(input.dataset.itemId);
        let quantidadeStr = input.value.replace('.', '').replace(',', '.'); // Normaliza para ponto decimal
        let quantidade = parseFloat(quantidadeStr);
        const itemDoCatalogo = JSON.parse(input.dataset.itemFull);

        // Remove do carrinho se quantidade for inválida ou zero
        if (isNaN(quantidade) || quantidade <= 0) {
            carrinho = carrinho.filter(item => item.id !== itemId);
            input.value = ''; // Limpa o input
            quantidade = 0; // Para lógica de classe CSS
        } else {
            const saldoDisponivel = parseFloat(itemDoCatalogo.saldo);
            if (quantidade > saldoDisponivel) {
                showNotification(`Saldo insuficiente! O máximo para "${itemDoCatalogo.descricao.descricao}" é ${saldoDisponivel.toLocaleString('pt-BR')}.`, 'warning');
                quantidade = saldoDisponivel;
                input.value = quantidade.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); // Formata de volta para vírgula
            }

            const valorUnitarioNumerico = parseFloat(itemDoCatalogo.valor_unitario);
            const itemExistente = carrinho.find(item => item.id === itemId);

            if (itemExistente) {
                itemExistente.quantidade = quantidade;
                itemExistente.subtotal = quantidade * itemExistente.preco;
            } else {
                carrinho.push({
                    id: itemId,
                    nome: itemDoCatalogo.descricao.descricao, // Acessa a descrição aninhada
                    quantidade: quantidade,
                    preco: valorUnitarioNumerico,
                    subtotal: quantidade * valorUnitarioNumerico,
                    idContrato: itemDoCatalogo.id_contrato, // Vem da API /categorias/{id}/itens
                    numeroContrato: itemDoCatalogo.numero_contrato // Vem da API
                });
            }
             // Formata o valor no input com vírgula após a validação
             input.value = quantidade.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        renderizarCarrinho();
        // Adiciona/remove classe CSS na linha da tabela
        input.closest('tr')?.classList.toggle('item-in-cart', quantidade > 0);
    }

    function abrirModalFinalizar() {
        if (!modal || !containerAOCSInputs || carrinho.length === 0) return;
        containerAOCSInputs.innerHTML = ''; // Limpa inputs anteriores

        // Agrupa contratos únicos no carrinho
        const contratosNoCarrinho = [...new Map(carrinho.map(item =>
            [item.idContrato, { numeroContrato: item.numeroContrato, idContrato: item.idContrato }]
        )).values()];

        // Gera um input para o número da AOCS para cada contrato
        contratosNoCarrinho.forEach(itemContrato => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';
            // Usa template literals para facilitar a leitura do HTML
            formGroup.innerHTML = `
                <label for="aocs-contrato-${itemContrato.idContrato}">
                    Nº AOCS para Contrato: <strong>${itemContrato.numeroContrato}</strong>
                </label>
                <input type="text" id="aocs-contrato-${itemContrato.idContrato}"
                       data-id-contrato="${itemContrato.idContrato}"
                       class="form-control aocs-input"
                       placeholder="Ex: 123/2025"
                       required>
            `;
            containerAOCSInputs.appendChild(formGroup);
        });

        modal.style.display = 'flex';
    }

    const fecharModal = () => { if (modal) modal.style.display = 'none'; };

    // Função de envio REESCRITA para o fluxo modular do FastAPI:
    async function enviarPedido() {
        if (!formFinalizar.checkValidity()) {
             showNotification('Por favor, preencha todos os campos obrigatórios do formulário AOCS.', 'warning');
             formFinalizar.reportValidity(); // Mostra validação HTML5 nativa
             return;
        }

        const submitButton = btnEnviarPedido;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...';

        const aocsDadosMestre = {
            unidade_requisitante_nome: document.getElementById('aocs-unidade').value,
            justificativa: document.getElementById('aocs-justificativa').value,
            dotacao_info_orcamentaria: document.getElementById('aocs-orcamento').value,
            local_entrega_descricao: document.getElementById('aocs-local-entrega').value,
            agente_responsavel_nome: document.getElementById('aocs-responsavel').value,
            // numero_pedido e empenho são opcionais e não estão no modal inicial
        };

        // Agrupamento de itens por Contrato, formatado para o PedidoCreateRequest
        const contratosAgrupados = {};
        carrinho.forEach(item => {
            if (!contratosAgrupados[item.idContrato]) { contratosAgrupados[item.idContrato] = []; }
            contratosAgrupados[item.idContrato].push({
                item_contrato_id: item.id,
                quantidade_pedida: item.quantidade.toFixed(2) // Envia como string formatada
            });
        });

        const promessasDeFetch = [];
        const inputsAOCS = document.querySelectorAll('.aocs-input');
        let erroValidacaoInput = false;

        for (const input of inputsAOCS) {
            const idContrato = parseInt(input.dataset.idContrato);
            const numeroAOCS = input.value.trim();

            // Validação de formulário (número AOCS preenchido)
            if (!numeroAOCS) {
                input.style.borderColor = 'red'; // Destaca input vazio
                erroValidacaoInput = true;
                continue; // Pula para o próximo input
            } else {
                 input.style.borderColor = ''; // Limpa destaque se preenchido
            }

            // 1. Cria a AOCS (POST /api/aocs)
            // Payload esperado por AocsCreateRequest
            const aocsPayload = { ...aocsDadosMestre, numero_aocs: numeroAOCS };

            const promiseChain = fetch('/api/aocs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(aocsPayload)
            })
            .then(async response => { // Usa async para poder usar await response.json() no erro
                if (!response.ok) {
                    const errorDetail = await response.json().catch(() => ({ detail: `Erro ${response.status}` }));
                    // Rejeita a promessa com uma mensagem mais detalhada
                    return Promise.reject({ message: `Falha ao criar AOCS ${numeroAOCS}.`, error: errorDetail.detail });
                }
                return response.json(); // Retorna os dados da AOCS criada (inclui ID)
            })
            .then(aocsResult => {
                const id_aocs_criada = aocsResult.id;
                // 2. Cria os Pedidos (POST /api/pedidos?id_aocs={id_aocs_criada})
                // Mapeia cada item do grupo para uma chamada fetch
                const pedidoPromises = contratosAgrupados[idContrato].map(item =>
                    fetch(`/api/pedidos?id_aocs=${id_aocs_criada}`, { // Passa id_aocs como query param
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(item) // Body = {item_contrato_id: X, quantidade_pedida: Y}
                    })
                    .then(async response => { // Usa async para erro
                        if (!response.ok) {
                            const errorDetail = await response.json().catch(() => ({ detail: `Erro ${response.status}` }));
                            // Rejeita com mensagem detalhada, incluindo o item
                            return Promise.reject({
                                message: `Falha ao adicionar Item ID ${item.item_contrato_id} à AOCS ${numeroAOCS}.`,
                                error: errorDetail.detail
                            });
                        }
                        return response.json(); // Retorna dados do pedido criado
                    })
                );
                // Retorna uma promessa que resolve quando todos os itens forem adicionados
                return Promise.all(pedidoPromises);
            });

            promessasDeFetch.push(promiseChain);
        }

        // Verifica se houve erro de validação nos inputs antes de prosseguir
        if (erroValidacaoInput) {
            showNotification('Preencha o número da AOCS para todos os contratos listados.', 'warning');
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Confirmar e Enviar';
            return;
        }

        try {
            // Espera todas as cadeias de promessas (criar AOCS -> criar Pedidos) completarem
            const resultados = await Promise.all(promessasDeFetch);
            // Se chegou aqui, todas as AOCS e seus itens foram criados
            showNotification(`${resultados.length} AOCS(s) criada(s) com sucesso! Redirecionando...`, 'success');
            // Redireciona para o histórico usando a URL global
            setTimeout(() => { window.location.href = redirectUrlPedidosGlobal; }, 2000);
        } catch (error) {
            console.error("Erro ao enviar pedido:", error);
            // Exibe a mensagem de erro específica que foi rejeitada na cadeia de promessas
            showNotification(`Erro ao enviar pedido. Detalhe: ${error.message} (${error.error || 'Erro desconhecido'})`, 'error');
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Confirmar e Enviar';
        }
    }


    // --- EVENT LISTENERS ---

    // Busca ao pressionar Enter no campo de busca
    if (campoBusca) {
        campoBusca.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                fetchItens(1, campoBusca.value); // Sempre busca da página 1
            }
        });
    }

    // Limpar carrinho
    if (btnLimparCarrinho) {
        btnLimparCarrinho.addEventListener('click', () => {
            if (confirm('Tem certeza que deseja limpar todos os itens do pedido?')) {
                carrinho = [];
                renderizarCarrinho();
                // Limpa visualmente os inputs na tabela e remove a classe 'item-in-cart'
                document.querySelectorAll('#corpo-tabela-itens input[type="number"]').forEach(input => {
                    input.value = '';
                    input.closest('tr')?.classList.remove('item-in-cart');
                });
                // Poderia recarregar os itens com fetchItens(), mas limpar os inputs é mais direto
            }
        });
    }

    // Abrir/Fechar Modal de Finalização
    if (btnFinalizarPedido) btnFinalizarPedido.addEventListener('click', abrirModalFinalizar);
    if (btnFecharModal) btnFecharModal.addEventListener('click', fecharModal);
    if (btnCancelarModal) btnCancelarModal.addEventListener('click', fecharModal);
    window.addEventListener('click', (event) => { if (modal && event.target == modal) fecharModal(); });

    // Enviar Pedido (Botão dentro do Modal)
    if (btnEnviarPedido) btnEnviarPedido.addEventListener('click', enviarPedido);

    // Adiciona listeners para ordenação nas colunas da tabela
    document.querySelectorAll('th.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const coluna = header.dataset.sort;
            if (coluna) { // Verifica se data-sort está definido
                handleSort(coluna);
            }
        });
    });

    // --- INICIALIZAÇÃO ---
    fetchItens(); // Carrega os itens iniciais ao carregar a página
});