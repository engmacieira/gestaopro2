from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.numero_modalidade_model import NumeroModalidade 
from app.schemas.numero_modalidade_schema import NumeroModalidadeRequest, NumeroModalidadeResponse 
from app.repositories.numero_modalidade_repository import NumeroModalidadeRepository 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/numeros-modalidade", 
    tags=["Números de Modalidade"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=NumeroModalidadeResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_numero_modalidade( 
    num_mod_req: NumeroModalidadeRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = NumeroModalidadeRepository(db_conn)
        novo_num_mod = repo.create(num_mod_req) 
        logger.info(f"Usuário '{current_user.username}' criou NumeroModalidade ID {novo_num_mod.id} ('{novo_num_mod.numero_ano}').")
        return novo_num_mod
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar numero_modalidade duplicado: '{num_mod_req.numero_ano}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Número/Ano de Modalidade '{num_mod_req.numero_ano}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar numero_modalidade por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[NumeroModalidadeResponse])
def get_all_numeros_modalidade( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = NumeroModalidadeRepository(db_conn)
        numeros_modalidade = repo.get_all() 
        return numeros_modalidade
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar numeros_modalidade: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=NumeroModalidadeResponse)
def get_numero_modalidade_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = NumeroModalidadeRepository(db_conn)
        num_mod = repo.get_by_id(id) 
        if not num_mod:
            logger.warning(f"NumeroModalidade ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Número/Ano de Modalidade não encontrado."
            )
        return num_mod
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar numero_modalidade ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=NumeroModalidadeResponse,
            dependencies=[Depends(require_access_level(2))])
def update_numero_modalidade( 
    id: int,
    num_mod_req: NumeroModalidadeRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = NumeroModalidadeRepository(db_conn)
    num_mod_db = repo.get_by_id(id) 
    if not num_mod_db:
         logger.warning(f"Tentativa de atualizar numero_modalidade ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Número/Ano de Modalidade não encontrado para atualização."
        )

    try:
        num_mod_atualizado = repo.update(id, num_mod_req) 
        if not num_mod_atualizado:
             logger.error(f"NumeroModalidade ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Número/Ano de Modalidade não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou NumeroModalidade ID {id} de '{num_mod_db.numero_ano}' para '{num_mod_atualizado.numero_ano}'.")
        return num_mod_atualizado
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar numero_modalidade ID {id} para valor duplicado '{num_mod_req.numero_ano}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O valor '{num_mod_req.numero_ano}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar numero_modalidade ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_numero_modalidade( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = NumeroModalidadeRepository(db_conn)
    num_mod_para_deletar = repo.get_by_id(id) 
    if not num_mod_para_deletar:
        logger.warning(f"Tentativa de deletar numero_modalidade ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Número/Ano de Modalidade não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou NumeroModalidade ID {id} ('{num_mod_para_deletar.numero_ano}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Número/Ano de Modalidade está vinculado a Contratos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar numero_modalidade ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")