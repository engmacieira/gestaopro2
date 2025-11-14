from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.modalidade_model import Modalidade
from app.schemas.modalidade_schema import ModalidadeRequest, ModalidadeResponse
from app.repositories.modalidade_repository import ModalidadeRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/modalidades", 
    tags=["Modalidades"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=ModalidadeResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_modalidade( 
    modalidade_req: ModalidadeRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = ModalidadeRepository(db_conn)
        nova_modalidade = repo.create(modalidade_req) 
        logger.info(f"Usuário '{current_user.username}' criou Modalidade ID {nova_modalidade.id} ('{nova_modalidade.nome}').")
        return nova_modalidade
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar modalidade duplicada: '{modalidade_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A Modalidade '{modalidade_req.nome}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar modalidade por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[ModalidadeResponse])
def get_all_modalidades( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ModalidadeRepository(db_conn)
        modalidades = repo.get_all() 
        return modalidades
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar modalidades: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=ModalidadeResponse)
def get_modalidade_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ModalidadeRepository(db_conn)
        modalidade = repo.get_by_id(id) 
        if not modalidade:
            logger.warning(f"Modalidade ID {id} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modalidade não encontrada."
            )
        return modalidade
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar modalidade ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
    
@router.put("/{id}",
            response_model=ModalidadeResponse,
            dependencies=[Depends(require_access_level(2))])
def update_modalidade( 
    id: int,
    modalidade_req: ModalidadeRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ModalidadeRepository(db_conn)
    modalidade_db = repo.get_by_id(id) 
    if not modalidade_db:
         logger.warning(f"Tentativa de atualizar modalidade ID {id} (não encontrada) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modalidade não encontrada para atualização."
        )

    try:
        modalidade_atualizada = repo.update(id, modalidade_req) 
        if not modalidade_atualizada:
             logger.error(f"Modalidade ID {id} não encontrada DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Modalidade não encontrada durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Modalidade ID {id} de '{modalidade_db.nome}' para '{modalidade_atualizada.nome}'.")
        return modalidade_atualizada
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar modalidade ID {id} para nome duplicado '{modalidade_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O nome '{modalidade_req.nome}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar modalidade ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_modalidade( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ModalidadeRepository(db_conn)
    modalidade_para_deletar = repo.get_by_id(id) 
    if not modalidade_para_deletar:
        logger.warning(f"Tentativa de deletar modalidade ID {id} (não encontrada) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modalidade não encontrada para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Modalidade ID {id} ('{modalidade_para_deletar.nome}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta Modalidade está vinculada a Contratos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar modalidade ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")