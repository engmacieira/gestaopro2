from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.pedido_model import Pedido 
from app.schemas.pedido_schema import PedidoRequest, PedidoResponse
from app.repositories.pedido_repository import PedidoRepository

router = APIRouter(
    prefix="/pedidos",      
    tags=["Pedido"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=PedidoResponse, 
             status_code=status.HTTP_201_CREATED)
def create_pedidos(
    pedidos_req: PedidoRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = PedidoRepository(db_conn)
        nova_pedidos = repo.create(pedidos_req)
        return nova_pedidos
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O pedidos '{pedidos_req.aocs_nome}' já existe."
        )

@router.get("/", response_model=list[PedidoResponse])
def get_all_pedidos(
    db_conn: connection = Depends(get_db)
):
    repo = PedidoRepository(db_conn)
    pedidos = repo.get_all()
    return pedidos

@router.get("/{id}", response_model=PedidoResponse)
def get_pedidos_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = PedidoRepository(db_conn)
    pedidos = repo.get_by_id(id)
    
    if not pedidos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pedidos não encontrada."
        )
    return pedidos

@router.put("/{id}", response_model=PedidoResponse)
def update_pedidos(
    id: int,
    pedidos_req: PedidoRequest,
    db_conn: connection = Depends(get_db)
):
    repo = PedidoRepository(db_conn)
    
    pedidos_db = repo.get_by_id(id)
    if not pedidos_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrada para atualização."
        )
        
    pedidos_atualizada = repo.update(id, pedidos_req)
    return pedidos_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pedidos(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = PedidoRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir"
        )