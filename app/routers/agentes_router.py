from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2 
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.agentes_models import Agentes 
from app.schemas.agentes_schema import AgentesRequest, AgentesResponse
from app.repositories.agentes_repository import AgentesRepository

router = APIRouter(
    prefix="/agentes",      
    tags=["Agentes"],       
    dependencies=[Depends(get_current_user)]
)

@router.post("/", 
             response_model=AgentesResponse, 
             status_code=status.HTTP_201_CREATED)
def create_Agentes(
    Agentes_req: AgentesRequest, 
    db_conn: connection = Depends(get_db)
):
    try:
        repo = AgentesRepository(db_conn)
        novo_Agentes = repo.create(Agentes_req)
        return novo_Agentes
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O Agentes contratual '{Agentes_req.nome}' já existe."
        )

@router.get("/", response_model=list[AgentesResponse])
def get_all_Agentes(
    db_conn: connection = Depends(get_db)
):
    repo = AgentesRepository(db_conn)
    Agentes = repo.get_all()
    return Agentes

@router.get("/{id}", response_model=AgentesResponse)
def get_Agentes_by_id(
    id: int, 
    db_conn: connection = Depends(get_db)
):
    repo = AgentesRepository(db_conn)
    Agentes = repo.get_by_id(id)
    
    if not Agentes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="agentes não encontrada."
        )
    return Agentes

@router.put("/{id}", response_model=AgentesResponse)
def update_Agentes(
    id: int,
    Agentes_req: AgentesRequest,
    db_conn: connection = Depends(get_db)
):
    repo = AgentesRepository(db_conn)
    
    Agentes_db = repo.get_by_id(id)
    if not Agentes_db:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="agentes não encontrada para atualização."
        )
        
    Agentes_atualizada = repo.update(id, Agentes_req)
    return Agentes_atualizada

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Agentes(
    id: int,
    db_conn: connection = Depends(get_db)
):
    repo = AgentesRepository(db_conn)
    
    try:
        sucesso = repo.delete(id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="agentes não encontrada para exclusão."
            )
        return
        
    except psycopg2.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir. Esta agentes não está vinculada a contratos."
        )