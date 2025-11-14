from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.unidade_model import Unidade 
from app.schemas.unidade_schema import UnidadeRequest, UnidadeResponse 
from app.repositories.unidade_repository import UnidadeRepository 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/unidades", 
    tags=["Unidades Requisitantes"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=UnidadeResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_unidade( 
    unidade_req: UnidadeRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = UnidadeRepository(db_conn)
        nova_unidade = repo.create(unidade_req) 
        logger.info(f"Usuário '{current_user.username}' criou Unidade ID {nova_unidade.id} ('{nova_unidade.nome}').")
        return nova_unidade
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar unidade duplicada: '{unidade_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A Unidade Requisitante '{unidade_req.nome}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar unidade por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[UnidadeResponse])
def get_all_unidades( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = UnidadeRepository(db_conn)
        unidades = repo.get_all() 
        return unidades
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar unidades: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=UnidadeResponse)
def get_unidade_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = UnidadeRepository(db_conn)
        unidade = repo.get_by_id(id) 
        if not unidade:
            logger.warning(f"Unidade ID {id} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade Requisitante não encontrada."
            )
        return unidade
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar unidade ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=UnidadeResponse,
            dependencies=[Depends(require_access_level(2))])
def update_unidade( 
    id: int,
    unidade_req: UnidadeRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = UnidadeRepository(db_conn)
    unidade_db = repo.get_by_id(id) 
    if not unidade_db:
         logger.warning(f"Tentativa de atualizar unidade ID {id} (não encontrada) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade Requisitante não encontrada para atualização."
        )

    try:
        unidade_atualizada = repo.update(id, unidade_req) 
        if not unidade_atualizada:
             logger.error(f"Unidade ID {id} não encontrada DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Unidade não encontrada durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Unidade ID {id} de '{unidade_db.nome}' para '{unidade_atualizada.nome}'.")
        return unidade_atualizada
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar unidade ID {id} para nome duplicado '{unidade_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O nome '{unidade_req.nome}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar unidade ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_unidade( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = UnidadeRepository(db_conn)
    unidade_para_deletar = repo.get_by_id(id) 
    if not unidade_para_deletar:
        logger.warning(f"Tentativa de deletar unidade ID {id} (não encontrada) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade Requisitante não encontrada para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Unidade ID {id} ('{unidade_para_deletar.nome}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta Unidade está vinculada a AOCS ou CIs."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar unidade ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")