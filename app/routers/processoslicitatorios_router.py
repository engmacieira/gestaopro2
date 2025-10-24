from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.processoslicitatorios_models import Processoslicitatorios 
from app.schemas.processoslicitatorios_schema import ProcessoslicitatoriosRequest, ProcessoslicitatoriosResponse
from app.repositories.processoslicitatorios_repository import ProcessoslicitatoriosRepository

router = APIRouter(
    prefix="/processoslicitatorios",      
    tags=["Processoslicitatorios"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=ProcessoslicitatoriosResponse, 
             status_code=status.HTTP_201_CREATED)
def create_processoslicitatorios(
    processoslicitatorios_req: ProcessoslicitatoriosRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ProcessoslicitatoriosRepository(db_conn)
        novo_processoslicitatorios = repo.create(processoslicitatorios_req)
        return novo_processoslicitatorios
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O processo licitatório '{processoslicitatorios_req.nome}' já existe."
        )

@router.get("/", response_model=list[ProcessoslicitatoriosResponse])
def get_all_processoslicitatorios(
    db_conn: connection = Depends(get_db)
):
    repo = ProcessoslicitatoriosRepository(db_conn)
    processoslicitatorios = repo.get_all()
    return processoslicitatorios

@router.get("/{id}", response_model=ProcessoslicitatoriosResponse)
def get_processoslicitatorios_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = ProcessoslicitatoriosRepository(db_conn)
    processoslicitatorios = repo.get_by_id(id)
    
    if not processoslicitatorios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="processo licitatório não encontrada."
        )
    return processoslicitatorios

@router.put("/{id}", response_model=ProcessoslicitatoriosResponse)
def update_processoslicitatorios(
    id: int,
    processoslicitatorios_req: ProcessoslicitatoriosRequest,
    db_conn: connection = Depends(get_db)
):
    repo = ProcessoslicitatoriosRepository(db_conn)
    
    processoslicitatorios_db = repo.get_by_id(id)
    if not processoslicitatorios_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="processo licitatório não encontrada para atualização."
        )
        
    processoslicitatorios_atualizada = repo.update(id, processoslicitatorios_req)
    return processoslicitatorios_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_processoslicitatorios(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = ProcessoslicitatoriosRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="processo licitatório não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta processo licitatório está vinculada a contratos."
        )