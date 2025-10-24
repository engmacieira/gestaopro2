from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.item_model import Item 
from app.schemas.item_schema import ItemRequest, ItemResponse
from app.repositories.item_repository import ItemRepository

router = APIRouter(
    prefix="/itens",      
    tags=["Item"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=ItemResponse, 
             status_code=status.HTTP_201_CREATED)
def create_itens(
    itens_req: ItemRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ItemRepository(db_conn)
        nova_itens = repo.create(itens_req)
        return nova_itens
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Ou 404, dependendo da semântica
            detail=str(e) # Exibe a mensagem "Contrato X não encontrado."
        )
    
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Erro ao criar item. Verifique os dados"
        )

@router.get("/", response_model=list[ItemResponse])
def get_all_itens(
    mostrar_inativos: bool = False, 
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    itens = repo.get_all(mostrar_inativos)
    return itens

@router.get("/{id}", response_model=ItemResponse)
def get_itens_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    itens = repo.get_by_id(id)
    
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrada."
        )
    return itens

@router.get("/por contrato/", response_model=list[ItemResponse])
def get_itens_contrato(
    contrato_id: int | None = None,
    mostrar_inativos: bool = False,
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    if contrato_id:
        itens = repo.get_by_contrato_id(contrato_id)
    else:
        itens = repo.get_all(mostrar_inativos)
    return itens

@router.get("/descricao/{descricao}", response_model=ItemResponse)
def get_itens_by_descricao(
    descricao: str, 
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    itens = repo.get_by_descricao(descricao)
    
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrada."
        )
    return itens

@router.put("/{id}", response_model=ItemResponse)
def update_itens(
    id: int,
    itens_req: ItemRequest,
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    
    itens_db = repo.get_by_id(id)
    if not itens_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrada para atualização."
        )
         
    try:
        itens_atualizada = repo.update(id, itens_req)
        if not itens_atualizada:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, # Ou 500 se for inesperado
                detail="Erro ao atualizar: Item não encontrado após a operação."
            )
        return itens_atualizada
    
    except ValueError as e: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
             
    except psycopg2.IntegrityError:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Erro de integridade ao atualizar item. Verifique os dados."
        )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itens(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = ItemRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Este item está vinculado a pedidos."
        )