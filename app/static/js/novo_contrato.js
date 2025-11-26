document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('formNovoContrato');

    // Helper to get the text of the selected option
    // Returns null if nothing is selected
    const getSelectedText = (selectId) => {
        const select = document.getElementById(selectId);
        if (select && select.selectedIndex >= 0) {
            return select.options[select.selectedIndex].text.trim();
        }
        return null;
    };

    // Helper specifically for Processo to remove "Proc. " prefix if it exists
    const getProcessoNumero = (selectId) => {
        const text = getSelectedText(selectId);
        if (text) {
            return text.replace('Proc. ', '').trim();
        }
        return null;
    };

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // 1. Captura dados básicos do form
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            // 2. Monta o Payload conforme o Schema ContratoCreateRequest
            // O backend espera NOMES, não IDs.
            const payload = {
                numero_contrato: data.numero_contrato,
                data_inicio: data.data_inicio,
                data_fim: data.data_fim,
                ativo: data.ativo === 'true',
                
                // Mapeando os TEXTOS dos selects para os campos *_nome
                categoria_nome: getSelectedText('id_categoria'),
                instrumento_nome: getSelectedText('id_instrumento_contratual'),
                modalidade_nome: getSelectedText('id_modalidade'),
                numero_modalidade_str: getSelectedText('id_numero_modalidade'),
                
                // Tratamento especial para o número do processo
                processo_licitatorio_numero: getProcessoNumero('id_processo_licitatorio'),
                
                // Objeto Aninhado (VO)
                fornecedor: {
                    nome: data.fornecedor_nome,
                    cpf_cnpj: data.fornecedor_cnpj,
                    email: data.fornecedor_email || null,
                    telefone: data.fornecedor_telefone || null
                }
            };

            try {
                const response = await fetch('/api/contratos/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const result = await response.json();
                    alert('Contrato cadastrado com sucesso!');
                    // Redireciona para o detalhe do contrato criado
                    window.location.href = `/contrato/${result.id}`;
                } else {
                    const errorData = await response.json();
                    console.error('Erro API:', errorData);
                    // Exibe mensagem amigável se houver detalhe
                    let msg = 'Verifique os dados.';
                    if (errorData.detail) {
                        msg = Array.isArray(errorData.detail) 
                            ? errorData.detail.map(d => `${d.loc[1]}: ${d.msg}`).join('\n')
                            : errorData.detail;
                    }
                    alert(`Erro ao salvar:\n${msg}`);
                }
            } catch (error) {
                console.error('Erro de rede:', error);
                alert('Erro de conexão com o servidor.');
            }
        });
    }
});