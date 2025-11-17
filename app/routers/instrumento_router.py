from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.instrumento_model import Instrumento
from app.schemas.instrumento_schema import InstrumentoRequest, InstrumentoResponse
from app.repositories.instrumento_repository import InstrumentoRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/instrumentos", 
    tags=["Instrumentos Contratuais"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=InstrumentoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_instrumento( 
    instrumento_req: InstrumentoRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = InstrumentoRepository(db_conn)
        novo_instrumento = repo.create(instrumento_req) 
        logger.info(f"Usuário '{current_user.username}' criou Instrumento ID {novo_instrumento.id} ('{novo_instrumento.nome}').")
        return novo_instrumento
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar instrumento duplicado: '{instrumento_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Instrumento Contratual '{instrumento_req.nome}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar instrumento por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=List[InstrumentoResponse])
def get_all_instrumentos( 
    db_conn: connection = Depends(get_db)
):

    try:
        repo = InstrumentoRepository(db_conn)
        
        instrumentos = repo.get_all() 
        
        return instrumentos
    
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar todos os instrumentos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=InstrumentoResponse)
def get_instrumento_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = InstrumentoRepository(db_conn)
        instrumento = repo.get_by_id(id) 
        if not instrumento:
            logger.warning(f"Instrumento ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrumento Contratual não encontrado."
            )
        return instrumento
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar instrumento ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
    
@router.put("/{id}",
            response_model=InstrumentoResponse,
            dependencies=[Depends(require_access_level(2))])
def update_instrumento( 
    id: int,
    instrumento_req: InstrumentoRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = InstrumentoRepository(db_conn)
    instrumento_db = repo.get_by_id(id) 
    if not instrumento_db:
         logger.warning(f"Tentativa de atualizar instrumento ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrumento Contratual não encontrado para atualização."
        )

    try:
        instrumento_atualizado = repo.update(id, instrumento_req) 
        if not instrumento_atualizado:
             logger.error(f"Instrumento ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Instrumento não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Instrumento ID {id} de '{instrumento_db.nome}' para '{instrumento_atualizado.nome}'.")
        return instrumento_atualizado
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar instrumento ID {id} para nome duplicado '{instrumento_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O nome '{instrumento_req.nome}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar instrumento ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_instrumento( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = InstrumentoRepository(db_conn)
    instrumento_para_deletar = repo.get_by_id(id) 
    if not instrumento_para_deletar:
        logger.warning(f"Tentativa de deletar instrumento ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instrumento Contratual não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Instrumento ID {id} ('{instrumento_para_deletar.nome}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Instrumento Contratual está vinculado a Contratos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar instrumento ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")