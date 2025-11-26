document.addEventListener('DOMContentLoaded', function() {

    // --- Elementos Globais ---
    const notificationArea = document.querySelector('.main-content #notification-area');
    let idPedidoParaEntrega = null;
    let listasCarregadas = false; // Cache para não buscar listas toda vez

    // --- Inicialização de Mensagens (Pós-Reload) ---
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType') || 'success');
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    // --- Funções Auxiliares ---

    function showNotification(message, type = 'error') {
        if (!notificationArea) { alert(message); return; }
        
        notificationArea.innerHTML = '';
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationArea.prepend(notification); 
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.addEventListener('transitionend', () => notification.remove());
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

    // --- FUNÇÃO DE ATUALIZAÇÃO GENÉRICA (Para Data, Número e Empenho) ---
    async function updateAocsField(campo, valor) {
        // Usa o ID global da AOCS para maior segurança
        const aocsId = window.aocsDadosAtuais ? window.aocsDadosAtuais.id : null;
        
        if (!aocsId) {
            showNotification("Erro: ID da AOCS não encontrado. Recarregue a página.", "error");
            return;
        }

        try {
            // Payload dinâmico: { "data_criacao": "2023-01-01" } ou { "numero_pedido": "123" }
            const payload = {};
            payload[campo] = valor;

            const response = await fetch(`/api/aocs/${aocsId}`, { 
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || err.erro || `Erro ${response.status}`);
            }
            
            showNotification('Atualizado com sucesso.', 'success');
        } catch (error) {
            showNotification(`Erro ao atualizar: ${error.message}`, 'error');
        }
    }

    // --- LISTENERS DOS INPUTS DE EDIÇÃO RÁPIDA ---
    const numPedidoInput = document.getElementById('numero-pedido-input');
    const empenhoInput = document.getElementById('empenho-input');
    const dataPedidoInput = document.getElementById('data_pedido_input');

    if (numPedidoInput) {
        numPedidoInput.addEventListener('change', (e) => updateAocsField('numero_pedido', e.target.value));
    }
    
    if (empenhoInput) {
        empenhoInput.addEventListener('change', (e) => updateAocsField('empenho', e.target.value));
    }
    
    // [CORREÇÃO DA DATA] Agora usa a mesma função genérica, apontando para 'data_criacao'
    if (dataPedidoInput) {
        dataPedidoInput.addEventListener('change', (e) => updateAocsField('data_criacao', e.target.value));
    }

    // --- CARREGAMENTO DE DROPDOWNS (Para o Modal de Edição) ---
    async function carregarListasDropdowns() {
        if (listasCarregadas) return; 

        try {
            const [unidades, locais, agentes, dotacoes] = await Promise.all([
                fetch('/api/tabelas-sistema/unidade-requisitante').then(r => r.json()),
                fetch('/api/tabelas-sistema/local-entrega').then(r => r.json()),
                fetch('/api/tabelas-sistema/agente-responsavel').then(r => r.json()),
                fetch('/api/tabelas-sistema/dotacao').then(r => r.json())
            ]);

            const popularSelect = (id, dados, campoTexto) => {
                const select = document.getElementById(id);
                if (!select) return;
                
                select.innerHTML = '<option value="" disabled selected>Selecione...</option>';
                
                dados.forEach(item => {
                    const valor = item[campoTexto] || item.nome || item.descricao || '---';
                    const option = document.createElement('option');
                    option.value = valor;
                    option.textContent = valor;
                    select.appendChild(option);
                });
            };

            popularSelect('edit-aocs-unidade', unidades, 'nome');
            popularSelect('edit-aocs-local-entrega', locais, 'descricao');
            popularSelect('edit-aocs-responsavel', agentes, 'nome');
            popularSelect('edit-aocs-orcamento', dotacoes, 'info_orcamentaria');

            listasCarregadas = true;

        } catch (error) {
            console.error("Erro ao carregar listas:", error);
            showNotification("Erro ao carregar opções dos formulários.", "error");
        }
    }

    // --- MODAL: EDIÇÃO DE DADOS DA AOCS ---
    const modalEdicao = document.getElementById('modal-edicao-aocs');
    const btnAbrirModalEdicao = document.getElementById('btn-abrir-modal-edicao'); 
    const formEdicao = modalEdicao?.querySelector('#form-edicao-aocs');

    if (modalEdicao && btnAbrirModalEdicao && formEdicao) {
        
        btnAbrirModalEdicao.addEventListener('click', async () => {
            await carregarListasDropdowns(); // Garante que as opções existam

            const dados = window.aocsDadosAtuais; // Pega dados atuais da tela
            
            if (dados) {
                // Preenche os campos
                const setVal = (name, val) => {
                    if (formEdicao.elements[name]) formEdicao.elements[name].value = val;
                };

                setVal('unidade_requisitante', dados.unidade_requisitante);
                setVal('justificativa', dados.justificativa);
                setVal('info_orcamentaria', dados.info_orcamentaria);
                setVal('local_entrega', dados.local_entrega);
                setVal('agente_responsavel', dados.agente_responsavel);

                modalEdicao.style.display = 'flex';
            } else {
                showNotification("Erro: Dados da AOCS não carregados.", "error");
            }
        });

        modalEdicao.querySelectorAll('.close-button').forEach(btn => {
            btn.addEventListener('click', () => modalEdicao.style.display = 'none');
        });

        formEdicao.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(formEdicao);
            
            const payload = {
                unidade_requisitante_nome: formData.get('unidade_requisitante'),
                justificativa: formData.get('justificativa'),
                dotacao_info_orcamentaria: formData.get('info_orcamentaria'),
                local_entrega_descricao: formData.get('local_entrega'),
                agente_responsavel_nome: formData.get('agente_responsavel')
            };

            const submitButton = this.querySelector('button[type="submit"]');
            if(submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';
            }

            try {
                const aocsId = window.aocsDadosAtuais.id;
                const response = await fetch(`/api/aocs/${aocsId}`, { 
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload) 
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Erro ao salvar');
                }
                reloadPageWithMessage('Dados da AOCS atualizados!', 'success');
            } catch (error) {
                showNotification(`Erro ao salvar: ${error.message}`, 'error');
            } finally {
                if(submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Alterações';
                }
            }
        });
    }

    // --- MODAL: REGISTRAR ENTREGA ---
    const modalEntrega = document.getElementById('modal-registrar-entrega');
    const formEntrega = modalEntrega?.querySelector('#form-registrar-entrega');
    const inputQtdEntrega = modalEntrega?.querySelector('#quantidade_entregue');
    const descModalEntrega = modalEntrega?.querySelector('#entrega-item-descricao');
    const saldoModalEntrega = modalEntrega?.querySelector('#entrega-saldo-restante');
    const dataEntregaInput = modalEntrega?.querySelector('#data_entrega'); 

    window.abrirModalEntrega = function(idPedido, descricao, saldo) {
        if (!modalEntrega) return;
        idPedidoParaEntrega = idPedido;
        
        if(descModalEntrega) descModalEntrega.textContent = descricao;
        
        const saldoFmt = saldo.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        if(saldoModalEntrega) saldoModalEntrega.textContent = saldoFmt;
        
        if(inputQtdEntrega) {
            inputQtdEntrega.value = saldoFmt;
            inputQtdEntrega.max = saldo;
        }
        if(dataEntregaInput) dataEntregaInput.valueAsDate = new Date();
        
        formEntrega.reset();
        if(inputQtdEntrega) inputQtdEntrega.value = saldoFmt;
        
        modalEntrega.style.display = 'flex';
        if(inputQtdEntrega) { inputQtdEntrega.focus(); inputQtdEntrega.select(); }
    }

    if (modalEntrega) {
        modalEntrega.querySelectorAll('.close-button').forEach(btn => {
            btn.addEventListener('click', () => modalEntrega.style.display = 'none');
        });
    }

    if (formEntrega) {
        formEntrega.addEventListener('submit', async function(event) {
             event.preventDefault();
             const dados = Object.fromEntries(new FormData(formEntrega).entries());

             let qtdNum;
             try {
                qtdNum = parseBrazilianFloat(dados.quantidade_entregue);
                if (qtdNum <= 0) throw new Error("Quantidade deve ser maior que zero.");
             } catch(e) {
                 showNotification(e.message, 'error');
                 return;
             }

             if (!dados.data_entrega) { showNotification("Data obrigatória.", "error"); return; }
             if (!dados.nota_fiscal) { showNotification("Nota Fiscal obrigatória.", "error"); return; }

            const btn = this.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ...';

            try {
                const response = await fetch(`/api/pedidos/${idPedidoParaEntrega}/registrar-entrega`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        quantidade: qtdNum.toFixed(2), 
                        data_entrega: dados.data_entrega,
                        nota_fiscal: dados.nota_fiscal
                    })
                });
                
                if (!response.ok) {
                    const res = await response.json();
                    throw new Error(res.detail || 'Erro ao registrar entrega');
                }
                reloadPageWithMessage('Entrega registrada com sucesso!', 'success');
            } catch (error) {
                showNotification(`Erro: ${error.message}`);
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Confirmar';
            }
        });
    }

    // --- FORMULÁRIO DE ANEXOS ---
    const formAnexos = document.getElementById('form-anexos'); 
    if (formAnexos) {
        const tipoSelect = formAnexos.querySelector('#tipo_documento_select');
        const tipoNovo = formAnexos.querySelector('#tipo_documento_novo');
        const fileInput = formAnexos.querySelector('#file'); 

        if (tipoSelect && tipoNovo) {
            tipoSelect.addEventListener('change', function() {
                const isNovo = this.value === 'NOVO';
                tipoNovo.style.display = isNovo ? 'block' : 'none';
                tipoNovo.required = isNovo;
            });
        }

        formAnexos.addEventListener('submit', async function(e) {
            e.preventDefault();
            if (!fileInput.files.length) { showNotification("Selecione um arquivo.", "error"); return; }
            
            const formData = new FormData(formAnexos);
            const btn = this.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = 'Enviando...';

            try {
                const response = await fetch(formAnexos.action, { method: 'POST', body: formData });
                if (!response.ok) {
                    const res = await response.json();
                    throw new Error(res.detail || 'Erro ao enviar');
                }
                reloadPageWithMessage('Anexo enviado!', 'success');
            } catch (error) {
                showNotification(error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Enviar Anexo';
            }
        });
    }

    window.excluirAnexo = async function(idAnexo, nomeOriginal) {
         if (!confirm(`Excluir o anexo "${nomeOriginal}"?`)) return;
        try {
            const response = await fetch(`/api/anexos/${idAnexo}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('Erro ao excluir');
            reloadPageWithMessage("Anexo excluído.", 'success');
        } catch (error) {
            showNotification(error.message);
        }
    }

    // --- EXCLUIR AOCS ---
    const btnExcluirAOCS = document.getElementById('btn-excluir-aocs'); 
    if (btnExcluirAOCS) {
        btnExcluirAOCS.addEventListener('click', async function() {
            if (!confirm(`ATENÇÃO: Excluir a AOCS ${numeroAOCSGlobal} apagará tudo. Continuar?`)) return;

            try {
                const aocsId = window.aocsDadosAtuais.id;
                const response = await fetch(`/api/aocs/${aocsId}`, { method: 'DELETE' }); 
                if (!response.ok) throw new Error('Erro ao excluir');
                
                window.location.href = document.querySelector('.back-link').href; 
            } catch (error) {
                showNotification(error.message, 'error');
            }
        });
    }

    // Fecha modais ao clicar fora
    window.addEventListener('click', (event) => {
        if (modalEdicao && event.target == modalEdicao) modalEdicao.style.display = 'none';
        if (modalEntrega && event.target == modalEntrega) modalEntrega.style.display = 'none';
    });
});

// ... código existente ...

    // --- LÓGICA DE ENTREGA EM LOTE ---
    const modalLote = document.getElementById('modal-entrega-lote');
    const btnLote = document.getElementById('btn-entrega-lote');
    const formLote = document.getElementById('form-entrega-lote');

    if (btnLote && modalLote) {
        btnLote.addEventListener('click', () => {
            // Define data de hoje como padrão
            const inputData = modalLote.querySelector('#lote_data_entrega');
            if(inputData) inputData.valueAsDate = new Date();
            
            modalLote.style.display = 'flex';
        });

        modalLote.querySelectorAll('.close-button').forEach(btn => {
            btn.addEventListener('click', () => modalLote.style.display = 'none');
        });
    }

    if (formLote) {
        formLote.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const dataEntrega = formLote.querySelector('#lote_data_entrega').value;
            const notaFiscal = formLote.querySelector('#lote_nota_fiscal').value;
            
            if (!dataEntrega || !notaFiscal) {
                showNotification("Preencha Data e Nota Fiscal.", "error");
                return;
            }

            // Coleta os itens marcados
            const itensParaEnviar = [];
            const rows = formLote.querySelectorAll('.item-row');
            
            rows.forEach(row => {
                const check = row.querySelector('.item-check');
                const inputQtd = row.querySelector('.item-qtd');
                const idPedido = row.dataset.id;
                
                if (check && check.checked && inputQtd) {
                    const qtd = parseFloat(inputQtd.value);
                    if (qtd > 0) {
                        itensParaEnviar.push({
                            id_pedido: parseInt(idPedido),
                            quantidade: qtd
                        });
                    }
                }
            });

            if (itensParaEnviar.length === 0) {
                showNotification("Nenhum item selecionado para entrega.", "warning");
                return;
            }

            // Monta Payload
            const payload = {
                data_entrega: dataEntrega,
                nota_fiscal: notaFiscal,
                itens: itensParaEnviar
            };

            const btn = formLote.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = 'Processando...';

            try {
                const response = await fetch('/api/pedidos/entrega-lote', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Erro ao processar lote');
                }

                reloadPageWithMessage('Entrega em lote registrada com sucesso!', 'success');

            } catch (error) {
                showNotification(`Erro: ${error.message}`, 'error');
                btn.disabled = false;
                btn.innerHTML = 'Tentar Novamente';
            }
        });
    }