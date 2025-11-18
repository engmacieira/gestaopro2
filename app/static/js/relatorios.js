document.addEventListener('DOMContentLoaded', function() {

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
    
    window.gerarRelatorio = function(nomeRelatorio) {
        const selectOrdenacao = document.getElementById(`ordenacao-${nomeRelatorio}`);

        if (!selectOrdenacao) {
            console.error(`Elemento select 'ordenacao-${nomeRelatorio}' não encontrado.`);
            showNotification(`Erro: Não foi possível encontrar as opções de ordenação para ${nomeRelatorio}.`, 'error'); 
            return;
        }

        const ordenacao = selectOrdenacao.value;

        if (!ordenacao) {
            showNotification('Por favor, selecione uma opção de ordenação.', 'warning');
            return;
        }

        const url = `/api/relatorios/${nomeRelatorio}?ordenacao=${encodeURIComponent(ordenacao)}`;

        window.open(url, '_blank');
        
        showNotification(`Relatório '${nomeRelatorio}' solicitado. Verifique a nova aba.`, 'success');
    }

    console.log("Página de relatórios carregada.");
    
    document.querySelectorAll('[data-relatorio-btn]').forEach(btn => {
        btn.addEventListener('click', () => {
            const nomeRelatorio = btn.dataset.relatorioBtn;
            if (nomeRelatorio) {
                window.gerarRelatorio(nomeRelatorio);
            }
        });
    });
});