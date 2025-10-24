import os                     
from dotenv import load_dotenv 
load_dotenv()

import logging
from app.core.logging_config import setup_logging 
setup_logging()

from fastapi import FastAPI
from app.routers import agente_router
from app.routers import anexo_router
from app.routers import aocs_router
from app.routers import categoria_router
from app.routers import ci_router
from app.routers import contrato_router
from app.routers import dotacao_router
from app.routers import instrumento_router
from app.routers import item_router
from app.routers import local_router
from app.routers import modalidade_router
from app.routers import numeromodalidade_router
from app.routers import pedido_router
from app.routers import processolicitatorio_router
from app.routers import tipodocumento_router
from app.routers import unidade_router
from app.routers import user_router
from app.routers import auth_router

app = FastAPI(
    title="Gestão Pública API", 
    description="API para o sistema de gestão pública", 
    version="3.0.0-beta"
)
app.include_router(agente_router.router)
app.include_router(anexo_router.router)
app.include_router(aocs_router.router)
app.include_router(categoria_router.router)
app.include_router(ci_router.router)
app.include_router(contrato_router.router)
app.include_router(dotacao_router.router)
app.include_router(instrumento_router.router)
app.include_router(item_router.router)
app.include_router(local_router.router)
app.include_router(modalidade_router.router)
app.include_router(numeromodalidade_router.router)
app.include_router(pedido_router.router)
app.include_router(processolicitatorio_router.router)
app.include_router(tipodocumento_router.router)
app.include_router(unidade_router.router)
app.include_router(user_router.router)
app.include_router(auth_router.router)

@app.on_event("startup")
async def startup_event():
    logging.info("Aplicação iniciada com sucesso.")