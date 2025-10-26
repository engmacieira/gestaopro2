document.addEventListener('DOMContentLoaded', function() {

    // --- Lógica das Abas ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    if (tabLinks.length > 0 && tabContents.length > 0) {
        tabLinks.forEach(link => {
            link.addEventListener('click', () => {
                const tabId = link.dataset.tab;
                tabLinks.forEach(l => l.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                link.classList.add('active');
                const activeTab = document.getElementById(tabId);
                if(activeTab) activeTab.classList.add('active');
            });
        });
    } else {
        console.warn("Elementos das abas não encontrados.");
    }

    // --- Lógica de Notificação ---
    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');
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
            if(notification) {
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    // Exibir notificação após redirecionamento/reload (se houver)
    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    // --- Lógica de Importação (Função Genérica) ---
    function setupImportSection(formId, previewContainerId, previewTableId, errorDivId, saveBtnId, previewUrl, saveUrl, redirectUrl) {
        const form = document.getElementById(formId);
        if (!form) {
            console.error(`Formulário com ID '${formId}' não encontrado.`);
            return;
        }

        const previewContainer = document.getElementById(previewContainerId);
        const previewTable = document.getElementById(previewTableId);
        const errorDiv = document.getElementById(errorDivId);
        const saveBtn = document.getElementById(saveBtnId);
        let dataToSave = [];

        // Verifica se todos os elementos necessários existem
        if (!previewContainer || !previewTable || !errorDiv || !saveBtn) {
            console.error(`Elementos necessários para a seção de import '${formId}' não foram encontrados.`);
            return;
        }

        const saveButtonTextDefault = saveBtn.innerText; // Guarda o texto original do botão salvar
        const uploadButton = form.querySelector('button[type="submit"]');
        const uploadButtonTextDefault = uploadButton ? uploadButton.innerHTML : ''; // Guarda texto original do upload

        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            errorDiv.textContent = '';
            previewContainer.style.display = 'none'; // Esconde preview
            dataToSave = []; // Limpa dados anteriores
            const formData = new FormData(form);

            if (uploadButton) {
                uploadButton.disabled = true;
                uploadButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Carregando...';
            }

            try {
                // Rota de Preview da API
                const response = await fetch(previewUrl, { method: 'POST', body: formData });
                const result = await response.json();

                if (!response.ok) {
                    let errorDetail = result.detail || result.erro || 'Erro desconhecido ao pré-visualizar.';
                    throw new Error(errorDetail);
                }

                dataToSave = result;
                renderPreview(dataToSave, previewTable, errorDiv, previewContainer);

            } catch (error) {
                console.error(`Erro no preview (${formId}):`, error);
                errorDiv.textContent = `Erro: ${error.message}`;
            } finally {
                if (uploadButton) {
                    uploadButton.disabled = false;
                    uploadButton.innerHTML = uploadButtonTextDefault;
                }
            }
        });

        saveBtn.addEventListener('click', async function() {
            if (dataToSave.length === 0) {
                showNotification('Não há dados pré-visualizados para salvar.');
                return;
            }
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';

            try {
                // Rota de Salvar da API
                const response = await fetch(saveUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dataToSave)
                });
                const result = await response.json();

                if (!response.ok) {
                    let errorDetail = result.detail || result.erro || 'Erro desconhecido ao salvar.';
                    throw new Error(errorDetail);
                }

                // Usa sessionStorage para exibir a mensagem na próxima página
                sessionStorage.setItem('notificationMessage', result.mensagem || `${dataToSave.length} registos importados com sucesso!`);
                sessionStorage.setItem('notificationType', 'success');
                window.location.href = redirectUrl; // Redireciona

            } catch (error) {
                console.error(`Erro ao salvar (${formId}):`, error);
                showNotification(`Erro ao salvar: ${error.message}`);
                saveBtn.disabled = false;
                saveBtn.innerHTML = saveButtonTextDefault; // Restaura texto original
            }
        });
    }

    // --- Função para Renderizar Pré-visualização ---
    function renderPreview(data, table, errorDiv, container) {
        if (!data || data.length === 0) {
            errorDiv.textContent = 'Nenhum dado válido encontrado na planilha.';
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex'; // Mostra container

        const thead = table.querySelector('thead') || table.createTHead();
        const tbody = table.querySelector('tbody') || table.createTBody();
        thead.innerHTML = ''; // Limpa cabeçalho anterior
        tbody.innerHTML = ''; // Limpa corpo anterior

        // Assume que o primeiro item tem todas as colunas
        const headers = Object.keys(data[0]);
        thead.innerHTML = `<tr>${headers.map(h => `<th>${h.replace(/_/g, ' ')}</th>`).join('')}</tr>`;

        tbody.innerHTML = data.map(row => `
            <tr>
                ${headers.map(h => {
                    let value = row[h];
                    // Formatação de data (melhorada)
                    if ((h.includes('data_inicio') || h.includes('data_fim')) && value) {
                        try {
                             // Tenta interpretar como data ISO e formatar PT-BR
                            const dateObj = new Date(value);
                             // Verifica se é uma data válida antes de formatar
                             if (!isNaN(dateObj.getTime())) {
                                 value = dateObj.toLocaleDateString('pt-BR', { timeZone: 'UTC' }); // Adiciona UTC para evitar problemas de fuso
                             } else {
                                 value = String(value); // Mantém como string se não for data válida
                             }
                        } catch (e) {
                             value = String(value); // Mantém como string em caso de erro
                        }
                    } else if (value === null || value === undefined) {
                         value = ''; // Exibe vazio em vez de 'null'
                    } else if (typeof value === 'number' && (h === 'quantidade' || h === 'valor_unitario')) {
                         // Formata números decimais com vírgula (se aplicável)
                         value = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                    }
                    // Escapa HTML para segurança básica
                    const escapedValue = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    return `<td>${escapedValue}</td>`;
                }).join('')}
            </tr>
        `).join('');
    }

    // --- Inicialização das Secções de Importação ---
    // Usa as URLs de redirecionamento globais definidas no HTML
    setupImportSection(
        'form-upload-contratos', 'preview-container-contratos', 'preview-table-contratos',
        'error-message-contratos', 'btn-salvar-contratos',
        '/api/importar/contratos/preview',
        '/api/importar/contratos/salvar',
        redirectUrlContratos // Variável global do HTML
    );

    setupImportSection(
        'form-upload-itens', 'preview-container-itens', 'preview-table-itens',
        'error-message-itens', 'btn-salvar-itens',
        '/api/importar/itens/global/preview',
        '/api/importar/itens/global/salvar',
        redirectUrlItens // Variável global do HTML
    );
});