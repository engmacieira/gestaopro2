from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.pedidos_models import Pedidos 
from app.schemas.pedidos_schema import PedidosRequest, PedidosResponse
from app.repositories.pedidos_repository import PedidosRepository

router = APIRouter(
    prefix="/pedidos",      
    tags=["Pedidos"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=PedidosResponse, 
             status_code=status.HTTP_201_CREATED)
def create_pedidos(
    pedidos_req: PedidosRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = PedidosRepository(db_conn)
        nova_pedidos = repo.create(pedidos_req)
        return nova_pedidos
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O pedidos '{pedidos_req.aocs_nome}' já existe."
        )

@router.get("/", response_model=list[PedidosResponse])
def get_all_pedidos(
    db_conn: connection = Depends(get_db)
):
    repo = PedidosRepository(db_conn)
    pedidos = repo.get_all()
    return pedidos

@router.get("/{id}", response_model=PedidosResponse)
def get_pedidos_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = PedidosRepository(db_conn)
    pedidos = repo.get_by_id(id)
    
    if not pedidos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pedidos não encontrada."
        )
    return pedidos

@router.put("/{id}", response_model=PedidosResponse)
def update_pedidos(
    id: int,
    pedidos_req: PedidosRequest,
    db_conn: connection = Depends(get_db)
):
    repo = PedidosRepository(db_conn)
    
    pedidos_db = repo.get_by_id(id)
    if not pedidos_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedidos não encontrada para atualização."
        )
        
    pedidos_atualizada = repo.update(id, pedidos_req)
    return pedidos_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pedidos(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = PedidosRepository(db_conn)
    
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