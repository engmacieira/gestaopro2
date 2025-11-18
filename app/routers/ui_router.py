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

from app.core.security import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token,
                               get_current_user, require_access_level)
from app.models.user_model import User
from app.repositories.user_repository import UserRepository 

from app.core.database import get_db
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.contrato_repository import ContratoRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.aocs_repository import AocsRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.ci_pagamento_repository import CiPagamentoRepository
from app.repositories.anexo_repository import AnexoRepository
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(os.path.dirname(BASE_DIR), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
try:
    from num2words import num2words
    templates.env.globals['num2words'] = num2words
except ImportError:
    logger.warning("Biblioteca 'num2words' não encontrada. A função por extenso não funcionará.")
    templates.env.globals['num2words'] = lambda x, **kwargs: f"Erro: num2words não instalada ({x})"


VERSAO_SOFTWARE = "3.0.0" 
ITENS_POR_PAGINA = 10 

templates.env.globals['versao_software'] = VERSAO_SOFTWARE

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
ENTIDADES_PESQUISAVEIS = { 
    'processo_licitatorio': {'label': 'Contratos por Processo Licitatório', 'tabela_principal': 'processoslicitatorios', 'coluna_texto': 'numero'},
    'unidade_requisitante': {'label': 'AOCS por Unidade Requisitante', 'tabela_principal': 'unidadesrequisitantes', 'coluna_texto': 'nome'},
    'local_entrega': {'label': 'AOCS por Local de Entrega', 'tabela_principal': 'locaisentrega', 'coluna_texto': 'descricao'},
    'dotacao': {'label': 'AOCS por Dotação Orçamentária', 'tabela_principal': 'dotacao', 'coluna_texto': 'info_orcamentaria'}
}
RELATORIOS_DISPONIVEIS = { 
    'lista_fornecedores': {'titulo': 'Lista de Fornecedores', 'descricao': '...', 'ordenacao_opcoes': {}},
    'lista_contratos': {'titulo': 'Lista de Contratos Ativos', 'descricao': '...', 'ordenacao_opcoes': {}}
}

@router.get("/login", response_class=HTMLResponse, name="login")
async def login_ui(request: Request, msg: str = None, category: str = None):
    """Renderiza a página de login."""
    context = {
        "messages": [(category, msg)] if msg and category else None,
        "get_flashed_messages": lambda **kwargs: [(category, msg)] if msg and category else []
    }
    return templates.TemplateResponse(request, "login.html", context)

@router.post("/login", name="login_post")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db_conn: connection = Depends(get_db) 
):
    """Processa o formulário de login, autentica e define o cookie."""
    user_repo = UserRepository(db_conn)
    user = user_repo.get_by_username(username)

    if not user or not user.verificar_senha(password):
        login_url = request.app.url_path_for("login")
        return RedirectResponse(
            url=f"{login_url}?msg=Usuário ou senha inválidos.&category=error",
            status_code=status.HTTP_302_FOUND
        )

    access_token = create_access_token(user=user)
    token_type = "bearer"

    response = RedirectResponse(url=request.app.url_path_for("home_ui"), status_code=status.HTTP_302_FOUND)
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expires = datetime.now(timezone.utc) + expires_delta

    response.set_cookie(
        key="access_token",
        value=f"{token_type} {access_token}",
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"), 
        httponly=True,
        samesite="lax",
        secure=False, 
        path="/"
    )
    return response

@router.get("/logout", name="logout")
async def logout(request: Request): 
    response = RedirectResponse(
        url=f"{request.app.url_path_for('login')}?msg=Você foi desconectado com sucesso.&category=success",
        status_code=status.HTTP_302_FOUND
    )
    response.delete_cookie(key="access_token", path="/", httponly=True)
    return response

@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def read_root(request: Request):
    return RedirectResponse(url=request.app.url_path_for("login"))

