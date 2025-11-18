document.addEventListener('DOMContentLoaded', function() {

    let idPedidoParaEntrega = null;

    const notificationArea = document.querySelector('.main-content #notification-area');

    function showNotification(message, type = 'error') {
        if (!notificationArea) { console.error("Notification area not found!"); return; }

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

    function reloadPageWithMessage(message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        location.reload();
    }

    function parseBrazilianFloat(str) {
        if (!str) return 0;
        const cleanedStr = String(str).replace(/\./g, '').replace(',', '.'); 
        const num = parseFloat(cleanedStr);
        if (isNaN(num) || num < 0) {
            throw new Error("O valor deve ser um número válido e não negativo.");
        }
        return num;
    }

    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType') || 'success');
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    async function updateAocsField(campo, valor) {
        const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
        try {
            const response = await fetch(`/api/aocs/${encodedAOCS}/dados-gerais`, { 
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [campo]: valor })
            });
            const resultado = await response.json();
            
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao atualizar campo.`);
            
            showNotification(resultado.mensagem || 'Campo atualizado.', 'success');
        } catch (error) {
            showNotification(`Erro ao atualizar ${campo}: ${error.message}`, 'error');
        }
    }

    async function updateAocsDate(data) {
        const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
         try {
            const response = await fetch(`/api/aocs/${encodedAOCS}/data`, { 
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data_criacao: data }) 
            });
            const resultado = await response.json();
            
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao atualizar data.`);
            
            showNotification(resultado.mensagem || 'Data atualizada.', 'success');
        } catch (error) {
            showNotification(`Erro ao atualizar data: ${error.message}`, 'error');
        }
    }

    const modalEntrega = document.getElementById('modal-registrar-entrega');
    const formEntrega = modalEntrega?.querySelector('#form-registrar-entrega');
    const inputQtdEntrega = modalEntrega?.querySelector('#quantidade_entregue');
    const descModalEntrega = modalEntrega?.querySelector('#entrega-item-descricao');
    const saldoModalEntrega = modalEntrega?.querySelector('#entrega-saldo-restante');
    const dataEntregaInput = modalEntrega?.querySelector('#data_entrega'); 

    window.abrirModalEntrega = function(idPedido, descricao, saldo) {
        if (!modalEntrega || !inputQtdEntrega || !descModalEntrega || !saldoModalEntrega || !dataEntregaInput) {
            console.error("Elementos do modal de entrega não encontrados!");
            showNotification("Erro ao abrir modal de entrega.", "error");
            return;
        }
        idPedidoParaEntrega = idPedido;
        descModalEntrega.textContent = descricao; 
        
        const saldoFormatado = saldo.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        saldoModalEntrega.textContent = saldoFormatado; 
        
        inputQtdEntrega.value = saldoFormatado;
        inputQtdEntrega.max = saldo; 
        inputQtdEntrega.placeholder = saldoFormatado; 
        
        dataEntregaInput.valueAsDate = new Date(); 
        formEntrega.reset(); 
        formEntrega.elements['item_pedido_id'].value = idPedido;
        formEntrega.elements['quantidade_entregue'].value = saldoFormatado; 

        modalEntrega.style.display = 'flex';
        inputQtdEntrega.focus();
        inputQtdEntrega.select();
    }

    if (modalEntrega) {
        const fecharModalEntrega = () => { modalEntrega.style.display = 'none'; };
        modalEntrega.querySelectorAll('.close-button').forEach(btn => btn.addEventListener('click', fecharModalEntrega));
    }

    if (formEntrega) {
        formEntrega.addEventListener('submit', async function(event) {
             event.preventDefault();
             const formData = new FormData(formEntrega);
             const dados = Object.fromEntries(formData.entries());

             let quantidadeEntregueNum;
             const max = parseFloat(inputQtdEntrega.max); 
             
             try {
                quantidadeEntregueNum = parseBrazilianFloat(dados.quantidade_entregue);
                
                 if (quantidadeEntregueNum <= 0 || quantidadeEntregueNum > max) {
                    throw new Error(`Quantidade inválida. Deve ser maior que 0 e no máximo ${max.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.`);
                 }
             } catch(e) {
                 showNotification(e.message, 'error');
                 return;
             }

             if (!dados.data_entrega) { showNotification("Data da entrega é obrigatória.", "error"); return; }
             if (!dados.nota_fiscal || dados.nota_fiscal.trim() === "") { showNotification("Número da Nota Fiscal/Documento é obrigatório.", "error"); return; }

            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Confirmando...';

            try {
                const response = await fetch(`/api/pedidos/${idPedidoParaEntrega}/registrar-entrega`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        quantidade: quantidadeEntregueNum.toFixed(2), 
                        data_entrega: dados.data_entrega,
                        nota_fiscal: dados.nota_fiscal
                    })
                });
                
                const resultado = await response.json();
                
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao registrar entrega`);

                const pedidoAtualizado = resultado; 
                
                reloadPageWithMessage(`Entrega de ${pedidoAtualizado.quantidade_entregue} registrada com sucesso!`, 'success');
                
            } catch (error) {
                showNotification(`Erro: ${error.message}`);
            } finally {
                submitButton.disabled = false;
                 submitButton.innerHTML = '<i class="fa-solid fa-truck-ramp-box"></i> Confirmar Entrega';
            }
        });
    } else {
        console.error("Formulário de registro de entrega não encontrado.");
    }

    const numPedidoInput = document.getElementById('numero-pedido-input');
    const empenhoInput = document.getElementById('empenho-input');
    const dataPedidoInput = document.getElementById('data_pedido_input');

    if (numPedidoInput) numPedidoInput.addEventListener('change', (e) => updateAocsField(e.target.dataset.campo, e.target.value));
    if (empenhoInput) empenhoInput.addEventListener('change', (e) => updateAocsField(e.target.dataset.campo, e.target.value));
    if (dataPedidoInput) dataPedidoInput.addEventListener('change', (e) => updateAocsDate(e.target.value));

    const modalEdicao = document.getElementById('modal-edicao-aocs');
    const btnAbrirModalEdicao = document.getElementById('btn-abrir-modal-edicao'); 
    const formEdicao = modalEdicao?.querySelector('#form-edicao-aocs');

    if (modalEdicao && btnAbrirModalEdicao && formEdicao) {
        btnAbrirModalEdicao.addEventListener('click', async () => {
             const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
             try {
                const response = await fetch(`/api/aocs/numero/${encodedAOCS}`); 
                const aocsDados = await response.json();
                if (!response.ok) throw new Error(aocsDados.detail || aocsDados.erro || 'Erro ao carregar dados da AOCS');

                formEdicao.elements['unidade_requisitante'].value = aocsDados.unidade_requisitante_nome || '';
                formEdicao.elements['justificativa'].value = aocsDados.justificativa || '';
                formEdicao.elements['info_orcamentaria'].value = aocsDados.dotacao_info_orcamentaria || ''; 
                formEdicao.elements['local_entrega'].value = aocsDados.local_entrega_descricao || ''; 
                formEdicao.elements['agente_responsavel'].value = aocsDados.agente_responsavel_nome || ''; 

                modalEdicao.style.display = 'flex';
            } catch (error) {
                showNotification(`Erro ao carregar dados para edição: ${error.message}`, 'error');
            }
        });

        const fecharModalEdicao = () => { modalEdicao.style.display = 'none'; };
        modalEdicao.querySelectorAll('.close-button').forEach(btn => btn.addEventListener('click', fecharModalEdicao));

        formEdicao.addEventListener('submit', async function(event) {
            event.preventDefault();
            const dadosParaSalvar = Object.fromEntries(new FormData(formEdicao).entries());
            const payload = {
                unidade_requisitante_nome: dadosParaSalvar.unidade_requisitante,
                justificativa: dadosParaSalvar.justificativa,
                dotacao_info_orcamentaria: dadosParaSalvar.info_orcamentaria,
                local_entrega_descricao: dadosParaSalvar.local_entrega,
                agente_responsavel_nome: dadosParaSalvar.agente_responsavel
            };

            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';

            const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
            try {
                 const getResponse = await fetch(`/api/aocs/numero/${encodedAOCS}`);
                 const aocsData = await getResponse.json();
                 if (!getResponse.ok) throw new Error("AOCS não encontrada para obter ID.");
                 const aocsId = aocsData.id;

                const response = await fetch(`/api/aocs/${aocsId}`, { 
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload) 
                });
                const resultado = await response.json();
                
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao salvar alterações`);
                
                const aocsAtualizada = resultado;

                reloadPageWithMessage(`Dados da AOCS ${aocsAtualizada.numero_aocs} atualizados!`, 'success');
            } catch (error) {
                showNotification(`Erro ao salvar: ${error.message}`, 'error');
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Alterações';
            }
        });
    } else {
        console.error("Elementos do modal de edição da AOCS não foram completamente encontrados.");
    }

    const formAnexos = document.getElementById('form-anexos'); 
    const tipoDocumentoSelectAnexo = formAnexos?.querySelector('#tipo_documento_select');
    const tipoDocumentoNovoInputAnexo = formAnexos?.querySelector('#tipo_documento_novo');
    const anexoFileInput = formAnexos?.querySelector('#file'); 

    if (formAnexos && tipoDocumentoSelectAnexo && tipoDocumentoNovoInputAnexo && anexoFileInput) {
        tipoDocumentoSelectAnexo.addEventListener('change', function() {
            const isNovo = this.value === 'NOVO';
            tipoDocumentoNovoInputAnexo.style.display = isNovo ? 'block' : 'none';
            tipoDocumentoNovoInputAnexo.required = isNovo;
            if (!isNovo) tipoDocumentoNovoInputAnexo.value = '';
        });

        formAnexos.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(formAnexos);
            const submitButton = this.querySelector('button[type="submit"]');

            if (!anexoFileInput.files || anexoFileInput.files.length === 0) {
                 showNotification("Selecione um arquivo.", "error"); return;
            }
            const tipoDoc = formData.get('tipo_documento');
            const novoTipo = formData.get('tipo_documento_novo');
             if (tipoDoc === 'NOVO' && (!novoTipo || novoTipo.trim() === '')) {
                 showNotification("Informe o nome do novo tipo.", "error"); return;
            }
            if (!tipoDoc && tipoDoc !== 'NOVO') { 
                 showNotification("Selecione ou crie um tipo.", "error"); return;
            }

            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...';

            try {
                const response = await fetch(formAnexos.action, { method: 'POST', body: formData });
                
                 if (response.status === 204) {
                     formAnexos.reset();
                     if(tipoDocumentoNovoInputAnexo) tipoDocumentoNovoInputAnexo.style.display = 'none';
                     reloadPageWithMessage('Anexo enviado com sucesso!', 'success');
                     return;
                 }
                 
                const resultado = await response.json(); 
                
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status}`);

                formAnexos.reset();
                 if(tipoDocumentoNovoInputAnexo) tipoDocumentoNovoInputAnexo.style.display = 'none';
                reloadPageWithMessage('Anexo enviado com sucesso!', 'success');

            } catch (error) {
                showNotification(`Erro ao enviar anexo: ${error.message}`, 'error');
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-upload"></i> Enviar Anexo';
            }
        });
    } else {
         console.error("Elementos do formulário de anexos não encontrados.");
    }

    window.excluirAnexo = async function(idAnexo, nomeOriginal) {
         if (!confirm(`Tem certeza que deseja excluir o anexo "${nomeOriginal}"?`)) return;
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

    const btnExcluirAOCS = document.getElementById('btn-excluir-aocs'); 
    if (btnExcluirAOCS) {
        btnExcluirAOCS.addEventListener('click', async function() {
            if (!confirm(`ATENÇÃO: Ação irreversível!\n\nExcluir a AOCS nº ${numeroAOCSGlobal} irá apagar todos os registos de entrega associados.\nDeseja continuar?`)) return;

            const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
            try {
                 const getResponse = await fetch(`/api/aocs/numero/${encodedAOCS}`);
                 const aocsData = await getResponse.json();
                 if (!getResponse.ok) throw new Error("AOCS não encontrada para obter ID.");
                 const aocsId = aocsData.id;

                const response = await fetch(`/api/aocs/${aocsId}`, { method: 'DELETE' }); 

                if (response.status === 204) { 
                    sessionStorage.setItem('notificationMessage', `AOCS ${numeroAOCSGlobal} excluída com sucesso.`);
                    sessionStorage.setItem('notificationType', 'success');
                    window.location.href = document.querySelector('.back-link').href; 
                    return;
                }
                
                const resultado = await response.json();
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao excluir AOCS');
                 
                 sessionStorage.setItem('notificationMessage', resultado.mensagem || `AOCS ${numeroAOCSGlobal} excluída.`);
                 sessionStorage.setItem('notificationType', 'success');
                 window.location.href = document.querySelector('.back-link').href;


            } catch (error) {
                showNotification(`Erro ao excluir AOCS: ${error.message}`, 'error');
            }
        });
    }

     window.addEventListener('click', (event) => {
         if (modalEdicao && event.target == modalEdicao) modalEdicao.style.display = 'none';
         if (modalEntrega && event.target == modalEntrega) modalEntrega.style.display = 'none';
     });

});