from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.tipo_documento_model import TipoDocumento 
from app.schemas.tipo_documento_schema import TipoDocumentoRequest, TipoDocumentoResponse 
from app.repositories.tipo_documento_repository import TipoDocumentoRepository 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tipos-documento", 
    tags=["Tipos de Documento"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=TipoDocumentoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_tipo_documento( 
    tipo_doc_req: TipoDocumentoRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = TipoDocumentoRepository(db_conn)
        novo_tipo_doc = repo.create(tipo_doc_req) 
        logger.info(f"Usuário '{current_user.username}' criou TipoDocumento ID {novo_tipo_doc.id} ('{novo_tipo_doc.nome}').")
        return novo_tipo_doc
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar tipo de documento duplicado: '{tipo_doc_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Tipo de Documento '{tipo_doc_req.nome}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar tipo de documento por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[TipoDocumentoResponse])
def get_all_tipos_documento( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = TipoDocumentoRepository(db_conn)
        tipos_documento = repo.get_all() 
        return tipos_documento
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar tipos de documento: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=TipoDocumentoResponse)
def get_tipo_documento_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = TipoDocumentoRepository(db_conn)
        tipo_documento = repo.get_by_id(id) 
        if not tipo_documento:
            logger.warning(f"TipoDocumento ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo de Documento não encontrado."
            )
        return tipo_documento
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar tipo de documento ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=TipoDocumentoResponse,
            dependencies=[Depends(require_access_level(2))])
def update_tipo_documento( 
    id: int,
    tipo_doc_req: TipoDocumentoRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = TipoDocumentoRepository(db_conn)
    tipo_doc_db = repo.get_by_id(id) 
    if not tipo_doc_db:
         logger.warning(f"Tentativa de atualizar tipo de documento ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de Documento não encontrado para atualização."
        )

    try:
        tipo_doc_atualizado = repo.update(id, tipo_doc_req) 
        if not tipo_doc_atualizado:
             logger.error(f"TipoDocumento ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Tipo de Documento não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou TipoDocumento ID {id} de '{tipo_doc_db.nome}' para '{tipo_doc_atualizado.nome}'.")
        return tipo_doc_atualizado
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar tipo de documento ID {id} para nome duplicado '{tipo_doc_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O nome '{tipo_doc_req.nome}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar tipo de documento ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_tipo_documento( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = TipoDocumentoRepository(db_conn)
    tipo_doc_para_deletar = repo.get_by_id(id) 
    if not tipo_doc_para_deletar:
        logger.warning(f"Tentativa de deletar tipo de documento ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de Documento não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou TipoDocumento ID {id} ('{tipo_doc_para_deletar.nome}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Tipo de Documento está vinculado a Anexos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar tipo de documento ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")