from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.categoria_model import Categoria
from app.schemas.categoria_schema import CategoriaRequest, CategoriaResponse
from app.repositories.categoria_repository import CategoriaRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/categorias",
    tags=["Categorias"],
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=CategoriaResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_categoria(
    categoria_req: CategoriaRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = CategoriaRepository(db_conn)
        nova_categoria = repo.create(categoria_req)
        logger.info(f"Usuário '{current_user.username}' criou Categoria ID {nova_categoria.id} ('{nova_categoria.nome}').")
        return nova_categoria
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar categoria duplicada: '{categoria_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A Categoria '{categoria_req.nome}' já existe."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar categoria por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[CategoriaResponse])
def get_all_categorias(
    mostrar_inativos: bool = False, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CategoriaRepository(db_conn)
        categorias = repo.get_all(mostrar_inativos)
        return categorias
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar categorias (inativos={mostrar_inativos}): {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=CategoriaResponse)
def get_categoria_by_id(
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CategoriaRepository(db_conn)
        categoria = repo.get_by_id(id)
        if not categoria:
            logger.warning(f"Categoria ID {id} não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada."
            )
        return categoria
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar categoria ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=CategoriaResponse,
            dependencies=[Depends(require_access_level(2))])
def update_categoria(
    id: int,
    categoria_req: CategoriaRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = CategoriaRepository(db_conn)
    categoria_db = repo.get_by_id(id)
    if not categoria_db:
         logger.warning(f"Tentativa de atualizar categoria ID {id} (não encontrada) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada para atualização."
        )

    try:
        categoria_atualizada = repo.update(id, categoria_req)
        if not categoria_atualizada:
             logger.error(f"Categoria ID {id} não encontrada DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Categoria não encontrada durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Categoria ID {id} de '{categoria_db.nome}' para '{categoria_atualizada.nome}'.")
        return categoria_atualizada
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de atualizar categoria ID {id} para nome duplicado '{categoria_req.nome}' por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O nome '{categoria_req.nome}' já está em uso."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar categoria ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.patch("/{id}/status", 
             response_model=CategoriaResponse,
             dependencies=[Depends(require_access_level(2))])
def toggle_categoria_status(
    id: int,
    activate: bool, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = CategoriaRepository(db_conn)
    categoria_atualizada = repo.set_active_status(id, activate) 

    if not categoria_atualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada para alterar status."
        )

    action_str = "ativada" if activate else "desativada"
    logger.info(f"Usuário '{current_user.username}' {action_str} Categoria ID {id} ('{categoria_atualizada.nome}').")
    return categoria_atualizada

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_categoria(
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = CategoriaRepository(db_conn)
    categoria_para_deletar = repo.get_by_id(id)
    if not categoria_para_deletar:
        logger.warning(f"Tentativa de deletar categoria ID {id} (não encontrada) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Categoria ID {id} ('{categoria_para_deletar.nome}').")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta Categoria está vinculada a Contratos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar categoria ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")