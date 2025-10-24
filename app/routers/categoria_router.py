from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user_model import User 
from app.schemas.categoria_schema import CategoriaRequest, CategoriaResponse
from app.repositories.categoria_repository import CategoriaRepository

router = APIRouter(
    prefix="/categorias",      
    tags=["Categorias"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=CategoriaResponse, 
             status_code=status.HTTP_201_CREATED)
def create_categoria(
    categoria_req: CategoriaRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CategoriaRepository(db_conn)
        nova_categoria = repo.create(categoria_req)
        return nova_categoria
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A categoria '{categoria_req.nome}' já existe."
        )

@router.get("/", response_model=list[CategoriaResponse])
def get_all_categorias(
    mostrar_inativos: bool = False, 
    db_conn: connection = Depends(get_db)
):
    repo = CategoriaRepository(db_conn)
    categorias = repo.get_all(mostrar_inativos)
    return categorias

@router.get("/{id}", response_model=CategoriaResponse)
def get_categoria_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = CategoriaRepository(db_conn)
    categoria = repo.get_by_id(id)
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada."
        )
    return categoria

@router.put("/{id}", response_model=CategoriaResponse)
def update_categoria(
    id: int,
    categoria_req: CategoriaRequest,
    db_conn: connection = Depends(get_db)
):
    repo = CategoriaRepository(db_conn)
    
    categoria_db = repo.get_by_id(id)
    if not categoria_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada para atualização."
        )
        
    categoria_atualizada = repo.update(id, categoria_req)
    return categoria_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = CategoriaRepository(db_conn)
    
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
            detail="Não é possível excluir. Esta categoria está vinculada a contratos."
        )