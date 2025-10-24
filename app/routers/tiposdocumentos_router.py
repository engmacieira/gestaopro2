from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.tiposdocumentos_models import Tiposdocumentos 
from app.schemas.tiposdocumentos_schema import TiposdocumentosRequest, TiposdocumentosResponse
from app.repositories.tiposdocumentos_repository import TiposdocumentosRepository

router = APIRouter(
    prefix="/tiposdocumentos",      
    tags=["Tiposdocumentos"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=TiposdocumentosResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Tiposdocumentos(
    Tiposdocumentos_req: TiposdocumentosRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = TiposdocumentosRepository(db_conn)
        novo_Tiposdocumentos = repo.create(Tiposdocumentos_req)
        return novo_Tiposdocumentos
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Tiposdocumentos contratual '{Tiposdocumentos_req.nome}' já existe."
        )

@router.get("/", response_model=list[TiposdocumentosResponse])
def get_all_Tiposdocumentos(
    db_conn: connection = Depends(get_db)
):
    repo = TiposdocumentosRepository(db_conn)
    Tiposdocumentos = repo.get_all()
    return Tiposdocumentos

@router.get("/{id}", response_model=TiposdocumentosResponse)
def get_Tiposdocumentos_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = TiposdocumentosRepository(db_conn)
    Tiposdocumentos = repo.get_by_id(id)
    
    if not Tiposdocumentos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tiposdocumentos não encontrada."
        )
    return Tiposdocumentos

@router.put("/{id}", response_model=TiposdocumentosResponse)
def update_Tiposdocumentos(
    id: int,
    Tiposdocumentos_req: TiposdocumentosRequest,
    db_conn: connection = Depends(get_db)
):
    repo = TiposdocumentosRepository(db_conn)
    
    Tiposdocumentos_db = repo.get_by_id(id)
    if not Tiposdocumentos_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tiposdocumentos não encontrada para atualização."
        )
        
    Tiposdocumentos_atualizada = repo.update(id, Tiposdocumentos_req)
    return Tiposdocumentos_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Tiposdocumentos(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = TiposdocumentosRepository(db_conn)
    
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