# app/routers/ui_router.py

import os
import logging
import math
import psycopg2 
from psycopg2.extras import DictCursor
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                     Response, status)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from psycopg2.extensions import connection

# Funções e modelos de segurança
from app.core.security import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token,
                               get_current_user, require_access_level)
from app.models.user_model import User
from app.repositories.user_repository import UserRepository # Para login

# Banco de dados e outros repositórios
from app.core.database import get_db
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.contrato_repository import ContratoRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.aocs_repository import AocsRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.ci_pagamento_repository import CiPagamentoRepository
from app.repositories.anexo_repository import AnexoRepository
# Repositórios para tabelas de domínio (necessários para formulários/contexto)
from app.repositories.unidade_repository import UnidadeRepository
from app.repositories.local_repository import LocalRepository
from app.repositories.agente_repository import AgenteRepository
from app.repositories.dotacao_repository import DotacaoRepository
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.repositories.instrumento_repository import InstrumentoRepository
from app.repositories.modalidade_repository import ModalidadeRepository
from app.repositories.numero_modalidade_repository import NumeroModalidadeRepository
from app.repositories.processo_licitatorio_repository import ProcessoLicitatorioRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["UI - Páginas Web"])

# --- Configuração de Templates ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(os.path.dirname(BASE_DIR), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
# Adiciona num2words ao ambiente Jinja (se necessário para templates de CI)
try:
    from num2words import num2words
    templates.env.globals['num2words'] = num2words
except ImportError:
    logger.warning("Biblioteca 'num2words' não encontrada. A função por extenso não funcionará.")
    templates.env.globals['num2words'] = lambda x, **kwargs: f"Erro: num2words não instalada ({x})"


# --- Constantes e Configurações Globais (se houver) ---
VERSAO_SOFTWARE = "3.0.0" # Ou leia de um arquivo de configuração
ITENS_POR_PAGINA = 10 # Padrão para paginação

# Adiciona variáveis globais aos templates
templates.env.globals['versao_software'] = VERSAO_SOFTWARE

# Dicionários do Flask migrados (simplificados para exemplo)
TABELAS_GERENCIAVEIS = {
    'instrumento-contratual': {'tabela': 'instrumentocontratual', 'coluna': 'nome'},
    'modalidade': {'tabela': 'modalidade', 'coluna': 'nome'},
    'numero-modalidade': {'tabela': 'numeromodalidade', 'coluna': 'numero_ano'},
    'processo-licitatorio': {'tabela': 'processoslicitatorios', 'coluna': 'numero'},
    'unidade-requisitante': {'tabela': 'unidadesrequisitantes', 'coluna': 'nome'},
    'local-entrega': {'tabela': 'locaisentrega', 'coluna': 'descricao'},
    'agente-responsavel': {'tabela': 'agentesresponsaveis', 'coluna': 'nome'},
    'dotacao': {'tabela': 'dotacao', 'coluna': 'info_orcamentaria'},
    'tipo-documento': {'tabela': 'tipos_documento', 'coluna': 'nome'}
}
ENTIDADES_PESQUISAVEIS = { # Simplificado - Adicionar SQLs depois
    'processo_licitatorio': {'label': 'Contratos por Processo Licitatório', 'tabela_principal': 'processoslicitatorios', 'coluna_texto': 'numero'},
    'unidade_requisitante': {'label': 'AOCS por Unidade Requisitante', 'tabela_principal': 'unidadesrequisitantes', 'coluna_texto': 'nome'},
    'local_entrega': {'label': 'AOCS por Local de Entrega', 'tabela_principal': 'locaisentrega', 'coluna_texto': 'descricao'},
    'dotacao': {'label': 'AOCS por Dotação Orçamentária', 'tabela_principal': 'dotacao', 'coluna_texto': 'info_orcamentaria'}
}
RELATORIOS_DISPONIVEIS = { # Simplificado - Adicionar SQLs depois
    'lista_fornecedores': {'titulo': 'Lista de Fornecedores', 'descricao': '...', 'ordenacao_opcoes': {}},
    'lista_contratos': {'titulo': 'Lista de Contratos Ativos', 'descricao': '...', 'ordenacao_opcoes': {}}
}


# --- Rotas de Autenticação e Básicas ---

