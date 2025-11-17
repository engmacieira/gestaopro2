function gerarRelatorio(nomeRelatorio) {
    const selectOrdenacao = document.getElementById(`ordenacao-${nomeRelatorio}`);

    if (!selectOrdenacao) {
        console.error(`Elemento select 'ordenacao-${nomeRelatorio}' não encontrado.`);
        alert("Erro: Não foi possível encontrar as opções de ordenação."); 
        return;
    }

    const ordenacao = selectOrdenacao.value;

    const url = `/api/relatorios/${nomeRelatorio}?ordenacao=${encodeURIComponent(ordenacao)}`;

    window.open(url, '_blank');
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("Página de relatórios carregada.");
});