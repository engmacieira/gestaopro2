import pytest
from fastapi.testclient import TestClient
import os
import shutil

# Fixture para criar um contrato "pai" para o anexo
@pytest.fixture
def setup_contrato_para_anexo(test_client: TestClient, admin_auth_headers: dict) -> int:
    # Cria dependências necessárias (Categoria, Instrumento, etc)
    # Assumimos que o banco de teste está limpo ou permite duplicatas de nomes que não são chaves
    # Se der erro de Unique, mude os nomes aqui
    
    # Tenta criar ou ignora se já existe (para testes repetidos)
    test_client.post("/api/categorias/", json={"nome": "Categoria Teste Anexo"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Instrumento Teste Anexo"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade Teste Anexo"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "99/2099"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "Proc. Teste Anexo"}, headers=admin_auth_headers)
    
    payload = {
        "numero_contrato": "CT-TESTE-ANEXO/2099",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Fornecedor Teste", "cpf_cnpj": "99.999.999/0001-99"},
        "categoria_nome": "Categoria Teste Anexo",
        "instrumento_nome": "Instrumento Teste Anexo",
        "modalidade_nome": "Modalidade Teste Anexo",
        "numero_modalidade_str": "99/2099",
        "processo_licitatorio_numero": "Proc. Teste Anexo",
        "ativo": True
    }
    
    # Cria o contrato
    resp = test_client.post("/api/contratos/", json=payload, headers=admin_auth_headers)
    if resp.status_code == 201:
        return resp.json()["id"]
    
    # Se falhou (ex: contrato já existe), tenta buscar o ID
    # (Lógica de fallback para não travar o teste)
    resp_get = test_client.get("/api/contratos/", headers=admin_auth_headers)
    for c in resp_get.json():
        if c["numero_contrato"] == "CT-TESTE-ANEXO/2099":
            return c["id"]
    
    pytest.fail(f"Não foi possível criar nem encontrar o contrato para o teste: {resp.text}")

def test_fluxo_completo_anexo(test_client: TestClient, admin_auth_headers: dict, setup_contrato_para_anexo: int):
    """
    Testa o ciclo de vida completo de um anexo:
    1. Upload (POST)
    2. Download (GET)
    3. Exclusão (DELETE)
    4. Verificação de remoção (GET -> 404)
    """
    id_contrato = setup_contrato_para_anexo
    file_name = "teste_anexo_pytest.txt"
    file_content = b"Conteudo de teste para upload e download."
    
    # 1. TESTE DE UPLOAD
    response_create = test_client.post(
        "/api/anexos/upload/",
        data={
            "id_entidade": id_contrato, 
            "tipo_entidade": "contrato", 
            "tipo_documento": "Documento de Teste",
            "tipo_documento_novo": "" # Opcional
        },
        files={"file": (file_name, file_content, "text/plain")},
        headers=admin_auth_headers
    )
    
    assert response_create.status_code == 201, f"Erro no upload: {response_create.text}"
    data = response_create.json()
    new_id = data["anexo"]["id"]
    nome_seguro = data["anexo"]["nome_seguro"]
    
    print(f"Anexo criado: ID {new_id} - {nome_seguro}")

    # 2. TESTE DE DOWNLOAD
    # [CORREÇÃO]: A URL agora é /api/anexos/{id}/download
    response_download = test_client.get(
        f"/api/anexos/{new_id}/download",
        headers=admin_auth_headers
    )
    
    assert response_download.status_code == 200, "Erro no download"
    assert response_download.content == file_content, "O conteúdo do arquivo baixado não confere com o original"

    # 3. TESTE DE EXCLUSÃO
    response_delete = test_client.delete(
        f"/api/anexos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204, "Erro ao deletar"

    # 4. VERIFICAÇÃO PÓS-EXCLUSÃO (Deve retornar 404)
    response_download_fail = test_client.get(
        f"/api/anexos/{new_id}/download",
        headers=admin_auth_headers
    )
    assert response_download_fail.status_code == 404, "O arquivo deveria ter sido removido, mas ainda foi encontrado."

    # Limpeza Extra (Opcional): Se o teste falhar antes do delete, o arquivo físico pode sobrar.
    # Em um ambiente de teste real, usaríamos um diretório temporário configurado no conftest.py