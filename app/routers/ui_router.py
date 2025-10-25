import os
import logging
from fastapi import APIRouter, Request, Depends, Form, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# Importações necessárias para a autenticação e cookies
from app.core.security import get_current_user, require_access_level, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta, datetime
from starlette.routing import Mount # Mantido para compatibilidade, se necessário

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["UI - Páginas Web"]
)

# --- Configuração Local de Templates ---
# Define o caminho absoluto para a pasta `templates` (Subindo um nível do `routers`, e mais um do `app`)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(os.path.dirname(BASE_DIR), "templates")

# Instancia o objeto Templates.
templates = Jinja2Templates(directory=TEMPLATES_DIR)
# ----------------------------------------


# Rota de Login (GET /login)
@router.get("/login", response_class=HTMLResponse, name="login")
async def login_ui(request: Request, msg: str = None, category: str = None):
    """Renderiza a página de login."""
    
    # Corrigido: Passamos request.url_for para o contexto para resolver static files
    context = {
        "request": request,
        "url_for": request.url_for,
        # Simulação de flash messages (que o template espera)
        "messages": [(category, msg)] if msg and category else None
    }
    return templates.TemplateResponse("login.html", context)


# Rota de Login (POST /login) - Implementa o fluxo de autenticação via API
@router.post("/login", name="login_post") 
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    # 1. Preparar dados para a API /auth/login (que espera form-data)
    form_data = {
        "username": username,
        "password": password
    }

    # ATENÇÃO: Devido às restrições deste ambiente, SIMULAMOS o sucesso/falha do login.
    # Em um projeto real, você faria uma chamada HTTP (e.g., httpx) ou de serviço
    # para a rota /auth/login para obter o JWT.
    
    # --- SIMULAÇÃO DA CHAMADA INTERNA AO AUTH_ROUTER ---
    try:
        # Se a autenticação falhar, redirecionamos com mensagem de erro
        if username == "fail" or password == "fail":
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")
        
        # Simulação de sucesso (o token real viria da API)
        access_token = "fake.jwt.token." + username
        token_type = "bearer"
        
        
    except HTTPException as e:
        # Se a autenticação falhar, redirecionamos de volta para a página de login com a mensagem.
        return RedirectResponse(
            url=request.url_for("login", msg="Usuário ou senha inválidos.", category="error"),
            status_code=302
        )
    except Exception as e:
         # Se houver outro erro, redirecionamos com mensagem de erro genérica
        return RedirectResponse(
            url=request.url_for("login", msg="Erro interno ao tentar fazer login.", category="error"),
            status_code=302
        )


    # 2. Sucesso: Redirecionar e Definir o Cookie JWT (Crucial para a UI)
    response = RedirectResponse(url=request.url_for("home_ui"), status_code=302)
    
    # Cálculo de expiração para o cookie
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expires = datetime.utcnow() + expires_delta
    
    # Configura o cookie 'access_token'
    response.set_cookie(
        key="access_token",
        value=f"{token_type} {access_token}",
        expires=expires,
        httponly=True,  # Impede acesso via JavaScript (Segurança!)
        samesite="lax",
        secure=False,  # Mude para True em produção com HTTPS
        path="/"
    )

    return response


# Rota Home (GET /home ou /)
@router.get("/home", response_class=HTMLResponse, name="home_ui", dependencies=[Depends(require_access_level(3))])
async def home_ui(request: Request, current_user=Depends(get_current_user)):
    """Renderiza a página principal (dashboard) - Requer Nível de Acesso 3 (Visualização)."""
    
    # Simulação de dados (para o index.html renderizar)
    indicadores = {"contratos_ativos": 5, "pedidos_mes": 12, "contratos_a_vencer": 2}
    pedidos_pendentes = [
        {"numero_aocs": "AOCS-001/2025", "numero_contrato": "C-05/2024", "data_pedido": "20/09/2025", "dias_passados": 35},
        {"numero_aocs": "AOCS-002/2025", "numero_contrato": "C-10/2023", "data_pedido": "15/08/2025", "dias_passados": 70},
    ] 
    
    context = {
        "request": request,
        "url_for": request.url_for, 
        "current_user": current_user,
        "indicadores": indicadores,
        "pedidos_pendentes": pedidos_pendentes,
        "pagina_atual": 1,
        "total_paginas": 1,
        "versao_software": "3.0.0" 
    }
    return templates.TemplateResponse("index.html", context)


# Rota Logout (GET /logout)
@router.get("/logout", name="logout")
async def logout(response: Response):
    """Remove o cookie de acesso e redireciona para o login."""
    
    # Remove o cookie 'access_token'
    response.delete_cookie(key="access_token", path="/", httponly=True)
    
    # Redireciona para o login com mensagem
    return RedirectResponse(
        url=router.url_path_for("login", msg="Você foi desconectado com sucesso.", category="success"),
        status_code=302
    )