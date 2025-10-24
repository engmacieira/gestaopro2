from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.local_model import Local 
from app.schemas.local_schema import LocalRequest, LocalResponse
from app.repositories.local_repository import LocalRepository

router = APIRouter(
    prefix="/locais",      
    tags=["Local"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=LocalResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Local(
    Local_req: LocalRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = LocalRepository(db_conn)
        novo_Local = repo.create(Local_req)
        return novo_Local
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Local contratual '{Local_req.descricao}' já existe."
        )

@router.get("/", response_model=list[LocalResponse])
def get_all_Local(
    db_conn: connection = Depends(get_db)
):
    repo = LocalRepository(db_conn)
    Local = repo.get_all()
    return Local

@router.get("/{id}", response_model=LocalResponse)
def get_Local_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = LocalRepository(db_conn)
    Local = repo.get_by_id(id)
    
    if not Local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="locais não encontrada."
        )
    return Local

@router.put("/{id}", response_model=LocalResponse)
def update_Local(
    id: int,
    Local_req: LocalRequest,
    db_conn: connection = Depends(get_db)
):
    repo = LocalRepository(db_conn)
    
    Local_db = repo.get_by_id(id)
    if not Local_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="locais não encontrada para atualização."
        )
        
    Local_atualizada = repo.update(id, Local_req)
    return Local_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Local(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = LocalRepository(db_conn)
    
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