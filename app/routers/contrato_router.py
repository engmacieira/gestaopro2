from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.contrato_model import Contrato
from app.schemas.contrato_schema import ContratoCreateRequest, ContratoUpdateRequest, ContratoResponse
from app.repositories.contrato_repository import ContratoRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/contratos", 
    tags=["Contratos"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=ContratoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_contrato( 
    contrato_req: ContratoCreateRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = ContratoRepository(db_conn)
        novo_contrato = repo.create(contrato_req) 
        logger.info(f"Usuário '{current_user.username}' criou Contrato ID {novo_contrato.id} ('{novo_contrato.numero_contrato}').")
        return novo_contrato
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao criar Contrato por '{current_user.username}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar Contrato duplicado: '{contrato_req.numero_contrato}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Contrato '{contrato_req.numero_contrato}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar Contrato por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[ContratoResponse])
def get_all_contratos( 
    mostrar_inativos: bool = False, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ContratoRepository(db_conn)
        contratos = repo.get_all(mostrar_inativos) 
        return contratos
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar Contratos (inativos={mostrar_inativos}): {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=ContratoResponse)
def get_contrato_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ContratoRepository(db_conn)
        contrato = repo.get_by_id(id) 
        if not contrato:
            logger.warning(f"Contrato ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado."
            )
        return contrato
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar Contrato ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/numero/{numero_contrato:path}", response_model=ContratoResponse)
def get_contrato_by_numero(
    numero_contrato: str,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ContratoRepository(db_conn)
        contrato = repo.get_by_numero_contrato(numero_contrato)
        if not contrato:
            logger.warning(f"Contrato com número '{numero_contrato}' não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contrato com número '{numero_contrato}' não encontrado."
            )
        return contrato
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar Contrato pelo número '{numero_contrato}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=ContratoResponse,
            dependencies=[Depends(require_access_level(2))])
def update_contrato( 
    id: int,
    contrato_req: ContratoUpdateRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ContratoRepository(db_conn)
    contrato_db = repo.get_by_id(id)
    if not contrato_db:
         logger.warning(f"Tentativa de atualizar Contrato ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado para atualização."
        )

    try:
        contrato_atualizado = repo.update(id, contrato_req)
        if not contrato_atualizado:
             logger.error(f"Contrato ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Contrato não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Contrato ID {id} ('{contrato_atualizado.numero_contrato}').")
        return contrato_atualizado
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao atualizar Contrato ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Erro de integridade ao atualizar Contrato ID {id} (Num Contrato duplicado?) por '{current_user.username}'. Req: {contrato_req.model_dump(exclude_unset=True)}")
        detail = "Erro de integridade ao atualizar Contrato."
        if contrato_req.numero_contrato:
            detail = f"O número de Contrato '{contrato_req.numero_contrato}' já pode estar em uso."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar Contrato ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.patch("/{id}/status",
             response_model=ContratoResponse,
             dependencies=[Depends(require_access_level(2))])
def set_contrato_status(
    id: int,
    activate: bool, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ContratoRepository(db_conn)
    contrato_atualizado = repo.set_active_status(id, activate) 

    if not contrato_atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado para alterar status."
        )

    action_str = "ativado" if activate else "desativado"
    logger.info(f"Usuário '{current_user.username}' {action_str} Contrato ID {id} ('{contrato_atualizado.numero_contrato}').")
    return contrato_atualizado

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_contrato( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ContratoRepository(db_conn)
    contrato_para_deletar = repo.get_by_id(id)
    if not contrato_para_deletar:
        logger.warning(f"Tentativa de deletar Contrato ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Contrato ID {id} ('{contrato_para_deletar.numero_contrato}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Contrato possui Itens vinculados."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar Contrato ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")