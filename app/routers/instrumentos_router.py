from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.instrumentos_models import Instrumentos 
from app.schemas.instrumentos_schema import InstrumentosRequest, InstrumentosResponse
from app.repositories.instrumentos_repository import InstrumentosRepository

router = APIRouter(
    prefix="/instrumentos",      
    tags=["Instrumentos"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=InstrumentosResponse, 
             status_code=status.HTTP_201_CREATED)
def create_instrumentos(
    instrumentos_req: InstrumentosRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = InstrumentosRepository(db_conn)
        novo_instrumentos = repo.create(instrumentos_req)
        return novo_instrumentos
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O instrumentos contratual '{instrumentos_req.nome}' já existe."
        )

@router.get("/", response_model=list[InstrumentosResponse])
def get_all_instrumentos(
    db_conn: connection = Depends(get_db)
):
    repo = InstrumentosRepository(db_conn)
    instrumentos = repo.get_all()
    return instrumentos

@router.get("/{id}", response_model=InstrumentosResponse)
def get_instrumentos_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = InstrumentosRepository(db_conn)
    instrumentos = repo.get_by_id(id)
    
    if not instrumentos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="instrumento contratual não encontrada."
        )
    return instrumentos

@router.put("/{id}", response_model=InstrumentosResponse)
def update_instrumentos(
    id: int,
    instrumentos_req: InstrumentosRequest,
    db_conn: connection = Depends(get_db)
):
    repo = InstrumentosRepository(db_conn)
    
    instrumentos_db = repo.get_by_id(id)
    if not instrumentos_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="instrumento contratual não encontrada para atualização."
        )
        
    instrumentos_atualizada = repo.update(id, instrumentos_req)
    return instrumentos_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrumentos(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = InstrumentosRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="instrumento contratual não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta instrumento contratual não está vinculada a contratos."
        )