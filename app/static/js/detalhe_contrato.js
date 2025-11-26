document.addEventListener('DOMContentLoaded', function() {

    // --- Referências aos Elementos do DOM ---
    const formContainer = document.getElementById('form-container-item');
    const formItem = document.getElementById('form-item');
    const formItemTitulo = document.getElementById('form-item-titulo');
    const notificationArea = document.querySelector('.main-content #notification-area');
    const formAnexos = document.getElementById('form-upload-anexo-contrato');
    const btnToggleForm = document.getElementById('btn-toggle-form');

    let idItemEmEdicao = null;

    // --- Funções Auxiliares ---

    function showNotification(message, type = 'error') {
        if(notificationArea) {
            // Limpa notificações anteriores para não empilhar
            notificationArea.innerHTML = '';
            
            const notificationDiv = document.createElement('div');
            notificationDiv.className = `notification ${type}`;
            notificationDiv.textContent = message;
            notificationArea.prepend(notificationDiv); 
            
            // Remove automaticamente após 5 segundos
            setTimeout(() => {
                if (notificationDiv && notificationDiv.parentNode) {
                    notificationDiv.style.opacity = '0';
                    notificationDiv.addEventListener('transitionend', () => notificationDiv.remove());
                }
            }, 5000);
        } else {
            // Fallback se não houver área de notificação
            alert(message);
        }
    }

    function reloadPageWithMessage(message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        location.reload();
    }

    function parseBrazilianFloat(str) {
        if (!str) return 0;
        // Remove pontos de milhar (ex: 1.000 -> 1000) e troca vírgula por ponto (ex: 50,00 -> 50.00)
        const cleanedStr = String(str).replace(/\./g, '').replace(',', '.');
        const num = parseFloat(cleanedStr);
        if (isNaN(num) || num < 0) {
            throw new Error("Quantidade e Valor Unitário devem ser números válidos.");
        }
        return num;
    }

    // --- Inicialização da Página ---

    // Exibe mensagens de sucesso após reload (ex: "Item Salvo")
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    // Evento: Botão "Adicionar Novo Item" (Abre/Fecha formulário)
    if (btnToggleForm) {
        btnToggleForm.addEventListener('click', () => {
            idItemEmEdicao = null;
            if(formItemTitulo) formItemTitulo.innerText = 'Adicionar Novo Item';
            if(formItem) formItem.reset();
            
            if(formContainer) {
                const isHidden = formContainer.style.display === 'none';
                formContainer.style.display = isHidden ? 'block' : 'none';
                if (isHidden) { 
                    formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' }); 
                }
            }
        });
    }

    // --- LÓGICA PRINCIPAL: Salvar Item (POST/PUT) ---

    if (formItem) {
        formItem.addEventListener('submit', async function(event) {
            event.preventDefault();

            const submitButton = this.querySelector('button[type="submit"]');
            const dadosForm = Object.fromEntries(new FormData(formItem).entries());
            
            // 1. Validação Crítica: Nome do Contrato
            // Este valor deve vir do HTML via <script>window.nomeContratoGlobal = ...</script>
            if (!window.nomeContratoGlobal) {
                console.error("ERRO FATAL: window.nomeContratoGlobal está vazio.");
                showNotification("Erro interno: O número do contrato não foi carregado. Tente atualizar a página (F5).", "error");
                return;
            }

            // 2. Validação: Número do Item
            const numItem = parseInt(dadosForm.numero_item);
            if (isNaN(numItem)) {
                showNotification("O Número do Item é obrigatório e deve ser um número inteiro.", "error");
                return;
            }

            // 3. Tratamento de Valores Monetários
            let quantidadeNumerica, valorNumerico;
            try {
                quantidadeNumerica = parseBrazilianFloat(dadosForm.quantidade);
                valorNumerico = parseBrazilianFloat(dadosForm.valor_unitario);
            } catch (e) {
                showNotification(e.message, "error");
                return;
            }

            // Bloqueia o botão para evitar duplo clique
            if(submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Salvando...`;
            }

            // Monta o JSON exato que o Backend espera (ItemRequest)
            const payload = {
                numero_item: numItem, 
                marca: dadosForm.marca || null, 
                unidade_medida: dadosForm.unidade_medida,
                quantidade: quantidadeNumerica, 
                valor_unitario: valorNumerico,   
                contrato_nome: window.nomeContratoGlobal, // Variável injetada pelo HTML
                descricao: {
                    descricao: dadosForm.descricao
                }
            };

            console.log("Enviando Payload para API:", payload); // DEBUG: Veja isso no Console (F12)

            // Define URL e Método (Novo ou Edição)
            const url = idItemEmEdicao ? `/api/itens/${idItemEmEdicao}` : `/api/itens/`;
            const method = idItemEmEdicao ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) {
                     const erro = await response.json();
                     console.error("Erro API:", erro); // DEBUG

                     // Tenta extrair mensagem amigável do erro de validação (422)
                     let msgErro = erro.detail || erro.erro || `Erro ${response.status} ao salvar.`;
                     
                     if (Array.isArray(erro.detail)) {
                         // Formata erros do Pydantic (ex: "campo: missing")
                         msgErro = erro.detail.map(d => `${d.loc[d.loc.length-1]}: ${d.msg}`).join(" | ");
                     }
                     
                     throw new Error(msgErro);
                }

                const item = await response.json();
                
                // Limpa estado
                formContainer.style.display = 'none';
                formItem.reset();
                idItemEmEdicao = null;

                const acao = idItemEmEdicao ? 'atualizado' : 'cadastrado';
                reloadPageWithMessage(`Item #${item.numero_item} ${acao} com sucesso!`, 'success');

            } catch (error) {
                showNotification(`Falha ao salvar: ${error.message}`, "error");
            } finally {
                // Libera o botão
                if(submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = `Salvar`;
                }
            }
        });
    }

    // --- Funções Globais (Acessíveis via onclick no HTML) ---

    // Preenche o formulário para edição
    window.abrirFormParaEditarItem = async (id) => {
        idItemEmEdicao = id;
        try {
            const response = await fetch(`/api/itens/${id}`);
            if (!response.ok) throw new Error('Erro ao buscar dados do item.');
            
            const item = await response.json();

            if(formItemTitulo) formItemTitulo.innerText = 'Editar Item';

            // Popula os campos do formulário
            if (formItem) {
                formItem.elements['numero_item'].value = item.numero_item;
                formItem.elements['unidade_medida'].value = item.unidade_medida;
                formItem.elements['marca'].value = item.marca || '';
                
                // Acessa objeto aninhado de descrição
                if(item.descricao && item.descricao.descricao) {
                    formItem.elements['descricao'].value = item.descricao.descricao;
                } else {
                    formItem.elements['descricao'].value = "";
                }
                
                // Formata números de volta para o padrão PT-BR para edição
                formItem.elements['quantidade'].value = parseFloat(item.quantidade).toLocaleString('pt-BR', {minimumFractionDigits: 2});
                formItem.elements['valor_unitario'].value = parseFloat(item.valor_unitario).toLocaleString('pt-BR', {minimumFractionDigits: 2});
            }

            if(formContainer) {
                formContainer.style.display = 'block';
                formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } catch (error) {
            showNotification(`Erro ao abrir edição: ${error.message}`);
        }
    };

    // Alterna status (Ativo/Inativo)
    window.toggleItemStatus = async (id, statusAtualBool) => {
        const acaoTexto = statusAtualBool ? 'inativar' : 'ativar';
        if (!confirm(`Tem certeza que deseja ${acaoTexto} este item?`)) return;

        const novoStatusBool = !statusAtualBool;

        try {
            const response = await fetch(`/api/itens/${id}/status?activate=${novoStatusBool}`, { method: 'PATCH' });
            
            if (!response.ok) {
                const erro = await response.json();
                throw new Error(erro.detail || 'Erro ao alterar status');
            }
            
            const acaoPassada = novoStatusBool ? 'ativado' : 'inativado';
            reloadPageWithMessage(`Item ${acaoPassada} com sucesso!`, 'success');
        } catch(error) {
            showNotification(`Erro: ${error.message}`);
        }
    }

    // Exclui item
    window.excluirItem = async (id) => {
        if (!confirm('ATENÇÃO: Ação permanente. Tem certeza que deseja excluir este item?')) return;
        try {
            const response = await fetch(`/api/itens/${id}`, { method: 'DELETE' });

            if (response.status === 204) { 
                reloadPageWithMessage("Item excluído com sucesso!", 'success');
                return;
            }
            
            if (!response.ok) {
                const res = await response.json();
                throw new Error(res.detail || 'Erro na exclusão');
            }
            reloadPageWithMessage("Item excluído.", 'success');

        } catch(error) {
            showNotification(`Erro ao excluir: ${error.message}`);
        }
    }

    // Exclui anexo
    window.excluirAnexo = async function(idAnexo, nomeSeguro, nomeOriginal) {
        if (!confirm(`Excluir o anexo "${nomeOriginal}"?`)) return;

        try {
            const response = await fetch(`/api/anexos/${idAnexo}`, { method: 'DELETE' });

            if (response.status === 204) { 
                 reloadPageWithMessage("Anexo excluído.", 'success');
                 return;
            }
            if (!response.ok) {
                throw new Error('Erro ao excluir anexo');
            }
            reloadPageWithMessage("Anexo excluído.", 'success');
        } catch (error) {
            showNotification(`Erro: ${error.message}`);
        }
    }

    // --- Lógica da Aba de Anexos ---

    const tipoDocumentoSelectAnexo = document.getElementById('tipo_documento_select_anexo');
    const tipoDocumentoNovoInputAnexo = document.getElementById('tipo_documento_novo_anexo');

    if (tipoDocumentoSelectAnexo && tipoDocumentoNovoInputAnexo) {
        tipoDocumentoSelectAnexo.addEventListener('change', function() {
            const isNovo = this.value === 'NOVO';
            tipoDocumentoNovoInputAnexo.style.display = isNovo ? 'block' : 'none'; 
            tipoDocumentoNovoInputAnexo.required = isNovo;
            if (!isNovo) tipoDocumentoNovoInputAnexo.value = '';
        });
    }

    if (formAnexos) {
        formAnexos.addEventListener('submit', async function(event) {
            event.preventDefault(); 

            const formData = new FormData(formAnexos);
            const submitButton = this.querySelector('button[type="submit"]');
            const fileInput = document.getElementById('anexo_file');

            // Validações de Anexo
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                 showNotification("Selecione um arquivo.", "error");
                 return;
            }
            const tipoDoc = formData.get('tipo_documento');
            const novoTipo = formData.get('tipo_documento_novo');
            
            if (tipoDoc === 'NOVO' && (!novoTipo || novoTipo.trim() === '')) {
                 showNotification("Informe o nome do novo tipo de documento.", "error");
                 return;
            }
            if (!tipoDoc) {
                 showNotification("Selecione um tipo de documento.", "error");
                 return;
            }

            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...';

            try {
                const response = await fetch(formAnexos.action, {
                    method: 'POST',
                    body: formData 
                });

                if (!response.ok) {
                    const res = await response.json();
                    throw new Error(res.detail || `Erro ${response.status}`);
                }

                formAnexos.reset();
                if(tipoDocumentoNovoInputAnexo) tipoDocumentoNovoInputAnexo.style.display = 'none'; 
                
                reloadPageWithMessage('Anexo enviado!', 'success');

            } catch (error) {
                showNotification(`Erro ao enviar anexo: ${error.message}`);
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-upload"></i> Enviar';
            }
        });
    }

});