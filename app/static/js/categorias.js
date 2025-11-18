document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modal-categoria');
    const modalTitulo = document.getElementById('modal-titulo');
    const formCategoria = document.getElementById('form-categoria');
    const inputNomeCategoria = document.getElementById('nome-categoria');
    const notificationArea = document.querySelector('.main-content #notification-area');
    let idCategoriaEmEdicao = null;

    function showNotification(message, type = 'error') {
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();

        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if(existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationArea.prepend(notification); 
        setTimeout(() => {
            if (notification) { 
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    function showNotificationAndReload(message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        window.location.reload();
    }

    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    const fecharModal = () => {
        modal.style.display = 'none';
        formCategoria.reset();
        idCategoriaEmEdicao = null;
    };

    const btnAbrirModal = document.getElementById('btn-abrir-modal');
    if (btnAbrirModal) {
        btnAbrirModal.addEventListener('click', () => {
            idCategoriaEmEdicao = null;
            modalTitulo.innerText = 'Cadastrar Nova Categoria';
            formCategoria.reset();
            modal.style.display = 'flex';
        });
    } else {
        console.error("Botão 'btn-abrir-modal' não encontrado.");
    }

    const btnFechar = document.getElementById('btn-fechar-modal');
    const btnCancelar = document.getElementById('btn-cancelar-modal');
    if (btnFechar) btnFechar.addEventListener('click', fecharModal);
    if (btnCancelar) btnCancelar.addEventListener('click', fecharModal);

    window.addEventListener('click', (event) => { if (event.target == modal) fecharModal(); });

    window.abrirModalParaEditar = async (id) => {
        idCategoriaEmEdicao = id;
        try {
            const response = await fetch(`/api/categorias/${id}`);
            const categoria = await response.json();

            if (!response.ok) throw new Error(categoria.detail || categoria.erro || 'Categoria não encontrada.');

            modalTitulo.innerText = 'Editar Categoria';
            inputNomeCategoria.value = categoria.nome;
            modal.style.display = 'flex';

        } catch (error) {
            showNotification(`Erro ao buscar categoria: ${error.message}`);
        }
    }

    formCategoria.addEventListener('submit', async function(event) {
        event.preventDefault();
        const nome = inputNomeCategoria.value.trim();

        if (!nome) {
            showNotification("O nome da categoria não pode estar vazio.", "error");
            return;
        }

        const url = idCategoriaEmEdicao ? `/api/categorias/${idCategoriaEmEdicao}` : '/api/categorias';
        const method = idCategoriaEmEdicao ? 'PUT' : 'POST';

        const submitButton = this.querySelector('button[type="submit"]');
        submitButton.disabled = true;

        try {
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome: nome })
            });

            if (!response.ok) {
                const erro = await response.json();
                throw new Error(erro.detail || erro.erro || `Erro de servidor: ${response.status}`);
            }
            
            const categoria = await response.json(); 

            const acao = idCategoriaEmEdicao ? 'atualizada' : 'criada';
            showNotificationAndReload(`Categoria '${categoria.nome}' ${acao} com sucesso!`, 'success');

        } catch (error) {
            showNotification(`Erro ao salvar: ${error.message}`);
        } finally {
            submitButton.disabled = false;
        }
    });

    window.toggleStatusCategoria = async (id, statusAtualBool) => {
        if (!confirm('Tem certeza que deseja alterar o status desta categoria?')) return;

        const novoStatusBool = !statusAtualBool;

        try {
            const response = await fetch(`/api/categorias/${id}/status?activate=${novoStatusBool}`, { method: 'PATCH' });
            
            if (!response.ok) {
                const erro = await response.json();
                throw new Error(erro.detail || erro.erro || `Erro de servidor: ${response.status}`);
            }

            const categoria = await response.json();

            const acao = novoStatusBool ? 'ativada' : 'inativada';
            showNotificationAndReload(`Categoria '${categoria.nome}' ${acao} com sucesso!`, 'success');

        } catch(error) {
            showNotification(`Erro ao alterar status: ${error.message}`);
        }
    }

    window.excluirCategoria = async (id) => {
        if (!confirm('ATENÇÃO: Ação permanente. Tem certeza que deseja excluir esta categoria?')) return;

        try {
            const response = await fetch(`/api/categorias/${id}`, { method: 'DELETE' });

            if (response.status === 204) {
                 showNotificationAndReload("Categoria excluída com sucesso!", 'success');
                 return;
            }

            if (!response.ok) {
                const resultado = await response.json();
                throw new Error(resultado.detail || resultado.erro || `Erro de servidor: ${response.status}`);
            }
            
            showNotificationAndReload("Categoria excluída com sucesso!", 'success');


        } catch(error) {
            showNotification(`Erro ao excluir: ${error.message}`);
        }
    }

});