from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.tipodocumento_model import Tipodocumento 
from app.schemas.tipodocumento_schema import TipodocumentoRequest, TipodocumentoResponse
from app.repositories.tipodocumento_repository import TipodocumentoRepository

router = APIRouter(
    prefix="/tiposdocumentos",      
    tags=["Tipodocumento"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=TipodocumentoResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Tipodocumento(
    Tipodocumento_req: TipodocumentoRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = TipodocumentoRepository(db_conn)
        novo_Tipodocumento = repo.create(Tipodocumento_req)
        return novo_Tipodocumento
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Tipodocumento contratual '{Tipodocumento_req.nome}' já existe."
        )

@router.get("/", response_model=list[TipodocumentoResponse])
def get_all_Tipodocumento(
    db_conn: connection = Depends(get_db)
):
    repo = TipodocumentoRepository(db_conn)
    Tipodocumento = repo.get_all()
    return Tipodocumento

@router.get("/{id}", response_model=TipodocumentoResponse)
def get_Tipodocumento_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = TipodocumentoRepository(db_conn)
    Tipodocumento = repo.get_by_id(id)
    
    if not Tipodocumento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tiposdocumentos não encontrada."
        )
    return Tipodocumento

@router.put("/{id}", response_model=TipodocumentoResponse)
def update_Tipodocumento(
    id: int,
    Tipodocumento_req: TipodocumentoRequest,
    db_conn: connection = Depends(get_db)
):
    repo = TipodocumentoRepository(db_conn)
    
    Tipodocumento_db = repo.get_by_id(id)
    if not Tipodocumento_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tiposdocumentos não encontrada para atualização."
        )
        
    Tipodocumento_atualizada = repo.update(id, Tipodocumento_req)
    return Tipodocumento_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Tipodocumento(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = TipodocumentoRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="tiposdocumentos não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta tiposdocumentos não está vinculada a contratos."
        )