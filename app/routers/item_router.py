from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.item_model import Item
from app.schemas.item_schema import ItemRequest, ItemResponse
from app.repositories.item_repository import ItemRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/itens", 
    tags=["Itens de Contrato"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=ItemResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_item( 
    item_req: ItemRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = ItemRepository(db_conn)
        novo_item = repo.create(item_req) 
        logger.info(f"Usuário '{current_user.username}' criou Item ID {novo_item.id} (Num: {novo_item.numero_item}) para Contrato ID {novo_item.id_contrato}.")
        return novo_item
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao criar Item por '{current_user.username}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar Item duplicado (Num Item?) para Contrato '{item_req.contrato_nome}' por '{current_user.username}'. Req: {item_req.model_dump()}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Erro de integridade ao criar item. O número do item ({item_req.numero_item}) já pode existir para este contrato."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar Item por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=list[ItemResponse])
def get_itens( 
    contrato_id: int | None = None,
    descricao: str | None = None, 
    mostrar_inativos: bool = False,
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    items_list = [] 
    try:
        if descricao:
            item = repo.get_by_descricao(descricao)
            items_list = [item] if item else []
            if not mostrar_inativos and items_list:
                items_list = [i for i in items_list if i.ativo]
        elif contrato_id:
            items_contrato = repo.get_by_contrato_id(contrato_id)
            if not mostrar_inativos:
                items_list = [item for item in items_contrato if item.ativo]
            else:
                items_list = items_contrato
        else:
            items_list = repo.get_all(mostrar_inativos)

        return items_list
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar itens (filtros: ctId={contrato_id}, desc={descricao}, inat={mostrar_inativos}): {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")


@router.get("/{id}", response_model=ItemResponse)
def get_item_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ItemRepository(db_conn)
        item = repo.get_by_id(id) 
        if not item:
            logger.warning(f"Item ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item de Contrato não encontrado."
            )
        return item
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar Item ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")


@router.put("/{id}",
            response_model=ItemResponse,
            dependencies=[Depends(require_access_level(2))])
def update_item( 
    id: int,
    item_req: ItemRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ItemRepository(db_conn)
    item_db = repo.get_by_id(id) 
    if not item_db:
         logger.warning(f"Tentativa de atualizar Item ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item de Contrato não encontrado para atualização."
        )

    try:
        item_atualizado = repo.update(id, item_req) 
        if not item_atualizado:
             logger.error(f"Item ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Item não encontrado durante a atualização.")

        logger.info(f"Usuário '{current_user.username}' atualizou Item ID {id} (Contrato ID {item_atualizado.id_contrato}).")
        return item_atualizado
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao atualizar Item ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Erro de integridade ao atualizar Item ID {id} (Num Item duplicado?) por '{current_user.username}'. Req: {item_req.model_dump()}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Erro de integridade ao atualizar item. O número do item ({item_req.numero_item}) já pode existir para este contrato."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar Item ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.patch("/{id}/status",
             response_model=ItemResponse,
             dependencies=[Depends(require_access_level(2))])
def set_item_status(
    id: int,
    activate: bool,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ItemRepository(db_conn)
    item_atualizado = repo.set_active_status(id, activate)

    if not item_atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item de Contrato não encontrado para alterar status."
        )

    action_str = "ativado" if activate else "desativado"
    logger.info(f"Usuário '{current_user.username}' {action_str} Item ID {id} (Num: {item_atualizado.numero_item}).")
    return item_atualizado

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_item( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ItemRepository(db_conn)
    item_para_deletar = repo.get_by_id(id) 
    if not item_para_deletar:
        logger.warning(f"Tentativa de deletar Item ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item de Contrato não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Item ID {id} (Num: {item_para_deletar.numero_item}, Contrato ID: {item_para_deletar.id_contrato}).")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este Item está vinculado a Pedidos."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar Item ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")