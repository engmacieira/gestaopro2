import pytest
from fastapi.testclient import TestClient
from datetime import date
import os

@pytest.fixture
def setup_contrato_para_anexo(test_client: TestClient, admin_auth_headers: dict) -> int:
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
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
def setup_aocs_para_anexo(test_client: TestClient, admin_auth_headers: dict) -> int:
    test_client.post("/api/unidades/", json={"nome": "Unidade (Anexo)"}, headers=admin_auth_headers)
    test_client.post("/api/locais/", json={"descricao": "Local (Anexo)"}, headers=admin_auth_headers)
    test_client.post("/api/agentes/", json={"nome": "Agente (Anexo)"}, headers=admin_auth_headers)
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotação (Anexo)"}, headers=admin_auth_headers)
    
    aocs_payload = {
        "numero_aocs": "AOCS-ANEXO-555/2025",
        "data_criacao": date.today().isoformat(),
        "justificativa": "AOCS para teste de anexo",
        "unidade_requisitante_nome": "Unidade (Anexo)",
        "local_entrega_descricao": "Local (Anexo)",
        "agente_responsavel_nome": "Agente (Anexo)",
        "dotacao_info_orcamentaria": "Dotação (Anexo)"
    }
    response = test_client.post("/api/aocs/", json=aocs_payload, headers=admin_auth_headers)
    assert response.status_code == 201
    return response.json()["id"]

def test_upload_anexo_contrato(test_client: TestClient, admin_auth_headers: dict, setup_contrato_para_anexo: int):
    id_contrato = setup_contrato_para_anexo
    file_name = "teste_contrato.txt"
    file_content = b"Conteudo do anexo do contrato"
    
    data_payload = {"id_entidade": id_contrato, "tipo_entidade": "contrato", "tipo_documento": "Outros"}
    file_payload = {"file": (file_name, file_content, "text/plain")}
    
    response_create = test_client.post(
        "/api/anexos/upload/",
        data=data_payload,
        files=file_payload,
        headers=admin_auth_headers
    )
    
    assert response_create.status_code == 201
    response_json = response_create.json()
    
    assert response_json["nome_original"] == file_name
    assert response_json["id_contrato"] == id_contrato
    assert response_json["id_aocs"] is None # Deve ser nulo

def test_upload_anexo_aocs(test_client: TestClient, admin_auth_headers: dict, setup_aocs_para_anexo: int):
    id_aocs = setup_aocs_para_anexo
    file_name = "teste_aocs.pdf"
    file_content = b"Conteudo do anexo da aocs"

    data_payload = {"id_entidade": id_aocs, "tipo_entidade": "aocs", "tipo_documento": "Nota Fiscal"}
    file_payload = {"file": (file_name, file_content, "application/pdf")}
    
    response = test_client.post(
        "/api/anexos/upload/",
        data=data_payload,
        files=file_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    response_json = response.json()

    assert response_json["nome_original"] == file_name
    assert response_json["id_aocs"] == id_aocs
    assert response_json["id_contrato"] is None # Deve ser nulo

def test_upload_anexo_contrato_e_get_all(test_client: TestClient, admin_auth_headers: dict, setup_contrato_para_anexo: int):
    id_contrato = setup_contrato_para_anexo
    file_name = "anexo_para_get_all.txt"
    file_content = b"Conteudo para o teste de get_all"
    
    response_create = test_client.post(
        "/api/anexos/upload/",
        data={"id_entidade": id_contrato, "tipo_entidade": "contrato", "tipo_documento": "Teste"},
        files={"file": (file_name, file_content, "text/plain")},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201

    response_get_all = test_client.get(
        f"/api/anexos/{id_contrato}/contrato",
        headers=admin_auth_headers
    )
    
    assert response_get_all.status_code == 200
    assert isinstance(response_get_all.json(), list)
    assert len(response_get_all.json()) == 1
    
    response_data = response_get_all.json()[0]
    
    assert response_data["nome_original"] == file_name
    assert response_data["tipo_entidade"] == "contrato"
    assert response_data["id_contrato"] == id_contrato
    assert response_data["id_aocs"] is None

def test_download_e_delete_anexo(test_client: TestClient, admin_auth_headers: dict, setup_contrato_para_anexo: int):
    id_contrato = setup_contrato_para_anexo
    file_name = "anexo_para_download_e_delete.txt"
    file_content = b"Download e Delete"

    response_create = test_client.post(
        "/api/anexos/upload/",
        data={"id_entidade": id_contrato, "tipo_entidade": "contrato", "tipo_documento": "Para Deletar"},
        files={"file": (file_name, file_content, "text/plain")},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]
    nome_seguro = response_create.json()["nome_seguro"]

    response_download = test_client.get(
        f"/api/anexos/download/{new_id}",
        headers=admin_auth_headers
    )
    assert response_download.status_code == 200
    assert response_download.content == file_content
    
    response_delete = test_client.delete(
        f"/api/anexos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204

    response_download_fail = test_client.get(
        f"/api/anexos/download/{new_id}",
        headers=admin_auth_headers
    )
    assert response_download_fail.status_code == 404

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    file_path = os.path.join(BASE_DIR, 'app', nome_seguro)
    
    assert not os.path.exists(file_path), f"O ficheiro físico {file_path} não foi apagado do disco."