document.addEventListener('DOMContentLoaded', function() {

    const tipoConsultaSelect = document.getElementById('tipo-consulta');
    const valorConsultaContainer = document.getElementById('container-valor-consulta');
    const valorConsultaSelect = document.getElementById('valor-consulta');
    const valorConsultaLabel = document.getElementById('label-valor-consulta');
    const formConsulta = document.getElementById('form-consulta');
    const areaResultados = document.getElementById('area-resultados');

    function formatarValor(col, valor) {
        if (col.format && typeof col.format === 'function') {
            return col.format(valor);
        }
        if (valor === true) return 'Sim';
        if (valor === false) return 'Não';
        if (valor === null || valor === undefined) return 'N/D';
        return valor;
    }

    function criarLink(col, item, valor) {
        if (col.link) {
            const linkValue = item.id !== undefined ? item.id : item.numero_aocs;
            const encodedLinkValue = encodeURIComponent(linkValue);
            return `<a href="${col.link}${encodedLinkValue}"><strong>${valor}</strong></a>`;
        }
        return valor;
    }

    function criarLinha(item, colunas) {
        let rowHtml = '<tr>';
        colunas.forEach(col => {
            let valor = item[col.key];
            valor = formatarValor(col, valor);
            valor = criarLink(col, item, valor);
            rowHtml += `<td>${valor}</td>`;
        });
        rowHtml += '</tr>';
        return rowHtml;
    }

    const colunasMap = {
        'processo_licitatorio': [
            { header: 'Contrato', key: 'numero_contrato', link: '/contrato/' }, 
            { header: 'Fornecedor', key: 'fornecedor' },
            { header: 'Categoria', key: 'nome_categoria' },
            { header: 'Status', key: 'ativo', format: (val) => `<span class="status-badge ${val ? 'green' : 'gray'}">${val ? 'Ativo' : 'Inativo'}</span>` }
        ],
        'unidade_requisitante': [
            { header: 'AOCS', key: 'numero_aocs', link: '/pedido/' }, 
            { header: 'Data', key: 'data_criacao' },
            { header: 'Fornecedor', key: 'fornecedor' },
            { header: 'Status', key: 'status_entrega', format: (val) => {
                 const statusClass = val === 'Entregue' ? 'green' : (val === 'Entrega Parcial' ? 'orange' : 'gray');
                 return `<span class="status-badge ${statusClass}">${val}</span>`;
            }}
        ],
        'local_entrega': [
            { header: 'AOCS', key: 'numero_aocs', link: '/pedido/' }, 
            { header: 'Data', key: 'data_criacao' },
            { header: 'Fornecedor', key: 'fornecedor' },
             { header: 'Status', key: 'status_entrega', format: (val) => {
                 const statusClass = val === 'Entregue' ? 'green' : (val === 'Entrega Parcial' ? 'orange' : 'gray');
                 return `<span class="status-badge ${statusClass}">${val}</span>`;
            }}
        ],
        'dotacao': [
            { header: 'AOCS', key: 'numero_aocs', link: '/pedido/' }, 
            { header: 'Data', key: 'data_criacao' },
            { header: 'Fornecedor', key: 'fornecedor' },
             { header: 'Status', key: 'status_entrega', format: (val) => {
                 const statusClass = val === 'Entregue' ? 'green' : (val === 'Entrega Parcial' ? 'orange' : 'gray');
                 return `<span class="status-badge ${statusClass}">${val}</span>`;
            }}
        ]
    };

    tipoConsultaSelect.addEventListener('change', async function() {
        const tipo = this.value;
        valorConsultaSelect.innerHTML = '<option value="">Carregando...</option>';
        valorConsultaSelect.disabled = true;

        if (!tipo) {
            valorConsultaContainer.style.display = 'none';
            return;
        }

        const config = configEntidades[tipo];
        if (!config) {
            console.error(`Configuração não encontrada para o tipo: ${tipo}`);
            valorConsultaContainer.style.display = 'none';
            return;
        }

        valorConsultaLabel.innerText = config.label || `Selecionar ${tipo.replace('_', ' ')}`; 
        valorConsultaContainer.style.display = 'block';

        try {
            const response = await fetch(`/api/consultas/entidades/${tipo}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || data.erro || 'Erro ao carregar opções.');

            valorConsultaSelect.innerHTML = '<option value="" disabled selected>Selecione...</option>';
            data.forEach(item => {
                valorConsultaSelect.innerHTML += `<option value="${item.id}">${item.texto}</option>`;
            });
            valorConsultaSelect.disabled = false;

        } catch (error) {
            valorConsultaSelect.innerHTML = '<option value="">Erro ao carregar</option>';
            console.error(error);
        }
    });

    formConsulta.addEventListener('submit', async function(event) {
        event.preventDefault();
        const tipo = tipoConsultaSelect.value;
        const valor = valorConsultaSelect.value;

        if (!tipo || !valor) { return; }

        areaResultados.innerHTML = '<div class="empty-state mini"><i class="fa-solid fa-spinner fa-spin"></i><p>Buscando...</p></div>';

        try {
            const response = await fetch(`/api/consultas?tipo=${tipo}&valor=${valor}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || data.erro || 'Erro na consulta.');

            renderizarResultados(data);

        } catch (error) {
            areaResultados.innerHTML = `<div class="notification error">${error.message}</div>`;
        }
    });

    function renderizarResultados(data) {
        
        const resultados = data.resultados;
        
        if (!resultados || resultados.length === 0) {
            areaResultados.innerHTML = '<div class="empty-state mini"><p>Nenhum resultado encontrado.</p></div>';
            return;
        }

        const colunas = colunasMap[data.tipo];
        if (!colunas) { areaResultados.innerHTML = '<div class="notification error">Erro de configuração de renderização para este tipo de consulta.</div>'; return; }

        let tableHtml = `
            <div class="card full-width">
                <h2>${data.titulo || 'Resultados da Consulta'} (${resultados.length})</h2>
                <div class="table-wrapper"><table class="data-table">
                    <thead><tr>${colunas.map(c => `<th>${c.header}</th>`).join('')}</tr></thead>
                    <tbody>
        `;

        resultados.forEach(item => {
            tableHtml += criarLinha(item, colunas); 
        });

        tableHtml += '</tbody></table></div></div>';
        areaResultados.innerHTML = tableHtml;
    }

});