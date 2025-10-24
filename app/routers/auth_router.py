from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg2.extensions import connection

from app.schemas.auth_schema import LoginRequest, Token, UserResponse
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.repositories.user_repository import UserRepository
from app.models.user_models import User

router = APIRouter(prefix="/auth", tags=["Autenticação"])

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