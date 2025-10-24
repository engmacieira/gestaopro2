from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.modalidade_model import Modalidade 
from app.schemas.modalidade_schema import ModalidadeRequest, ModalidadeResponse
from app.repositories.modalidade_repository import ModalidadeRepository

router = APIRouter(
    prefix="/modalidade",      
    tags=["Modalidade"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=ModalidadeResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Modalidade(
    Modalidade_req: ModalidadeRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ModalidadeRepository(db_conn)
        novo_Modalidade = repo.create(Modalidade_req)
        return novo_Modalidade
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Modalidade contratual '{Modalidade_req.nome}' já existe."
        )

@router.get("/", response_model=list[ModalidadeResponse])
def get_all_Modalidade(
    db_conn: connection = Depends(get_db)
):
    repo = ModalidadeRepository(db_conn)
    Modalidade = repo.get_all()
    return Modalidade

@router.get("/{id}", response_model=ModalidadeResponse)
def get_Modalidade_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = ModalidadeRepository(db_conn)
    Modalidade = repo.get_by_id(id)
    
    if not Modalidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="modalidade não encontrada."
        )
    return Modalidade

@router.put("/{id}", response_model=ModalidadeResponse)
def update_Modalidade(
    id: int,
    Modalidade_req: ModalidadeRequest,
    db_conn: connection = Depends(get_db)
):
    repo = ModalidadeRepository(db_conn)
    
    Modalidade_db = repo.get_by_id(id)
    if not Modalidade_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="modalidade não encontrada para atualização."
        )
        
    Modalidade_atualizada = repo.update(id, Modalidade_req)
    return Modalidade_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Modalidade(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = ModalidadeRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="modalidade não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta modalidade não está vinculada a contratos."
        )