@router.get("/login", response_class=HTMLResponse, name="login")
async def login_ui(request: Request, msg: str = None, category: str = None):
    """Renderiza a página de login."""
    context = {
        "request": request,
        "messages": [(category, msg)] if msg and category else None,
        # Adicionar get_flashed_messages simulado se necessário por algum template
        "get_flashed_messages": lambda **kwargs: [(category, msg)] if msg and category else []
    }
    return templates.TemplateResponse("login.html", context)

@router.post("/login", name="login_post")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db_conn: connection = Depends(get_db) # Adicionar dependência do DB
):
    """Processa o formulário de login, autentica e define o cookie."""
    user_repo = UserRepository(db_conn)
    user = user_repo.get_by_username(username)

    # Autenticação Real
    if not user or not user.verificar_senha(password):
        # Redireciona de volta para o login com mensagem de erro
        login_url = request.app.url_path_for("login")
        return RedirectResponse(
            url=f"{login_url}?msg=Usuário ou senha inválidos.&category=error",
            status_code=status.HTTP_302_FOUND
        )

    # Cria o token JWT real
    access_token = create_access_token(user=user)
    token_type = "bearer"

    # Redireciona para o home e define o cookie
    response = RedirectResponse(url=request.app.url_path_for("home_ui"), status_code=status.HTTP_302_FOUND)
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Correção de Fuso Horário
    expires = datetime.now(timezone.utc) + expires_delta

    response.set_cookie(
        key="access_token",
        value=f"{token_type} {access_token}",
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"), # Formato correto para cookie expires
        httponly=True,
        samesite="lax",
        secure=False, # Mude para True em produção com HTTPS
        path="/"
    )
    return response

@router.get("/logout", name="logout")
async def logout(request: Request): # Precisa do request para url_for
    """Remove o cookie de acesso e redireciona para o login."""
    response = RedirectResponse(
        url=f"{request.app.url_path_for('login')}?msg=Você foi desconectado com sucesso.&category=success",
        status_code=status.HTTP_302_FOUND
    )
    response.delete_cookie(key="access_token", path="/", httponly=True)
    return response

@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def read_root(request: Request):
    """Redireciona a raiz para a página de login."""
    return RedirectResponse(url=request.app.url_path_for("login"))


# --- Rotas Principais da UI ---

