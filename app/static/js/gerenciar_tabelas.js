document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENTOS DA NAVEGAÇÃO E TABELA ---
    const buttons = document.querySelectorAll('.nav-btn');
    const emptyState = document.getElementById('empty-state');
    const tabelaContainer = document.getElementById('tabela-container');
    const tableBody = document.getElementById('tableBody');
    const pageTitle = document.getElementById('pageTitle');
    const btnNovoItem = document.getElementById('btnNovoItem');

    // --- ELEMENTOS DO MODAL (Baseado no seu upload) ---
    const modal = document.getElementById('modal-item'); 
    const form = document.getElementById('form-item');
    const inputNome = document.getElementById('item-nome');
    const modalTitulo = document.getElementById('modal-titulo');
    const btnFechar = document.getElementById('btn-fechar-modal');
    const btnCancelar = document.getElementById('btn-cancelar-modal');

    // --- ESTADO DA APLICAÇÃO ---
    let currentTabela = null;
    let currentColuna = 'nome'; // Padrão, atualizado pelo botão
    let currentTitulo = '';

    // =========================================================================
    // 1. NAVEGAÇÃO (Troca de Tabelas)
    // =========================================================================
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Visual: destaca o botão clicado
            buttons.forEach(b => {
                b.classList.remove('btn-primary', 'active');
                b.classList.add('btn-light');
            });
            btn.classList.remove('btn-light');
            btn.classList.add('btn-primary', 'active');

            // Dados: captura configuração do botão
            currentTabela = btn.dataset.target;
            currentColuna = btn.dataset.coluna;
            currentTitulo = btn.textContent.trim();

            // UI: Atualiza títulos e mostra a tabela
            if (pageTitle) pageTitle.textContent = currentTitulo;
            if (emptyState) emptyState.style.display = 'none';
            if (tabelaContainer) tabelaContainer.style.display = 'block';

            // Carrega os dados
            console.log(`[UI] Carregando tabela: ${currentTabela}, Coluna chave: ${currentColuna}`);
            carregarDados(currentTabela);
        });
    });

    // =========================================================================
    // 2. API: LEITURA (GET)
    // =========================================================================
    async function carregarDados(tabela) {
        if (!tableBody) return;
        tableBody.innerHTML = '<tr><td colspan="3" class="text-center">Carregando...</td></tr>';

        try {
            const response = await fetch(`/api/tabelas-sistema/${tabela}`);
            if (!response.ok) throw new Error(`Erro API: ${response.status}`);
            
            const data = await response.json();
            renderizarTabela(data);
        } catch (error) {
            console.error(error);
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center error-msg">Erro ao carregar dados.</td></tr>';
        }
    }

    function renderizarTabela(data) {
        tableBody.innerHTML = '';

        if (!data || data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Nenhum registro encontrado.</td></tr>';
            return;
        }

        data.forEach(item => {
            // Tenta pegar o valor correto usando a coluna configurada no Python
            // Se falhar, tenta os nomes comuns como fallback
            let valor = item[currentColuna] || item.nome || item.descricao || item.numero || item.info_orcamentaria || '---';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td><strong>${valor}</strong></td>
                <td class="text-center">
                    <button class="btn-icon delete-btn" onclick="deletarItem(${item.id})" title="Excluir">
                        <i class="fa-solid fa-trash" style="color: #dc3545;"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    // =========================================================================
    // 3. API: CRIAÇÃO (POST)
    // =========================================================================
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const valor = inputNome.value.trim();
            if (!valor) return alert("Campo obrigatório.");

            // Monta o JSON dinâmico: { "nome": "Valor" } ou { "descricao": "Valor" }
            const payload = {};
            payload[currentColuna] = valor;

            try {
                const response = await fetch(`/api/tabelas-sistema/${currentTabela}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    toggleModal(false);
                    inputNome.value = '';
                    carregarDados(currentTabela);
                    alert('Salvo com sucesso!');
                } else {
                    const err = await response.json();
                    alert(`Erro ao salvar: ${err.detail || 'Verifique os dados'}`);
                }
            } catch (error) {
                console.error(error);
                alert('Erro de conexão.');
            }
        });
    }

    // =========================================================================
    // 4. API: DELEÇÃO (DELETE)
    // =========================================================================
    // Global para ser acessível via onclick no HTML gerado
    window.deletarItem = async (id) => {
        if (!confirm('Tem certeza que deseja excluir este item?')) return;

        try {
            const response = await fetch(`/api/tabelas-sistema/${currentTabela}/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                carregarDados(currentTabela);
            } else {
                const err = await response.json();
                alert(`Erro: ${err.detail || 'Não foi possível excluir.'}`);
            }
        } catch (error) {
            console.error(error);
            alert('Erro de conexão.');
        }
    };

    // =========================================================================
    // 5. CONTROLE DO MODAL
    // =========================================================================
    function toggleModal(show) {
        if (!modal) return;
        
        if (show) {
            modal.classList.add('active'); // Classe para mostrar (se usar CSS de classe)
            modal.style.display = 'flex';  // Fallback inline
            if (modalTitulo) modalTitulo.textContent = `Adicionar: ${currentTitulo}`;
            if (inputNome) inputNome.focus();
        } else {
            modal.classList.remove('active');
            modal.style.display = 'none';
        }
    }

    // Event Listeners do Modal
    if (btnNovoItem) btnNovoItem.addEventListener('click', () => toggleModal(true));
    if (btnFechar) btnFechar.addEventListener('click', () => toggleModal(false));
    if (btnCancelar) btnCancelar.addEventListener('click', () => toggleModal(false));

    // Fecha ao clicar fora
    window.addEventListener('click', (e) => {
        if (e.target === modal) toggleModal(false);
    });

    // Auto-Load: Clica no primeiro botão ao abrir a tela para não ficar vazio
    if (buttons.length > 0) {
        buttons[0].click();
    }
});