@router.get("/home", response_class=HTMLResponse, name="home_ui", dependencies=[Depends(require_access_level(3))])
async def home_ui(request: Request, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    indicadores = {"contratos_ativos": 0, "pedidos_mes": 0, "contratos_a_vencer": 0}
    pedidos_pendentes = []
    pagina_atual = 1
    total_paginas = 1
    try:
         cursor = db_conn.cursor()
         cursor.execute("SELECT COUNT(id) FROM Contratos WHERE ativo = TRUE")
         indicadores["contratos_ativos"] = cursor.fetchone()[0]
         cursor.close()
    except Exception as e:
         logger.error(f"Erro ao buscar dados do dashboard: {e}")

    context = {
        "current_user": current_user,
        "indicadores": indicadores,
        "pedidos_pendentes": pedidos_pendentes,
        "pagina_atual": pagina_atual,
        "total_paginas": total_paginas,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "index.html", context)

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
    repo = CategoriaRepository(db_conn)
    categorias_db = []
    total_paginas = 1
    try:
        categorias_db = repo.get_all(mostrar_inativos=mostrar_inativos)
        offset = (page - 1) * ITENS_POR_PAGINA
        total_itens = len(categorias_db)
        categorias_paginadas = categorias_db[offset:offset + ITENS_POR_PAGINA]
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

    except Exception as e:
        logger.error(f"Erro ao buscar categorias para UI: {e}")

    query_params = dict(request.query_params)

    context = {
        "current_user": current_user,
        "categorias": categorias_paginadas, 
        "pagina_atual": page,
        "total_paginas": total_paginas,
        "query_params": query_params,
        "mostrar_inativos": mostrar_inativos,
        "sort_by": sort_by,
        "order": order,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "categorias.html", context)

@router.get("/contratos-ui", response_class=HTMLResponse, name="contratos_ui", dependencies=[Depends(require_access_level(3))])
async def contratos_ui(
    request: Request,
    page: int = Query(1, alias="page"),
    busca: str | None = Query(None),
    status: str | None = Query(None),
    sort_by: str = Query('numero_contrato'),
    order: str = Query('asc'),
    mostrar_vencidos: str | None = Query(None),
    data_vencimento_filtro: str | None = Query(None),
    current_user=Depends(get_current_user),
    db_conn: connection = Depends(get_db)
):
    contratos_view = [] 
    total_paginas = 1
    hoje = date.today()

    try:
        logger.info(f"Buscando contratos: page={page}, busca={busca}, status={status}, sort={sort_by}, order={order}, mv={mostrar_vencidos}, dvf={data_vencimento_filtro}")

        repo = ContratoRepository(db_conn)
        todos_contratos = repo.get_all(mostrar_inativos=True)

        contratos_filtrados = todos_contratos

        if busca:
            termo = busca.lower()
            contratos_filtrados = [
                c for c in contratos_filtrados
                if termo in c.numero_contrato.lower() or (c.fornecedor and termo in c.fornecedor.nome.lower())
            ]

        if status == 'ativo':
            contratos_filtrados = [c for c in contratos_filtrados if c.ativo and c.data_fim >= hoje]
        elif status == 'inativo':
            contratos_filtrados = [c for c in contratos_filtrados if not c.ativo or (c.ativo and c.data_fim < hoje)]
        elif status == 'expirado':
             contratos_filtrados = [c for c in contratos_filtrados if c.data_fim < hoje]

        if mostrar_vencidos == 'false':
             contratos_filtrados = [c for c in contratos_filtrados if c.data_fim >= hoje]

        if data_vencimento_filtro == '60d':
             limite_vencimento = hoje + timedelta(days=60)
             contratos_filtrados = [c for c in contratos_filtrados if c.ativo and c.data_fim >= hoje and c.data_fim <= limite_vencimento]

        reverse_order = (order == 'desc')
        if sort_by == 'numero_contrato':
             contratos_filtrados.sort(key=lambda c: c.numero_contrato, reverse=reverse_order)
        elif sort_by == 'fornecedor':
             contratos_filtrados.sort(key=lambda c: c.fornecedor.nome if c.fornecedor else "", reverse=reverse_order)
        elif sort_by == 'data_vigencia_fim':
             contratos_filtrados.sort(key=lambda c: c.data_fim, reverse=reverse_order)
        elif sort_by == 'status_ativo':
             contratos_filtrados.sort(key=lambda c: c.ativo, reverse=reverse_order)
        offset = (page - 1) * ITENS_POR_PAGINA
        total_itens = len(contratos_filtrados)
        contratos_paginados = contratos_filtrados[offset:offset + ITENS_POR_PAGINA]
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA) if total_itens > 0 else 1

        cat_repo = CategoriaRepository(db_conn)
        proc_repo = ProcessoLicitatorioRepository(db_conn)
        for c in contratos_paginados:
             proc = proc_repo.get_by_id(c.id_processo_licitatorio) 
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
    return templates.TemplateResponse(request, "contratos.html", context)
    
