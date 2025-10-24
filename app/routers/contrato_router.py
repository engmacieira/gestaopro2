from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.contrato_model import Contrato 
from app.schemas.contrato_schema import ContratoRequest, ContratoResponse
from app.repositories.contrato_repository import ContratoRepository

router = APIRouter(
    prefix="/contratos",      
    tags=["Contrato"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=ContratoResponse, 
             status_code=status.HTTP_201_CREATED)
def create_contratos(
    contratos_req: ContratoRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = ContratoRepository(db_conn)
        nova_contratos = repo.create(contratos_req)
        return nova_contratos
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O contrato '{contratos_req.numero_contrato}' já existe."
        )

@router.get("/", response_model=list[ContratoResponse])
def get_all_contratos(
    mostrar_inativos: bool = False, 
    db_conn: connection = Depends(get_db)
):
    repo = ContratoRepository(db_conn)
    contratos = repo.get_all(mostrar_inativos)
    return contratos

@router.get("/{id}", response_model=ContratoResponse)
def get_contratos_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = ContratoRepository(db_conn)
    contratos = repo.get_by_id(id)
    
    if not contratos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="contratos não encontrada."
        )
    return contratos

@router.put("/{id}", response_model=ContratoResponse)
def update_contratos(
    id: int,
    contratos_req: ContratoRequest,
    db_conn: connection = Depends(get_db)
):
    repo = ContratoRepository(db_conn)
    
    contratos_db = repo.get_by_id(id)
    if not contratos_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrada para atualização."
        )
        
    contratos_atualizada = repo.update(id, contratos_req)
    return contratos_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contratos(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = ContratoRepository(db_conn)
    
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