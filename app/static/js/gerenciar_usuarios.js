document.addEventListener('DOMContentLoaded', function() {

    const modal = document.getElementById('modal-user');
    const modalTitle = document.getElementById('modal-user-title');
    const formUser = document.getElementById('form-user');
    const passwordGroup = document.getElementById('password-group');
    const btnAddUser = document.getElementById('btn-add-user');
    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');
    let idUsuarioEmEdicao = null;

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

    // Exibir notificação após redirecionamento/reload
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    const fecharModal = () => {
        if (!modal) return;
        modal.style.display = 'none';
        formUser.reset();
        idUsuarioEmEdicao = null;
    };

    const abrirModalParaCriar = () => {
        if (!modal || !modalTitle || !formUser || !passwordGroup) return;
        idUsuarioEmEdicao = null;
        formUser.reset();
        modalTitle.textContent = 'Adicionar Novo Usuário';
        passwordGroup.style.display = 'block'; // Mostra campo senha
        formUser.elements.password.required = true; // Torna senha obrigatória
        modal.style.display = 'flex';
    };

    // Tornada global para ser chamada pelo onclick
    window.abrirModalParaEditar = async (id) => {
        if (!modal || !modalTitle || !formUser || !passwordGroup) return;
        idUsuarioEmEdicao = id;
        formUser.reset();
        try {
            // Chamada GET para buscar o usuário (API: /api/users/{id})
            const response = await fetch(`/api/users/${id}`);
            const usuario = await response.json();

            if (!response.ok) throw new Error(usuario.detail || 'Erro ao carregar usuário');

            modalTitle.textContent = 'Editar Usuário';
            formUser.elements.username.value = usuario.username;
            formUser.elements.nivel_acesso.value = usuario.nivel_acesso;

            // Esconde o campo de senha na edição e torna não obrigatório
            passwordGroup.style.display = 'none';
            formUser.elements.password.required = false;
            formUser.elements.password.value = ""; // Limpa campo senha

            modal.style.display = 'flex';
        } catch (error) {
            showNotification(`Erro ao carregar usuário: ${error.message}`);
        }
    };

    // Tornada global para ser chamada pelo onclick
    // Recebe o status atual como booleano
    window.toggleUserStatus = async (id, statusAtualBool) => {
         if (!confirm(`Tem certeza que deseja ${statusAtualBool ? 'inativar' : 'ativar'} este usuário?`)) return;

         const novoStatusBool = !statusAtualBool;

         try {
             // Chamada PUT para alterar o campo 'ativo' (API: /api/users/{id})
             // O user_router espera um UserUpdateRequest
             const response = await fetch(`/api/users/${id}`, {
                 method: 'PUT',
                 headers: { 'Content-Type': 'application/json' },
                 body: JSON.stringify({ ativo: novoStatusBool }) // Envia apenas o campo a alterar
             });
             const resultado = await response.json();

             if (!response.ok) throw new Error(resultado.detail || 'Erro ao alterar status');

             const acao = novoStatusBool ? 'ativado' : 'inativado';
             showNotificationAndReload(`Usuário ${acao} com sucesso!`, 'success');

         } catch (error) {
             showNotification(`Erro ao alterar status: ${error.message}`);
         }
    };

    // Tornada global para ser chamada pelo onclick
    window.resetarSenha = async (id) => {
        if (!confirm('ATENÇÃO: Isto irá gerar uma nova senha para o usuário e invalidar a antiga. Deseja continuar?')) return;
        try {
            // Chamada POST para resetar senha (API: /api/users/{id}/reset-password)
            const response = await fetch(`/api/users/${id}/reset-password`, { method: 'POST' });
            const resultado = await response.json();

            if (!response.ok) throw new Error(resultado.detail || 'Erro ao resetar senha');

            // Mostra a nova senha num alert (considerar alternativa mais segura se necessário)
            alert(`Senha redefinida com sucesso!\n\nA nova senha temporária é:\n\n${resultado.new_password}\n\nCopie esta senha e a entregue ao usuário de forma segura.`);

        } catch (error) {
            showNotification(`Erro ao redefinir senha: ${error.message}`);
        }
    };

    // --- Adiciona Listeners ---
    if (btnAddUser) btnAddUser.addEventListener('click', abrirModalParaCriar);
    if (modal) modal.querySelectorAll('.close-button').forEach(btn => btn.addEventListener('click', fecharModal));
    window.addEventListener('click', (event) => { if (modal && event.target == modal) fecharModal(); });

    if (formUser) {
        formUser.addEventListener('submit', async function(event) {
            event.preventDefault();

            const formData = new FormData(formUser);
            const dados = Object.fromEntries(formData.entries());

            // Garante que nivel_acesso seja número
            dados.nivel_acesso = parseInt(dados.nivel_acesso);
            if (isNaN(dados.nivel_acesso)) {
                showNotification("Nível de acesso inválido.", "error");
                return;
            }


            const url = idUsuarioEmEdicao ? `/api/users/${idUsuarioEmEdicao}` : '/api/users/';
            const method = idUsuarioEmEdicao ? 'PUT' : 'POST';

            // Prepara o payload correto para PUT (UserUpdateRequest)
            let payload = {};
            if (method === 'PUT') {
                 payload = {
                     username: dados.username,
                     nivel_acesso: dados.nivel_acesso
                     // Não inclui 'ativo' ou 'password' aqui, são tratados por rotas separadas
                 };
            } else { // POST (UserCreateRequest)
                 payload = {
                     username: dados.username,
                     password: dados.password,
                     nivel_acesso: dados.nivel_acesso,
                     ativo: true // Assume ativo por defeito na criação
                 };
                 // Validação básica da senha (mínimo 8 caracteres)
                 if (!dados.password || dados.password.length < 8) {
                      showNotification("A senha é obrigatória e deve ter no mínimo 8 caracteres.", "error");
                      return;
                 }
            }


            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Salvando...`;


            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload) // Envia o payload correto
                });
                const resultado = await response.json();

                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status}`);

                showNotificationAndReload(resultado.mensagem || `Usuário ${idUsuarioEmEdicao ? 'atualizado' : 'criado'} com sucesso!`, 'success');

            } catch (error) {
                showNotification(`Erro: ${error.message}`);
                 submitButton.disabled = false;
                 submitButton.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Salvar`;
            }
        });
    }

});