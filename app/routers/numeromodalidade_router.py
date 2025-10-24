from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.numeromodalidade_model import Numeromodalidade 
from app.schemas.numeromodalidade_schema import NumeromodalidadeRequest, NumeromodalidadeResponse
from app.repositories.numeromodalidade_repository import NumeromodalidadeRepository

router = APIRouter(
    prefix="/numeromodalidade",      
    tags=["Numeromodalidade"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=NumeromodalidadeResponse, 
             status_code=status.HTTP_201_CREATED)
def create_numeromodalidade(
    numeromodalidade_req: NumeromodalidadeRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = NumeromodalidadeRepository(db_conn)
        novo_numeromodalidade = repo.create(numeromodalidade_req)
        return novo_numeromodalidade
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O numero da modalidade '{numeromodalidade_req.numero_ano}' já existe."
        )

@router.get("/", response_model=list[NumeromodalidadeResponse])
def get_all_Numeromodalidade(
    db_conn: connection = Depends(get_db)
):
    repo = NumeromodalidadeRepository(db_conn)
    Numeromodalidade = repo.get_all()
    return Numeromodalidade

@router.get("/{id}", response_model=NumeromodalidadeResponse)
def get_numeromodalidade_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = NumeromodalidadeRepository(db_conn)
    numeromodalidade = repo.get_by_id(id)
    
    if not numeromodalidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="numero da modalidade não encontrada."
        )
    return numeromodalidade

@router.put("/{id}", response_model=NumeromodalidadeResponse)
def update_numeromodalidade(
    id: int,
    numeromodalidade_req: NumeromodalidadeRequest,
    db_conn: connection = Depends(get_db)
):
    repo = NumeromodalidadeRepository(db_conn)
    
    Numeromodalidade_db = repo.get_by_id(id)
    if not Numeromodalidade_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="numero da modalidade não encontrada para atualização."
        )
        
    numeromodalidade_atualizada = repo.update(id, numeromodalidade_req)
    return numeromodalidade_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_numeromodalidade(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = NumeromodalidadeRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="numero da modalidade não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta numero da modalidade está vinculada a contratos."
        )