@router.get("/pedidos-ui", response_class=HTMLResponse, name="pedidos_ui", dependencies=[Depends(require_access_level(3))])
async def pedidos_ui(request: Request, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    repo = PedidoRepository(db_conn)
    item_repo = ItemRepository(db_conn)
    aocs_repo = AocsRepository(db_conn)
    
    termo_busca = request.query_params.get('busca', '')
    sort_by = request.query_params.get('sort_by', 'data')
    order = request.query_params.get('order', 'desc')
    
    todos_pedidos = repo.get_all()
    
    pedidos_view = []
    for p in todos_pedidos:
        item = item_repo.get_by_id(p.id_item_contrato)
        aocs = aocs_repo.get_by_id(p.id_aocs)
        
        if termo_busca:
            termo = termo_busca.lower()
            if not (aocs and termo in aocs.numero_aocs.lower()) and \
               not (item and termo in item.descricao.descricao.lower()):
                continue
        
        valor_unitario = item.valor_unitario if item else Decimal('0.0')
        valor_total = p.quantidade_pedida * valor_unitario
        
        pedidos_view.append({
            "id": p.id,
            "numero_aocs": aocs.numero_aocs if aocs else "N/D",
            "descricao_item": item.descricao.descricao if item else "N/D",
            "quantidade": p.quantidade_pedida,
            "valor_unitario": valor_unitario,
            "valor_total": valor_total,
            "status": p.status_entrega,
            "data_pedido": p.data_pedido
        })

    total_itens = len(pedidos_view)
    pagina_atual = int(request.query_params.get('page', 1))
    offset = (pagina_atual - 1) * ITENS_POR_PAGINA
    pedidos_paginados = pedidos_view[offset:offset + ITENS_POR_PAGINA]
    total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA) if total_itens > 0 else 1

    context = {
        "current_user": current_user,
        "pedidos_lista": pedidos_paginados, 
        "pagina_atual": pagina_atual, 
        "total_paginas": total_paginas,
        "query_params": dict(request.query_params), 
        "sort_by": sort_by, 
        "order": order, 
        "termo_busca": termo_busca,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "pedidos.html", context)

@router.get("/consultas", response_class=HTMLResponse, name="consultas_ui", dependencies=[Depends(require_access_level(3))])
async def consultas_ui(request: Request, current_user=Depends(get_current_user)):
    context = {
        "current_user": current_user,
        "entidades_pesquisaveis": ENTIDADES_PESQUISAVEIS, 
        "processos": [], "unidades": [], "locais": [], "dotacoes": [],
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "consultas.html", context)

@router.get("/relatorios", response_class=HTMLResponse, name="relatorios_ui", dependencies=[Depends(require_access_level(3))])
async def relatorios_ui(request: Request, current_user=Depends(get_current_user)):
    context = {
        "current_user": current_user,
        "relatorios": RELATORIOS_DISPONIVEIS, 
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "relatorios.html", context)

