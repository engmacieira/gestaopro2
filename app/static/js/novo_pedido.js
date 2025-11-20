document.addEventListener('DOMContentLoaded', function() {

    let carrinho = [];
    let sortColumn = 'descricao';
    let sortDirection = 'asc';

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
    const notificationArea = document.querySelector('.main-content #notification-area');
    const paginationContainer = document.getElementById('pagination-container');
    const containerAOCSInputs = document.getElementById('aocs-por-contrato-container'); 

    function formatBrazilianNumber(value) {
        if (value === null || value === undefined) return 'N/D';
        if (typeof value !== 'number') value = parseFloat(value);
        if (isNaN(value)) return 'N/D';
        return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function parseBrazilianFloat(str) {
        if (!str) return 0;
        const cleanedStr = String(str).replace(/\./g, '').replace(',', '.'); 
        const num = parseFloat(cleanedStr);
        return isNaN(num) ? 0 : num;
    }

    function showNotification(message, type = 'error') {
        if (!notificationArea) return;
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();
        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if(existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationArea.prepend(notification); 
        setTimeout(() => {
            if(notification) {
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    function navigateWithMessage(url, message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        window.location.href = url;
    }

    async function fetchItens(page = 1, busca = '') {
        if (!corpoTabelaItens) return; 
        corpoTabelaItens.innerHTML = '<tr><td colspan="5">Carregando itens...</td></tr>';
        try {
            const url = `/api/categorias/${idCategoriaGlobal}/itens?page=${page}&busca=${encodeURIComponent(busca)}&sort_by=${sortColumn}&order=${sortDirection}`;
            const response = await fetch(url);
            const data = await response.json().catch(() => ({})); 
            
            if (!response.ok) {
                const errorDetail = data.detail || data.erro || `Erro ${response.status} ao carregar itens.`;
                throw new Error(errorDetail);
            }

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
            sortDirection = 'asc'; 
        }
        fetchItens(1, campoBusca.value); 
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
            const quantidadeNoCarrinho = itemNoCarrinho ? formatBrazilianNumber(itemNoCarrinho.quantidade) : ''; 
            const linha = document.createElement('tr');
            linha.className = itemNoCarrinho ? 'item-in-cart' : '';

            const saldoFormatado = formatBrazilianNumber(item.saldo); 
            const valorUnitFormatado = parseFloat(item.valor_unitario).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

            linha.innerHTML = `
                <td>${item.numero_item}</td>
                <td><strong>${item.descricao.descricao}</strong><br><small>Contrato: ${item.numero_contrato}</small></td>
                <td class="text-center" style="font-weight: 600;">${saldoFormatado}</td>
                <td class="text-center">${valorUnitFormatado}</td>
                <td class="text-center">
                    <input type="text" inputmode="decimal" class="form-control small-input" max="${item.saldo}"
                           data-item-id="${item.id}" data-item-full='${JSON.stringify(item)}'
                           value="${quantidadeNoCarrinho}" placeholder="0,00"
                           style="width: 100px; min-width: 80px;">
                </td>
            `;
            const inputQtd = linha.querySelector('.small-input');
            inputQtd.addEventListener('change', (e) => handleQuantidadeChange(e.target));
            corpoTabelaItens.appendChild(linha);
        });
    }
    
    function renderizarPaginacao(total_paginas, pagina_atual) {
        if (!paginationContainer) return;
        paginationContainer.innerHTML = ''; 
        if (total_paginas <= 1) return;

        let paginationHtml = '<nav class="pagination-nav"><ul class="pagination">';
        const maxPagesToShow = 5;
        let startPage = Math.max(1, pagina_atual - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(total_paginas, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        if (pagina_atual > 1) {
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="1" aria-label="Primeira"><i class="fa-solid fa-backward-fast"></i></a></li>`;
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagina_atual - 1}" aria-label="Anterior"><i class="fa-solid fa-backward-step"></i></a></li>`;
        } else {
             paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Primeira"><i class="fa-solid fa-backward-fast"></i></span></li>`;
             paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Anterior"><i class="fa-solid fa-backward-step"></i></span></li>`;
        }

        for (let i = startPage; i <= endPage; i++) {
             paginationHtml += `<li class="page-item ${i === pagina_atual ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }

        if (pagina_atual < total_paginas) {
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagina_atual + 1}" aria-label="Próxima"><i class="fa-solid fa-forward-step"></i></a></li>`;
             paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${total_paginas}" aria-label="Última"><i class="fa-solid fa-forward-fast"></i></a></li>`;
        } else {
              paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Próxima"><i class="fa-solid fa-forward-step"></i></span></li>`;
              paginationHtml += `<li class="page-item disabled"><span class="page-link" aria-label="Última"><i class="fa-solid fa-forward-fast"></i></span></li>`;
        }

        paginationHtml += '</ul></nav>';
        paginationContainer.innerHTML = paginationHtml;

        paginationContainer.querySelectorAll('.page-link').forEach(link => {
            if (link.closest('.page-item.disabled')) return; 
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

        divItensCarrinho.innerHTML = ''; 
        carrinho.forEach(item => {
            const precoFormatado = item.preco.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            const subtotalFormatado = item.subtotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            const quantidadeFormatada = formatBrazilianNumber(item.quantidade);
            
            divItensCarrinho.innerHTML += `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <span class="cart-item-name">${item.nome}</span>
                        <span class="cart-item-price">${quantidadeFormatada} x ${precoFormatado}</span>
                    </div>
                    <strong class="cart-item-subtotal">${subtotalFormatado}</strong>
                </div>`;
        });

        btnFinalizarPedido.disabled = false;
        divTotalCarrinho.querySelector('strong').innerText = totalGeral.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function handleQuantidadeChange(input) {
        const itemId = parseInt(input.dataset.itemId);
        let quantidade = parseBrazilianFloat(input.value); 
        const itemDoCatalogo = JSON.parse(input.dataset.itemFull);
        const saldoDisponivel = parseFloat(itemDoCatalogo.saldo);

        if (quantidade <= 0) {
            carrinho = carrinho.filter(item => item.id !== itemId);
            input.value = ''; 
            quantidade = 0; 
        } else {
            if (quantidade > saldoDisponivel) {
                showNotification(`Saldo insuficiente! O máximo para "${itemDoCatalogo.descricao.descricao}" é ${formatBrazilianNumber(saldoDisponivel)}.`, 'warning');
                quantidade = saldoDisponivel;
            }

            const valorUnitarioNumerico = parseFloat(itemDoCatalogo.valor_unitario);
            const itemExistente = carrinho.find(item => item.id === itemId);

            if (itemExistente) {
                itemExistente.quantidade = quantidade;
                itemExistente.subtotal = quantidade * itemExistente.preco;
            } else {
                carrinho.push({
                    id: itemId,
                    nome: itemDoCatalogo.descricao.descricao, 
                    quantidade: quantidade,
                    preco: valorUnitarioNumerico,
                    subtotal: quantidade * valorUnitarioNumerico,
                    idContrato: itemDoCatalogo.id_contrato, 
                    numeroContrato: itemDoCatalogo.numero_contrato 
                });
            }
             input.value = formatBrazilianNumber(quantidade); 
        }

        renderizarCarrinho();
        input.closest('tr')?.classList.toggle('item-in-cart', quantidade > 0);
    }

    function abrirModalFinalizar() {
        if (!modal || !containerAOCSInputs || carrinho.length === 0) return;
        containerAOCSInputs.innerHTML = ''; 

        const contratosNoCarrinho = [...new Map(carrinho.map(item =>
            [item.idContrato, { numeroContrato: item.numeroContrato, idContrato: item.idContrato }]
        )).values()];

        contratosNoCarrinho.forEach(itemContrato => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';
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

    async function enviarPedido() {
        if (!formFinalizar.checkValidity()) {
             showNotification('Por favor, preencha todos os campos obrigatórios do formulário AOCS.', 'warning');
             formFinalizar.reportValidity(); 
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
        };

        const contratosAgrupados = {};
        carrinho.forEach(item => {
            if (!contratosAgrupados[item.idContrato]) { contratosAgrupados[item.idContrato] = []; }
            contratosAgrupados[item.idContrato].push({
                item_contrato_id: item.id,
                quantidade_pedida: item.quantidade.toFixed(2) 
            });
        });

        const promessasDeFetch = [];
        const inputsAOCS = document.querySelectorAll('.aocs-input');
        let erroValidacaoInput = false;

        for (const input of inputsAOCS) {
            const idContrato = parseInt(input.dataset.idContrato);
            const numeroAOCS = input.value.trim();

            // --- BLINDAGEM: Verifica se o contrato existe no agrupamento ---
            const itensDoContrato = contratosAgrupados[idContrato];
            if (!itensDoContrato) {
                // Log de erro silencioso para o dev, sem travar o loop
                console.error(`Erro de Consistência: Contrato ID ${idContrato} sem itens no carrinho.`);
                continue; 
            }
            // ---------------------------------------------------------------

            if (!numeroAOCS) {
                input.style.borderColor = 'red'; 
                erroValidacaoInput = true;
                continue; 
            } else {
                 input.style.borderColor = ''; 
            }

            const aocsPayload = { ...aocsDadosMestre, numero_aocs: numeroAOCS };

            const promiseChain = fetch('/api/aocs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(aocsPayload)
            })
            .then(async response => { 
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    const errorDetail = data.detail || data.erro || `Erro ${response.status} na criação da AOCS.`;
                    return Promise.reject({ message: `Falha ao criar AOCS ${numeroAOCS}.`, error: errorDetail });
                }
                return data; 
            })
            .then(aocsResult => {
                const id_aocs_criada = aocsResult.id;
                
                const pedidoPromises = itensDoContrato.map(item =>
                    fetch(`/api/pedidos?id_aocs=${id_aocs_criada}`, { 
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(item) 
                    })
                    .then(async response => { 
                        const data = await response.json().catch(() => ({}));
                        if (!response.ok) {
                            const errorDetail = data.detail || data.erro || `Erro ${response.status} ao adicionar item.`;
                            return Promise.reject({
                                message: `Falha ao adicionar Item ID ${item.item_contrato_id} à AOCS ${numeroAOCS}.`,
                                error: errorDetail
                            });
                        }
                        return data; 
                    })
                );
                return Promise.all(pedidoPromises);
            });

            promessasDeFetch.push(promiseChain);
        }

        if (erroValidacaoInput) {
            showNotification('Preencha o número da AOCS para todos os contratos listados.', 'warning');
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Confirmar e Enviar';
            return;
        }

        try {
            const resultados = await Promise.all(promessasDeFetch);
            
            const aocsCriadas = resultados.length; 
            
            showNotification(`${aocsCriadas} AOCS(s) criada(s) com sucesso! Redirecionando...`, 'success');
            
            setTimeout(() => { navigateWithMessage(redirectUrlPedidosGlobal, `${aocsCriadas} AOCS(s) criada(s) com sucesso!`, 'success'); }, 2000);

        } catch (error) {
            console.error("Erro ao enviar pedido:", error);
            const errorMessage = `Erro ao enviar pedido: ${error.message}. Detalhe: ${error.error || 'Erro desconhecido.'}`;
            showNotification(errorMessage, 'error');
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Confirmar e Enviar';
        }
    }

    if (campoBusca) {
        campoBusca.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                fetchItens(1, campoBusca.value); 
            }
        });
    }

    if (btnLimparCarrinho) {
        btnLimparCarrinho.addEventListener('click', () => {
            if (confirm('Tem certeza que deseja limpar todos os itens do pedido?')) {
                carrinho = [];
                renderizarCarrinho();
                document.querySelectorAll('.small-input').forEach(input => {
                    input.value = '';
                    input.closest('tr')?.classList.remove('item-in-cart');
                });
                fetchItens(1, campoBusca.value);
            }
        });
    }

    if (btnFinalizarPedido) btnFinalizarPedido.addEventListener('click', abrirModalFinalizar);
    if (btnFecharModal) btnFecharModal.addEventListener('click', fecharModal);
    if (btnCancelarModal) btnCancelarModal.addEventListener('click', fecharModal);
    window.addEventListener('click', (event) => { if (modal && event.target == modal) fecharModal(); });

    if (btnEnviarPedido) btnEnviarPedido.addEventListener('click', enviarPedido);

    document.querySelectorAll('th.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const coluna = header.dataset.sort;
            if (coluna) { 
                handleSort(coluna);
            }
        });
    });

    fetchItens(); 
});