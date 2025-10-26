document.addEventListener('DOMContentLoaded', function() {

    const formUpload = document.getElementById('form-upload-itens');
    const previewContainer = document.getElementById('preview-container');
    const previewTable = document.getElementById('preview-table');
    const errorMessageDiv = document.getElementById('error-message');
    const btnSalvar = document.getElementById('btn-salvar-dados');
    // Seleciona a área de notificação dentro do main-content
    const notificationArea = document.querySelector('.main-content #notification-area');

    // idContratoGlobal e redirectUrlGlobal são definidos no HTML
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
        notificationArea.prepend(notification); // Usa prepend
        setTimeout(() => {
            if (notification) {
                notification.style.opacity = '0';
                notification.addEventListener('transitionend', () => notification.remove());
            }
        }, 5000);
    }

    // Função para recarregar ou redirecionar com mensagem
    function navigateWithMessage(url, message, type = 'success') {
        sessionStorage.setItem('notificationMessage', message);
        sessionStorage.setItem('notificationType', type);
        window.location.href = url; // Redireciona para a URL fornecida
    }

    // Exibir notificação após redirecionamento/reload (se houver)
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
            dadosParaSalvar = []; // Limpa dados anteriores

            const formData = new FormData(formUpload);
            const submitButton = formUpload.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Carregando...';

            try {
                // API CALL: Preview (POST /api/importar/itens/{id_contrato}/preview)
                // Certifique-se que este endpoint existe no seu router (ex: item_router.py)
                const response = await fetch(`/api/importar/itens/${idContratoGlobal}/preview`, {
                    method: 'POST',
                    body: formData
                });
                const resultado = await response.json();

                if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Ocorreu um erro ao pré-visualizar.');

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
            previewContainer.style.display = 'none'; // Esconde se vazio
            return;
        }

        // UX Improvement: usa flex para exibir o container do passo 2
        previewContainer.style.display = 'flex';
        previewTable.innerHTML = ''; // Limpa tabela anterior

        // Assume que o primeiro item tem todas as colunas
        const headers = Object.keys(dados[0]);
        let headerHTML = '<tr>';
        headers.forEach(h => headerHTML += `<th>${h.replace(/_/g, ' ')}</th>`); // Formata cabeçalhos
        headerHTML += '</tr>';
        previewTable.createTHead().innerHTML = headerHTML;

        let bodyHTML = '';
        dados.forEach(linha => {
            bodyHTML += '<tr>';
            headers.forEach(h => {
                let value = linha[h];
                if (value === null || value === undefined) {
                    value = ''; // Exibe vazio em vez de 'null'
                } else if (typeof value === 'number' && (h === 'quantidade' || h === 'valor_unitario')) {
                    // Formata números decimais com vírgula
                    value = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
                // API CALL: Save (POST /api/importar/itens/{id_contrato}/salvar)
                // Certifique-se que este endpoint existe no seu router (ex: item_router.py)
                const response = await fetch(`/api/importar/itens/${idContratoGlobal}/salvar`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dadosParaSalvar) // Envia os dados pré-visualizados
                });
                const resultado = await response.json();

                if (!response.ok) throw new Error(resultado.detail || resultado.erro || 'Ocorreu um erro ao salvar os itens.');

                // Usa a URL de redirecionamento global definida no HTML
                navigateWithMessage(redirectUrlGlobal, resultado.mensagem || `${dadosParaSalvar.length} itens importados com sucesso!`, 'success');

            } catch (error) {
                console.error('Erro ao salvar:', error);
                showNotification(`Erro ao salvar: ${error.message}`);
                btnSalvar.disabled = false;
                btnSalvar.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Itens no Contrato';
            }
        });
    } else {
         console.error("Botão 'btn-salvar-dados' não encontrado.");
    }
});