@router.get("/importar", response_class=HTMLResponse, name="importar_ui", dependencies=[Depends(require_access_level(2))])
async def importar_ui(request: Request, current_user=Depends(get_current_user)):
    context = {"current_user": current_user, "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse(request, "importar.html", context)

@router.get("/contratos/novo", response_class=HTMLResponse, name="novo_contrato_ui", dependencies=[Depends(require_access_level(2))])
async def novo_contrato_ui(request: Request, current_user=Depends(get_current_user)):
    context = {"current_user": current_user, "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse(request, "importar.html", context)

@router.get("/gerenciar-tabelas", response_class=HTMLResponse, name="gerenciar_tabelas_ui", dependencies=[Depends(require_access_level(2))])
async def gerenciar_tabelas_ui(request: Request, current_user=Depends(get_current_user)):
    context = {
        "current_user": current_user,
        "tabelas": TABELAS_GERENCIAVEIS,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "gerenciar_tabelas.html", context)

@router.get("/admin/usuarios", response_class=HTMLResponse, name="gerenciar_usuarios_ui", dependencies=[Depends(require_access_level(1))])
async def gerenciar_usuarios_ui(request: Request, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    repo = UserRepository(db_conn)
    usuarios = []
    try:
        usuarios = repo.get_all(mostrar_inativos=True)
    except Exception as e:
        logger.error(f"Erro ao buscar usuários para UI admin: {e}")

    context = {
        "current_user": current_user,
        "usuarios": usuarios,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "gerenciar_usuarios.html", context)

@router.get("/contrato/{id_contrato}", response_class=HTMLResponse, name="detalhe_contrato", dependencies=[Depends(require_access_level(3))])
async def detalhe_contrato(request: Request, id_contrato: int, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    contrato_repo = ContratoRepository(db_conn)
    item_repo = ItemRepository(db_conn)
    anexo_repo = AnexoRepository(db_conn)
    tipo_doc_repo = TipoDocumentoRepository(db_conn)

    contrato = contrato_repo.get_by_id(id_contrato)
    if not contrato: raise HTTPException(status_code=404, detail="Contrato não encontrado")

    itens = item_repo.get_by_contrato_id(id_contrato)
    anexos = anexo_repo.get_by_entidade(id_entidade=id_contrato, tipo_entidade='contrato')
    tipos_documento = [td.nome for td in tipo_doc_repo.get_all()] 

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
    }


    context = {
        "current_user": current_user,
        "contrato": contrato_view, "itens": itens, "anexos": anexos,
        "tipos_documento": tipos_documento,
        "pagina_atual": 1, "total_paginas": 1, 
        "query_params": dict(request.query_params), "sort_by": 'numero_item', "order": 'asc', 
        "get_flashed_messages": lambda **kwargs: []
    }
    
    return templates.TemplateResponse(request, "detalhe_contrato.html", context)

@router.get("/contrato/{id_contrato}/importar-itens", response_class=HTMLResponse, name="importar_itens_ui", dependencies=[Depends(require_access_level(2))])
async def importar_itens_ui(
    request: Request, 
    id_contrato: int, 
    current_user=Depends(get_current_user), 
    db_conn: connection = Depends(get_db)
):
    contrato_repo = ContratoRepository(db_conn)
    contrato = contrato_repo.get_by_id(id_contrato)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")

    contrato_view = {
        "id": contrato.id,
        "numero_contrato": contrato.numero_contrato,
    }

    context = {
        "url_for": request.app.url_path_for, 
        "current_user": current_user,
        "contrato": contrato_view,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "importar_itens.html", context)

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
    cat_repo = CategoriaRepository(db_conn)
    categoria = cat_repo.get_by_id(id_categoria)
    if not categoria: 
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    itens = []
    total_paginas = 1
    query_params = dict(request.query_params)

    ITENS_POR_PAGINA = 10 
    cursor = None

    try:
        cursor = db_conn.cursor(cursor_factory=DictCursor)

        params = [id_categoria]
        where_clause = "WHERE c.id_categoria = %s AND c.ativo = TRUE AND ic.ativo = TRUE"

        if busca:
            where_clause += " AND ic.descricao ILIKE %s"
            params.append(f"%{busca}%")

        colunas_ordenaveis = {
            'descricao': 'ic.descricao', 
            'contrato': 'c.numero_contrato',
            'saldo': 'saldo', 
            'valor': 'ic.valor_unitario', 
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

        cursor.execute(sql_select, params)
        itens_db = cursor.fetchall()

        total_itens = 0
        if itens_db:
            total_itens = itens_db[0]['total_geral']
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

        itens = [dict(item) for item in itens_db]

    except (Exception, psycopg2.DatabaseError) as error:
         if cursor: cursor.close()
         logger.exception(f"Erro ao buscar itens com saldo para UI Categoria ID {id_categoria}: {error}")
         query_params["erro"] = "Erro ao consultar o banco de dados."
    finally:
        if cursor: cursor.close()

    context = {
        "current_user": current_user,
        "categoria": categoria, 
        "itens": itens, 
        "pagina_atual": page, 
        "total_paginas": total_paginas,
        "query_params": query_params, 
        "sort_by": sort_by, 
        "order": order,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "contratos_por_categoria.html", context)


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
        "current_user": current_user,
        "categoria": categoria,
        "unidades": [u.nome for u in unidade_repo.get_all()],
        "locais": [l.descricao for l in local_repo.get_all()],
        "responsaveis": [a.nome for a in agente_repo.get_all()],
        "dotacoes": [d.info_orcamentaria for d in dotacao_repo.get_all()],
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "novo_pedido.html", context)

@router.get("/pedido/{numero_aocs:path}/nova-ci", response_class=HTMLResponse, name="nova_ci_ui", dependencies=[Depends(require_access_level(2))])
async def nova_ci_ui(
    request: Request, 
    numero_aocs: str, 
    current_user=Depends(get_current_user), 
    db_conn: connection = Depends(get_db)
):
    aocs_repo = AocsRepository(db_conn)
    dotacao_repo = DotacaoRepository(db_conn)
    agente_repo = AgenteRepository(db_conn)
    unidade_repo = UnidadeRepository(db_conn)
    
    aocs = aocs_repo.get_by_numero_aocs(numero_aocs)
    if not aocs:
        raise HTTPException(status_code=404, detail="AOCS não encontrada.")

    primeiro_fornecedor = 'N/D'
    primeiro_cnpj = 'N/D'
    pedido_repo = PedidoRepository(db_conn)
    item_repo = ItemRepository(db_conn)
    contrato_repo = ContratoRepository(db_conn)
    
    pedidos = pedido_repo.get_by_aocs_id(aocs.id)
    if pedidos:
        item = item_repo.get_by_id(pedidos[0].id_item_contrato)
        contrato = contrato_repo.get_by_id(item.id_contrato) if item else None
        if contrato and contrato.fornecedor:
            primeiro_fornecedor = contrato.fornecedor.nome
            primeiro_cnpj = contrato.fornecedor.cpf_cnpj
            
    aocs_view = {
        "id": aocs.id,
        "justificativa": aocs.justificativa,
        "fornecedor": primeiro_fornecedor,
        "cpf_cnpj": primeiro_cnpj,
        "id_unidade_requisitante": aocs.id_unidade_requisitante,
        "id_agente_responsavel": aocs.id_agente_responsavel,
        "id_dotacao": aocs.id_dotacao
    }

    dotacoes = dotacao_repo.get_all()
    solicitantes = agente_repo.get_all()
    secretarias = unidade_repo.get_all()

    context = {
        "url_for": request.app.url_path_for, "current_user": current_user, 
        "numero_aocs": numero_aocs,
        "aocs": aocs_view, 
        "dotacoes": dotacoes, 
        "solicitantes": solicitantes, 
        "secretarias": secretarias, 
        "ci": {}, 
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "nova_ci.html", context)

@router.post("/pedido/{numero_aocs:path}/nova-ci", name="nova_ci_post", dependencies=[Depends(require_access_level(2))])
async def nova_ci_post(request: Request, numero_aocs: str, db_conn: connection = Depends(get_db)):
    form_data = await request.form()
    return RedirectResponse(url=request.app.url_path_for('detalhe_pedido', numero_aocs=numero_aocs), status_code=status.HTTP_302_FOUND)


@router.get("/ci/{id_ci}/editar", response_class=HTMLResponse, name="editar_ci_ui", dependencies=[Depends(require_access_level(2))])
async def editar_ci_ui(request: Request, id_ci: int, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    context = {"current_user": current_user, "id_ci": id_ci,
               "ci": {}, "aocs": {}, "dotacoes": [], "solicitantes": [], "secretarias": [],
               "get_flashed_messages": lambda **kwargs: []}
    return templates.TemplateResponse(request, "editar_ci.html", context)

@router.post("/ci/{id_ci}/editar", name="editar_ci_post", dependencies=[Depends(require_access_level(2))])
async def editar_ci_post(request: Request, id_ci: int, db_conn: connection = Depends(get_db)):
    form_data = await request.form()
    numero_aocs = "NUMERO_AOCS_AQUI" 
    return RedirectResponse(url=request.app.url_path_for('detalhe_pedido', numero_aocs=numero_aocs), status_code=status.HTTP_302_FOUND)

@router.get("/pedido/{numero_aocs:path}/imprimir", name="imprimir_aocs", dependencies=[Depends(require_access_level(2))])
async def imprimir_aocs(request: Request, numero_aocs: str, db_conn: connection = Depends(get_db)):
    return Response(content="PDF AOCS aqui", media_type='application/pdf')

@router.get("/pedido/{numero_aocs:path}/imprimir-pendentes", name="imprimir_pendentes_aocs", dependencies=[Depends(require_access_level(2))])
async def imprimir_pendentes_aocs(request: Request, numero_aocs: str, db_conn: connection = Depends(get_db)):
    return Response(content="PDF Pendentes aqui", media_type='application/pdf')

@router.get("/ci/{id_ci}/imprimir", name="imprimir_ci", dependencies=[Depends(require_access_level(2))])
async def imprimir_ci(request: Request, id_ci: int, db_conn: connection = Depends(get_db)):
    return Response(content="PDF CI aqui", media_type='application/pdf')

@router.get("/pedido/{numero_aocs:path}", response_class=HTMLResponse, name="detalhe_pedido", dependencies=[Depends(require_access_level(3))])
async def detalhe_pedido(request: Request, numero_aocs: str, current_user=Depends(get_current_user), db_conn: connection = Depends(get_db)):
    aocs_repo = AocsRepository(db_conn)
    pedido_repo = PedidoRepository(db_conn)
    item_repo = ItemRepository(db_conn)
    contrato_repo = ContratoRepository(db_conn)
    ci_repo = CiPagamentoRepository(db_conn)
    anexo_repo = AnexoRepository(db_conn)
    unidade_repo = UnidadeRepository(db_conn)
    local_repo = LocalRepository(db_conn)
    agente_repo = AgenteRepository(db_conn)
    dotacao_repo = DotacaoRepository(db_conn)
    tipo_doc_repo = TipoDocumentoRepository(db_conn)

    aocs = aocs_repo.get_by_numero_aocs(numero_aocs)
    if not aocs: 
        raise HTTPException(status_code=404, detail="AOCS não encontrada")

    pedidos = pedido_repo.get_by_aocs_id(aocs.id)
    itens_view = []
    total_pedido_valor = Decimal('0.0')
    total_entregue_qtd = Decimal('0.0')
    total_pedido_qtd = Decimal('0.0')
    
    primeiro_fornecedor = 'N/D'
    primeiro_cnpj = 'N/D'

    for p in pedidos:
        item = item_repo.get_by_id(p.id_item_contrato)
        contrato = contrato_repo.get_by_id(item.id_contrato) if item else None
        
        if item and contrato:
            subtotal = p.quantidade_pedida * item.valor_unitario
            total_pedido_valor += subtotal
            total_entregue_qtd += p.quantidade_entregue
            total_pedido_qtd += p.quantidade_pedida

            if not itens_view: 
                primeiro_fornecedor = contrato.fornecedor.nome if contrato.fornecedor else 'N/D'
                primeiro_cnpj = contrato.fornecedor.cpf_cnpj if contrato.fornecedor else 'N/D'
            
            itens_view.append({
                "id_pedido": p.id,
                "quantidade_pedida": p.quantidade_pedida,
                "quantidade_entregue": p.quantidade_entregue,
                "descricao": item.descricao.descricao,
                "valor_unitario": item.valor_unitario,
                "numero_item_contrato": item.numero_item,
                "numero_contrato": contrato.numero_contrato,
                "unidade_medida": item.unidade_medida,
            })

    if total_pedido_qtd == 0: status_geral = 'Vazio'
    elif total_entregue_qtd >= total_pedido_qtd: status_geral = 'Entregue'
    elif total_entregue_qtd > 0: status_geral = 'Entrega Parcial'
    else: status_geral = 'Pendente'

    cis = ci_repo.get_all() 
    cis_filtradas = [ci for ci in cis if ci.id_aocs == aocs.id]
    anexos = anexo_repo.get_by_entidade(id_entidade=aocs.id, tipo_entidade='aocs')

    unidades = [u.nome for u in unidade_repo.get_all()]
    locais = [l.descricao for l in local_repo.get_all()]
    responsaveis = [a.nome for a in agente_repo.get_all()]
    dotacoes = [d.info_orcamentaria for d in dotacao_repo.get_all()]
    tipos_documento = [td.nome for td in tipo_doc_repo.get_all()]

    aocs_view = {
        "id": aocs.id,
        "numero_aocs": aocs.numero_aocs,
        "data_criacao": aocs.data_criacao,
        "numero_pedido": aocs.numero_pedido,
        "empenho": aocs.empenho,
        "status_entrega": status_geral,
        "valor_total": total_pedido_valor,
        
        "fornecedor": primeiro_fornecedor,
        "cpf_cnpj": primeiro_cnpj,
        "unidade_requisitante": unidade_repo.get_by_id(aocs.id_unidade_requisitante).nome if aocs.id_unidade_requisitante else 'N/D',
        "local_entrega": local_repo.get_by_id(aocs.id_local_entrega).descricao if aocs.id_local_entrega else 'N/D',
        "agente_responsavel": agente_repo.get_by_id(aocs.id_agente_responsavel).nome if aocs.id_agente_responsavel else 'N/D',
        "info_orcamentaria": dotacao_repo.get_by_id(aocs.id_dotacao).info_orcamentaria if aocs.id_dotacao else 'N/D',
    }

    context = {
        "url_for": request.app.url_path_for, "current_user": current_user,
        "aocs": aocs_view, "itens": itens_view, "anexos": anexos, "cis_pagamento": cis_filtradas,
        "unidades": unidades, "locais": locais, "responsaveis": responsaveis,
        "dotacoes": dotacoes, "tipos_documento": tipos_documento,
        "get_flashed_messages": lambda **kwargs: []
    }
    return templates.TemplateResponse(request, "detalhe_pedido.html", context)

@router.get("/uploads/{path:path}", name="uploaded_file")
async def uploaded_file(path: str):
     raise HTTPException(status_code=404, detail="Rota de upload não implementada ou insegura")