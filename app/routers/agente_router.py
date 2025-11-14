from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.agente_model import Agente
from app.schemas.agente_schema import AgenteRequest, AgenteResponse
from app.repositories.agente_repository import AgenteRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agentes",
    tags=["Agentes"],
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=AgenteResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_agente(
    agente_req: AgenteRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    try:
        repo = AgenteRepository(db_conn)
        novo_agente = repo.create(agente_req)
        logger.info(f"Usuário '{current_user.username}' criou Agente ID {novo_agente.id} ('{novo_agente.nome}').")
        return novo_agente
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar agente com nome duplicado: '{agente_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Agente Responsável '{agente_req.nome}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar agente por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[AgenteResponse])
def get_all_agentes(
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AgenteRepository(db_conn)
        agentes = repo.get_all()
        return agentes
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar agentes: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=AgenteResponse)
def get_agente_by_id(
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AgenteRepository(db_conn)
        agente = repo.get_by_id(id)
        if not agente:
            logger.warning(f"Agente ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agente Responsável não encontrado."
            )
        return agente
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e: 
        logger.exception(f"Erro inesperado ao buscar agente ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=AgenteResponse,
            dependencies=[Depends(require_access_level(2))])
def update_agente(
    id: int,
    agente_req: AgenteRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AgenteRepository(db_conn)
    agente_db = repo.get_by_id(id) 
    if not agente_db:
         logger.warning(f"Tentativa de atualizar agente ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente Responsável não encontrado para atualização."
        )

    try:
        agente_atualizado = repo.update(id, agente_req)
        if not agente_atualizado:
             logger.error(f"Agente ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Agente não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Agente ID {id} de '{agente_db.nome}' para '{agente_atualizado.nome}'.")
        return agente_atualizado
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar agente ID {id} para nome duplicado '{agente_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O nome '{agente_req.nome}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar agente ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_agente(
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AgenteRepository(db_conn)
    agente_para_deletar = repo.get_by_id(id)
    if not agente_para_deletar:
        logger.warning(f"Tentativa de deletar agente ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente Responsável não encontrado para exclusão."
        )

    try:
        repo.delete(id)
        logger.info(f"Usuário '{current_user.username}' deletou Agente ID {id} ('{agente_para_deletar.nome}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Agente Responsável está vinculado a uma ou mais AOCS."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar agente ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")