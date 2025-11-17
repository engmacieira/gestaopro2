document.addEventListener('DOMContentLoaded', function() {

    const formContainer = document.getElementById('form-container-item');
    const formItem = document.getElementById('form-item');
    const formItemTitulo = document.getElementById('form-item-titulo');
    const notificationArea = document.querySelector('.main-content #notification-area');
    const formAnexos = document.getElementById('form-upload-anexo-contrato');

    let idItemEmEdicao = null;

    function showNotification(message, type = 'error') {
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();

        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if(existing) existing.remove();

        const notificationDiv = document.createElement('div');
        notificationDiv.className = `notification ${type}`;
        notificationDiv.textContent = message;
        notificationArea.prepend(notificationDiv); 
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

    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

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

    window.abrirFormParaEditarItem = async (id) => {
        idItemEmEdicao = id;
        try {
            const response = await fetch(`/api/itens/${id}`);
            const item = await response.json();
            if (!response.ok) throw new Error(item.detail || item.erro || 'Item não encontrado');

            formItemTitulo.innerText = 'Editar Item';

            for (const key in item) {
                if (key === 'descricao' && formItem.elements['descricao']) { 
                    formItem.elements['descricao'].value = item[key].descricao;
                } else if ((key === 'quantidade' || key === 'valor_unitario') && formItem.elements[key]) { 
                     formItem.elements[key].value = parseFloat(item[key]).toFixed(2).replace('.', ',');
                } else if (formItem.elements[key]) { 
                    formItem.elements[key].value = item[key];
                }
            }

            formContainer.style.display = 'block';
            formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (error) {
            showNotification(`Erro ao buscar item: ${error.message}`);
        }
    };

    formItem.addEventListener('submit', async function(event) {
        event.preventDefault();

        const dadosForm = Object.fromEntries(new FormData(formItem).entries());
        let quantidadeNumerica, valorNumerico;

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

        const payload = {
            numero_item: parseInt(dadosForm.numero_item), 
            marca: dadosForm.marca || null, 
            unidade_medida: dadosForm.unidade_medida,
            quantidade: quantidadeNumerica.toFixed(2), 
            valor_unitario: valorNumerico.toFixed(2), 
            contrato_nome: nomeContratoGlobal, 
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

            formContainer.style.display = 'none';
            formItem.reset();
            idItemEmEdicao = null;

            reloadPageWithMessage(resultado.mensagem || `Item ${idItemEmEdicao ? 'atualizado' : 'cadastrado'} com sucesso!`, 'success');

        } catch (error) {
            showNotification(`Erro ao salvar item: ${error.message}`);
            submitButton.disabled = false;
             submitButton.innerHTML = `Salvar`;
        }
    });

    window.toggleItemStatus = async (id, statusAtualBool) => {
        if (!confirm(`Tem certeza que deseja ${statusAtualBool ? 'inativar' : 'ativar'} este item?`)) return;

        const novoStatusBool = !statusAtualBool;

        try {
            const response = await fetch(`/api/itens/${id}/status?activate=${novoStatusBool}`, { method: 'PATCH' });
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao alterar status');

            reloadPageWithMessage(resultado.mensagem || `Status do item alterado com sucesso!`, 'success');
        } catch(error) {
            showNotification(`Erro ao alterar status: ${error.message}`);
        }
    }

    window.excluirItem = async (id) => {
        if (!confirm('ATENÇÃO: Ação permanente. Tem certeza que deseja excluir este item?')) return;
        try {
            const response = await fetch(`/api/itens/${id}`, { method: 'DELETE' });

            if (response.status === 204) { 
                reloadPageWithMessage("Item excluído com sucesso!", 'success');
                return;
            }
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro na exclusão');
             reloadPageWithMessage(resultado.mensagem || "Item excluído.", 'success');

        } catch(error) {
            showNotification(`Erro ao excluir item: ${error.message}`);
        }
    }

    window.excluirAnexo = async function(idAnexo, nomeSeguro, nomeOriginal) {
        const mensagemAlerta = `Você está prestes a excluir o anexo "${nomeOriginal}". Deseja continuar?`;
        if (!confirm(mensagemAlerta)) return;

        try {
            const response = await fetch(`/api/anexos/${idAnexo}`, { method: 'DELETE' });

            if (response.status === 204) { 
                 reloadPageWithMessage("Anexo excluído com sucesso.", 'success');
                 return;
            }
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao excluir anexo');
             reloadPageWithMessage(resultado.mensagem || "Anexo excluído.", 'success');

        } catch (error) {
            showNotification(`Erro ao excluir anexo: ${error.message}`);
        }
    }

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

    if (formAnexos) {
        formAnexos.addEventListener('submit', async function(event) {
            event.preventDefault(); 

            const formData = new FormData(formAnexos);
            const submitButton = this.querySelector('button[type="submit"]');

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
                const response = await fetch(formAnexos.action, {
                    method: 'POST',
                    body: formData 
                });

                const resultado = await response.json(); 

                if (!response.ok) {
                    throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao enviar anexo.`);
                }

                formAnexos.reset();
                if(tipoDocumentoNovoInputAnexo) tipoDocumentoNovoInputAnexo.style.display = 'none'; 
                reloadPageWithMessage(resultado.mensagem || 'Anexo enviado com sucesso!', 'success');

            } catch (error) {
                showNotification(`Erro ao enviar anexo: ${error.message}`);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-upload"></i> Enviar';
            }
        });
    }

});