document.addEventListener('DOMContentLoaded', function() {

    // --- Referências Globais e de Elementos ---
    const formContainer = document.getElementById('form-container-item');
    const formItem = document.getElementById('form-item');
    const formItemTitulo = document.getElementById('form-item-titulo');
    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');
    // Referência ao formulário de anexos pelo ID adicionado
    const formAnexos = document.getElementById('form-upload-anexo-contrato');

    let idItemEmEdicao = null;
    // idContratoGlobal e nomeContratoGlobal são definidos no HTML

    // --- Funções de UI Auxiliares ---
    function showNotification(message, type = 'error') {
        // Remove notificação flash inicial se houver
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();

        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if(existing) existing.remove();

        const notificationDiv = document.createElement('div');
        notificationDiv.className = `notification ${type}`;
        notificationDiv.textContent = message;
        notificationArea.prepend(notificationDiv); // Usa prepend
        setTimeout(() => {
            if (notificationDiv) {
                notificationDiv.style.opacity = '0';
                notificationDiv.addEventListener('transitionend', () => notificationDiv.remove());
            }
        }, 5000);
    }

    function reloadPageWithMessage(message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        location.reload();
    }

    // Exibir notificação após redirecionamento/reload
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    // --- Lógica do Formulário de Item ---

    // Botão para mostrar/esconder formulário de item
    const btnToggleForm = document.getElementById('btn-toggle-form');
    if (btnToggleForm) {
        btnToggleForm.addEventListener('click', () => {
            idItemEmEdicao = null;
            formItemTitulo.innerText = 'Adicionar Novo Item';
            formItem.reset();
            const isHidden = formContainer.style.display === 'none';
            formContainer.style.display = isHidden ? 'block' : 'none';
            if (isHidden) { formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
        });
    }

    // Função global para abrir modal de edição de item (chamada pelo onclick)
    window.abrirFormParaEditarItem = async (id) => {
        idItemEmEdicao = id;
        try {
            // API GET /api/itens/{id}
            const response = await fetch(`/api/itens/${id}`);
            const item = await response.json();
            if (!response.ok) throw new Error(item.detail || item.erro || 'Item não encontrado');

            formItemTitulo.innerText = 'Editar Item';

            // Preenche os campos do formulário
            for (const key in item) {
                if (key === 'descricao' && formItem.elements['descricao']) { // Trata objeto aninhado
                    formItem.elements['descricao'].value = item[key].descricao;
                } else if ((key === 'quantidade' || key === 'valor_unitario') && formItem.elements[key]) { // Formata decimais
                     formItem.elements[key].value = parseFloat(item[key]).toFixed(2).replace('.', ',');
                } else if (formItem.elements[key]) { // Campos simples
                    formItem.elements[key].value = item[key];
                }
            }

            formContainer.style.display = 'block';
            formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (error) {
            showNotification(`Erro ao buscar item: ${error.message}`);
        }
    };

    // Submissão do formulário de item (Adicionar/Editar)
    formItem.addEventListener('submit', async function(event) {
        event.preventDefault();

        const dadosForm = Object.fromEntries(new FormData(formItem).entries());
        let quantidadeNumerica, valorNumerico;

        // 1. Validação e Conversão de Decimais
        try {
            const qtdStr = String(dadosForm.quantidade).replace('.', '').replace(',', '.');
            const valorStr = String(dadosForm.valor_unitario).replace('.', '').replace(',', '.');

            quantidadeNumerica = parseFloat(qtdStr);
            valorNumerico = parseFloat(valorStr);

            if (isNaN(quantidadeNumerica) || isNaN(valorNumerico) || quantidadeNumerica < 0 || valorNumerico < 0) {
                throw new Error("Quantidade e Valor Unitário devem ser números válidos e não negativos.");
            }
        } catch (e) {
            showNotification(e.message);
            return;
        }

        // 2. Monta o Payload para a API (Schema ItemRequest)
        const payload = {
            numero_item: parseInt(dadosForm.numero_item), // Garante que seja número
            marca: dadosForm.marca || null, // Envia null se vazio
            unidade_medida: dadosForm.unidade_medida,
            quantidade: quantidadeNumerica.toFixed(2), // Envia como string formatada para API (Pydantic/Decimal lidam com isso)
            valor_unitario: valorNumerico.toFixed(2), // Envia como string formatada
            contrato_nome: nomeContratoGlobal, // Usa a variável global
            descricao: {
                descricao: dadosForm.descricao
            }
        };

        const url = idItemEmEdicao ? `/api/itens/${idItemEmEdicao}` : `/api/itens`;
        const method = idItemEmEdicao ? 'PUT' : 'POST';

        const submitButton = this.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Salvando...`;

        try {
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const resultado = await response.json();

            if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status}`);

            // Esconde o formulário após sucesso
            formContainer.style.display = 'none';
            formItem.reset();
            idItemEmEdicao = null;

            // Recarrega a página com mensagem
            reloadPageWithMessage(resultado.mensagem || `Item ${idItemEmEdicao ? 'atualizado' : 'cadastrado'} com sucesso!`, 'success');

        } catch (error) {
            showNotification(`Erro ao salvar item: ${error.message}`);
            submitButton.disabled = false;
             submitButton.innerHTML = `Salvar`;
        }
    });

    // Função global para Ativar/Inativar Item (chamada pelo onclick)
    window.toggleItemStatus = async (id, statusAtualBool) => {
        if (!confirm(`Tem certeza que deseja ${statusAtualBool ? 'inativar' : 'ativar'} este item?`)) return;

        const novoStatusBool = !statusAtualBool;

        try {
            // API PATCH /api/itens/{id}/status?activate=true/false
            const response = await fetch(`/api/itens/${id}/status?activate=${novoStatusBool}`, { method: 'PATCH' });
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao alterar status');

            reloadPageWithMessage(resultado.mensagem || `Status do item alterado com sucesso!`, 'success');
        } catch(error) {
            showNotification(`Erro ao alterar status: ${error.message}`);
        }
    }

    // Função global para Excluir Item (chamada pelo onclick)
    window.excluirItem = async (id) => {
        if (!confirm('ATENÇÃO: Ação permanente. Tem certeza que deseja excluir este item?')) return;
        try {
            // API DELETE /api/itens/{id}
            const response = await fetch(`/api/itens/${id}`, { method: 'DELETE' });

            if (response.status === 204) { // Sucesso sem conteúdo
                reloadPageWithMessage("Item excluído com sucesso!", 'success');
                return;
            }
            // Se não for 204, tenta ler o erro
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro na exclusão');
            // Caso raro: 200 OK com mensagem
             reloadPageWithMessage(resultado.mensagem || "Item excluído.", 'success');

        } catch(error) {
            showNotification(`Erro ao excluir item: ${error.message}`);
        }
    }

    // --- Lógica de Anexos ---

    // Função global para Excluir Anexo (chamada pelo onclick)
    window.excluirAnexo = async function(idAnexo, nomeSeguro, nomeOriginal) {
        const mensagemAlerta = `Você está prestes a excluir o anexo "${nomeOriginal}". Deseja continuar?`;
        if (!confirm(mensagemAlerta)) return;

        try {
            // API DELETE /api/anexos/{id}
            const response = await fetch(`/api/anexos/${idAnexo}`, { method: 'DELETE' });

            if (response.status === 204) { // Sucesso
                 reloadPageWithMessage("Anexo excluído com sucesso.", 'success');
                 return;
            }
            // Tenta ler erro
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao excluir anexo');
             // Caso raro: 200 OK com mensagem
             reloadPageWithMessage(resultado.mensagem || "Anexo excluído.", 'success');

        } catch (error) {
            showNotification(`Erro ao excluir anexo: ${error.message}`);
        }
    }

    // Lógica para o select "NOVO TIPO" no formulário de anexos
    const tipoDocumentoSelectAnexo = document.getElementById('tipo_documento_select_anexo');
    const tipoDocumentoNovoInputAnexo = document.getElementById('tipo_documento_novo_anexo');

    if (tipoDocumentoSelectAnexo && tipoDocumentoNovoInputAnexo) {
        tipoDocumentoSelectAnexo.addEventListener('change', function() {
            const isNovo = this.value === 'NOVO';
            tipoDocumentoNovoInputAnexo.style.display = isNovo ? 'block' : 'none';
            tipoDocumentoNovoInputAnexo.required = isNovo;
            if (!isNovo) {
                tipoDocumentoNovoInputAnexo.value = '';
            }
        });
    }

    // Intercepta o submit do formulário de anexos para tratar via Fetch API
    if (formAnexos) {
        formAnexos.addEventListener('submit', async function(event) {
            event.preventDefault(); // Impede o envio tradicional

            const formData = new FormData(formAnexos);
            const submitButton = this.querySelector('button[type="submit"]');

            // Validação simples no frontend
            const fileInput = document.getElementById('anexo_file');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                 showNotification("Por favor, selecione um arquivo.", "error");
                 return;
            }
            const tipoDoc = formData.get('tipo_documento');
            const novoTipo = formData.get('tipo_documento_novo');
            if (tipoDoc === 'NOVO' && (!novoTipo || novoTipo.trim() === '')) {
                 showNotification("Por favor, informe o nome do novo tipo de documento.", "error");
                 return;
            }
            if (tipoDoc === '' || tipoDoc === null) {
                 showNotification("Por favor, selecione ou crie um tipo de documento.", "error");
                 return;
            }

            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...';

            try {
                // API POST /api/anexos/upload/
                const response = await fetch(formAnexos.action, {
                    method: 'POST',
                    body: formData // Envia como FormData
                });

                const resultado = await response.json(); // Tenta ler JSON mesmo em caso de erro

                if (!response.ok) {
                    throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao enviar anexo.`);
                }

                // Limpa o formulário e recarrega
                formAnexos.reset();
                if(tipoDocumentoNovoInputAnexo) tipoDocumentoNovoInputAnexo.style.display = 'none'; // Esconde campo novo tipo
                reloadPageWithMessage(resultado.mensagem || 'Anexo enviado com sucesso!', 'success');

            } catch (error) {
                showNotification(`Erro ao enviar anexo: ${error.message}`);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-upload"></i> Enviar';
            }
        });
    }

});