document.addEventListener('DOMContentLoaded', function() {

    // --- ESTADO GLOBAL E REFERÊNCIAS ---
    // numeroAOCSGlobal é definido no HTML
    let idPedidoParaEntrega = null;

    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');

    // --- FUNÇÕES DE UI ---
    function showNotification(message, type = 'error') {
        if (!notificationArea) { console.error("Notification area not found!"); return; }
        // Remove notificação flash inicial se houver
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

    function reloadPageWithMessage(message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        location.reload();
    }

    // Exibir notificação após redirecionamento/reload
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType') || 'success');
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    // --- FUNÇÕES DE LÓGICA (API CALLS) ---
    async function updateAocsField(campo, valor) {
        // Codifica o numeroAOCS para o URL (caso contenha '/')
        const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
        try {
            // API PUT /api/aocs/{numero_aocs}/dados-gerais
            const response = await fetch(`/api/aocs/${encodedAOCS}/dados-gerais`, { // Usa a rota correta
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [campo]: valor })
            });
            const resultado = await response.json();
             if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao atualizar campo.');
            showNotification(resultado.mensagem || 'Campo atualizado.', 'success');
        } catch (error) {
            showNotification(`Erro ao atualizar ${campo}: ${error.message}`, 'error');
            // Reverter o valor no input se desejar
        }
    }

    async function updateAocsDate(data) {
        const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
         try {
             // API PUT /api/aocs/{numero_aocs}/data (ou usar /api/aocs/{id} ?)
             // Ajuste o endpoint se a API usar o ID em vez do número para atualização de data
            const response = await fetch(`/api/aocs/${encodedAOCS}/data`, { // Verificar se esta rota existe na API
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data_criacao: data }) // A API espera 'data_criacao' ?
            });
            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao atualizar data.');
            showNotification(resultado.mensagem || 'Data atualizada.', 'success');
             // Recarregar pode ser necessário se a data afeta cálculos na página (dias pendentes)
             // reloadPageWithMessage(resultado.mensagem || 'Data atualizada.', 'success');
        } catch (error) {
            showNotification(`Erro ao atualizar data: ${error.message}`, 'error');
            // Reverter o valor no input se desejar
        }
    }

    // --- LÓGICA DO MODAL DE ENTREGA ---
    const modalEntrega = document.getElementById('modal-registrar-entrega');
    const formEntrega = modalEntrega?.querySelector('#form-registrar-entrega');
    // Corrigindo seletores para pegar elementos pelo ID correto
    const inputQtdEntrega = modalEntrega?.querySelector('#quantidade_entregue');
    const descModalEntrega = modalEntrega?.querySelector('#entrega-item-descricao');
    const saldoModalEntrega = modalEntrega?.querySelector('#entrega-saldo-restante');
    const dataEntregaInput = modalEntrega?.querySelector('#data_entrega'); // Referência à data

    // Torna a função globalmente acessível
    window.abrirModalEntrega = function(idPedido, descricao, saldo) {
        if (!modalEntrega || !inputQtdEntrega || !descModalEntrega || !saldoModalEntrega || !dataEntregaInput) {
            console.error("Elementos do modal de entrega não encontrados!");
            showNotification("Erro ao abrir modal de entrega.", "error");
            return;
        }
        idPedidoParaEntrega = idPedido;
        descModalEntrega.textContent = descricao; // Apenas a descrição
        saldoModalEntrega.textContent = saldo.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); // Formata saldo
        // Define o valor inicial e máximo do input de quantidade
        inputQtdEntrega.value = saldo.toFixed(2).replace('.', ','); // Define valor inicial formatado
        inputQtdEntrega.max = saldo; // Define o máximo permitido pelo HTML5
        inputQtdEntrega.placeholder = saldo.toFixed(2).replace('.', ','); // Placeholder como guia
        dataEntregaInput.valueAsDate = new Date(); // Pré-preenche data com hoje
        formEntrega.reset(); // Limpa outros campos como NF e Obs
        // Re-aplica os valores após o reset
        formEntrega.elements['item_pedido_id'].value = idPedido;
        formEntrega.elements['quantidade_entregue'].value = saldo.toFixed(2).replace('.', ',');


        modalEntrega.style.display = 'flex';
        inputQtdEntrega.focus();
        inputQtdEntrega.select();
    }

    if (modalEntrega) {
        const fecharModalEntrega = () => { modalEntrega.style.display = 'none'; };
        modalEntrega.querySelectorAll('.close-button').forEach(btn => btn.addEventListener('click', fecharModalEntrega));
        // Listener de clique fora já é tratado globalmente no final
    }

    if (formEntrega) {
        formEntrega.addEventListener('submit', async function(event) {
             event.preventDefault();
             const formData = new FormData(formEntrega);
             const dados = Object.fromEntries(formData.entries());

             // Validação da Quantidade
             let quantidadeEntregueNum;
             try {
                const qtdStr = String(dados.quantidade_entregue).replace('.', '').replace(',', '.');
                quantidadeEntregueNum = parseFloat(qtdStr);
                const max = parseFloat(inputQtdEntrega.max); // Pega o max definido ao abrir o modal
                 if (isNaN(quantidadeEntregueNum) || quantidadeEntregueNum <= 0 || quantidadeEntregueNum > max) {
                    throw new Error(`Quantidade inválida. Deve ser maior que 0 e no máximo ${max.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.`);
                 }
             } catch(e) {
                 showNotification(e.message, 'error');
                 return;
             }

             // Validação da Data e NF
             if (!dados.data_entrega) { showNotification("Data da entrega é obrigatória.", "error"); return; }
             if (!dados.nota_fiscal || dados.nota_fiscal.trim() === "") { showNotification("Número da Nota Fiscal/Documento é obrigatório.", "error"); return; }


            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Confirmando...';

            try {
                // API PUT /api/pedidos/{id}/registrar-entrega (Verificar se este é o endpoint correto no seu pedido_router.py)
                // Assumindo que a API espera apenas a quantidade entregue *agora*
                const response = await fetch(`/api/pedidos/${idPedidoParaEntrega}/registrar-entrega`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    // Envia apenas a quantidade que está sendo entregue AGORA
                    body: JSON.stringify({
                        quantidade: quantidadeEntregueNum.toFixed(2) // Envia como string formatada
                        // A API no backend deve SOMAR esta quantidade à existente
                    })
                    // Se a API esperar a quantidade TOTAL entregue, o body seria:
                    // body: JSON.stringify({ quantidade_entregue: novaQuantidadeTotalCalculadaAqui })
                });
                const resultado = await response.json();
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao registrar entrega');

                // Opcional: Registrar os dados de NF e Obs em outra tabela/API se necessário
                // console.log("Dados adicionais:", { data: dados.data_entrega, nf: dados.nota_fiscal, obs: dados.observacao });

                reloadPageWithMessage(resultado.mensagem || 'Entrega registrada com sucesso!', 'success');
            } catch (error) {
                showNotification(`Erro: ${error.message}`);
                submitButton.disabled = false;
                 submitButton.innerHTML = '<i class="fa-solid fa-truck-ramp-box"></i> Confirmar Entrega';
            }
        });
    } else {
        console.error("Formulário de registro de entrega não encontrado.");
    }

    // --- LÓGICA DOS CAMPOS INDIVIDUAIS (Status/Dados) ---
    // Adiciona listeners aos inputs no _pedido_dados_status.html
    const numPedidoInput = document.getElementById('numero-pedido-input');
    const empenhoInput = document.getElementById('empenho-input');
    const dataPedidoInput = document.getElementById('data_pedido_input');

    if (numPedidoInput) numPedidoInput.addEventListener('change', (e) => updateAocsField(e.target.dataset.campo, e.target.value));
    if (empenhoInput) empenhoInput.addEventListener('change', (e) => updateAocsField(e.target.dataset.campo, e.target.value));
    if (dataPedidoInput) dataPedidoInput.addEventListener('change', (e) => updateAocsDate(e.target.value));

    // --- LÓGICA DO MODAL DE EDIÇÃO DA AOCS ---
    const modalEdicao = document.getElementById('modal-edicao-aocs');
    const btnAbrirModalEdicao = document.getElementById('btn-abrir-modal-edicao'); // Botão no Header
    const formEdicao = modalEdicao?.querySelector('#form-edicao-aocs');

    if (modalEdicao && btnAbrirModalEdicao && formEdicao) {
        btnAbrirModalEdicao.addEventListener('click', async () => {
             const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
             try {
                // API GET /api/aocs/numero/{numero_aocs}
                const response = await fetch(`/api/aocs/numero/${encodedAOCS}`); // Usar rota por número
                const aocsDados = await response.json();
                if (!response.ok) throw new Error(aocsDados.detail || aocsDados.erro || 'Erro ao carregar dados da AOCS');

                // Preenche o formulário (precisa buscar os NOMES/DESCRICOES das FKs, não só os IDs)
                // A API /api/aocs/numero/{numero_aocs} PRECISA retornar os nomes/descrições das entidades relacionadas
                // Exemplo: assumindo que a API retorna 'unidade_requisitante_nome', etc.
                formEdicao.elements['unidade_requisitante'].value = aocsDados.unidade_requisitante_nome || '';
                formEdicao.elements['justificativa'].value = aocsDados.justificativa || '';
                formEdicao.elements['info_orcamentaria'].value = aocsDados.dotacao_info_orcamentaria || ''; // Nome do campo da API
                formEdicao.elements['local_entrega'].value = aocsDados.local_entrega_descricao || ''; // Nome do campo da API
                formEdicao.elements['agente_responsavel'].value = aocsDados.agente_responsavel_nome || ''; // Nome do campo da API

                modalEdicao.style.display = 'flex';
            } catch (error) {
                showNotification(`Erro ao carregar dados para edição: ${error.message}`, 'error');
            }
        });

        const fecharModalEdicao = () => { modalEdicao.style.display = 'none'; };
        modalEdicao.querySelectorAll('.close-button').forEach(btn => btn.addEventListener('click', fecharModalEdicao));
        // Listener de clique fora já é tratado globalmente no final

        formEdicao.addEventListener('submit', async function(event) {
            event.preventDefault();
            const dadosParaSalvar = Object.fromEntries(new FormData(formEdicao).entries());
            // Renomeia os campos para corresponder ao AocsUpdateRequest (se necessário)
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
                // API PUT /api/aocs/{id} (Precisa buscar o ID primeiro ou criar rota PUT por número)
                // Assumindo que temos o ID da AOCS disponível (precisa ser passado do template ou buscado)
                // Vamos buscar o ID para usar a rota PUT padrão
                 const getResponse = await fetch(`/api/aocs/numero/${encodedAOCS}`);
                 const aocsData = await getResponse.json();
                 if (!getResponse.ok) throw new Error("AOCS não encontrada para obter ID.");
                 const aocsId = aocsData.id;

                const response = await fetch(`/api/aocs/${aocsId}`, { // Usa o ID
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload) // Envia o payload com nomes corretos
                });
                const resultado = await response.json();
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao salvar alterações');
                reloadPageWithMessage(resultado.mensagem || 'Dados da AOCS atualizados!', 'success');
            } catch (error) {
                showNotification(`Erro ao salvar: ${error.message}`, 'error');
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Alterações';
            }
        });
    } else {
        console.error("Elementos do modal de edição da AOCS não foram completamente encontrados.");
    }

    // --- LÓGICA DE ANEXOS ---
    const formAnexos = document.getElementById('form-anexos'); // ID adicionado no HTML
    const tipoDocumentoSelectAnexo = formAnexos?.querySelector('#tipo_documento_select');
    const tipoDocumentoNovoInputAnexo = formAnexos?.querySelector('#tipo_documento_novo');
    const anexoFileInput = formAnexos?.querySelector('#file'); // Corrigido ID/Name no HTML

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

            // Validações
            if (!anexoFileInput.files || anexoFileInput.files.length === 0) {
                 showNotification("Selecione um arquivo.", "error"); return;
            }
            const tipoDoc = formData.get('tipo_documento');
            const novoTipo = formData.get('tipo_documento_novo');
             if (tipoDoc === 'NOVO' && (!novoTipo || novoTipo.trim() === '')) {
                 showNotification("Informe o nome do novo tipo.", "error"); return;
            }
            if (!tipoDoc && tipoDoc !== 'NOVO') { // Permite 'NOVO' mesmo que vazio inicialmente
                 showNotification("Selecione ou crie um tipo.", "error"); return;
            }

            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...';

            try {
                // API POST /api/anexos/upload/
                const response = await fetch(formAnexos.action, { method: 'POST', body: formData });
                const resultado = await response.json(); // Tenta ler JSON
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status}`);

                formAnexos.reset();
                 if(tipoDocumentoNovoInputAnexo) tipoDocumentoNovoInputAnexo.style.display = 'none';
                reloadPageWithMessage(resultado.mensagem || 'Anexo enviado com sucesso!', 'success');

            } catch (error) {
                showNotification(`Erro ao enviar anexo: ${error.message}`, 'error');
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-upload"></i> Enviar Anexo';
            }
        });
    } else {
         console.error("Elementos do formulário de anexos não encontrados.");
    }

    // Função global para excluir anexo (chamada pelo onclick)
    window.excluirAnexo = async function(idAnexo, nomeOriginal) {
         if (!confirm(`Tem certeza que deseja excluir o anexo "${nomeOriginal}"?`)) return;
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

    // --- LÓGICA DE EXCLUSÃO DA AOCS ---
    const btnExcluirAOCS = document.getElementById('btn-excluir-aocs'); // Botão no Header
    if (btnExcluirAOCS) {
        btnExcluirAOCS.addEventListener('click', async function() {
            if (!confirm(`ATENÇÃO: Ação irreversível!\n\nExcluir a AOCS nº ${numeroAOCSGlobal} irá apagar todos os registos de entrega associados.\nDeseja continuar?`)) return;

            const encodedAOCS = encodeURIComponent(numeroAOCSGlobal);
            try {
                // API DELETE /api/aocs/{id} (Precisa buscar ID ou criar rota DELETE por número)
                // Buscando ID para usar rota DELETE padrão
                 const getResponse = await fetch(`/api/aocs/numero/${encodedAOCS}`);
                 const aocsData = await getResponse.json();
                 if (!getResponse.ok) throw new Error("AOCS não encontrada para obter ID.");
                 const aocsId = aocsData.id;

                const response = await fetch(`/api/aocs/${aocsId}`, { method: 'DELETE' }); // Usa ID

                if (response.status === 204) { // Sucesso
                    sessionStorage.setItem('notificationMessage', `AOCS ${numeroAOCSGlobal} excluída com sucesso.`);
                    sessionStorage.setItem('notificationType', 'success');
                    // Redireciona para o histórico de pedidos
                    window.location.href = document.querySelector('.back-link').href; // Pega URL do link Voltar
                    return;
                }
                // Tenta ler erro
                const resultado = await response.json();
                if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Erro ao excluir AOCS');
                 // Caso raro: 200 OK com mensagem
                 sessionStorage.setItem('notificationMessage', resultado.mensagem || `AOCS ${numeroAOCSGlobal} excluída.`);
                 sessionStorage.setItem('notificationType', 'success');
                 window.location.href = document.querySelector('.back-link').href;


            } catch (error) {
                showNotification(`Erro ao excluir AOCS: ${error.message}`, 'error');
            }
        });
    }

    // --- Listener global para fechar modais clicando fora ---
     window.addEventListener('click', (event) => {
         if (modalEdicao && event.target == modalEdicao) modalEdicao.style.display = 'none';
         if (modalEntrega && event.target == modalEntrega) modalEntrega.style.display = 'none';
     });

});