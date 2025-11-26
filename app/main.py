import os
from dotenv import load_dotenv

if os.environ.get("TESTING") != "true":
    load_dotenv()

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone 

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import jwt, JWTError
 
from app.routers import (
    agente_router, anexo_router, aocs_router, categoria_router, 
    ci_pagamento_router, contrato_router, dotacao_router, 
    instrumento_router, item_router, local_router, modalidade_router, 
    numero_modalidade_router, pedido_router, processo_licitatorio_router, 
    tipo_documento_router, unidade_router, auth_router, user_router, ui_router
)

from app.core.logging_config import setup_logging
from app.core.database import get_db
from app.core.security import (
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    SECRET_KEY, 
    ALGORITHM
)

setup_logging()
logger = logging.getLogger(__name__) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Aplicação Gestão Pública API iniciada.")
    yield
    logger.info("Aplicação Gestão Pública API encerrada.")

APP_DIR = os.path.dirname(os.path.abspath(__file__)) 
BASE_DIR = os.path.dirname(APP_DIR) 

app = FastAPI(
    title="Gestão Pública API",
    description="API para o sistema de gestão pública (Refatorado com FastAPI)", 
    version="3.0.0",
    lifespan=lifespan  
)

app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")

@app.middleware("http")
async def sliding_session_middleware(request: Request, call_next):
    response = await call_next(request)
    
    if request.url.path.startswith("/static") or request.url.path == "/login" or response.status_code == 401:
        return response

    token_header = request.cookies.get("access_token")
    
    if token_header:
        try:
            scheme, token = token_header.split()
            if scheme.lower() != "bearer":
                return response
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            
            if username:
                current_data = {
                    "sub": payload.get("sub"),
                    "id": payload.get("id"),
                    "nivel": payload.get("nivel")
                }
                
                new_access_token = create_access_token(data=current_data)
                
                expires = datetime.now(timezone.utc) + timedelta(minutes=30)
                response.set_cookie(
                    key="access_token",
                    value=f"bearer {new_access_token}",
                    expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    httponly=True,
                    samesite="lax",
                    secure=False, 
                    path="/"
                )
        except (ValueError, JWTError):
            pass
            
    return response

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Redireciona para o login se der erro 401 em uma página HTML.
    Mantém o JSON se for uma chamada de API (AJAX/Fetch).
    """
    if exc.status_code == 401:
        accept = request.headers.get("accept", "")
        
        if "text/html" in accept:
            return RedirectResponse(
                url="/login?msg=Sessão expirada por inatividade. Faça login novamente.&category=warning",
                status_code=status.HTTP_302_FOUND
            )
        
        return JSONResponse(
            status_code=401,
            content={"detail": "Não autenticado. Faça login novamente."}
        )
        
    return await http_exception_handler(request, exc)

@app.get("/")
def read_root():
    return RedirectResponse(url="/login", status_code=302)

app.include_router(auth_router.router, prefix="/api")
app.include_router(user_router.router, prefix="/api") 
app.include_router(agente_router.router, prefix="/api")
app.include_router(anexo_router.router, prefix="/api") 
app.include_router(aocs_router.router, prefix="/api")
app.include_router(categoria_router.router, prefix="/api")
app.include_router(ci_pagamento_router.router, prefix="/api") 
app.include_router(contrato_router.router, prefix="/api")
app.include_router(dotacao_router.router, prefix="/api")
app.include_router(instrumento_router.router, prefix="/api")
app.include_router(item_router.router, prefix="/api")
app.include_router(local_router.router, prefix="/api")
app.include_router(modalidade_router.router, prefix="/api")
app.include_router(numero_modalidade_router.router, prefix="/api")
app.include_router(pedido_router.router, prefix="/api") 
app.include_router(processo_licitatorio_router.router, prefix="/api")
app.include_router(tipo_documento_router.router, prefix="/api")
app.include_router(unidade_router.router, prefix="/api")

app.include_router(ui_router.router) 
