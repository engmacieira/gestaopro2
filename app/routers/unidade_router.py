from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.unidade_model import Unidade 
from app.schemas.unidade_schema import UnidadeRequest, UnidadeResponse
from app.repositories.unidade_repository import UnidadeRepository

router = APIRouter(
    prefix="/unidades",      
    tags=["Unidade"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=UnidadeResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Unidade(
    Unidade_req: UnidadeRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = UnidadeRepository(db_conn)
        novo_Unidade = repo.create(Unidade_req)
        return novo_Unidade
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Unidade contratual '{Unidade_req.nome}' já existe."
        )

@router.get("/", response_model=list[UnidadeResponse])
def get_all_Unidade(
    db_conn: connection = Depends(get_db)
):
    repo = UnidadeRepository(db_conn)
    Unidade = repo.get_all()
    return Unidade

@router.get("/{id}", response_model=UnidadeResponse)
def get_Unidade_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = UnidadeRepository(db_conn)
    Unidade = repo.get_by_id(id)
    
    if not Unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unidades não encontrada."
        )
    return Unidade

@router.put("/{id}", response_model=UnidadeResponse)
def update_Unidade(
    id: int,
    Unidade_req: UnidadeRequest,
    db_conn: connection = Depends(get_db)
):
    repo = UnidadeRepository(db_conn)
    
    Unidade_db = repo.get_by_id(id)
    if not Unidade_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unidades não encontrada para atualização."
        )
        
    Unidade_atualizada = repo.update(id, Unidade_req)
    return Unidade_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Unidade(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = UnidadeRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="unidades não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta unidades não está vinculada a contratos."
        )