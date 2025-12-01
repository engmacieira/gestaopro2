import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from psycopg2.extensions import connection
import logging

from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.schemas.anexo_schema import AnexoCreate, AnexoResponse
from app.repositories.anexo_repository import AnexoRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/anexos",
    tags=["Anexos"],
    dependencies=[Depends(require_access_level(2))] # Requer nível 2 para gerenciar
)

# Defina o diretório de upload (ajuste conforme sua estrutura)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/", status_code=status.HTTP_201_CREATED)
async def upload_file(
    tipo_entidade: str = Form(...),
    id_entidade: int = Form(...),
    tipo_documento: str = Form(...),
    tipo_documento_novo: str = Form(None),
    file: UploadFile = File(...),
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Lógica para tipo de documento "NOVO"
        tipo_doc_final = tipo_documento
        if tipo_documento == "NOVO" and tipo_documento_novo:
            tipo_doc_final = tipo_documento_novo
            # Opcional: Salvar o novo tipo na tabela tipos_documento se desejar
        
        # 1. Salvar arquivo no disco
        # Cria estrutura de pastas organizada: uploads/contrato/123/arquivo.pdf
        entidade_dir = os.path.join(UPLOAD_DIR, tipo_entidade, str(id_entidade))
        os.makedirs(entidade_dir, exist_ok=True)
        
        # Gera nome seguro e único para evitar sobrescrita
        import time
        timestamp = int(time.time())
        nome_seguro = f"{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join(entidade_dir, nome_seguro)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Caminho relativo para salvar no banco (para ser servido depois)
        # Ex: contrato/123/169876543_arquivo.pdf
        caminho_relativo = f"{tipo_entidade}/{id_entidade}/{nome_seguro}"

        # 2. Salvar metadados no Banco
        anexo_data = AnexoCreate(
            nome_original=file.filename,
            nome_seguro=caminho_relativo, # Salvamos o caminho relativo aqui
            tipo_documento=tipo_doc_final,
            tipo_entidade=tipo_entidade,
            id_entidade=id_entidade
        )
        
        repo = AnexoRepository(db_conn)
        novo_anexo = repo.create(anexo_data)
        
        logger.info(f"Usuário '{current_user.username}' fez upload Anexo ID {novo_anexo.id} ('{novo_anexo.nome_original}')")
        return {"mensagem": "Upload realizado com sucesso", "anexo": novo_anexo}

    except Exception as e:
        logger.exception(f"Erro ao criar registro do anexo '{file.filename}' no BD por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar anexo: {str(e)}")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_anexo(
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AnexoRepository(db_conn)
    anexo = repo.get_by_id(id)
    
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
        
    try:
        # 1. Remove do Banco
        repo.delete(id)
        
        # 2. Remove do Disco
        # Reconstrói o caminho completo
        file_path = os.path.join(UPLOAD_DIR, anexo.nome_seguro) # nome_seguro guarda o caminho relativo
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Arquivo físico '{file_path}' removido.")
        else:
            logger.warning(f"Arquivo físico não encontrado para remoção: {file_path}")
            
        logger.info(f"Usuário '{current_user.username}' deletou Anexo ID {id}.")
        return

    except Exception as e:
        logger.exception(f"Erro ao deletar anexo ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao excluir anexo.")

# --- NOVA ROTA PARA DOWNLOAD ---
@router.get("/{id}/download", name="download_anexo_file")
def download_anexo(
    id: int,
    db_conn: connection = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Opcional: proteger download
):
    repo = AnexoRepository(db_conn)
    anexo = repo.get_by_id(id)
    
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    
    # Reconstrói o caminho completo
    # O campo nome_seguro no banco deve conter algo como: aocs/79/1764611548_arquivo.pdf
    file_path = os.path.join(UPLOAD_DIR, anexo.nome_seguro)
    
    if not os.path.exists(file_path):
        logger.error(f"Arquivo físico não encontrado no disco: {file_path}")
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado no servidor.")
        
    return FileResponse(
        path=file_path, 
        filename=anexo.nome_original, # Nome original para o usuário baixar
        media_type='application/octet-stream' # Força download
    )