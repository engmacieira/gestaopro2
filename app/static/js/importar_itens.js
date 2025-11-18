document.addEventListener('DOMContentLoaded', function() {

    const formUpload = document.getElementById('form-upload-itens');
    const previewContainer = document.getElementById('preview-container');
    const previewTable = document.getElementById('preview-table');
    const errorMessageDiv = document.getElementById('error-message');
    const btnSalvar = document.getElementById('btn-salvar-dados');
    const notificationArea = document.querySelector('.main-content #notification-area');

    let dadosParaSalvar = [];

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
            if (notification) {
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    function navigateWithMessage(url, message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        window.location.href = url; 
    }

    function formatNumberForDisplay(value) {
        if (typeof value === 'number') {
            return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        return value;
    }

    const msg = sessionStorage.getItem('notificationMessage');
    if (msg) {
        showNotification(msg, sessionStorage.getItem('notificationType'));
        sessionStorage.removeItem('notificationMessage');
        sessionStorage.removeItem('notificationType');
    }

    if (formUpload) {
        formUpload.addEventListener('submit', async function(event) {
            event.preventDefault();
            errorMessageDiv.innerText = '';
            previewContainer.style.display = 'none';
            dadosParaSalvar = [];

            const formData = new FormData(formUpload);
            const submitButton = formUpload.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Carregando...';

            try {
                const response = await fetch(`/api/importar/itens/${idContratoGlobal}/preview`, {
                    method: 'POST',
                    body: formData
                });
                const resultado = await response.json();

                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao pré-visualizar.`);

                dadosParaSalvar = resultado;
                renderizarPreview(dadosParaSalvar);

            } catch (error) {
                console.error('Erro no upload preview:', error);
                errorMessageDiv.innerText = `Erro: ${error.message}`;
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Carregar e Pré-visualizar';
            }
        });
    } else {
        console.error("Formulário de upload de itens não encontrado.");
    }

    function renderizarPreview(dados) {
        if (!dados || dados.length === 0) {
            errorMessageDiv.innerText = 'Nenhum dado válido encontrado na planilha.';
            previewContainer.style.display = 'none'; 
            return;
        }

        previewContainer.style.display = 'flex';
        previewTable.innerHTML = ''; 

        const headers = Object.keys(dados[0]);
        let headerHTML = '<tr>';
        headers.forEach(h => headerHTML += `<th>${h.replace(/_/g, ' ')}</th>`); 
        headerHTML += '</tr>';
        
        if (previewTable.tHead) previewTable.tHead.remove();
        if (previewTable.tBodies.length > 0) previewTable.tBodies[0].remove();
        
        previewTable.createTHead().innerHTML = headerHTML;

        let bodyHTML = '';
        dados.forEach(linha => {
            bodyHTML += '<tr>';
            headers.forEach(h => {
                let value = linha[h];
                if (value === null || value === undefined) {
                    value = ''; 
                } else if (h === 'quantidade' || h === 'valor_unitario') {
                    value = formatNumberForDisplay(value); 
                }
                bodyHTML += `<td>${value}</td>`;
            });
            bodyHTML += '</tr>';
        });
        previewTable.createTBody().innerHTML = bodyHTML;
    }

    if (btnSalvar) {
        btnSalvar.addEventListener('click', async function() {
            if (dadosParaSalvar.length === 0) {
                showNotification('Não há dados pré-visualizados para salvar.');
                return;
            }

            btnSalvar.disabled = true;
            btnSalvar.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';

            try {
                const response = await fetch(`/api/importar/itens/${idContratoGlobal}/salvar`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dadosParaSalvar) 
                });
                const resultado = await response.json();

                if (!response.ok) throw new Error(resultado.detail || resultado.erro || `Erro ${response.status} ao salvar os itens.`);

                const successMessage = resultado.mensagem || `${dadosParaSalvar.length} itens importados com sucesso!`;
                
                navigateWithMessage(redirectUrlGlobal, successMessage, 'success');

            } catch (error) {
                console.error('Erro ao salvar:', error);
                showNotification(`Erro ao salvar: ${error.message}`);
            } finally {
                btnSalvar.disabled = false;
                btnSalvar.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Itens no Contrato';
            }
        });
    } else {
         console.error("Botão 'btn-salvar-dados' não encontrado.");
    }
});