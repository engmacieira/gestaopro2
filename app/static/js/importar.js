document.addEventListener('DOMContentLoaded', function() {

    // --- Funções Auxiliares ---

    function escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return '';
        const str = String(unsafe);
        return str
             .replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
             .replace(/"/g, '&quot;')
             .replace(/'/g, '&#039;');
    }
    
    function formatBrazilianNumber(value) {
        if (typeof value === 'number') {
            return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        return value;
    }

    function formatDateForPreview(value) {
        if (!value) return '';
        try {
            const dateObj = new Date(value);
            if (!isNaN(dateObj.getTime())) {
                return dateObj.toLocaleDateString('pt-BR', { timeZone: 'UTC' }); 
            }
        } catch (e) {
            console.warn("Erro ao formatar data:", e);
        }
        return String(value); 
    }

    // --- Lógica de Abas ---

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
    }

    // --- Lógica de Notificações ---

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
        notificationArea.prepend(notification); 
        setTimeout(() => {
            if(notification) {
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }
    
    // --- Lógica Principal de Importação ---

    function setupImportSection(formId, previewContainerId, previewTableId, errorDivId, saveBtnId, previewUrl, saveUrl, redirectUrl) {
        const form = document.getElementById(formId);
        if (!form) return;

        // Verifica se já foi inicializado para evitar duplicidade
        if (form.dataset.jsImportInitialized === 'true') return; 
        form.dataset.jsImportInitialized = 'true';

        const previewContainer = document.getElementById(previewContainerId);
        const previewTable = document.getElementById(previewTableId);
        const errorDiv = document.getElementById(errorDivId);
        const saveBtn = document.getElementById(saveBtnId);
        
        if (saveBtn) saveBtn.type = 'button';

        if (!previewContainer || !previewTable || !errorDiv || !saveBtn) {
            console.error(`Elementos necessários para a seção de import '${formId}' não foram encontrados.`);
            return;
        }

        const saveButtonTextDefault = saveBtn.innerText; 
        const uploadButton = form.querySelector('button[type="submit"]');
        const uploadButtonTextDefault = uploadButton ? uploadButton.innerHTML : ''; 

        // Evento 1: Submit do Formulário (Preview)
        form.addEventListener('submit', async function(event) {
            // Guard Clause: Se o submitter for o botão de salvar, abortar
            if (saveBtn && event.submitter === saveBtn) {
                event.preventDefault();
                event.stopPropagation();
                return; 
            }

            event.preventDefault();
            
            errorDiv.textContent = '';
            previewContainer.style.display = 'none';
            
            // Limpa o cache de dados anterior
            delete previewContainer.dataset.cacheData;
            
            const formData = new FormData(form);

            if (uploadButton) {
                uploadButton.disabled = true;
                uploadButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Carregando...';
            }

            try {
                const response = await fetch(previewUrl, { method: 'POST', body: formData });
                const result = await response.json();

                if (!response.ok) {
                    let errorDetail = result.detail || result.erro || `Erro ${response.status} ao pré-visualizar.`;
                    throw new Error(errorDetail);
                }

                // [FIX SÊNIOR] Armazena os dados no DOM (Dataset) para persistência
                // Isso evita que variáveis locais sejam limpas por race conditions
                previewContainer.dataset.cacheData = JSON.stringify(result);
                
                renderPreview(result, previewTable, errorDiv, previewContainer);

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

        // Evento 2: Clique no botão Salvar
        saveBtn.addEventListener('click', async function(event) {
            event.preventDefault(); 
            
            // [FIX SÊNIOR] Recupera os dados do "cofre" (DOM)
            const cachedData = previewContainer.dataset.cacheData;
            const dataToSave = cachedData ? JSON.parse(cachedData) : [];

            if (dataToSave.length === 0) {
                showNotification('Não há dados pré-visualizados para salvar.');
                return;
            }
            
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';

            try {
                const response = await fetch(saveUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dataToSave)
                });
                const result = await response.json();

                if (!response.ok) {
                    let errorDetail = result.detail || result.erro || `Erro ${response.status} ao salvar.`;
                    throw new Error(errorDetail);
                }

                sessionStorage.setItem('notificationMessage', result.mensagem || `${dataToSave.length} registos importados com sucesso!`);
                sessionStorage.setItem('notificationType', 'success');
                window.location.href = redirectUrl; 

            } catch (error) {
                console.error(`Erro ao salvar (${formId}):`, error);
                showNotification(`Erro ao salvar: ${error.message}`);
                saveBtn.disabled = false;
                saveBtn.innerHTML = saveButtonTextDefault; 
            }
        });
    }

    function renderPreview(data, table, errorDiv, container) {
        if (!data || data.length === 0) {
            errorDiv.textContent = 'Nenhum dado válido encontrado na planilha.';
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex'; 

        const thead = table.querySelector('thead') || table.createTHead();
        const tbody = table.querySelector('tbody') || table.createTBody();
        thead.innerHTML = ''; 
        tbody.innerHTML = ''; 

        const headers = Object.keys(data[0]);
        thead.innerHTML = `<tr>${headers.map(h => `<th>${h.replace(/_/g, ' ')}</th>`).join('')}</tr>`;

        tbody.innerHTML = data.map(row => `
            <tr>
                ${headers.map(h => {
                    let value = row[h];

                    if (h.includes('data_inicio') || h.includes('data_fim') || h.includes('data_criacao') ) { 
                        value = formatDateForPreview(value);
                    } 
                    else if (h === 'quantidade' || h === 'valor_unitario') {
                         value = formatBrazilianNumber(value);
                    } 
                    
                    if (value === null || value === undefined) {
                         value = ''; 
                    } else {
                         value = String(value);
                    }

                    const escapedValue = escapeHtml(value);
                    
                    return `<td>${escapedValue}</td>`;
                }).join('')}
            </tr>
        `).join('');
    }

    // --- Inicialização ---

    setupImportSection(
        'form-upload-contratos', 'preview-container-contratos', 'preview-table-contratos',
        'error-message-contratos', 'btn-salvar-contratos',
        '/api/importar/contratos/preview',
        '/api/importar/contratos/salvar',
        redirectUrlContratos 
    );

    setupImportSection(
        'form-upload-itens', 'preview-container-itens', 'preview-table-itens',
        'error-message-itens', 'btn-salvar-itens',
        '/api/importar/itens/global/preview',
        '/api/importar/itens/global/salvar',
        redirectUrlItens 
    );
});