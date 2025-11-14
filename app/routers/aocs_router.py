from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.aocs_model import Aocs
from app.schemas.aocs_schema import AocsCreateRequest, AocsUpdateRequest, AocsResponse
from app.repositories.aocs_repository import AocsRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/aocs",
    tags=["AOCS"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=AocsResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_aocs(
    aocs_req: AocsCreateRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = AocsRepository(db_conn)
        nova_aocs = repo.create(aocs_req)
        logger.info(f"Usuário '{current_user.username}' criou AOCS ID {nova_aocs.id} ('{nova_aocs.numero_aocs}').")
        return nova_aocs
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao criar AOCS por '{current_user.username}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar AOCS com número duplicado: '{aocs_req.numero_aocs}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A AOCS '{aocs_req.numero_aocs}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar AOCS por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[AocsResponse])
def get_all_aocs(
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AocsRepository(db_conn)
        lista_aocs = repo.get_all() 
        return lista_aocs
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar AOCS: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=AocsResponse)
def get_aocs_by_id(
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AocsRepository(db_conn)
        aocs = repo.get_by_id(id) 
        if not aocs:
            logger.warning(f"AOCS ID {id} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AOCS não encontrada."
            )
        return aocs
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar AOCS ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/numero/{numero_aocs:path}", response_model=AocsResponse)
def get_aocs_by_numero( 
    numero_aocs: str, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AocsRepository(db_conn)
        aocs = repo.get_by_numero_aocs(numero_aocs) 
        if not aocs:
            logger.warning(f"AOCS com número '{numero_aocs}' não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AOCS com número '{numero_aocs}' não encontrada."
            )
        return aocs
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar AOCS pelo número '{numero_aocs}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")


@router.put("/{id}",
            response_model=AocsResponse,
            dependencies=[Depends(require_access_level(2))])
def update_aocs(
    id: int,
    aocs_req: AocsUpdateRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AocsRepository(db_conn)
    aocs_db = repo.get_by_id(id)
    if not aocs_db:
         logger.warning(f"Tentativa de atualizar AOCS ID {id} (não encontrada) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AOCS não encontrada para atualização."
        )

    try:
        aocs_atualizada = repo.update(id, aocs_req)
        if not aocs_atualizada:
             logger.error(f"AOCS ID {id} não encontrada DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="AOCS não encontrada durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou AOCS ID {id} ('{aocs_atualizada.numero_aocs}').")
        return aocs_atualizada
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao atualizar AOCS ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar AOCS ID {id} para número duplicado '{aocs_req.numero_aocs}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O número AOCS '{aocs_req.numero_aocs}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar AOCS ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_aocs(
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = AocsRepository(db_conn)
    aocs_para_deletar = repo.get_by_id(id)
    if not aocs_para_deletar:
        logger.warning(f"Tentativa de deletar AOCS ID {id} (não encontrada) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AOCS não encontrada para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou AOCS ID {id} ('{aocs_para_deletar.numero_aocs}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. A AOCS possui Pedidos ou CIs vinculados."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar AOCS ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")