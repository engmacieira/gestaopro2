from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg2.extensions import connection
import logging

from app.schemas.auth_schema import LoginRequest, Token, UserResponse
from app.schemas.user_schema import UserChangePasswordRequest
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, verify_password, get_password_hash
from app.repositories.user_repository import UserRepository
from app.models.user_model import User

router = APIRouter(prefix="/auth", tags=["Autenticação"])

logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db_conn: connection = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário ou senha incorretos.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_repo = UserRepository(db_conn)
    user = user_repo.get_by_username(form_data.username) 

    if not user:
        raise credentials_exception
    
    if not user.verificar_senha(form_data.password):
        raise credentials_exception

    access_token = create_access_token(user=user)

    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user)
    ):

    return current_user

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: UserChangePasswordRequest,
    db_conn: connection = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = UserRepository(db_conn)
    
    # 1. Busca o usuário atual no banco para ter o hash atualizado
    user_db = repo.get_by_id(current_user.id)
    
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # 2. Valida a senha antiga
    if not verify_password(payload.current_password, user_db.password_hash):
        raise HTTPException(status_code=400, detail="A senha atual está incorreta.")
    
    # 3. Gera hash da nova senha
    new_hash = get_password_hash(payload.new_password)
    
    # 4. Salva
    success = repo.update_password(current_user.id, new_hash)
    
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atualizar a senha no banco de dados.")
        
    logger.info(f"Usuário '{current_user.username}' alterou sua senha com sucesso.")
    return {"message": "Senha alterada com sucesso!"}