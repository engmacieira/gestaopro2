import os                     
from dotenv import load_dotenv 
load_dotenv()

from fastapi import FastAPI
from app.routers import agentes_router
from app.routers import anexos_router
from app.routers import aocs_router
from app.routers import categoria_router
from app.routers import ci_router
from app.routers import contratos_router
from app.routers import dotacao_router
from app.routers import instrumentos_router
from app.routers import itens_router
from app.routers import locais_router
from app.routers import modalidade_router
from app.routers import numeromodalidade_router
from app.routers import pedidos_router
from app.routers import processoslicitatorios_router
from app.routers import tiposdocumentos_router
from app.routers import unidades_router
from app.routers import home_router
from app.routers import auth_router

app = FastAPI(
    title="Gestão Pública API", 
    description="API para o sistema de gestão pública", 
    version="3.0.0-beta"
)
app.include_router(agentes_router.router)
app.include_router(anexos_router.router)
app.include_router(aocs_router.router)
app.include_router(categoria_router.router)
app.include_router(ci_router.router)
app.include_router(contratos_router.router)
app.include_router(dotacao_router.router)
app.include_router(instrumentos_router.router)
app.include_router(itens_router.router)
app.include_router(locais_router.router)
app.include_router(modalidade_router.router)
app.include_router(numeromodalidade_router.router)
app.include_router(pedidos_router.router)
app.include_router(processoslicitatorios_router.router)
app.include_router(tiposdocumentos_router.router)
app.include_router(unidades_router.router)
app.include_router(home_router.router)
app.include_router(auth_router.router)