from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.local_model import Local 
from app.schemas.local_schema import LocalRequest, LocalResponse 
from app.repositories.local_repository import LocalRepository 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/locais", 
    tags=["Locais de Entrega"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=LocalResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_local( 
    local_req: LocalRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = LocalRepository(db_conn)
        novo_local = repo.create(local_req) 
        logger.info(f"Usuário '{current_user.username}' criou Local ID {novo_local.id} ('{novo_local.descricao}').")
        return novo_local
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar local duplicado: '{local_req.descricao}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Local de Entrega '{local_req.descricao}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar local por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[LocalResponse])
def get_all_locais( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = LocalRepository(db_conn)
        locais = repo.get_all() 
        return locais
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar locais: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=LocalResponse)
def get_local_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = LocalRepository(db_conn)
        local = repo.get_by_id(id) 
        if not local:
            logger.warning(f"Local ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local de Entrega não encontrado."
            )
        return local
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar local ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=LocalResponse,
            dependencies=[Depends(require_access_level(2))])
def update_local( 
    id: int,
    local_req: LocalRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = LocalRepository(db_conn)
    local_db = repo.get_by_id(id) 
    if not local_db:
         logger.warning(f"Tentativa de atualizar local ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local de Entrega não encontrado para atualização."
        )

    try:
        local_atualizado = repo.update(id, local_req) 
        if not local_atualizado:
             logger.error(f"Local ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Local não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Local ID {id} de '{local_db.descricao}' para '{local_atualizado.descricao}'.")
        return local_atualizado
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar local ID {id} para descrição duplicada '{local_req.descricao}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A descrição '{local_req.descricao}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar local ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_local( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = LocalRepository(db_conn)
    local_para_deletar = repo.get_by_id(id) 
    if not local_para_deletar:
        logger.warning(f"Tentativa de deletar local ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local de Entrega não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Local ID {id} ('{local_para_deletar.descricao}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Local de Entrega está vinculado a AOCS."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar local ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")