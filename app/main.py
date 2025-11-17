import os
from dotenv import load_dotenv

if os.environ.get("TESTING") != "true":
    load_dotenv()

import logging
from contextlib import asynccontextmanager 
from app.core.logging_config import setup_logging
setup_logging()

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles 
 
from app.routers import (
    agente_router, anexo_router, aocs_router, categoria_router, 
    ci_pagamento_router, contrato_router, dotacao_router, 
    instrumento_router, item_router, local_router, modalidade_router, 
    numero_modalidade_router, pedido_router, processo_licitatorio_router, 
    tipo_documento_router, unidade_router, auth_router, user_router, ui_router
)

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
