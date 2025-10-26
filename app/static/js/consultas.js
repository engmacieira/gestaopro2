document.addEventListener('DOMContentLoaded', function() {

    const tipoConsultaSelect = document.getElementById('tipo-consulta');
    const valorConsultaContainer = document.getElementById('container-valor-consulta');
    const valorConsultaSelect = document.getElementById('valor-consulta');
    const valorConsultaLabel = document.getElementById('label-valor-consulta');
    const formConsulta = document.getElementById('form-consulta');
    const areaResultados = document.getElementById('area-resultados');

    // 'configEntidades' agora é uma variável global definida no HTML
    // const configEntidades = {}; // Removido, pois é injetado pelo HTML

    tipoConsultaSelect.addEventListener('change', async function() {
        const tipo = this.value;
        valorConsultaSelect.innerHTML = '<option value="">Carregando...</option>';
        valorConsultaSelect.disabled = true;

        if (!tipo) {
            valorConsultaContainer.style.display = 'none';
            return;
        }

        // Usa a variável global injetada
        const config = configEntidades[tipo];
        if (!config) {
            console.error(`Configuração não encontrada para o tipo: ${tipo}`);
            valorConsultaContainer.style.display = 'none';
            return;
        }

        valorConsultaLabel.innerText = config.label || `Selecionar ${tipo.replace('_', ' ')}`; // Fallback label
        valorConsultaContainer.style.display = 'block';

        try {
            // 1. Fetch dos valores disponíveis para o tipo de consulta
            // Endpoint API para buscar as opções do select
            const response = await fetch(`/api/consultas/entidades/${tipo}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || data.erro || 'Erro ao carregar opções.');

            valorConsultaSelect.innerHTML = '<option value="" disabled selected>Selecione...</option>';
            data.forEach(item => {
                // 'texto' e 'id' são os campos esperados da API
                valorConsultaSelect.innerHTML += `<option value="${item.id}">${item.texto}</option>`;
            });
            valorConsultaSelect.disabled = false;

        } catch (error) {
            valorConsultaSelect.innerHTML = '<option value="">Erro ao carregar</option>';
            console.error(error);
            // Poderia mostrar uma notificação aqui também
        }
    });

    formConsulta.addEventListener('submit', async function(event) {
        event.preventDefault();
        const tipo = tipoConsultaSelect.value;
        const valor = valorConsultaSelect.value;

        if (!tipo || !valor) { return; }

        areaResultados.innerHTML = '<div class="empty-state mini"><i class="fa-solid fa-spinner fa-spin"></i><p>Buscando...</p></div>';

        try {
            // 2. Fetch dos resultados da consulta
            // Endpoint API para buscar os resultados
            const response = await fetch(`/api/consultas?tipo=${tipo}&valor=${valor}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || data.erro || 'Erro na consulta.');

            renderizarResultados(data);

        } catch (error) {
            areaResultados.innerHTML = `<div class="notification error">${error.message}</div>`;
        }
    });

    // Função de renderização de resultados (USANDO CONFIGURAÇÃO DO BACKEND)
    function renderizarResultados(data) {
        if (!data.resultados || data.resultados.length === 0) {
            areaResultados.innerHTML = '<div class="empty-state mini"><p>Nenhum resultado encontrado.</p></div>';
            return;
        }

        // Mapeamento de colunas para renderização dinâmica
        // Nota: Este mapeamento está hardcoded no JS. Uma melhoria futura
        // seria passar esta configuração também do backend.
        const colunasMap = {
            'processo_licitatorio': [
                { header: 'Contrato', key: 'numero_contrato', link: '/contrato/' }, // Link base
                { header: 'Fornecedor', key: 'fornecedor' },
                { header: 'Categoria', key: 'nome_categoria' },
                { header: 'Status', key: 'ativo', format: (val) => `<span class="status-badge ${val ? 'green' : 'gray'}">${val ? 'Ativo' : 'Inativo'}</span>` }
            ],
            'unidade_requisitante': [
                { header: 'AOCS', key: 'numero_aocs', link: '/pedido/' }, // Link base
                { header: 'Data', key: 'data_criacao' },
                { header: 'Fornecedor', key: 'fornecedor' },
                { header: 'Status', key: 'status_entrega', format: (val) => {
                     const statusClass = val === 'Entregue' ? 'green' : (val === 'Entrega Parcial' ? 'orange' : 'gray');
                     return `<span class="status-badge ${statusClass}">${val}</span>`;
                }}
            ],
            'local_entrega': [
                { header: 'AOCS', key: 'numero_aocs', link: '/pedido/' }, // Link base
                { header: 'Data', key: 'data_criacao' },
                { header: 'Fornecedor', key: 'fornecedor' },
                 { header: 'Status', key: 'status_entrega', format: (val) => {
                     const statusClass = val === 'Entregue' ? 'green' : (val === 'Entrega Parcial' ? 'orange' : 'gray');
                     return `<span class="status-badge ${statusClass}">${val}</span>`;
                }}
            ],
            'dotacao': [
                { header: 'AOCS', key: 'numero_aocs', link: '/pedido/' }, // Link base
                { header: 'Data', key: 'data_criacao' },
                { header: 'Fornecedor', key: 'fornecedor' },
                 { header: 'Status', key: 'status_entrega', format: (val) => {
                     const statusClass = val === 'Entregue' ? 'green' : (val === 'Entrega Parcial' ? 'orange' : 'gray');
                     return `<span class="status-badge ${statusClass}">${val}</span>`;
                }}
            ]
            // Adicionar outros tipos de consulta aqui se existirem
        };

        const colunas = colunasMap[data.tipo];
        if (!colunas) { areaResultados.innerHTML = '<div class="notification error">Erro de configuração de renderização para este tipo de consulta.</div>'; return; }

        let tableHtml = `
            <div class="card full-width">
                <h2>${data.titulo || 'Resultados da Consulta'} (${data.resultados.length})</h2>
                <div class="table-wrapper"><table class="data-table">
                    <thead><tr>${colunas.map(c => `<th>${c.header}</th>`).join('')}</tr></thead>
                    <tbody>
        `;

        data.resultados.forEach(item => {
            tableHtml += '<tr>';
            colunas.forEach(col => {
                let valor = item[col.key];

                // Aplica formatação customizada se definida
                if (col.format && typeof col.format === 'function') {
                    valor = col.format(valor);
                } else if (valor === true) {
                     valor = 'Sim';
                } else if (valor === false) {
                     valor = 'Não';
                } else if (valor === null || valor === undefined) {
                     valor = 'N/D';
                }

                // Aplica link se definido
                if (col.link) {
                    // Determina o valor do link: 'id' para Contrato, 'numero_aocs' para Pedido/AOCS
                    // Adapte esta lógica se houver outras entidades com chaves diferentes
                    const linkValue = item.id !== undefined ? item.id : item.numero_aocs;
                    // Codifica o valor do link para URLs (importante para AOCS com '/')
                    const encodedLinkValue = encodeURIComponent(linkValue);
                    valor = `<a href="${col.link}${encodedLinkValue}"><strong>${valor}</strong></a>`;
                }

                tableHtml += `<td>${valor}</td>`;
            });
            tableHtml += '</tr>';
        });

        tableHtml += '</tbody></table></div></div>';
        areaResultados.innerHTML = tableHtml;
    }
});