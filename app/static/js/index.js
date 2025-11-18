document.addEventListener('DOMContentLoaded', function() {

    const modalPedido = document.getElementById('modal-novo-pedido');
    const btnAbrirModalPedido = document.getElementById('btn-iniciar-pedido-modal');
    const btnAbrirModalShortcut = document.getElementById('btn-iniciar-pedido-shortcut');
    const notificationArea = document.querySelector('.main-content #notification-area');

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

    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }


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
        selectCategoriaPedido.innerHTML = '<option value="">Carregando categorias...</option>'; 
        selectCategoriaPedido.disabled = true;
        btnContinuarPedido.disabled = true; 

        try {
            const response = await fetch("/api/categorias?mostrar_inativos=false");
            
            const data = await response.json().catch(() => ({})); 

            if (!response.ok) {
                 const errorDetail = data.detail || data.erro || 'Falha ao buscar categorias.';
                 throw new Error(errorDetail);
            }

            const categorias = data; 

            selectCategoriaPedido.innerHTML = '<option value="" disabled selected>Selecione uma categoria ativa</option>';
            if (categorias.length > 0) {
                categorias.forEach(cat => {
                    if (cat.ativo) { 
                         const option = new Option(cat.nome, cat.id); 
                         selectCategoriaPedido.add(option);
                    }
                });
                selectCategoriaPedido.disabled = false;
                if (selectCategoriaPedido.options.length > 1) {
                    btnContinuarPedido.disabled = false; 
                } else {
                    selectCategoriaPedido.innerHTML = '<option value="">Nenhuma categoria ativa encontrada</option>';
                }
            } else {
                 selectCategoriaPedido.innerHTML = '<option value="">Nenhuma categoria ativa encontrada</option>';
            }

        } catch (error) {
            selectCategoriaPedido.innerHTML = '<option value="">Erro ao carregar</option>';
            console.error("Erro ao buscar categorias:", error);
            showNotification(`Erro ao carregar categorias: ${error.message}`, 'error');
        }
    }

    const fecharModalPedido = () => {
        if(modalPedido) modalPedido.style.display = 'none';
    };

    if (btnAbrirModalPedido) btnAbrirModalPedido.addEventListener('click', carregarCategoriasEAbrirModal);
    if (btnAbrirModalShortcut) btnAbrirModalShortcut.addEventListener('click', carregarCategoriasEAbrirModal);

    if (btnFecharModalPedido) btnFecharModalPedido.addEventListener('click', fecharModalPedido);
    if (btnCancelarModalPedido) btnCancelarModalPedido.addEventListener('click', fecharModalPedido);
    window.addEventListener('click', (event) => {
        if (modalPedido && event.target == modalPedido) fecharModalPedido();
    });

    if (btnContinuarPedido) {
        btnContinuarPedido.addEventListener('click', () => {
            const categoriaId = selectCategoriaPedido.value;
            if (categoriaId) {
                window.location.href = `/categoria/${categoriaId}/novo-pedido`;
            } else {
                showNotification('Por favor, selecione uma categoria para continuar.');
            }
        });
    }

});