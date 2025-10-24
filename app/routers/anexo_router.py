from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.anexo_model import Anexo 
from app.schemas.anexo_schema import AnexoRequest, AnexoResponse
from app.repositories.anexo_repository import AnexoRepository

router = APIRouter(
    prefix="/anexos",      
    tags=["Anexo"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=AnexoResponse, 
             status_code=status.HTTP_201_CREATED)
def create_anexos(
    anexos_req: AnexoRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AnexoRepository(db_conn)
        nova_anexos = repo.create(anexos_req)
        return nova_anexos
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O anexos '{anexos_req.tipo_documento}' já existe."
        )

@router.get("/", response_model=list[AnexoResponse])
def get_all_anexos(
    db_conn: connection = Depends(get_db)
):
    repo = AnexoRepository(db_conn)
    anexos = repo.get_all()
    return anexos

@router.get("/{id}", response_model=AnexoResponse)
def get_anexos_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = AnexoRepository(db_conn)
    anexos = repo.get_by_id(id)
    
    if not anexos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="anexos não encontrada."
        )
    return anexos

@router.put("/{id}", response_model=AnexoResponse)
def update_anexos(
    id: int,
    anexos_req: AnexoRequest,
    db_conn: connection = Depends(get_db)
):
    repo = AnexoRepository(db_conn)
    
    anexos_db = repo.get_by_id(id)
    if not anexos_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrada para atualização."
        )
        
    anexos_atualizada = repo.update(id, anexos_req)
    return anexos_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_anexos(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = AnexoRepository(db_conn)
    
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