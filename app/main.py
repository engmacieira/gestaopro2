import os
from dotenv import load_dotenv

load_dotenv()

import logging
from app.core.logging_config import setup_logging
setup_logging()

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles 
 
from app.routers import agente_router 
from app.routers import anexo_router 
from app.routers import aocs_router
from app.routers import categoria_router
from app.routers import ci_pagamento_router
from app.routers import contrato_router 
from app.routers import dotacao_router
from app.routers import instrumento_router 
from app.routers import item_router 
from app.routers import local_router 
from app.routers import modalidade_router
from app.routers import numero_modalidade_router 
from app.routers import pedido_router 
from app.routers import processo_licitatorio_router 
from app.routers import tipo_documento_router 
from app.routers import unidade_router 
from app.routers import auth_router 
from app.routers import user_router 
from app.routers import ui_router

logger = logging.getLogger(__name__) 

APP_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="Gestão Pública API",
    description="API para o sistema de gestão pública (Refatorado com FastAPI)", 
    version="3.0.0" 
)

app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")

@app.get("/")
def read_root():
    return RedirectResponse(url="/login", status_code=302)

app.include_router(auth_router.router)
app.include_router(user_router.router) 

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


@app.on_event("startup")
async def startup_event():
    """Loga uma mensagem quando a aplicação inicia."""
    logger.info("Aplicação Gestão Pública API iniciada.")

@app.on_event("shutdown")
async def shutdown_event():
    """Loga uma mensagem quando a aplicação encerra."""
    logger.info("Aplicação Gestão Pública API encerrada.")
