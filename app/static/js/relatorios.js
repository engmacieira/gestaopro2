// Função global para ser chamada pelo onclick no _relatorio_item.html
function gerarRelatorio(nomeRelatorio) {
    // Encontra o select de ordenação específico para este relatório
    const selectOrdenacao = document.getElementById(`ordenacao-${nomeRelatorio}`);

    if (!selectOrdenacao) {
        console.error(`Elemento select 'ordenacao-${nomeRelatorio}' não encontrado.`);
        alert("Erro: Não foi possível encontrar as opções de ordenação."); // Feedback para o utilizador
        return;
    }

    const ordenacao = selectOrdenacao.value;

    // Constrói a URL da API FastAPI
    // A API /api/relatorios/{nome_relatorio} espera 'ordenacao' como query parameter
    const url = `/api/relatorios/${nomeRelatorio}?ordenacao=${encodeURIComponent(ordenacao)}`;

    // Abre o PDF (gerado pela API) numa nova aba
    window.open(url, '_blank');
}

// Opcional: Adicionar listeners ou outras lógicas se necessário no futuro
document.addEventListener('DOMContentLoaded', function() {
    // Código a ser executado após o carregamento do DOM, se necessário
    console.log("Página de relatórios carregada.");
});