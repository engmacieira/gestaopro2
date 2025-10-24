from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.unidades_models import Unidades 
from app.schemas.unidades_schema import UnidadesRequest, UnidadesResponse
from app.repositories.unidades_repository import UnidadesRepository

router = APIRouter(
    prefix="/unidades",      
    tags=["Unidades"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=UnidadesResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Unidades(
    Unidades_req: UnidadesRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = UnidadesRepository(db_conn)
        novo_Unidades = repo.create(Unidades_req)
        return novo_Unidades
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Unidades contratual '{Unidades_req.nome}' já existe."
        )

@router.get("/", response_model=list[UnidadesResponse])
def get_all_Unidades(
    db_conn: connection = Depends(get_db)
):
    repo = UnidadesRepository(db_conn)
    Unidades = repo.get_all()
    return Unidades

@router.get("/{id}", response_model=UnidadesResponse)
def get_Unidades_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = UnidadesRepository(db_conn)
    Unidades = repo.get_by_id(id)
    
    if not Unidades:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unidades não encontrada."
        )
    return Unidades

@router.put("/{id}", response_model=UnidadesResponse)
def update_Unidades(
    id: int,
    Unidades_req: UnidadesRequest,
    db_conn: connection = Depends(get_db)
):
    repo = UnidadesRepository(db_conn)
    
    Unidades_db = repo.get_by_id(id)
    if not Unidades_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unidades não encontrada para atualização."
        )
        
    Unidades_atualizada = repo.update(id, Unidades_req)
    return Unidades_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Unidades(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = UnidadesRepository(db_conn)
    
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