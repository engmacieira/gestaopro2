from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection
import psycopg2
import secrets 
import string 
from werkzeug.security import generate_password_hash 

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user_model import User
from app.schemas.user_schema import (UserCreateRequest, UserResponse,
                                     UserUpdateRequest, UserAdminResponse)
from app.repositories.user_repository import UserRepository
from functools import wraps

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.nivel_acesso != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de administrador."
        )

router = APIRouter(
    prefix="/users",
    tags=["Usuários"],
    dependencies=[Depends(require_admin)]
)

@router.post("/", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_create: UserCreateRequest,
    db_conn: connection = Depends(get_db)
):

    repo = UserRepository(db_conn)
    existing_user = repo.get_by_username(user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nome de usuário já está em uso."
        )
    try:
        new_user = repo.create(user_create)
        return new_user
    except psycopg2.IntegrityError: 
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Erro ao criar usuário. Verifique os dados fornecidos."
        )
    except Exception as e: 
        raise HTTPException(status_code=500, detail="Erro interno ao criar usuário.")


@router.get("/", response_model=list[UserAdminResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    mostrar_inativos: bool = False,
    db_conn: connection = Depends(get_db)
):

    repo = UserRepository(db_conn)
    users = repo.get_all(skip=skip, limit=limit, mostrar_inativos=mostrar_inativos)
    return users


@router.get("/{user_id}", response_model=UserAdminResponse)
def read_user(
    user_id: int,
    db_conn: connection = Depends(get_db)
):

    repo = UserRepository(db_conn)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.put("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db_conn: connection = Depends(get_db)
):

    repo = UserRepository(db_conn)
    user_db = repo.get_by_id(user_id)
    if not user_db:
         raise HTTPException(status_code=404, detail="Usuário não encontrado para atualização.")

    try:
        updated_user = repo.update(user_id, user_update)
        if not updated_user:
             raise HTTPException(status_code=404, detail="Usuário não encontrado após atualização.")
        return updated_user
    except psycopg2.IntegrityError: 
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nome de usuário já está em uso por outro usuário."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar usuário.")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db_conn: connection = Depends(get_db)
):

    repo = UserRepository(db_conn)

    success = repo.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado para desativação.")

@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def reset_user_password(
    user_id: int,
    db_conn: connection = Depends(get_db)
):

    repo = UserRepository(db_conn)
    user_db = repo.get_by_id(user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado para reset de senha.")

    alfabeto = string.ascii_letters + string.digits
    nova_senha = ''.join(secrets.choice(alfabeto) for i in range(12))
    novo_hash = generate_password_hash(nova_senha)

    success = repo.reset_password(user_id, novo_hash)
    if not success:
         raise HTTPException(status_code=500, detail="Erro interno ao resetar a senha.")

    return {"message": "Senha redefinida com sucesso!", "new_password": nova_senha}