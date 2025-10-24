from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.dotacao_model import Dotacao 
from app.schemas.dotacao_schema import DotacaoRequest, DotacaoResponse
from app.repositories.dotacao_repository import DotacaoRepository

router = APIRouter(
    prefix="/dotacao",      
    tags=["Dotacao"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=DotacaoResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Dotacao(
    Dotacao_req: DotacaoRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = DotacaoRepository(db_conn)
        novo_Dotacao = repo.create(Dotacao_req)
        return novo_Dotacao
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Dotacao contratual '{Dotacao_req.info_orcamentaria}' já existe."
        )

@router.get("/", response_model=list[DotacaoResponse])
def get_all_Dotacao(
    db_conn: connection = Depends(get_db)
):
    repo = DotacaoRepository(db_conn)
    Dotacao = repo.get_all()
    return Dotacao

@router.get("/{id}", response_model=DotacaoResponse)
def get_Dotacao_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = DotacaoRepository(db_conn)
    Dotacao = repo.get_by_id(id)
    
    if not Dotacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="dotacao não encontrada."
        )
    return Dotacao

@router.put("/{id}", response_model=DotacaoResponse)
def update_Dotacao(
    id: int,
    Dotacao_req: DotacaoRequest,
    db_conn: connection = Depends(get_db)
):
    repo = DotacaoRepository(db_conn)
    
    Dotacao_db = repo.get_by_id(id)
    if not Dotacao_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="dotacao não encontrada para atualização."
        )
        
    Dotacao_atualizada = repo.update(id, Dotacao_req)
    return Dotacao_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Dotacao(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = DotacaoRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="dotacao não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta dotacao não está vinculada a contratos."
        )