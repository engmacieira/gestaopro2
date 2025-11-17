from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from psycopg2.extensions import connection
import psycopg2
import logging
import os 
import shutil 
from typing import List
from datetime import date 
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.anexo_model import Anexo
from app.schemas.anexo_schema import AnexoCreate, AnexoResponse
from app.repositories.anexo_repository import AnexoRepository
from app.repositories.contrato_repository import ContratoRepository
from app.repositories.aocs_repository import AocsRepository
from werkzeug.utils import secure_filename 
from datetime import datetime

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
BASE_DIR = os.path.dirname(APP_DIR)
UPLOAD_FOLDER = os.path.join(BASE_DIR, os.environ.get("UPLOAD_FOLDER", "uploads"))

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/anexos",
    tags=["Anexos"],
    dependencies=[Depends(require_access_level(3))]
)

def _generate_secure_filename_paths(original_filename: str, tipo_doc: str | None,
                                  entidade_id: int, tipo_entidade: str, 
                                  db_conn: connection) -> tuple[str, str, str]:

    if tipo_doc:
        tipo_doc_saneado = secure_filename(tipo_doc).upper()
    else:
        tipo_doc_saneado = "OUTROS"
    
    entidade_nome = f"ENTIDADE-{entidade_id}"
    try:
        if tipo_entidade == 'contrato':
            entidade_obj = ContratoRepository(db_conn).get_by_id(entidade_id)
            if entidade_obj: entidade_nome = f"CT-{entidade_obj.numero_contrato}"
        elif tipo_entidade == 'aocs':
            entidade_obj = AocsRepository(db_conn).get_by_id(entidade_id)
            if entidade_obj: entidade_nome = f"AOCS-{entidade_obj.numero_aocs}"
    except Exception as e:
        logger.error(f"Erro ao buscar entidade (ID {entidade_id}, Tipo {tipo_entidade}) para nomear anexo: {e}")

    timestamp = int(datetime.now().timestamp())
    nome_base, extensao = os.path.splitext(original_filename)
    nome_seguro_base = f"{timestamp}_{tipo_doc_saneado}_{secure_filename(entidade_nome)}{extensao}"
    
    path_relativo = os.path.join(tipo_entidade, str(entidade_id))
    path_absoluto_save = os.path.join(UPLOAD_FOLDER, path_relativo)
    nome_seguro_com_path = os.path.join(path_relativo, nome_seguro_base).replace("\\", "/")
    
    return path_absoluto_save, nome_seguro_base, nome_seguro_com_path

@router.get("/download/{id}", 
            response_class=FileResponse,
            dependencies=[Depends(require_access_level(3))])
async def download_anexo(id: int, db_conn: connection = Depends(get_db)):

    repo = AnexoRepository(db_conn)
    anexo = repo.get_by_id(id)
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    
    file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, anexo.nome_seguro))
    
    if not file_path.startswith(os.path.abspath(UPLOAD_FOLDER)):
        logger.error(f"Tentativa de Path Traversal ao baixar anexo ID {id}. Path: {file_path}")
        raise HTTPException(status_code=403, detail="Acesso negado.")
        
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado no disco (ID {id}), mas existe no BD: {file_path}")
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor, embora exista registro.")

    return FileResponse(path=file_path, filename=anexo.nome_original, media_type='application/octet-stream')

@router.get("/{id_entidade}/{tipo_entidade}", 
            response_model=List[AnexoResponse],
            status_code=status.HTTP_200_OK)
def get_anexos_por_entidade(
    id_entidade: int, 
    tipo_entidade: str, 
    db_conn: connection = Depends(get_db)
):

    try:
        repo_anexo = AnexoRepository(db_conn)
        anexos = repo_anexo.get_by_entidade(id_entidade, tipo_entidade)
        return anexos
    
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar anexos para {tipo_entidade} ID {id_entidade}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.post("/upload/", 
             response_model=AnexoResponse, 
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
async def upload_file(
    file: UploadFile = File(...), 
    id_entidade: int = Form(...),
    tipo_entidade: str = Form(...),
    tipo_documento: str = Form(None),
    current_user: User = Depends(get_current_user),
    db_conn: connection = Depends(get_db)
):

    try:
        save_dir, _, nome_seguro_com_path = _generate_secure_filename_paths(
            file.filename, tipo_documento, id_entidade, tipo_entidade, db_conn
        )
        os.makedirs(save_dir, exist_ok=True)
        file_path_save = os.path.join(save_dir, os.path.basename(nome_seguro_com_path))
        
        with open(file_path_save, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    except Exception as e:
        logger.exception(f"Erro ao salvar arquivo físico '{file.filename}' por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar o arquivo no servidor.")
    finally:
        file.file.close()

    try:

        repo = AnexoRepository(db_conn)
        anexo_data = AnexoCreate(
            id_entidade=id_entidade, 
            tipo_entidade=tipo_entidade,
            tipo_documento=tipo_documento,
            nome_original=file.filename,
            nome_seguro=nome_seguro_com_path,
        )
        novo_anexo = repo.create(anexo_data) 
        
        logger.info(f"Usuário '{current_user.username}' fez upload Anexo ID {novo_anexo.id} ('{novo_anexo.nome_original}')")
        return novo_anexo
        
    except Exception as e:
        logger.exception(f"Erro ao criar registro do anexo '{file.filename}' no BD por '{current_user.username}': {e}")
        try:
            if os.path.exists(file_path_save):
                os.remove(file_path_save)
        except Exception as e_clean:
            logger.error(f"Erro CRÍTICO ao limpar ficheiro órfão {file_path_save}: {e_clean}")
        raise HTTPException(status_code=500, detail="Erro ao gravar informações do arquivo no banco.")


@router.delete("/{id}", 
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
async def delete_anexo(
    id: int,
    current_user: User = Depends(get_current_user), 
    db_conn: connection = Depends(get_db)
):

    repo = AnexoRepository(db_conn)
    success, anexo_deletado = repo.delete(id)
    
    if not success and anexo_deletado is None:
         raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    elif not success and anexo_deletado is not None:
         logger.error(f"Falha ao deletar anexo ID {id} (existente). Nenhuma linha afetada.")
         raise HTTPException(status_code=500, detail="Erro ao deletar registro do anexo.")
    elif success and anexo_deletado:
        try:
            file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, anexo_deletado.nome_seguro))
            
            if not file_path.startswith(os.path.abspath(UPLOAD_FOLDER)):
                 logger.error(f"Tentativa de Path Traversal ao deletar anexo ID {id}. Path: {file_path}")
            elif os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Usuário '{current_user.username}' deletou arquivo físico: {file_path}")
            else:
                logger.warning(f"Arquivo físico não encontrado para anexo ID {id} deletado do banco: {file_path}")
            return 

        except OSError as e:
            logger.exception(f"Erro OS ao deletar arquivo físico {anexo_deletado.nome_seguro} (anexo ID {id}, registro BD removido): {e}")
            raise HTTPException(status_code=500, detail="Erro ao deletar o arquivo físico associado.")
        except psycopg2.IntegrityError: 
             raise HTTPException(status_code=409, detail="Erro de integridade ao deletar anexo.")
        except Exception as e: 
             logger.exception(f"Erro inesperado ao deletar arquivo físico anexo ID {id}: {e}")
             raise HTTPException(status_code=500, detail="Erro interno do servidor ao limpar arquivo.")