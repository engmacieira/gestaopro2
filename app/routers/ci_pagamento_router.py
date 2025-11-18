from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.ci_pagamento_model import CiPagamento 
from app.schemas.ci_pagamento_schema import CiPagamentoCreateRequest, CiPagamentoUpdateRequest, CiPagamentoResponse
from app.repositories.ci_pagamento_repository import CiPagamentoRepository 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ci-pagamento", 
    tags=["CI Pagamento"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=CiPagamentoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_ci_pagamento( 
    ci_req: CiPagamentoCreateRequest, 
    id_pedido: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = CiPagamentoRepository(db_conn)
        nova_ci = repo.create(ci_req, id_pedido)
        logger.info(f"Usuário '{current_user.username}' criou CI Pagamento ID {nova_ci.id} ('{nova_ci.numero_ci}').")
        return nova_ci
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao criar CI por '{current_user.username}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar CI duplicada (Num CI/NF?): '{ci_req.numero_ci}' / '{ci_req.numero_nota_fiscal}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A CI ou Nota Fiscal '{ci_req.numero_ci}' / '{ci_req.numero_nota_fiscal}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar CI por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[CiPagamentoResponse])
def get_all_ci_pagamentos( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CiPagamentoRepository(db_conn)
        ci_list = repo.get_all() 
        return ci_list
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar CIs de Pagamento: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=CiPagamentoResponse)
def get_ci_pagamento_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CiPagamentoRepository(db_conn)
        ci = repo.get_by_id(id) 
        if not ci:
            logger.warning(f"CI Pagamento ID {id} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CI de Pagamento não encontrada."
            )
        return ci
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar CI Pagamento ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/por-pedido/{id_pedido}", response_model=CiPagamentoResponse)
def get_ci_pagamento_by_pedido_id( 
    id_pedido: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CiPagamentoRepository(db_conn)
        ci = repo.get_by_pedido_id(id_pedido) 
        if not ci:
            logger.warning(f"CI Pagamento para Pedido ID {id_pedido} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CI de Pagamento não encontrada para este Pedido."
            )
        return ci
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar CI Pagamento por Pedido ID {id_pedido}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=CiPagamentoResponse,
            dependencies=[Depends(require_access_level(2))])
def update_ci_pagamento( 
    id: int,
    ci_req: CiPagamentoUpdateRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = CiPagamentoRepository(db_conn)
    ci_db = repo.get_by_id(id)
    if not ci_db:
         logger.warning(f"Tentativa de atualizar CI Pagamento ID {id} (não encontrada) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CI de Pagamento não encontrada para atualização."
        )

    try:
        ci_atualizada = repo.update(id, ci_req)
        if not ci_atualizada:
             logger.error(f"CI Pagamento ID {id} não encontrada DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="CI Pagamento não encontrada durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou CI Pagamento ID {id} ('{ci_atualizada.numero_ci}').")
        return ci_atualizada
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao atualizar CI ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Erro de integridade ao atualizar CI ID {id} (Num CI/NF duplicado?) por '{current_user.username}'. Req: {ci_req.model_dump(exclude_unset=True)}")
        detail = "Erro de integridade ao atualizar CI."
        if ci_req.numero_ci: detail += f" O número CI '{ci_req.numero_ci}' pode já estar em uso."
        if ci_req.numero_nota_fiscal: detail += f" O número NF '{ci_req.numero_nota_fiscal}' pode já estar em uso."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar CI ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_ci_pagamento( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = CiPagamentoRepository(db_conn)
    ci_para_deletar = repo.get_by_id(id)
    if not ci_para_deletar:
        logger.warning(f"Tentativa de deletar CI Pagamento ID {id} (não encontrada) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CI de Pagamento não encontrada para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou CI Pagamento ID {id} ('{ci_para_deletar.numero_ci}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir esta CI de Pagamento (Erro de integridade)."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar CI Pagamento ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")