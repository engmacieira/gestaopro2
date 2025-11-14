import pytest
from fastapi.testclient import TestClient
from datetime import date
import os

# O 'admin_auth_headers' é pego automaticamente do conftest.py
# O 'UPLOAD_FOLDER' é definido no anexo_router.py e lido a partir do .env

# --- Fixture de Preparação 1: Contrato "Pai" ---
@pytest.fixture
def setup_contrato_para_anexo(test_client: TestClient, admin_auth_headers: dict) -> int:
    """Cria um Contrato 'pai' e retorna o seu ID."""
    payload = {
        "numero_contrato": "CT-ANEXO-444/2025",
        "data_inicio": "2025-01-01", "data_fim": "2025-12-31",
        "fornecedor": {"nome": "Fornecedor de Anexos", "cpf_cnpj": "44.444.444/0001-44"},
        "categoria_nome": "Categoria de Anexos",
        "instrumento_nome": "Instrumento de Anexos",
        "modalidade_nome": "Modalidade de Anexos",
        "numero_modalidade_str": "NumMod Anexos",
        "processo_licitatorio_numero": "PL Anexos"
    }
    response = test_client.post("/api/contratos/", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201, "Falha ao criar o Contrato 'pai' para o teste de anexo."
    return response.json()["id"]

# --- Fixture de Preparação 2: AOCS "Pai" ---
@pytest.fixture
def setup_aocs_para_anexo(test_client: TestClient, admin_auth_headers: dict) -> int:
    """Cria uma AOCS 'pai' e retorna o seu ID."""
    aocs_payload = {
        "numero_aocs": "AOCS-ANEXO-555/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "AOCS para teste de anexos",
        "unidade_requisitante_nome": "Unidade (Anexo)",
        "local_entrega_descricao": "Local (Anexo)",
        "agente_responsavel_nome": "Agente (Anexo)",
        "dotacao_info_orcamentaria": "Dotação (Anexo)"
    }
    response = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert response.status_code == 201, "Falha ao criar a AOCS 'pai' para o teste de anexo."
    return response.json()["id"]

# --- Testes do Fluxo de Anexos ---

def test_upload_anexo_contrato(test_client: TestClient, admin_auth_headers: dict, setup_contrato_para_anexo: int):
    """Testa POST /api/anexos/upload/ para um Contrato."""
    id_contrato = setup_contrato_para_anexo
    
    # Prepara os dados do formulário (Form)
    data_payload = {
        "id_entidade": id_contrato,
        "tipo_entidade": "contrato",
        "tipo_documento": "Orçamento de Teste"
    }
    
    # Prepara o ficheiro a ser enviado
    # (nome, conteúdo em bytes, mime-type)
    file_payload = {
        "file": ("orcamento.txt", b"Este e um conteudo de teste.", "text/plain")
    }

    response = test_client.post(
        "/api/anexos/upload/",
        data=data_payload,
        files=file_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nome_original"] == "orcamento.txt"
    assert data["tipo_entidade"] == "contrato"
    assert data["id_entidade"] == id_contrato
    # Verifica se o ficheiro foi salvo (o path relativo está no 'nome_seguro')
    assert f"contrato/{id_contrato}" in data["nome_seguro"]

@pytest.mark.skip(reason="Preciso Mudar o Banco de Dados.")
def test_upload_anexo_aocs(test_client: TestClient, admin_auth_headers: dict, setup_aocs_para_anexo: int):
    """Testa POST /api/anexos/upload/ para uma AOCS."""
    id_aocs = setup_aocs_para_anexo
    
    data_payload = {"id_entidade": id_aocs, "tipo_entidade": "aocs", "tipo_documento": "Nota Fiscal"}
    file_payload = {"file": ("nota.pdf", b"Conteudo fake do PDF", "application/pdf")}

    response = test_client.post(
        "/api/anexos/upload/",
        data=data_payload,
        files=file_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nome_original"] == "nota.pdf"
    assert data["tipo_entidade"] == "aocs"
    assert data["id_entidade"] == id_aocs
    assert f"aocs/{id_aocs}" in data["nome_seguro"]

def test_download_and_delete_anexo(test_client: TestClient, admin_auth_headers: dict, setup_contrato_para_anexo: int):
    """Testa GET /api/anexos/download/{id} e DELETE /api/anexos/{id}"""
    
    # 1. Criar o anexo
    file_content = b"Conteudo para download e delete"
    response_create = test_client.post(
        "/api/anexos/upload/",
        data={"id_entidade": setup_contrato_para_anexo, "tipo_entidade": "contrato", "tipo_documento": "Para Deletar"},
        files={"file": ("deletar.txt", file_content, "text/plain")},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]
    nome_seguro = response_create.json()["nome_seguro"]

    # 2. Testar o Download
    response_download = test_client.get(
        f"/api/anexos/download/{new_id}",
        headers=admin_auth_headers
    )
    assert response_download.status_code == 200
    assert response_download.content == file_content
    
    # 3. Testar o Delete
    response_delete = test_client.delete(
        f"/api/anexos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204

    # 4. Verificar se o Download agora falha
    response_download_fail = test_client.get(
        f"/api/anexos/download/{new_id}",
        headers=admin_auth_headers
    )
    assert response_download_fail.status_code == 404

    # 5. (Opcional) Verificar se o ficheiro físico foi apagado
    # Esta verificação é importante para garantir que não deixamos lixo no disco
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    # Nota: O BASE_DIR vem do main.py, temos de o recriar aqui ou assumir o caminho
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    BASE_DIR = os.path.dirname(APP_DIR)
    file_path = os.path.join(BASE_DIR, UPLOAD_FOLDER, nome_seguro)
    
    assert not os.path.exists(file_path), "O ficheiro físico não foi apagado do disco após o DELETE."