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
                                  identificador_entidade: str) -> tuple[str, str, str]:
    """Gera nome seguro, caminho relativo (BD) e caminho absoluto da pasta."""
    nome_original_seguro = secure_filename(original_filename)
    _, extensao = os.path.splitext(nome_original_seguro)
    tipo_doc_limpo = ''.join(c for c in (tipo_doc or 'doc') if c.isalnum() or c == '-').upper()[:15]
    identificador_limpo = ''.join(c for c in identificador_entidade if c.isalnum() or c in ['-', '_']).replace('/', '-')[:20]
    timestamp = int(datetime.now().timestamp())

    nome_arquivo_final = f"{timestamp}_{tipo_doc_limpo}_{identificador_limpo}{extensao}"

    subpasta = os.path.join(tipo_entidade, str(entidade_id)) 

    caminho_relativo_db = os.path.join(subpasta, nome_arquivo_final).replace("\\", "/") 
    caminho_completo_pasta_destino = os.path.join(UPLOAD_FOLDER, subpasta)

    return nome_arquivo_final, caminho_relativo_db, caminho_completo_pasta_destino

@router.post("/upload/",
             response_model=AnexoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))]) 
async def upload_anexo_file(
    id_entidade: int = Form(...),
    tipo_entidade: str = Form(...), 
    tipo_documento: str | None = Form(None),
    file: UploadFile = File(...),
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo_anexo = AnexoRepository(db_conn)
    repo_contrato = ContratoRepository(db_conn)
    repo_aocs = AocsRepository(db_conn)

    if tipo_entidade not in ['contrato', 'aocs']:
        raise HTTPException(status_code=400, detail="Tipo de entidade inválido.")

    identificador_entidade = None
    try:
        if tipo_entidade == 'contrato':
            entidade = repo_contrato.get_by_id(id_entidade)
            if not entidade: raise ValueError("Contrato não encontrado.")
            identificador_entidade = entidade.numero_contrato
        elif tipo_entidade == 'aocs':
            entidade = repo_aocs.get_by_id(id_entidade)
            if not entidade: raise ValueError("AOCS não encontrada.")
            identificador_entidade = entidade.numero_aocs
    except ValueError as e:
        logger.warning(f"Entidade {tipo_entidade} ID {id_entidade} não encontrada p/ upload por '{current_user.username}': {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
         logger.exception(f"Erro ao buscar entidade {tipo_entidade} ID {id_entidade} p/ upload: {e}")
         raise HTTPException(status_code=500, detail="Erro ao verificar entidade.")

    try:
        if not file.filename: 
             raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

        nome_final, caminho_relativo_db, caminho_pasta_destino = _generate_secure_filename_paths(
            file.filename, tipo_documento, id_entidade, tipo_entidade, identificador_entidade
        )
        caminho_completo_arquivo = os.path.join(caminho_pasta_destino, nome_final)
        os.makedirs(caminho_pasta_destino, exist_ok=True)
    except Exception as e:
        logger.exception(f"Erro ao gerar nome/caminho para upload: {e}")
        raise HTTPException(status_code=500, detail="Erro ao preparar salvamento.")

    try:
        with open(caminho_completo_arquivo, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Arquivo '{file.filename}' salvo como '{caminho_completo_arquivo}' por '{current_user.username}'.")
    except Exception as e:
        logger.exception(f"Erro ao salvar arquivo '{caminho_completo_arquivo}': {e}")
        if os.path.exists(caminho_completo_arquivo):
            try: os.remove(caminho_completo_arquivo)
            except OSError: pass
        raise HTTPException(status_code=500, detail="Erro ao salvar arquivo.")
    finally:
        await file.close() 

    try:
        anexo_data = AnexoCreate(
            id_entidade=id_entidade,
            tipo_entidade=tipo_entidade,
            tipo_documento=tipo_documento,
            nome_original=file.filename,
            nome_seguro=caminho_relativo_db, 
        )
        novo_anexo = repo_anexo.create(anexo_data)
        logger.info(f"Usuário '{current_user.username}' fez upload Anexo ID {novo_anexo.id} ('{novo_anexo.nome_original}')")
        return novo_anexo
    except Exception as e:
        logger.exception(f"Erro ao criar registro BD p/ anexo '{caminho_completo_arquivo}': {e}")
        if os.path.exists(caminho_completo_arquivo):
             try: os.remove(caminho_completo_arquivo)
             except OSError: logger.error(f"Não foi possível remover arquivo órfão: {caminho_completo_arquivo}")
        raise HTTPException(status_code=500, detail="Erro ao registrar anexo no banco.")

@router.get("/download/{id}",
            dependencies=[Depends(require_access_level(3))])
async def download_anexo_file(
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AnexoRepository(db_conn)
    anexo = None
    try:
        anexo = repo.get_by_id(id)
        if not anexo or not anexo.nome_seguro: 
            raise HTTPException(status_code=404, detail="Anexo não encontrado ou sem arquivo associado.")

        file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, anexo.nome_seguro))

        if not file_path.startswith(os.path.abspath(UPLOAD_FOLDER)):
            logger.error(f"Tentativa de Path Traversal ao baixar anexo ID {id}. Path: {file_path}")
            raise HTTPException(status_code=403, detail="Acesso negado ao arquivo.")

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
             logger.error(f"Arquivo físico não encontrado para Anexo ID {id}: {file_path}")
             raise HTTPException(status_code=404, detail="Arquivo físico não encontrado.")

        logger.info(f"Usuário '{current_user.username}' baixando Anexo ID {id} ('{anexo.nome_original}') de {file_path}")

        return FileResponse(path=file_path, filename=anexo.nome_original)

    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        logger.exception(f"Erro inesperado ao baixar anexo ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar download.")

@router.get("/", response_model=List[AnexoResponse])
def get_anexos_por_entidade( 
    tipo_entidade: str | None = None,
    id_entidade: int | None = None,
    db_conn: connection = Depends(get_db)
):
    repo = AnexoRepository(db_conn)
    try:
        if tipo_entidade and id_entidade:
            if tipo_entidade not in ['contrato', 'aocs']:
                raise HTTPException(status_code=400, detail="Tipo de entidade inválido.")
            anexos = repo.get_by_entidade(id_entidade=id_entidade, tipo_entidade=tipo_entidade)
        elif tipo_entidade or id_entidade:
             raise HTTPException(status_code=400, detail="Para filtrar, 'tipo_entidade' e 'id_entidade' são necessários.")
        else:
            logger.warning("Listando TODOS os anexos sem filtro.")
            anexos = repo.get_all() 
        return anexos
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar anexos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=AnexoResponse)
def get_anexo_by_id(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = AnexoRepository(db_conn)
    try:
        anexo = repo.get_by_id(id)
        if not anexo:
            logger.warning(f"Anexo ID {id} não encontrado.")
            raise HTTPException(status_code=404, detail="Anexo não encontrado.")
        return anexo

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar anexo ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
    
@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
async def delete_anexo( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AnexoRepository(db_conn)
    success, anexo_deletado = repo.delete(id) 

    if not success and anexo_deletado is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    elif not success and anexo_deletado is not None:
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
             logger.exception(f"Erro inesperado no repo ao deletar anexo ID {id} por '{current_user.username}': {e}")
             raise HTTPException(status_code=500, detail="Erro interno ao deletar anexo.")