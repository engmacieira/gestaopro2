document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modal-categoria');
    const modalTitulo = document.getElementById('modal-titulo');
    const formCategoria = document.getElementById('form-categoria');
    const inputNomeCategoria = document.getElementById('nome-categoria');
    // Seleciona a área de notificação DENTRO do main-content para consistência
    const notificationArea = document.querySelector('.main-content #notification-area');
    let idCategoriaEmEdicao = null;

    function showNotification(message, type = 'error') {
        // Remove notificação flash inicial se houver
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();

        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if(existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationArea.prepend(notification); // Usa prepend para aparecer no topo
        setTimeout(() => {
            if (notification) { // Verifica se ainda existe
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    function showNotificationAndReload(message, type = 'success') {
        // Usa sessionStorage para exibir notificação após o reload
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        window.location.reload();
    }

    // Exibir notificação após redirecionamento/reload
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

    // Adiciona listener ao botão que está no _categorias_action_bar.html
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

    // Adiciona listeners aos botões dentro do modal
    const btnFechar = document.getElementById('btn-fechar-modal');
    const btnCancelar = document.getElementById('btn-cancelar-modal');
    if (btnFechar) btnFechar.addEventListener('click', fecharModal);
    if (btnCancelar) btnCancelar.addEventListener('click', fecharModal);

    // Listener para fechar clicando fora do modal
    window.addEventListener('click', (event) => { if (event.target == modal) fecharModal(); });

    // Torna a função acessível globalmente para os botões 'Editar' na tabela
    window.abrirModalParaEditar = async (id) => {
        idCategoriaEmEdicao = id;
        try {
            // GET /api/categorias/{id}
            const response = await fetch(`/api/categorias/${id}`);
            const categoria = await response.json();

            // Tratamento de resposta da API
            if (!response.ok) throw new Error(categoria.detail || categoria.erro || 'Categoria não encontrada.');

            modalTitulo.innerText = 'Editar Categoria';
            inputNomeCategoria.value = categoria.nome;
            modal.style.display = 'flex';

        } catch (error) {
            showNotification(`Erro ao buscar categoria: ${error.message}`);
        }
    }

    // Listener de submissão do formulário do modal
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
            const resultado = await response.json();

            // Tratamento de erros de validação e integridade (FastAPI)
            if (!response.ok) throw new Error(resultado.detail || resultado.erro);

            showNotificationAndReload(resultado.mensagem || `Categoria ${idCategoriaEmEdicao ? 'atualizada' : 'criada'} com sucesso!`, 'success');

        } catch (error) {
            showNotification(`Erro ao salvar: ${error.message}`);
        } finally {
            submitButton.disabled = false;
        }
    });

    // Torna a função acessível globalmente para os botões 'Ativar/Inativar' na tabela
    // Ajuste: Recebe o status atual como booleano diretamente do template
    window.toggleStatusCategoria = async (id, statusAtualBool) => {
        if (!confirm('Tem certeza que deseja alterar o status desta categoria?')) return;

        // O status a ser enviado para a API é o *oposto* do atual
        const novoStatusBool = !statusAtualBool;

        try {
            // A API PATCH espera o parâmetro 'activate' na query como booleano (true/false)
            const response = await fetch(`/api/categorias/${id}/status?activate=${novoStatusBool}`, { method: 'PATCH' });
            const resultado = await response.json();

            if (!response.ok) throw new Error(resultado.detail || resultado.erro);

            const acao = novoStatusBool ? 'ativada' : 'inativada';
            showNotificationAndReload(resultado.mensagem || `Categoria ${acao} com sucesso!`, 'success');

        } catch(error) {
            showNotification(`Erro ao alterar status: ${error.message}`);
        }
    }

    // Torna a função acessível globalmente para os botões 'Excluir' na tabela
    window.excluirCategoria = async (id) => {
        if (!confirm('ATENÇÃO: Ação permanente. Tem certeza que deseja excluir esta categoria?')) return;

        try {
            const response = await fetch(`/api/categorias/${id}`, { method: 'DELETE' });

            // O DELETE no FastAPI retorna 204 NO CONTENT em caso de sucesso
            if (response.status === 204) {
                 showNotificationAndReload("Categoria excluída com sucesso!", 'success');
                 return;
            }

            // Se não for 204, tenta ler a resposta JSON para obter o erro
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro);
            // Caso inesperado: status ok, mas não 204 (ex: 200 com mensagem)
            showNotificationAndReload(resultado.mensagem || "Categoria excluída.", 'success');


        } catch(error) {
            showNotification(`Erro ao excluir: ${error.message}`);
        }
    }

});