from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import logging
from typing import List 
from app.core.database import get_db
from app.core.security import get_current_user, require_access_level
from app.models.user_model import User
from app.models.pedido_model import Pedido 
from app.schemas.pedido_schema import PedidoCreateRequest, PedidoUpdateRequest, PedidoResponse
from app.repositories.pedido_repository import PedidoRepository 
from app.schemas.pedido_schema import (
    PedidoCreateRequest, 
    PedidoUpdateRequest, 
    PedidoResponse, 
    RegistrarEntregaRequest,
    RegistrarEntregaLoteRequest # <--- Adicione este import
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pedidos", 
    tags=["Pedidos (Itens da AOCS)"], 
    dependencies=[Depends(require_access_level(3))]
)

@router.post("/",
             response_model=PedidoResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_access_level(2))])
def create_pedido( 
    id_aocs: int, 
    pedido_req: PedidoCreateRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = PedidoRepository(db_conn)
        novo_pedido = repo.create(id_aocs, pedido_req) 
        logger.info(f"Usuário '{current_user.username}' adicionou Pedido ID {novo_pedido.id} (Item ID {novo_pedido.id_item_contrato}) à AOCS ID {id_aocs}.")
        return novo_pedido
    except ValueError as e: 
        logger.warning(f"Erro de validação (ValueError) ao criar Pedido por '{current_user.username}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except psycopg2.IntegrityError:
        logger.warning(f"Erro de integridade ao criar Pedido (Item já existe na AOCS?) por '{current_user.username}'. Req: {pedido_req.model_dump()}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Erro de integridade ao adicionar item ao pedido. O item ({pedido_req.item_contrato_id}) já pode existir nesta AOCS."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar Pedido por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=List[PedidoResponse])
def get_all_pedidos( 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = PedidoRepository(db_conn)
        pedidos = repo.get_all() 
        return pedidos
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar todos os pedidos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/por-aocs/{id_aocs}", response_model=List[PedidoResponse])
def get_pedidos_by_aocs_id( 
    id_aocs: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = PedidoRepository(db_conn)
        pedidos = repo.get_by_aocs_id(id_aocs) 
        return pedidos
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar pedidos para AOCS ID {id_aocs}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/{id}", response_model=PedidoResponse)
def get_pedido_by_id( 
    id: int,
    db_conn: connection = Depends(get_db)
):
    try:
        repo = PedidoRepository(db_conn)
        pedido = repo.get_by_id(id) 
        if not pedido:
            logger.warning(f"Pedido ID {id} não encontrado.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado."
            )
        return pedido
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar Pedido ID {id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}",
            response_model=PedidoResponse,
            dependencies=[Depends(require_access_level(2))])
def update_pedido( 
    id: int,
    pedido_req: PedidoUpdateRequest, 
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = PedidoRepository(db_conn)
    pedido_db = repo.get_by_id(id) 
    if not pedido_db:
         logger.warning(f"Tentativa de atualizar Pedido ID {id} (não encontrado) por '{current_user.username}'.")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado para atualização."
        )

    try:
        if pedido_req.quantidade_entregue is not None and pedido_req.quantidade_entregue > pedido_db.quantidade_pedida:
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail=f"Quantidade entregue ({pedido_req.quantidade_entregue}) não pode ser maior que a quantidade pedida ({pedido_db.quantidade_pedida})."
             )

        pedido_atualizado = repo.update(id, pedido_req) 
        if not pedido_atualizado:
             logger.error(f"Pedido ID {id} não encontrado DURANTE atualização por '{current_user.username}'.")
             raise HTTPException(status_code=404, detail="Pedido não encontrado durante a atualização.")

        changes = []
        if pedido_req.status_entrega is not None and pedido_db.status_entrega != pedido_atualizado.status_entrega:
             changes.append(f"status de '{pedido_db.status_entrega}' para '{pedido_atualizado.status_entrega}'")
        if pedido_req.quantidade_entregue is not None and pedido_db.quantidade_entregue != pedido_atualizado.quantidade_entregue:
             changes.append(f"qtd. entregue de {pedido_db.quantidade_entregue} para {pedido_atualizado.quantidade_entregue}")

        if changes:
             logger.info(f"Usuário '{current_user.username}' atualizou Pedido ID {id}: {', '.join(changes)}.")
        else:
             logger.info(f"Usuário '{current_user.username}' fez requisição PUT para Pedido ID {id} sem alterações efetivas.")

        return pedido_atualizado
    except ValueError as e:
        logger.warning(f"Erro de validação ao atualizar Pedido ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except psycopg2.IntegrityError: 
        logger.warning(f"Erro de integridade ao atualizar Pedido ID {id} por '{current_user.username}'. Req: {pedido_req.model_dump(exclude_unset=True)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro de integridade ao atualizar pedido (ex: status inválido?)."
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar Pedido ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.put("/{id}/registrar-entrega",
            response_model=PedidoResponse,
            dependencies=[Depends(require_access_level(2))])
def registrar_entrega(
    id: int,
    entrega_req: RegistrarEntregaRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = PedidoRepository(db_conn)
    pedido_atual = repo.get_by_id(id)
    
    if not pedido_atual:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    # 1. Calcula a nova quantidade total entregue
    nova_qtd_entregue = pedido_atual.quantidade_entregue + entrega_req.quantidade
    
    # Validação básica (opcional: impedir entregar mais que o pedido)
    # if nova_qtd_entregue > pedido_atual.quantidade_pedida:
    #     raise HTTPException(status_code=400, detail="Quantidade excede o total do pedido.")

    # 2. Define o novo status
    novo_status = "Entrega Parcial"
    if nova_qtd_entregue >= pedido_atual.quantidade_pedida:
        novo_status = "Entregue"

    # 3. Atualiza no Banco
    # Aqui convertemos nosso request específico para o update genérico do repositório
    update_data = PedidoUpdateRequest(
        quantidade_entregue=nova_qtd_entregue,
        status_entrega=novo_status
    )
    
    # TODO: Se tiver tabela de 'Histórico de Entregas', salvar nota_fiscal e data_entrega lá.
    # Por enquanto, atualizamos apenas o saldo do pedido.
    
    pedido_atualizado = repo.update(id, update_data)
    
    logger.info(f"Entrega registrada por '{current_user.username}': Pedido {id} recebeu +{entrega_req.quantidade}. Status: {novo_status}")
    
    return pedido_atualizado

@router.delete("/{id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_access_level(2))])
def delete_pedido( 
    id: int,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = PedidoRepository(db_conn)
    pedido_para_deletar = repo.get_by_id(id) 
    if not pedido_para_deletar:
        logger.warning(f"Tentativa de deletar Pedido ID {id} (não encontrado) por '{current_user.username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado para exclusão."
        )

    try:
        repo.delete(id) 
        logger.info(f"Usuário '{current_user.username}' deletou Pedido ID {id} (Item ID: {pedido_para_deletar.id_item_contrato}, AOCS ID: {pedido_para_deletar.id_aocs}).")
        return

    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir este Pedido (Erro de integridade)."
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao deletar Pedido ID {id} por '{current_user.username}': {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
    
@router.post("/entrega-lote", status_code=status.HTTP_200_OK, dependencies=[Depends(require_access_level(2))])
def registrar_entrega_lote(
    lote_req: RegistrarEntregaLoteRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        repo = PedidoRepository(db_conn)
        resultado = repo.registrar_entrega_lote(lote_req)
        
        logger.info(f"Usuário '{current_user.username}' registrou entrega em lote de {resultado['qtd_itens']} itens.")
        return {"mensagem": "Entregas registradas com sucesso!", "detalhes": resultado}
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Erro na rota de entrega em lote: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar entregas em lote.")