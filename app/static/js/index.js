document.addEventListener('DOMContentLoaded', function() {

    // --- Referências e Lógica do Modal/Atalhos ---
    const modalPedido = document.getElementById('modal-novo-pedido');
    // Botões que abrem o modal (Header e Atalho)
    const btnAbrirModalPedido = document.getElementById('btn-iniciar-pedido-modal');
    const btnAbrirModalShortcut = document.getElementById('btn-iniciar-pedido-shortcut');
    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');

    // --- Função de Notificação ---
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

     // Exibir notificação após redirecionamento/reload (se houver de outras páginas)
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }


    // --- Lógica do Modal Novo Pedido ---
    const btnFecharModalPedido = document.getElementById('btn-fechar-modal-pedido');
    const btnCancelarModalPedido = document.getElementById('btn-cancelar-modal-pedido');
    const btnContinuarPedido = document.getElementById('btn-continuar-pedido');
    const selectCategoriaPedido = document.getElementById('categoria-pedido-select');

    async function carregarCategoriasEAbrirModal() {
        if (!modalPedido || !selectCategoriaPedido) {
            console.error("Modal ou select de categoria não encontrado.");
            showNotification("Erro ao abrir modal.", "error");
            return;
        }

        modalPedido.style.display = 'flex';
        selectCategoriaPedido.innerHTML = '<option value="">Carregando categorias...</option>'; // Feedback visual
        selectCategoriaPedido.disabled = true;
        btnContinuarPedido.disabled = true; // Desabilita botão enquanto carrega

        try {
            // Chamada à API para buscar categorias ativas
            const response = await fetch("/api/categorias?mostrar_inativos=false");
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ detail: 'Falha ao buscar categorias.' }));
                 throw new Error(errorData.detail || `Erro ${response.status}`);
            }

            const categorias = await response.json();

            selectCategoriaPedido.innerHTML = '<option value="" disabled selected>Selecione uma categoria ativa</option>'; // Placeholder
            if (categorias.length > 0) {
                categorias.forEach(cat => {
                    const option = new Option(cat.nome, cat.id); // Texto, Valor
                    selectCategoriaPedido.add(option);
                });
                selectCategoriaPedido.disabled = false;
                btnContinuarPedido.disabled = false; // Habilita botão
            } else {
                 selectCategoriaPedido.innerHTML = '<option value="">Nenhuma categoria ativa encontrada</option>';
            }

        } catch (error) {
            selectCategoriaPedido.innerHTML = '<option value="">Erro ao carregar</option>';
            console.error("Erro ao buscar categorias:", error);
            showNotification(`Erro ao carregar categorias: ${error.message}`, 'error');
            // Mantém botões desabilitados
        }
    }

    const fecharModalPedido = () => {
        if(modalPedido) modalPedido.style.display = 'none';
    };

    // Atribuir eventos de abertura do modal
    if (btnAbrirModalPedido) btnAbrirModalPedido.addEventListener('click', carregarCategoriasEAbrirModal);
    if (btnAbrirModalShortcut) btnAbrirModalShortcut.addEventListener('click', carregarCategoriasEAbrirModal);

    // Atribuir eventos de fecho do modal
    if (btnFecharModalPedido) btnFecharModalPedido.addEventListener('click', fecharModalPedido);
    if (btnCancelarModalPedido) btnCancelarModalPedido.addEventListener('click', fecharModalPedido);
    window.addEventListener('click', (event) => {
        if (modalPedido && event.target == modalPedido) fecharModalPedido();
    });

    // Evento do botão Continuar
    if (btnContinuarPedido) {
        btnContinuarPedido.addEventListener('click', () => {
            const categoriaId = selectCategoriaPedido.value;
            if (categoriaId) {
                // Redirecionamento para a página de novo pedido da categoria selecionada
                window.location.href = `/categoria/${categoriaId}/novo-pedido`;
            } else {
                showNotification('Por favor, selecione uma categoria para continuar.');
            }
        });
    }

});