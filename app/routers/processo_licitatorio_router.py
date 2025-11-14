from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.processo_licitatorio_model import ProcessoLicitatorio 
from app.schemas.processo_licitatorio_schema import ProcessoLicitatorioRequest, ProcessoLicitatorioResponse 
from app.repositories.processo_licitatorio_repository import ProcessoLicitatorioRepository 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/processos-licitatorios", 
    tags=["Processos Licitatórios"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=ProcessoLicitatorioResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_processo_licitatorio( 
    proc_req: ProcessoLicitatorioRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = ProcessoLicitatorioRepository(db_conn)
        novo_proc = repo.create(proc_req) 
        logger.info(f"Usuário '{current_user.username}' criou Processo Licitatório ID {novo_proc.id} ('{novo_proc.numero}').")
        return novo_proc
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar processo licitatório duplicado: '{proc_req.numero}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Processo Licitatório '{proc_req.numero}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar processo licitatório por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[ProcessoLicitatorioResponse])
def get_all_processos_licitatorios( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ProcessoLicitatorioRepository(db_conn)
        processos = repo.get_all() 
        return processos
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar processos licitatórios: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=ProcessoLicitatorioResponse)
def get_processo_licitatorio_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ProcessoLicitatorioRepository(db_conn)
        processo = repo.get_by_id(id) 
        if not processo:
            logger.warning(f"Processo Licitatório ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processo Licitatório não encontrado."
            )
        return processo
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar processo licitatório ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=ProcessoLicitatorioResponse,
            dependencies=[Depends(require_access_level(2))])
def update_processo_licitatorio( 
    id: int,
    proc_req: ProcessoLicitatorioRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ProcessoLicitatorioRepository(db_conn)
    proc_db = repo.get_by_id(id) 
    if not proc_db:
         logger.warning(f"Tentativa de atualizar processo licitatório ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processo Licitatório não encontrado para atualização."
        )

    try:
        proc_atualizado = repo.update(id, proc_req) 
        if not proc_atualizado:
             logger.error(f"Processo Licitatório ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Processo Licitatório não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Processo Licitatório ID {id} de '{proc_db.numero}' para '{proc_atualizado.numero}'.")
        return proc_atualizado
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar processo licitatório ID {id} para número duplicado '{proc_req.numero}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O número '{proc_req.numero}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar processo licitatório ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_processo_licitatorio( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ProcessoLicitatorioRepository(db_conn)
    proc_para_deletar = repo.get_by_id(id) 
    if not proc_para_deletar:
        logger.warning(f"Tentativa de deletar processo licitatório ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processo Licitatório não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Processo Licitatório ID {id} ('{proc_para_deletar.numero}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Processo Licitatório está vinculado a Contratos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar processo licitatório ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")