document.addEventListener('DOMContentLoaded', function() {

    let tabelaAtiva = null;
    let nomeExibicaoTabelaAtiva = null;

    const contentArea = document.getElementById('content-area');
    const tableTemplate = document.getElementById('table-template'); 
    const modal = document.getElementById('modal-item');
    const modalTitulo = document.getElementById('modal-titulo');
    const formItem = document.getElementById('form-item');
    const inputNomeItem = document.getElementById('item-nome');
    const notificationArea = document.querySelector('.main-content #notification-area');
    let idItemEmEdicao = null;

    function showNotification(message, type = 'error') {
        if (!notificationArea) return;
        const initialFlash = notificationArea.querySelector('.notification.flash');
        if(initialFlash) initialFlash.remove();

        const existing = notificationArea.querySelector('.notification:not(.flash)');
        if (existing) existing.remove();

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

    const fecharModal = () => {
        if (!modal) return; 
        modal.style.display = 'none';
        formItem.reset();
        idItemEmEdicao = null;
    };

    async function carregarTabela(nomeTabela, nomeExibicao) {
        tabelaAtiva = nomeTabela;
        nomeExibicaoTabelaAtiva = nomeExibicao;

        contentArea.innerHTML = '';
        if (!tableTemplate) {
            contentArea.innerHTML = '<div class="notification error">Erro: Template da tabela não encontrado.</div>';
            return;
        }
        const clone = tableTemplate.content.cloneNode(true);
        contentArea.appendChild(clone);

        const tableTitle = contentArea.querySelector('#table-title');
        const btnAddNewItem = contentArea.querySelector('#btn-add-new-item');
        const tableBody = contentArea.querySelector('#table-body');

        if (!tableTitle || !btnAddNewItem || !tableBody) {
             contentArea.innerHTML = '<div class="notification error">Erro: Elementos internos do template da tabela não encontrados.</div>';
             return;
        }

        tableTitle.textContent = `Gerenciando: ${nomeExibicao}`;
        btnAddNewItem.addEventListener('click', abrirModalParaNovo); 
        tableBody.innerHTML = '<tr><td colspan="3">Carregando...</td></tr>';

        try {
            const response = await fetch(`/api/tabelas-sistema/${nomeTabela}`);
            const itens = await response.json();

            if (!response.ok) throw new Error(itens.detail || itens.erro || 'Erro desconhecido da API');

            tableBody.innerHTML = '';
            if (itens.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="3"><div class="empty-state mini"><p>Nenhum item cadastrado.</p></div></td></tr>';
                return;
            }

            itens.forEach(item => {
                const tr = document.createElement('tr');
                const nomeEscapado = JSON.stringify(item.nome); 
                tr.innerHTML = `
                    <td>${item.id}</td>
                    <td>${item.nome}</td>
                    <td class="actions-cell">
                        <button class="btn-link-action" onclick="abrirModalParaEditar(${item.id}, ${nomeEscapado})"><i class="fa-solid fa-pencil"></i> Editar</button>
                        <button class="btn-link-action red" onclick="excluirItem(${item.id})"><i class="fa-solid fa-trash-can"></i> Excluir</button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="3"><div class="notification error">Erro ao carregar dados: ${error.message}</div></td></tr>`;
        }
    }

    function abrirModalParaNovo() {
        if (!modal || !modalTitulo || !formItem) return; 
        idItemEmEdicao = null;
        modalTitulo.textContent = `Adicionar Novo em ${nomeExibicaoTabelaAtiva}`;
        formItem.reset();
        modal.style.display = 'flex';
    }

    window.abrirModalParaEditar = (id, nomeAtual) => {
        if (!modal || !modalTitulo || !inputNomeItem) return; 
        idItemEmEdicao = id;
        modalTitulo.textContent = `Editar Item em ${nomeExibicaoTabelaAtiva}`;
        inputNomeItem.value = nomeAtual; 
        modal.style.display = 'flex';
    }

    if (formItem) {
        formItem.addEventListener('submit', async function(event) {
            event.preventDefault();
            const nome = inputNomeItem.value.trim();

            if (!nome) { showNotification('O campo Nome é obrigatório.'); return; }
            if (!tabelaAtiva) { showNotification('Nenhuma tabela ativa selecionada.'); return; } 

            const url = idItemEmEdicao
                ? `/api/tabelas-sistema/${tabelaAtiva}/${idItemEmEdicao}` 
                : `/api/tabelas-sistema/${tabelaAtiva}`; 
            const method = idItemEmEdicao ? 'PUT' : 'POST';

            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Salvando...`;

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nome: nome })
                });
                
                if (!response.ok) {
                    const erro = await response.json();
                    throw new Error(erro.detail || erro.erro || `Erro ${response.status} na API`);
                }
                
                const item = await response.json();

                const acao = idItemEmEdicao ? 'atualizado' : 'criado';
                showNotification(`Item '${item.nome}' ${acao} com sucesso!`, 'success');

                fecharModal();
                if(tabelaAtiva) carregarTabela(tabelaAtiva, nomeExibicaoTabelaAtiva);

            } catch (error) {
                showNotification(`Erro: ${error.message}`);
            } finally {
                submitButton.disabled = false;
                 submitButton.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Salvar`;
            }
        });
    } else {
        console.error("Formulário do modal genérico não encontrado.");
    }

    window.excluirItem = async (id) => {
        if (!confirm('Tem certeza que deseja excluir este item? A ação não pode ser desfeita e pode falhar se o item estiver em uso.')) return;
        if (!tabelaAtiva) { showNotification('Nenhuma tabela ativa selecionada.'); return; } 

        try {
            const response = await fetch(`/api/tabelas-sistema/${tabelaAtiva}/${id}`, {
                method: 'DELETE'
            });

            if (response.status === 204) {
                 showNotification('Item excluído com sucesso!', 'success');
            } else {
                 const resultado = await response.json();
                 if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao excluir`);
                 showNotification(resultado.mensagem || 'Item excluído.', 'success');
            }

            if(tabelaAtiva) carregarTabela(tabelaAtiva, nomeExibicaoTabelaAtiva);

        } catch (error) {
            showNotification(`Erro ao excluir: ${error.message}`);
        }
    }

    document.querySelectorAll('.management-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.management-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            const nomeTabela = link.dataset.tabela;
            const nomeExibicao = link.dataset.nomeExibicao;
            carregarTabela(nomeTabela, nomeExibicao);
        });
    });

    const btnFecharModal = document.getElementById('btn-fechar-modal');
    const btnCancelarModal = document.getElementById('btn-cancelar-modal');
    if(btnFecharModal) btnFecharModal.addEventListener('click', fecharModal);
    if(btnCancelarModal) btnCancelarModal.addEventListener('click', fecharModal);

    window.addEventListener('click', (event) => {
        if (modal && event.target == modal) fecharModal();
    });

});