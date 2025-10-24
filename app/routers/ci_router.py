from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ci_models import Ci 
from app.schemas.ci_schema import CiRequest, CiResponse
from app.repositories.ci_repository import CiRepository

router = APIRouter(
    prefix="/ci",      
    tags=["Ci"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=CiResponse, 
             status_code=status.HTTP_201_CREATED)
def create_ci(
    ci_req: CiRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = CiRepository(db_conn)
        nova_ci = repo.create(ci_req)
        return nova_ci
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O ci '{ci_req.numero_ci}' já existe."
        )

@router.get("/", response_model=list[CiResponse])
def get_all_ci(
    db_conn: connection = Depends(get_db)
):
    repo = CiRepository(db_conn)
    ci = repo.get_all()
    return ci

@router.get("/{id}", response_model=CiResponse)
def get_ci_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = CiRepository(db_conn)
    ci = repo.get_by_id(id)
    
    if not ci:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ci não encontrada."
        )
    return ci

@router.put("/{id}", response_model=CiResponse)
def update_ci(
    id: int,
    ci_req: CiRequest,
    db_conn: connection = Depends(get_db)
):
    repo = CiRepository(db_conn)
    
    ci_db = repo.get_by_id(id)
    if not ci_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ci não encontrada para atualização."
        )
        
    ci_atualizada = repo.update(id, ci_req)
    return ci_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ci(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = CiRepository(db_conn)
    
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