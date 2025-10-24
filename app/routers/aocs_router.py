from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aocs_model import Aocs 
from app.schemas.aocs_schema import AocsRequest, AocsResponse
from app.repositories.aocs_repository import AocsRepository

router = APIRouter(
    prefix="/aocs",      
    tags=["Aocs"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=AocsResponse, 
             status_code=status.HTTP_201_CREATED)
def create_aocs(
    aocs_req: AocsRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AocsRepository(db_conn)
        nova_aocs = repo.create(aocs_req)
        return nova_aocs
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O aocs '{aocs_req.numero_aocs}' já existe."
        )

@router.get("/", response_model=list[AocsResponse])
def get_all_aocs(
    db_conn: connection = Depends(get_db)
):
    repo = AocsRepository(db_conn)
    aocs = repo.get_all()
    return aocs

@router.get("/{id}", response_model=AocsResponse)
def get_aocs_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = AocsRepository(db_conn)
    aocs = repo.get_by_id(id)
    
    if not aocs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="aocs não encontrada."
        )
    return aocs

@router.get("/NumeroAOCS/{numero_aocs:path}", response_model=AocsResponse)
def get_aocs_by_aocs(
    numero_aocs: str, 
    db_conn: connection = Depends(get_db)
):
    repo = AocsRepository(db_conn)
    aocs = repo.get_by_aocs(numero_aocs)
    
    if not aocs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="aocs não encontrada."
        )
    return aocs

@router.put("/{id}", response_model=AocsResponse)
def update_aocs(
    id: int,
    aocs_req: AocsRequest,
    db_conn: connection = Depends(get_db)
):
    repo = AocsRepository(db_conn)
    
    aocs_db = repo.get_by_id(id)
    if not aocs_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aocs não encontrada para atualização."
        )
        
    aocs_atualizada = repo.update(id, aocs_req)
    return aocs_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aocs(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = AocsRepository(db_conn)
    
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