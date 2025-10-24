from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.locais_models import Locais 
from app.schemas.locais_schema import LocaisRequest, LocaisResponse
from app.repositories.locais_repository import LocaisRepository

router = APIRouter(
    prefix="/locais",      
    tags=["Locais"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=LocaisResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Locais(
    Locais_req: LocaisRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = LocaisRepository(db_conn)
        novo_Locais = repo.create(Locais_req)
        return novo_Locais
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Locais contratual '{Locais_req.descricao}' já existe."
        )

@router.get("/", response_model=list[LocaisResponse])
def get_all_Locais(
    db_conn: connection = Depends(get_db)
):
    repo = LocaisRepository(db_conn)
    Locais = repo.get_all()
    return Locais

@router.get("/{id}", response_model=LocaisResponse)
def get_Locais_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = LocaisRepository(db_conn)
    Locais = repo.get_by_id(id)
    
    if not Locais:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="locais não encontrada."
        )
    return Locais

@router.put("/{id}", response_model=LocaisResponse)
def update_Locais(
    id: int,
    Locais_req: LocaisRequest,
    db_conn: connection = Depends(get_db)
):
    repo = LocaisRepository(db_conn)
    
    Locais_db = repo.get_by_id(id)
    if not Locais_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="locais não encontrada para atualização."
        )
        
    Locais_atualizada = repo.update(id, Locais_req)
    return Locais_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Locais(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = LocaisRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="locais não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta locais não está vinculada a contratos."
        )