@router.get("/home", response_class=HTMLResponse, name="home_ui", dependencies=[Depends(require_access_level(3))])
async def home_ui(request: Request, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    """Renderiza a página principal (dashboard)."""
    # Lógica de busca de dados reais (exemplo simplificado)
    indicadores = {"contratos_ativos": 0, "pedidos_mes": 0, "contratos_a_vencer": 0}
    pedidos_pendentes = []
    pagina_atual = 1
    total_paginas = 1
    # Tente buscar os dados reais aqui, se falhar, use os simulados
    try:
         # Exemplo de busca real (você precisará adaptar as queries do app-versaoantiga.py)
         cursor = db_conn.cursor()
         cursor.execute("SELECT COUNT(id) FROM Contratos WHERE ativo = TRUE")
         indicadores["contratos_ativos"] = cursor.fetchone()[0]
         # ... outras queries ...
         cursor.close()
    except Exception as e:
         logger.error(f"Erro ao buscar dados do dashboard: {e}")
         # Manter dados simulados em caso de erro

    context = {
        "request": request,
        "current_user": current_user,
        "indicadores": indicadores,
        "pedidos_pendentes": pedidos_pendentes,
        "pagina_atual": pagina_atual,
        "total_paginas": total_paginas,
        # Adicionar get_flashed_messages simulado
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("index.html", context)

@router.get("/categorias-ui", response_class=HTMLResponse, name="categorias_ui", dependencies=[Depends(require_access_level(3))])
async def categorias_ui(
    request: Request,
    page: int = Query(1, alias="page"),
    mostrar_inativos: bool = Query(False),
    sort_by: str = Query('id'),
    order: str = Query('asc'),
    current_user=Depends(get_current_user),
    db_conn: connection = Depends(get_db)
):
    """Renderiza a página de gerenciamento de categorias."""
    repo = CategoriaRepository(db_conn)
    categorias_db = []
    total_paginas = 1
    try:
        # Lógica de busca e paginação real (simplificada)
        # Você precisará adaptar a lógica de paginação e ordenação do seu repo ou aqui
        categorias_db = repo.get_all(mostrar_inativos=mostrar_inativos)
        # Simulação de paginação básica
        offset = (page - 1) * ITENS_POR_PAGINA
        total_itens = len(categorias_db)
        categorias_paginadas = categorias_db[offset:offset + ITENS_POR_PAGINA]
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

    except Exception as e:
        logger.error(f"Erro ao buscar categorias para UI: {e}")
        # Tratar erro, talvez mostrar mensagem

    query_params = dict(request.query_params)

    context = {
        "request": request,
        "current_user": current_user,
        "categorias": categorias_paginadas, # Usar dados paginados
        "pagina_atual": page,
        "total_paginas": total_paginas,
        "query_params": query_params,
        "mostrar_inativos": mostrar_inativos,
        "sort_by": sort_by,
        "order": order,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("categorias.html", context)

# Garanta que Query está importado: from fastapi import Query

@router.get("/contratos-ui", response_class=HTMLResponse, name="contratos_ui", dependencies=[Depends(require_access_level(3))])
async def contratos_ui(
    request: Request,
    page: int = Query(1, alias="page"),
    busca: str | None = Query(None),
    status: str | None = Query(None),
    sort_by: str = Query('numero_contrato'),
    order: str = Query('asc'),
    # --- PARÂMETROS ADICIONADOS ---
    mostrar_vencidos: str | None = Query(None),
    data_vencimento_filtro: str | None = Query(None),
    # --- FIM DA ADIÇÃO ---
    current_user=Depends(get_current_user),
    db_conn: connection = Depends(get_db)
):
    """Renderiza a página de gerenciamento de contratos."""
    contratos_view = [] # Inicializa com lista vazia
    total_paginas = 1
    hoje = date.today()

    try:
        logger.info(f"Buscando contratos: page={page}, busca={busca}, status={status}, sort={sort_by}, order={order}, mv={mostrar_vencidos}, dvf={data_vencimento_filtro}")

        repo = ContratoRepository(db_conn)
        # Busca inicial (considera inativos para filtros posteriores)
        todos_contratos = repo.get_all(mostrar_inativos=True)

        contratos_filtrados = todos_contratos

        # Aplicar filtro de busca textual
        if busca:
            termo = busca.lower()
            contratos_filtrados = [
                c for c in contratos_filtrados
                if termo in c.numero_contrato.lower() or (c.fornecedor and termo in c.fornecedor.nome.lower())
            ]

        # Aplicar filtro de status explícito da UI
        if status == 'ativo':
            contratos_filtrados = [c for c in contratos_filtrados if c.ativo and c.data_fim >= hoje]
        elif status == 'inativo':
            # Inclui inativos por flag E expirados que ainda estão marcados como ativos
            contratos_filtrados = [c for c in contratos_filtrados if not c.ativo or (c.ativo and c.data_fim < hoje)]
        elif status == 'expirado':
             contratos_filtrados = [c for c in contratos_filtrados if c.data_fim < hoje]

        # Aplicar filtros específicos do link "Contratos a Vencer"
        # O link passa mostrar_vencidos='false' e data_vencimento_filtro='60d'
        if mostrar_vencidos == 'false':
             # Garante que apenas contratos não expirados sejam considerados
             contratos_filtrados = [c for c in contratos_filtrados if c.data_fim >= hoje]

        if data_vencimento_filtro == '60d':
             limite_vencimento = hoje + timedelta(days=60)
             # Filtra apenas os ativos que vencem nos próximos 60 dias
             contratos_filtrados = [c for c in contratos_filtrados if c.ativo and c.data_fim >= hoje and c.data_fim <= limite_vencimento]

        # Aplicar ordenação (Exemplo simples - Adapte conforme necessidade)
        reverse_order = (order == 'desc')
        if sort_by == 'numero_contrato':
             # Ordenação numérica/alfabética simples (ajustar se necessário para formato X/YYYY)
             contratos_filtrados.sort(key=lambda c: c.numero_contrato, reverse=reverse_order)
        elif sort_by == 'fornecedor':
             contratos_filtrados.sort(key=lambda c: c.fornecedor.nome if c.fornecedor else "", reverse=reverse_order)
        elif sort_by == 'data_vigencia_fim':
             contratos_filtrados.sort(key=lambda c: c.data_fim, reverse=reverse_order)
        elif sort_by == 'status_ativo':
             contratos_filtrados.sort(key=lambda c: c.ativo, reverse=reverse_order)
        # Adicionar outras colunas de ordenação se necessário

        # Paginação
        offset = (page - 1) * ITENS_POR_PAGINA
        total_itens = len(contratos_filtrados)
        contratos_paginados = contratos_filtrados[offset:offset + ITENS_POR_PAGINA]
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA) if total_itens > 0 else 1

        # Mapeamento para View (após paginação)
        cat_repo = CategoriaRepository(db_conn)
        proc_repo = ProcessoLicitatorioRepository(db_conn)
        for c in contratos_paginados:
             # cat = cat_repo.get_by_id(c.id_categoria) # Otimizar: buscar todos os IDs necessários de uma vez
             proc = proc_repo.get_by_id(c.id_processo_licitatorio) # Otimizar
             contratos_view.append({
                 'id': c.id,
                 'numero_contrato': c.numero_contrato,
                 'processo_licitatorio': proc.numero if proc else 'N/D',
                 'fornecedor': c.fornecedor.nome if c.fornecedor else 'N/D',
                 'data_vigencia_fim': c.data_fim,
                 'status_ativo': c.ativo,
             })

    except Exception as e:
        logger.exception(f"Erro ao buscar contratos para UI: {e}")

    query_params = dict(request.query_params)

    context = {
        "request": request,
        "current_user": current_user,
        "contratos": contratos_view,
        "pagina_atual": page,
        "total_paginas": total_paginas,
        "query_params": query_params,
        "sort_by": sort_by,
        "order": order,
        "hoje": hoje,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("contratos.html", context)
    
# --- Rotas UI Adicionais (Estrutura Básica - PREENCHER LÓGICA) ---

@router.get("/pedidos-ui", response_class=HTMLResponse, name="pedidos_ui", dependencies=[Depends(require_access_level(3))])
async def pedidos_ui(request: Request, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    # Lógica para buscar pedidos (AOCS + status agregado), paginar, ordenar, filtrar
    pedidos_lista = []
    pagina_atual = int(request.query_params.get('page', 1))
    total_paginas = 1
    query_params = dict(request.query_params)
    sort_by = request.query_params.get('sort_by', 'data')
    order = request.query_params.get('order', 'desc')
    termo_busca = request.query_params.get('busca', '')

    # Adicione sua lógica de query complexa aqui
    # Exemplo: Chamar um método de repositório que retorna a visão agregada

    context = {
        "request": request, "current_user": current_user,
        "pedidos_lista": pedidos_lista, "pagina_atual": pagina_atual, "total_paginas": total_paginas,
        "query_params": query_params, "sort_by": sort_by, "order": order, "termo_busca": termo_busca,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("pedidos.html", context)

@router.get("/consultas", response_class=HTMLResponse, name="consultas_ui", dependencies=[Depends(require_access_level(3))])
async def consultas_ui(request: Request, current_user=Depends(get_current_user)):
    # Lógica para buscar opções dos selects (processos, unidades, etc.)
    context = {
        "request": request, "current_user": current_user,
        "entidades_pesquisaveis": ENTIDADES_PESQUISAVEIS, # Passar config
         # Adicionar listas de opções para os selects, se necessário pré-carregar
        "processos": [], "unidades": [], "locais": [], "dotacoes": [],
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("consultas.html", context)

@router.get("/relatorios", response_class=HTMLResponse, name="relatorios_ui", dependencies=[Depends(require_access_level(3))])
async def relatorios_ui(request: Request, current_user=Depends(get_current_user)):
    context = {
        "request": request, "current_user": current_user,
        "relatorios": RELATORIOS_DISPONIVEIS, # Passar config
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("relatorios.html", context)

@router.get("/importar", response_class=HTMLResponse, name="importar_ui", dependencies=[Depends(require_access_level(2))])
async def importar_ui(request: Request, current_user=Depends(get_current_user)):
    context = {"request": request, "current_user": current_user, "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse("importar.html", context)

@router.get("/contratos/novo", response_class=HTMLResponse, name="novo_contrato_ui", dependencies=[Depends(require_access_level(2))])
async def novo_contrato_ui(request: Request, current_user=Depends(get_current_user)):
    # TODO: Criar o template novo_contrato.html
    context = {"request": request, "current_user": current_user, "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse("importar.html", context)

@router.get("/gerenciar-tabelas", response_class=HTMLResponse, name="gerenciar_tabelas_ui", dependencies=[Depends(require_access_level(2))])
async def gerenciar_tabelas_ui(request: Request, current_user=Depends(get_current_user)):
    context = {
        "request": request, "current_user": current_user,
        "tabelas": TABELAS_GERENCIAVEIS, # Passar config
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("gerenciar_tabelas.html", context)

@router.get("/admin/usuarios", response_class=HTMLResponse, name="gerenciar_usuarios_ui", dependencies=[Depends(require_access_level(1))])
async def gerenciar_usuarios_ui(request: Request, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    repo = UserRepository(db_conn)
    usuarios = []
    try:
        # Busca todos, incluindo inativos, para a tela de admin
        usuarios = repo.get_all(mostrar_inativos=True)
    except Exception as e:
        logger.error(f"Erro ao buscar usuários para UI admin: {e}")

    context = {
        "request": request, "current_user": current_user,
        "usuarios": usuarios,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("gerenciar_usuarios.html", context)

# --- Rotas de Detalhe e Ação (Estrutura Básica - PREENCHER LÓGICA) ---

@router.get("/contrato/{id_contrato}", response_class=HTMLResponse, name="detalhe_contrato", dependencies=[Depends(require_access_level(3))])
async def detalhe_contrato(request: Request, id_contrato: int, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    # Lógica para buscar contrato, itens (paginado), anexos, tipos de documento
    contrato_repo = ContratoRepository(db_conn)
    item_repo = ItemRepository(db_conn)
    anexo_repo = AnexoRepository(db_conn)
    tipo_doc_repo = TipoDocumentoRepository(db_conn)

    contrato = contrato_repo.get_by_id(id_contrato)
    if not contrato: raise HTTPException(status_code=404, detail="Contrato não encontrado")

    # Adicionar lógica de paginação/ordenação para itens
    itens = item_repo.get_by_contrato_id(id_contrato)
    anexos = anexo_repo.get_by_entidade(id_entidade=id_contrato, tipo_entidade='contrato')
    tipos_documento = [td.nome for td in tipo_doc_repo.get_all()] # Simplificado

    # Buscar nomes de FKs para exibição
    cat_repo = CategoriaRepository(db_conn)
    inst_repo = InstrumentoRepository(db_conn)
    mod_repo = ModalidadeRepository(db_conn)
    num_mod_repo = NumeroModalidadeRepository(db_conn)
    proc_repo = ProcessoLicitatorioRepository(db_conn)

    categoria = cat_repo.get_by_id(contrato.id_categoria)
    instrumento = inst_repo.get_by_id(contrato.id_instrumento_contratual)
    modalidade = mod_repo.get_by_id(contrato.id_modalidade)
    num_modalidade = num_mod_repo.get_by_id(contrato.id_numero_modalidade)
    processo = proc_repo.get_by_id(contrato.id_processo_licitatorio)

    contrato_view = {
        "id": contrato.id,
        "numero_contrato": contrato.numero_contrato,
        "fornecedor": contrato.fornecedor.nome,
        "cpf_cnpj": contrato.fornecedor.cpf_cnpj,
        "email": contrato.fornecedor.email,
        "telefone": contrato.fornecedor.telefone,
        "data_inicio_br": contrato.data_inicio.strftime('%d/%m/%Y'),
        "data_fim_br": contrato.data_fim.strftime('%d/%m/%Y'),
        "nome_categoria": categoria.nome if categoria else 'N/D',
        "nome_instrumento": instrumento.nome if instrumento else 'N/D',
        "nome_modalidade": modalidade.nome if modalidade else 'N/D',
        "numero_modalidade_ano": num_modalidade.numero_ano if num_modalidade else 'N/D',
        "numero_processo": processo.numero if processo else 'N/D',
        # Adicione outros campos necessários
    }


    context = {
        "request": request, "current_user": current_user,
        "contrato": contrato_view, "itens": itens, "anexos": anexos,
        "tipos_documento": tipos_documento,
        "pagina_atual": 1, "total_paginas": 1, # Adicionar paginação real
        "query_params": dict(request.query_params), "sort_by": 'numero_item', "order": 'asc', # Adicionar ordenação real
        "get_flashed_messages": lambda **kwargs: []
    }
    # Adicionar lógica para servir arquivos estáticos via /uploads/<path:filename> se necessário
    # ou usar a rota API /anexos/download/{id}

    return templates.TemplateResponse("detalhe_contrato.html", context)


@router.get("/categoria/{id_categoria}/contratos", response_class=HTMLResponse, name="contratos_por_categoria", dependencies=[Depends(require_access_level(3))])
async def contratos_por_categoria(
    request: Request, 
    id_categoria: int, 
    page: int = Query(1, alias="page"),
    busca: str = Query(None),
    sort_by: str = Query("descricao"),
    order: str = Query("asc"),
    current_user=Depends(get_current_user), 
    db_conn: connection = Depends(get_db)
):
    # Lógica para buscar categoria e itens (com saldo), paginar, ordenar, filtrar
    cat_repo = CategoriaRepository(db_conn)
    categoria = cat_repo.get_by_id(id_categoria)
    if not categoria: 
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    itens = []
    total_paginas = 1
    query_params = dict(request.query_params)

    # --- LÓGICA DA API COLADA AQUI ---
    ITENS_POR_PAGINA = 10 # Você pode ajustar isso
    cursor = None

    try:
        cursor = db_conn.cursor(cursor_factory=DictCursor)

        # 1. Montagem da Query
        params = [id_categoria]
        where_clause = "WHERE c.id_categoria = %s AND c.ativo = TRUE AND ic.ativo = TRUE"

        if busca:
            where_clause += " AND ic.descricao ILIKE %s"
            params.append(f"%{busca}%")

        colunas_ordenaveis = {
            'descricao': 'ic.descricao', 
            'contrato': 'c.numero_contrato',
            'saldo': 'saldo', 
            'valor': 'ic.valor_unitario', # 'valor' é o nome usado no template
            'numero_item': 'ic.numero_item'
        }
        coluna_ordenacao = colunas_ordenaveis.get(sort_by, 'ic.descricao')
        direcao_ordenacao = 'DESC' if order == 'desc' else 'ASC'
        order_by_clause = f"ORDER BY {coluna_ordenacao} {direcao_ordenacao}"

        offset = (page - 1) * ITENS_POR_PAGINA
        limit_offset_clause = "LIMIT %s OFFSET %s"
        params.extend([ITENS_POR_PAGINA, offset])

        sql_select = f"""
            SELECT
                ic.*, 
                c.id AS id_contrato, 
                c.numero_contrato, 
                c.fornecedor,
                COALESCE(pedidos_sum.total_pedido, 0) AS total_pedido,
                (ic.quantidade - COALESCE(pedidos_sum.total_pedido, 0)) AS saldo,
                COUNT(*) OVER() as total_geral
            FROM itenscontrato ic
            JOIN contratos c ON ic.id_contrato = c.id
            LEFT JOIN (
                SELECT id_item_contrato, SUM(quantidade_pedida) as total_pedido
                FROM pedidos GROUP BY id_item_contrato
            ) AS pedidos_sum ON ic.id = pedidos_sum.id_item_contrato
            {where_clause} 
            {order_by_clause} 
            {limit_offset_clause}
        """

        # 2. Execução
        cursor.execute(sql_select, params)
        itens_db = cursor.fetchall()

        # 3. Cálculo da Paginação
        total_itens = 0
        if itens_db:
            total_itens = itens_db[0]['total_geral']
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

        # 4. Formatação da Resposta (o template HTML lê 'dict' direto, não precisa formatar como JSON)
        itens = [dict(item) for item in itens_db]

    except (Exception, psycopg2.DatabaseError) as error:
         if cursor: cursor.close()
         logger.exception(f"Erro ao buscar itens com saldo para UI Categoria ID {id_categoria}: {error}")
         # Em vez de levantar um 500, podemos só mostrar a página vazia com um erro
         query_params["erro"] = "Erro ao consultar o banco de dados."
    finally:
        if cursor: cursor.close()
    # --- FIM DA LÓGICA COLADA ---

    context = {
        "request": request, "current_user": current_user,
        "categoria": categoria, 
        "itens": itens, # Agora 'itens' contém os dados reais
        "pagina_atual": page, 
        "total_paginas": total_paginas,
        "query_params": query_params, 
        "sort_by": sort_by, 
        "order": order,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("contratos_por_categoria.html", context)


@router.get("/categoria/{id_categoria}/novo-pedido", response_class=HTMLResponse, name="novo_pedido_pagina", dependencies=[Depends(require_access_level(2))])
async def novo_pedido_pagina(request: Request, id_categoria: int, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    cat_repo = CategoriaRepository(db_conn)
    categoria = cat_repo.get_by_id(id_categoria)
    if not categoria: raise HTTPException(status_code=404, detail="Categoria não encontrada")

    unidade_repo = UnidadeRepository(db_conn)
    local_repo = LocalRepository(db_conn)
    agente_repo = AgenteRepository(db_conn)
    dotacao_repo = DotacaoRepository(db_conn)

    context = {
        "request": request, "current_user": current_user,
        "categoria": categoria,
        "unidades": [u.nome for u in unidade_repo.get_all()],
        "locais": [l.descricao for l in local_repo.get_all()],
        "responsaveis": [a.nome for a in agente_repo.get_all()],
        "dotacoes": [d.info_orcamentaria for d in dotacao_repo.get_all()],
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("novo_pedido.html", context)


@router.get("/pedido/{numero_aocs}", response_class=HTMLResponse, name="detalhe_pedido", dependencies=[Depends(require_access_level(3))])
async def detalhe_pedido(request: Request, numero_aocs: str, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    aocs_repo = AocsRepository(db_conn)
    pedido_repo = PedidoRepository(db_conn)
    item_repo = ItemRepository(db_conn)
    contrato_repo = ContratoRepository(db_conn)
    ci_repo = CiPagamentoRepository(db_conn)
    anexo_repo = AnexoRepository(db_conn)
    # Repos de domínio
    unidade_repo = UnidadeRepository(db_conn)
    local_repo = LocalRepository(db_conn)
    agente_repo = AgenteRepository(db_conn)
    dotacao_repo = DotacaoRepository(db_conn)
    tipo_doc_repo = TipoDocumentoRepository(db_conn)

    aocs = aocs_repo.get_by_numero_aocs(numero_aocs)
    if not aocs: raise HTTPException(status_code=404, detail="AOCS não encontrada")

    pedidos = pedido_repo.get_by_aocs_id(aocs.id)
    itens_view = []
    total_pedido_valor = Decimal('0.0')
    total_entregue_qtd = Decimal('0.0')
    total_pedido_qtd = Decimal('0.0')

    for p in pedidos:
        item = item_repo.get_by_id(p.id_item_contrato)
        contrato = contrato_repo.get_by_id(item.id_contrato) if item else None
        if item and contrato:
            subtotal = p.quantidade_pedida * item.valor_unitario
            total_pedido_valor += subtotal
            total_entregue_qtd += p.quantidade_entregue
            total_pedido_qtd += p.quantidade_pedida
            itens_view.append({
                "id_pedido": p.id,
                "quantidade_pedida": p.quantidade_pedida,
                "quantidade_entregue": p.quantidade_entregue,
                "descricao": item.descricao.descricao,
                "valor_unitario": item.valor_unitario,
                "numero_item_contrato": item.numero_item,
                "numero_contrato": contrato.numero_contrato,
                "unidade_medida": item.unidade_medida,
                # Adicionar mais campos se o template precisar
            })

    # Status Geral
    if total_pedido_qtd == 0: status_geral = 'Vazio'
    elif total_entregue_qtd >= total_pedido_qtd: status_geral = 'Entregue'
    elif total_entregue_qtd > 0: status_geral = 'Entrega Parcial'
    else: status_geral = 'Pendente'

    # Busca CIs e Anexos
    cis = ci_repo.get_all() # Filtrar por aocs.id seria melhor
    cis_filtradas = [ci for ci in cis if ci.id_aocs == aocs.id]
    anexos = anexo_repo.get_by_entidade(id_entidade=aocs.id, tipo_entidade='aocs')

    # Busca dados de domínio para modais
    unidades = [u.nome for u in unidade_repo.get_all()]
    locais = [l.descricao for l in local_repo.get_all()]
    responsaveis = [a.nome for a in agente_repo.get_all()]
    dotacoes = [d.info_orcamentaria for d in dotacao_repo.get_all()]
    tipos_documento = [td.nome for td in tipo_doc_repo.get_all()]

    # Dados da AOCS para o template
    aocs_view = {
        "id": aocs.id,
        "numero_aocs": aocs.numero_aocs,
        "data_criacao": aocs.data_criacao,
        "numero_pedido": aocs.numero_pedido,
        "empenho": aocs.empenho,
        "status_entrega": status_geral,
        "valor_total": total_pedido_valor,
        # Buscar nomes das FKs
        "fornecedor": itens_view[0]['fornecedor'] if itens_view else 'N/D', # Assumindo mesmo fornecedor
        "cpf_cnpj": itens_view[0]['cpf_cnpj'] if itens_view else 'N/D',
        # ... buscar nomes de unidade, local, agente, dotacao ...
    }


    context = {
        "request": request, "current_user": current_user,
        "aocs": aocs_view, "itens": itens_view, "anexos": anexos, "cis_pagamento": cis_filtradas,
        "unidades": unidades, "locais": locais, "responsaveis": responsaveis,
        "dotacoes": dotacoes, "tipos_documento": tipos_documento,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse("detalhe_pedido.html", context)


# --- Rotas para CIs (Adicionar lógica de GET/POST para nova_ci_ui e editar_ci_ui) ---
@router.get("/pedido/{numero_aocs}/nova-ci", response_class=HTMLResponse, name="nova_ci_ui", dependencies=[Depends(require_access_level(2))])
async def nova_ci_ui(request: Request, numero_aocs: str, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    # Buscar dados da AOCS e listas de domínio
    context = {"request": request, "current_user": current_user, "numero_aocs": numero_aocs,
               "aocs": {}, "dotacoes": [], "solicitantes": [], "secretarias": [], "ci": {}, # ci vazio para o template _ci_form_fields
               "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse("nova_ci.html", context)

@router.post("/pedido/{numero_aocs}/nova-ci", name="nova_ci_post", dependencies=[Depends(require_access_level(2))])
async def nova_ci_post(request: Request, numero_aocs: str, db_conn: connection = Depends(get_db)):
    # Processar form, criar CI, redirecionar
    form_data = await request.form()
    # ... Lógica de criação ...
    return RedirectResponse(url=request.app.url_path_for('detalhe_pedido', numero_aocs=numero_aocs), status_code=status.HTTP_302_FOUND)


@router.get("/ci/{id_ci}/editar", response_class=HTMLResponse, name="editar_ci_ui", dependencies=[Depends(require_access_level(2))])
async def editar_ci_ui(request: Request, id_ci: int, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    # Buscar dados da CI, AOCS associada e listas de domínio
    context = {"request": request, "current_user": current_user, "id_ci": id_ci,
               "ci": {}, "aocs": {}, "dotacoes": [], "solicitantes": [], "secretarias": [],
               "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse("editar_ci.html", context)

@router.post("/ci/{id_ci}/editar", name="editar_ci_post", dependencies=[Depends(require_access_level(2))])
async def editar_ci_post(request: Request, id_ci: int, db_conn: connection = Depends(get_db)):
    # Processar form, atualizar CI, redirecionar
    form_data = await request.form()
    # ... Lógica de atualização ...
    # Descobrir numero_aocs para redirecionar
    numero_aocs = "NUMERO_AOCS_AQUI" # Buscar do banco
    return RedirectResponse(url=request.app.url_path_for('detalhe_pedido', numero_aocs=numero_aocs), status_code=status.HTTP_302_FOUND)

# --- Rotas para Impressão (Adaptar lógica de _gerar_pdf_ci e outras) ---
@router.get("/pedido/{numero_aocs}/imprimir", name="imprimir_aocs", dependencies=[Depends(require_access_level(2))])
async def imprimir_aocs(request: Request, numero_aocs: str, db_conn: connection = Depends(get_db)):
    # Lógica para gerar PDF da AOCS
    # Use weasyprint e render_template('aocs_template.html', ...)
    return Response(content="PDF AOCS aqui", media_type='application/pdf')

@router.get("/pedido/{numero_aocs}/imprimir-pendentes", name="imprimir_pendentes_aocs", dependencies=[Depends(require_access_level(2))])
async def imprimir_pendentes_aocs(request: Request, numero_aocs: str, db_conn: connection = Depends(get_db)):
    # Lógica para gerar PDF dos itens pendentes
    # Use weasyprint e render_template('aocs_pendentes_template.html', ...)
    return Response(content="PDF Pendentes aqui", media_type='application/pdf')

@router.get("/ci/{id_ci}/imprimir", name="imprimir_ci", dependencies=[Depends(require_access_level(2))])
async def imprimir_ci(request: Request, id_ci: int, db_conn: connection = Depends(get_db)):
    # Lógica para gerar PDF da CI
    # Use weasyprint e render_template('ci_pagamento_template.html', ...)
    return Response(content="PDF CI aqui", media_type='application/pdf')

# Rota para servir arquivos de upload (Exemplo, pode precisar de ajustes)
# A rota API /anexos/download/{id} é mais segura e recomendada
@router.get("/uploads/{path:path}", name="uploaded_file")
async def uploaded_file(path: str):
     # Implementar lógica segura para servir arquivos
     # return FileResponse(...)
     raise HTTPException(status_code=404, detail="Rota de upload não implementada ou insegura")