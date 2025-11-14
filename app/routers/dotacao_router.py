from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.dotacao_model import Dotacao
from app.schemas.dotacao_schema import DotacaoRequest, DotacaoResponse
from app.repositories.dotacao_repository import DotacaoRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dotacoes", 
    tags=["Dotações"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=DotacaoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_dotacao( 
    dotacao_req: DotacaoRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = DotacaoRepository(db_conn)
        nova_dotacao = repo.create(dotacao_req) 
        logger.info(f"Usuário '{current_user.username}' criou Dotação ID {nova_dotacao.id} ('{nova_dotacao.info_orcamentaria}').")
        return nova_dotacao
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar dotação duplicada: '{dotacao_req.info_orcamentaria}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A Dotação '{dotacao_req.info_orcamentaria}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar dotação por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[DotacaoResponse])
def get_all_dotacoes( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = DotacaoRepository(db_conn)
        dotacoes = repo.get_all() 
        return dotacoes
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar dotações: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=DotacaoResponse)
def get_dotacao_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = DotacaoRepository(db_conn)
        dotacao = repo.get_by_id(id) 
        if not dotacao:
            logger.warning(f"Dotação ID {id} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dotação não encontrada."
            )
        return dotacao
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar dotação ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=DotacaoResponse,
            dependencies=[Depends(require_access_level(2))])
def update_dotacao( 
    id: int,
    dotacao_req: DotacaoRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = DotacaoRepository(db_conn)
    dotacao_db = repo.get_by_id(id) 
    if not dotacao_db:
         logger.warning(f"Tentativa de atualizar dotação ID {id} (não encontrada) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dotação não encontrada para atualização."
        )

    try:
        dotacao_atualizada = repo.update(id, dotacao_req) 
        if not dotacao_atualizada:
             logger.error(f"Dotação ID {id} não encontrada DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Dotação não encontrada durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Dotação ID {id} de '{dotacao_db.info_orcamentaria}' para '{dotacao_atualizada.info_orcamentaria}'.")
        return dotacao_atualizada
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar dotação ID {id} para valor duplicado '{dotacao_req.info_orcamentaria}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A informação orçamentária '{dotacao_req.info_orcamentaria}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar dotação ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_dotacao( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = DotacaoRepository(db_conn)
    dotacao_para_deletar = repo.get_by_id(id) 
    if not dotacao_para_deletar:
        logger.warning(f"Tentativa de deletar dotação ID {id} (não encontrada) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dotação não encontrada para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Dotação ID {id} ('{dotacao_para_deletar.info_orcamentaria}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta Dotação está vinculada a AOCS ou CIs."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar dotação ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")