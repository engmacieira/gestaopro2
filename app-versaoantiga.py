# ====================================================================
# Arquivo Principal do Backend - app.py
# Versão 2.1.0 (Refatorado e Estabilizado)
# ====================================================================

# --- 1. Importações ---

# Bibliotecas Padrão
import locale
import math
import os
import pathlib
import secrets
import string
import traceback
from collections import defaultdict
from decimal import Decimal
from datetime import date, datetime, timedelta

# Bibliotecas de Terceiros
import pandas as pd
import psycopg2
from flask import (Flask, Response, flash, jsonify, redirect, render_template,
                   request, send_from_directory, url_for)
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from psycopg2.extras import DictCursor
from num2words import num2words
from weasyprint import HTML
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# --- 2. Configuração da Aplicação e Funções Auxiliares ---

# --- Constantes Globais ---
VERSAO_SOFTWARE = "2.1.0"
UPLOAD_FOLDER = 'uploads'
CAMINHO_PROJETO = pathlib.Path(__file__).parent
SECRET_KEY = 'uma-chave-secreta-muito-segura-e-dificil-de-adivinhar'

TABELAS_GERENCIAVEIS = {
    'instrumento-contratual': {'tabela': 'instrumentocontratual', 'coluna': 'nome', 'fk_tabela': 'contratos', 'fk_coluna': 'id_instrumento_contratual'},
    'modalidade': {'tabela': 'modalidade', 'coluna': 'nome', 'fk_tabela': 'contratos', 'fk_coluna': 'id_modalidade'},
    'numero-modalidade': {'tabela': 'numeromodalidade', 'coluna': 'numero_ano', 'fk_tabela': 'contratos', 'fk_coluna': 'id_numero_modalidade'},
    'processo-licitatorio': {'tabela': 'processoslicitatorios', 'coluna': 'numero', 'fk_tabela': 'contratos', 'fk_coluna': 'id_processo_licitatorio'},
    'unidade-requisitante': {'tabela': 'unidadesrequisitantes', 'coluna': 'nome', 'fk_tabela': 'aocs', 'fk_coluna': 'id_unidade_requisitante'},
    'local-entrega': {'tabela': 'locaisentrega', 'coluna': 'descricao', 'fk_tabela': 'aocs', 'fk_coluna': 'id_local_entrega'},
    'agente-responsavel': {'tabela': 'agentesresponsaveis', 'coluna': 'nome', 'fk_tabela': 'aocs', 'fk_coluna': 'id_agente_responsavel'},
    'dotacao': {'tabela': 'dotacao', 'coluna': 'info_orcamentaria', 'fk_tabela': 'aocs', 'fk_coluna': 'id_dotacao'},
    'tipo-documento': {'tabela': 'tipos_documento', 'coluna': 'nome', 'fk_tabela': 'anexos', 'fk_coluna': 'tipo_documento'}
}

# --- Inicialização e Configuração do App Flask ---
app = Flask(__name__)

# --- Configuração do Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

class User(UserMixin):
    def __init__(self, id, username, password_hash, nivel_acesso):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.nivel_acesso = nivel_acesso
        
@login_manager.user_loader
def load_user(user_id):
    """Carrega um usuário do banco de dados a partir do seu ID."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = %s AND ativo = TRUE", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                nivel_acesso=user_data['nivel_acesso']
            )
        return None
    except Exception as e:
        traceback.print_exc()
        return None
    finally:
        if conexao:
            conexao.close()

app.config.update(
    SECRET_KEY=SECRET_KEY,
    UPLOAD_FOLDER=UPLOAD_FOLDER
)

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    print("Locale pt_BR.UTF-8 não encontrado. Usando o padrão do sistema.")
    pass

@app.context_processor
def inject_global_vars():
    return dict(versao_software=VERSAO_SOFTWARE)

def get_db_connection():
    """
    Cria uma conexão com o banco de dados.
    É inteligente o suficiente para funcionar tanto no Render (usando DATABASE_URL)
    quanto localmente (usando variáveis de ambiente separadas).
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        return psycopg2.connect(database_url, sslmode='require', cursor_factory=DictCursor)
    else:
        return psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            database=os.environ.get("DB_NAME", "gestao_contratos"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "34251311"),
            cursor_factory=DictCursor
        )
def _get_itens_por_categoria_com_saldo(id_categoria, termo_busca="", page=1, sort_by='descricao', order='asc', paginate=True):
    conexao = None
    try:
        ITENS_POR_PAGINA = 10
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute('SELECT * FROM Categorias WHERE id = %s', (id_categoria,))
        categoria = cursor.fetchone()
        if not categoria:
            return None, [], 0, 0, "Categoria não encontrada!"

        params = [id_categoria]
        where_clause = "WHERE c.id_categoria = %s AND c.ativo = TRUE AND ic.ativo = TRUE"
        if termo_busca:
            where_clause += " AND ic.descricao ILIKE %s"
            params.append(f"%{termo_busca}%")

        colunas_ordenaveis = {
            'descricao': 'ic.descricao', 'contrato': 'c.numero_contrato',
            'saldo': 'saldo', 'valor': 'ic.valor_unitario', 'numero_item': 'ic.numero_item'
        }
        coluna_ordenacao = colunas_ordenaveis.get(sort_by, 'ic.descricao')
        direcao_ordenacao = 'DESC' if order == 'desc' else 'ASC'
        order_by_clause = f"ORDER BY {coluna_ordenacao} {direcao_ordenacao}"
        
        limit_offset_clause = ""
        if paginate:
            offset = (page - 1) * ITENS_POR_PAGINA
            limit_offset_clause = "LIMIT %s OFFSET %s"
            params.extend([ITENS_POR_PAGINA, offset])

        sql_select = f"""
            SELECT
                ic.*, c.id AS id_contrato, c.numero_contrato, c.fornecedor,
                COALESCE(pedidos_sum.total_pedido, 0) AS total_pedido,
                (ic.quantidade - COALESCE(pedidos_sum.total_pedido, 0)) AS saldo,
                COUNT(*) OVER() as total_geral
            FROM ItensContrato ic
            JOIN Contratos c ON ic.id_contrato = c.id
            LEFT JOIN (
                SELECT id_item_contrato, SUM(quantidade_pedida) as total_pedido
                FROM Pedidos GROUP BY id_item_contrato
            ) AS pedidos_sum ON ic.id = pedidos_sum.id_item_contrato
            {where_clause} {order_by_clause} {limit_offset_clause}
        """
        cursor.execute(sql_select, params)
        itens_com_saldo = cursor.fetchall()
        
        total_paginas = 1
        if paginate and itens_com_saldo:
            total_itens = itens_com_saldo[0]['total_geral']
            total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)
        
        return categoria, itens_com_saldo, total_paginas, page, None

    except psycopg2.Error as e:
        traceback.print_exc()
        return None, [], 0, 0, f"Erro no banco de dados: {e}"
    finally:
        if conexao: conexao.close()
            
def _limpar_e_truncar(texto, tamanho):
    if not texto: return 'ND'
    texto_limpo = ''.join(c for c in texto if c.isalnum() or c == '-')
    return texto_limpo.upper()[:tamanho]

def _get_or_create_id(cursor, table_name, column_name, value):
    if not value or not str(value).strip(): return None
    cursor.execute(f"SELECT id FROM public.{table_name} WHERE {column_name} = %s", (value,))
    result = cursor.fetchone()
    if result: return result['id']
    cursor.execute(f"INSERT INTO public.{table_name} ({column_name}) VALUES (%s) RETURNING id", (value,))
    return cursor.fetchone()['id']

from functools import wraps

def nivel_acesso_required(nivel_exigido):
    """
    Decorator customizado que restringe o acesso a uma rota com base no nível do usuário.
    O acesso é permitido se o nível do usuário for MENOR OU IGUAL ao nível exigido.
    (Ex: Nível 1-Admin pode acessar rotas de nível 1, 2 e 3).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            
            if current_user.nivel_acesso > nivel_exigido:
                flash("Você não tem permissão para acessar esta página.", "error")
                return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- 3. Rotas que Servem Páginas de Interface (UI) ---

# --- Dashboard ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Exibe a página de login e processa o formulário de autenticação."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conexao = None
        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE username = %s AND ativo = TRUE", (username,))
            user_data = cursor.fetchone()

            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    nivel_acesso=user_data['nivel_acesso']
                )
                login_user(user) 
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
            else:
                flash('Usuário ou senha inválidos.', 'error')

        except Exception as e:
            traceback.print_exc()
            flash('Ocorreu um erro durante o login.', 'error')
        finally:
            if conexao:
                conexao.close()

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Faz o logout do usuário atual."""
    logout_user() 
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@nivel_acesso_required(3)
@login_required
def home():
    """Serve o dashboard principal com dados dinâmicos e pendências paginadas."""
    conexao = None
    indicadores = {"contratos_ativos": 0, "pedidos_mes": 0, "contratos_a_vencer": 0}
    
    try:
        pagina_atual = request.args.get('page', 1, type=int)
        ITENS_POR_PAGINA = 10
        offset = (pagina_atual - 1) * ITENS_POR_PAGINA

        conexao = get_db_connection()
        cursor = conexao.cursor()

        sql_indicadores = """
            SELECT 
                (SELECT COUNT(id) FROM Contratos WHERE ativo = TRUE) AS contratos_ativos,
                (SELECT COUNT(DISTINCT a.id) FROM Pedidos p JOIN AOCS a ON p.id_aocs = a.id WHERE TO_CHAR(a.data_criacao, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')) AS pedidos_mes,
                (SELECT COUNT(id) FROM Contratos WHERE ativo = TRUE AND data_fim BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days') AS contratos_a_vencer;
        """
        cursor.execute(sql_indicadores)
        indicadores = dict(cursor.fetchone())
        sql_count_pendentes = "SELECT COUNT(DISTINCT a.id) FROM Pedidos p JOIN AOCS a ON p.id_aocs = a.id WHERE p.status_entrega != 'Entregue'"
        cursor.execute(sql_count_pendentes)
        total_itens = cursor.fetchone()[0]
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

        sql_select_pendentes = """
            SELECT 
                a.numero_aocs, 
                TO_CHAR(a.data_criacao, 'DD/MM/YYYY') AS data_pedido, 
                c.numero_contrato,
                (CURRENT_DATE - a.data_criacao) AS dias_passados
            FROM Pedidos p
            JOIN ItensContrato ic ON p.id_item_contrato = ic.id
            JOIN Contratos c ON ic.id_contrato = c.id
            JOIN AOCS a ON p.id_aocs = a.id
            WHERE p.status_entrega != 'Entregue'
            GROUP BY a.id, c.numero_contrato
            ORDER BY a.data_criacao ASC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql_select_pendentes, (ITENS_POR_PAGINA, offset))
        pedidos_pendentes = cursor.fetchall()
        
        return render_template('index.html', 
                               indicadores=indicadores, 
                               pedidos_pendentes=pedidos_pendentes,
                               pagina_atual=pagina_atual, 
                               total_paginas=total_paginas)
    
    except psycopg2.Error as e:
        traceback.print_exc()
        return render_template('index.html', 
                               indicadores=indicadores, 
                               pedidos_pendentes=[], 
                               pagina_atual=1, 
                               total_paginas=1, 
                               erro=f"Erro no banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()

# --- Gestão de Categorias ---

@app.route('/categorias-ui')
@nivel_acesso_required(3)
@login_required
def categorias_ui():
    """Serve a página de categorias com dados paginados e ordenação."""
    conexao = None
    pagina_atual = request.args.get('page', 1, type=int)
    mostrar_inativos = request.args.get('mostrar_inativos') == 'true'
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')

    try:
        ITENS_POR_PAGINA = 10
        offset = (pagina_atual - 1) * ITENS_POR_PAGINA

        conexao = get_db_connection()
        cursor = conexao.cursor()

        where_clause = "" if mostrar_inativos else "WHERE ativo = TRUE"
        colunas_ordenaveis = {'id': 'id', 'nome': 'nome', 'status': 'ativo'}
        coluna_ordenacao = colunas_ordenaveis.get(sort_by, 'id')
        direcao_ordenacao = 'DESC' if order == 'desc' else 'ASC'
        order_by_clause = f"ORDER BY {coluna_ordenacao} {direcao_ordenacao}"

        sql = f"""
            SELECT *, COUNT(*) OVER() AS total_geral
            FROM Categorias
            {where_clause}
            {order_by_clause}
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (ITENS_POR_PAGINA, offset))
        categorias_db = cursor.fetchall()

        total_itens = categorias_db[0]['total_geral'] if categorias_db else 0
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

        query_params = {'mostrar_inativos': 'true' if mostrar_inativos else None, 
                        'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v is not None}

        return render_template('categorias.html', 
                               categorias=categorias_db, 
                               pagina_atual=pagina_atual, 
                               total_paginas=total_paginas,
                               query_params=query_params, 
                               mostrar_inativos=mostrar_inativos,
                               sort_by=sort_by, 
                               order=order)
                               
    except psycopg2.Error as e:
        traceback.print_exc()
        query_params = {'mostrar_inativos': 'true' if mostrar_inativos else None, 
                        'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v is not None}
        return render_template('categorias.html', 
                               categorias=[], 
                               pagina_atual=pagina_atual, 
                               total_paginas=1,
                               query_params=query_params, 
                               mostrar_inativos=mostrar_inativos,
                               sort_by=sort_by, 
                               order=order, 
                               erro=f"Erro no banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()

# --- Gestão de Contratos ---

@app.route('/contratos-ui')
@nivel_acesso_required(3)
@login_required
def contratos_ui():
    """Serve a página para gerenciar contratos, com dados das tabelas de domínio."""
    conexao = None
    pagina_atual = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')
    mostrar_inativos = request.args.get('mostrar_inativos') == 'true'
    mostrar_vencidos = request.args.get('mostrar_vencidos') == 'true'
    sort_by = request.args.get('sort_by', 'numero_contrato')
    order = request.args.get('order', 'asc') 

    try:
        ITENS_POR_PAGINA = 10
        offset = (pagina_atual - 1) * ITENS_POR_PAGINA

        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT nome FROM instrumentocontratual ORDER BY nome")
        instrumentos = [row['nome'] for row in cursor.fetchall()]
        cursor.execute("SELECT nome FROM modalidade ORDER BY nome")
        modalidades = [row['nome'] for row in cursor.fetchall()]
        
        params = []
        condicoes = []
        if not mostrar_inativos: condicoes.append("c.ativo = TRUE")
        if not mostrar_vencidos: condicoes.append("c.data_fim >= CURRENT_DATE")
        if termo_busca:
            condicoes.append("(c.numero_contrato ILIKE %s OR c.fornecedor ILIKE %s OR cat.nome ILIKE %s OR inst.nome ILIKE %s)")
            params.extend([f"%{termo_busca}%"] * 4)
        where_clause = " WHERE " + " AND ".join(condicoes) if condicoes else ""

        colunas_ordenaveis = {
            'numero_contrato': "CAST(SPLIT_PART(c.numero_contrato, '/', 2) AS INTEGER) {0}, CAST(SPLIT_PART(c.numero_contrato, '/', 1) AS INTEGER) {0}",
            'tipo': 'inst.nome {0}', 'fornecedor': 'c.fornecedor {0}', 'categoria': 'cat.nome {0}'}
        direcao_ordenacao = 'DESC' if order == 'desc' else 'ASC'
        coluna_tpl = colunas_ordenaveis.get(sort_by, colunas_ordenaveis['numero_contrato'])
        order_by_clause = f"ORDER BY {coluna_tpl.format(direcao_ordenacao)}"

        sql = f"""
            SELECT 
                c.id, c.numero_contrato, c.fornecedor, c.ativo, 
                cat.nome AS nome_categoria,
                inst.nome AS nome_instrumento,
                COALESCE(anexo_counts.total_anexos, 0) AS total_anexos,
                COUNT(*) OVER() as total_geral
            FROM Contratos c
            JOIN Categorias cat ON c.id_categoria = cat.id
            LEFT JOIN instrumentocontratual inst ON c.id_instrumento_contratual = inst.id
            LEFT JOIN (
                SELECT id_entidade, COUNT(id) AS total_anexos 
                FROM Anexos 
                WHERE tipo_entidade = 'contrato'
                GROUP BY id_entidade
            ) AS anexo_counts ON c.id = anexo_counts.id_entidade
            {where_clause} 
            {order_by_clause} 
            LIMIT %s OFFSET %s
        """
        params.extend([ITENS_POR_PAGINA, offset])
        cursor.execute(sql, params)
        contratos_db = cursor.fetchall()

        total_itens = contratos_db[0]['total_geral'] if contratos_db else 0
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)

        query_params = {'busca': termo_busca, 'mostrar_inativos': 'true' if mostrar_inativos else None,
                        'mostrar_vencidos': 'true' if mostrar_vencidos else None,
                        'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v}
        
        return render_template('contratos.html', 
                               contratos=contratos_db, 
                               pagina_atual=pagina_atual, total_paginas=total_paginas, 
                               query_params=query_params, termo_busca=termo_busca, 
                               mostrar_inativos=mostrar_inativos, mostrar_vencidos=mostrar_vencidos, 
                               sort_by=sort_by, order=order,
                               instrumentos=instrumentos, modalidades=modalidades)
    
    except psycopg2.Error as e:
        traceback.print_exc()
        query_params = {'busca': termo_busca, 'mostrar_inativos': 'true' if mostrar_inativos else None,
                        'mostrar_vencidos': 'true' if mostrar_vencidos else None,
                        'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v}
        return render_template('contratos.html', contratos=[], pagina_atual=1, total_paginas=1,
                               instrumentos=[], modalidades=[], query_params=query_params,
                               termo_busca=termo_busca, mostrar_inativos=mostrar_inativos,
                               mostrar_vencidos=mostrar_vencidos, sort_by=sort_by, order=order,
                               erro=f"Erro no banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()

@app.route('/contrato/<int:id_contrato>')
@nivel_acesso_required(3)
@login_required
def detalhe_contrato(id_contrato):
    """Serve a página de detalhes de um contrato, com dados das tabelas de domínio."""
    conexao = None
    try:
        pagina_atual = request.args.get('page', 1, type=int)
        mostrar_inativos = request.args.get('mostrar_inativos') == 'true'
        sort_by = request.args.get('sort_by', 'numero_item')
        order = request.args.get('order', 'asc')

        ITENS_POR_PAGINA = 10
        offset = (pagina_atual - 1) * ITENS_POR_PAGINA

        conexao = get_db_connection()
        cursor = conexao.cursor()   

        cursor.execute("SELECT nome FROM tipos_documento ORDER BY nome ASC")
        tipos_documento = [row['nome'] for row in cursor.fetchall()]
        
        sql_contrato = """
            SELECT c.*, cat.nome AS nome_categoria, inst.nome AS nome_instrumento, 
                   m.nome AS nome_modalidade, nm.numero_ano AS numero_modalidade_ano, 
                   pl.numero AS numero_processo,
                   TO_CHAR(c.data_inicio, 'DD/MM/YYYY') AS data_inicio_br,
                   TO_CHAR(c.data_fim, 'DD/MM/YYYY') AS data_fim_br
            FROM Contratos c 
            LEFT JOIN Categorias cat ON c.id_categoria = cat.id
            LEFT JOIN instrumentocontratual inst ON c.id_instrumento_contratual = inst.id
            LEFT JOIN modalidade m ON c.id_modalidade = m.id
            LEFT JOIN numeromodalidade nm ON c.id_numero_modalidade = nm.id
            LEFT JOIN processoslicitatorios pl ON c.id_processo_licitatorio = pl.id
            WHERE c.id = %s
        """
        cursor.execute(sql_contrato, (id_contrato,))
        contrato = cursor.fetchone()
        
        if not contrato: return "Contrato não encontrado!", 404

        params = [id_contrato]
        where_clause = "WHERE ic.id_contrato = %s"
        if not mostrar_inativos: where_clause += ' AND ic.ativo = TRUE'

        colunas_ordenaveis = {'numero_item': 'ic.numero_item', 'descricao': 'ic.descricao',
                              'saldo': 'saldo', 'valor': 'ic.valor_unitario'}
        coluna_ordenacao = colunas_ordenaveis.get(sort_by, 'ic.numero_item')
        direcao_ordenacao = 'DESC' if order == 'desc' else 'ASC'
        order_by_clause = f"ORDER BY {coluna_ordenacao} {direcao_ordenacao}"

        sql_itens = f"""
            SELECT ic.*, COALESCE(ps.total_pedido, 0) AS total_pedido,
                   (ic.quantidade - COALESCE(ps.total_pedido, 0)) AS saldo,
                   COUNT(*) OVER() AS total_geral
            FROM ItensContrato ic
            LEFT JOIN (SELECT id_item_contrato, SUM(quantidade_pedida) as total_pedido
                       FROM Pedidos GROUP BY id_item_contrato) AS ps ON ic.id = ps.id_item_contrato
            {where_clause} {order_by_clause} LIMIT %s OFFSET %s
        """
        params.extend([ITENS_POR_PAGINA, offset])
        cursor.execute(sql_itens, params)
        itens = cursor.fetchall()
        
        total_itens = itens[0]['total_geral'] if itens else 0
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)
        
        cursor.execute("""
            SELECT *, TO_CHAR(data_upload, 'DD/MM/YYYY') as data_upload_br 
            FROM Anexos 
            WHERE id_entidade = %s AND tipo_entidade = 'contrato' 
            ORDER BY id DESC
        """, (id_contrato,))
        anexos = cursor.fetchall()

        query_params = {'mostrar_inativos': 'true' if mostrar_inativos else None, 
                        'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v}
        
        return render_template('detalhe_contrato.html', contrato=contrato, itens=itens,
                               anexos=anexos, pagina_atual=pagina_atual,
                               total_paginas=total_paginas, query_params=query_params,
                               sort_by=sort_by, order=order,
                               tipos_documento=tipos_documento)
                               
    except psycopg2.Error as e:
        traceback.print_exc()
        return f"Erro no banco de dados: {e}", 500
    finally:
        if conexao:
            conexao.close()

# --- Gestão de Pedidos ---

@app.route('/pedidos-ui')
@nivel_acesso_required(3)
@login_required
def pedidos_ui():
    """Serve a página de histórico de pedidos, com paginação, filtros e ordenação."""
    conexao = None
    pagina_atual = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')
    sort_by = request.args.get('sort_by', 'data')
    order = request.args.get('order', 'desc')

    try:
        ITENS_POR_PAGINA = 10
        offset = (pagina_atual - 1) * ITENS_POR_PAGINA

        conexao = get_db_connection()
        cursor = conexao.cursor()

        params = []
        where_clause = ""
        if termo_busca:
            where_clause = " WHERE a.numero_aocs ILIKE %s OR c.fornecedor ILIKE %s"
            params.extend([f"%{termo_busca}%", f"%{termo_busca}%"])

        colunas_ordenaveis = {
            'aocs': 'a.numero_aocs', 'fornecedor': 'c.fornecedor',
            'valor': 'valor_total', 'data': 'a.data_criacao', 'status': 'p.status_entrega'
        }
        coluna_ordenacao = colunas_ordenaveis.get(sort_by, 'a.data_criacao')
        direcao_ordenacao = 'DESC' if order == 'desc' else 'ASC'
        order_by_clause = f"ORDER BY {coluna_ordenacao} {direcao_ordenacao}"

        sql = f"""
            SELECT 
                a.numero_aocs, 
                a.data_criacao AS data_pedido, 
                a.numero_pedido,
                p.status_entrega,
                c.fornecedor, 
                SUM(p.quantidade_pedida * ic.valor_unitario) AS valor_total,
                COUNT(*) OVER() AS total_geral
            FROM Pedidos p
            JOIN ItensContrato ic ON p.id_item_contrato = ic.id
            JOIN Contratos c ON ic.id_contrato = c.id
            JOIN AOCS a ON p.id_aocs = a.id
            {where_clause}
            GROUP BY a.id, c.fornecedor, p.status_entrega
            {order_by_clause} 
            LIMIT %s OFFSET %s
        """
        params.extend([ITENS_POR_PAGINA, offset])
        cursor.execute(sql, params)
        pedidos_lista = cursor.fetchall()
        
        total_itens = pedidos_lista[0]['total_geral'] if pedidos_lista else 0
        total_paginas = math.ceil(total_itens / ITENS_POR_PAGINA)
        
        query_params = {'busca': termo_busca, 'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v}

        return render_template('pedidos.html', 
                               pedidos_lista=pedidos_lista, 
                               pagina_atual=pagina_atual,
                               total_paginas=total_paginas, 
                               query_params=query_params,
                               sort_by=sort_by, 
                               order=order, 
                               termo_busca=termo_busca)

    except psycopg2.Error as e:
        traceback.print_exc()
        query_params = {'busca': termo_busca, 'sort_by': sort_by, 'order': order}
        query_params = {k: v for k, v in query_params.items() if v}
        return render_template('pedidos.html', pedidos_lista=[], pagina_atual=1, 
                               total_paginas=1, query_params=query_params, sort_by=sort_by,
                               order=order, termo_busca=termo_busca, 
                               erro=f"Erro no banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()

@app.route('/pedido/<path:numero_aocs>')
@nivel_acesso_required(3)
@login_required
def detalhe_pedido(numero_aocs):
    """Serve a página de detalhes do pedido, com lógica de controle de entrega."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT nome FROM unidadesrequisitantes ORDER BY nome")
        unidades = [row['nome'] for row in cursor.fetchall()]
        cursor.execute("SELECT descricao FROM locaisentrega ORDER BY descricao")
        locais = [row['descricao'] for row in cursor.fetchall()]
        cursor.execute("SELECT nome FROM agentesresponsaveis ORDER BY nome")
        responsaveis = [row['nome'] for row in cursor.fetchall()]
        cursor.execute("SELECT info_orcamentaria FROM dotacao ORDER BY info_orcamentaria")
        dotacoes = [row['info_orcamentaria'] for row in cursor.fetchall()]
        cursor.execute("SELECT nome FROM tipos_documento ORDER BY nome ASC")
        tipos_documento = [row['nome'] for row in cursor.fetchall()]
        
        sql = """
            SELECT
                a.*, p.id AS id_pedido, p.quantidade_pedida, p.quantidade_entregue,
                ic.id AS id_item_contrato, ic.descricao, ic.unidade_medida, ic.valor_unitario,
                ic.numero_item AS numero_item_contrato,
                c.id AS id_contrato, c.numero_contrato, c.fornecedor, c.cpf_cnpj
            FROM Pedidos p
            JOIN ItensContrato ic ON p.id_item_contrato = ic.id
            JOIN Contratos c ON ic.id_contrato = c.id
            JOIN AOCS a ON p.id_aocs = a.id
            WHERE a.numero_aocs = %s
        """
        cursor.execute(sql, (numero_aocs,))
        itens_do_pedido = cursor.fetchall()

        if not itens_do_pedido:
            return "Pedido não encontrado!", 404
        
        dados_aocs = dict(itens_do_pedido[0])
        id_aocs = dados_aocs['id']

        total_pedido = sum(item['quantidade_pedida'] for item in itens_do_pedido)
        total_entregue = sum(item['quantidade_entregue'] for item in itens_do_pedido)

        if total_entregue >= total_pedido:
            status_geral = 'Entregue'
        elif total_entregue > 0:
            status_geral = 'Entrega Parcial'
        else:
            status_geral = 'Pendente'
            
        dados_aocs['status_entrega'] = status_geral

        sql_anexos = """
            SELECT *, TO_CHAR(data_upload, 'DD/MM/YYYY') as data_upload_br 
            FROM Anexos 
            WHERE id_entidade = %s AND tipo_entidade = 'aocs' 
            ORDER BY id DESC
        """
        cursor.execute(sql_anexos, (id_aocs,))
        anexos = cursor.fetchall()

        cursor.execute("SELECT * FROM ci_pagamento WHERE id_aocs = %s ORDER BY data_ci DESC", (id_aocs,))
        cis_pagamento = cursor.fetchall()
        
        return render_template('detalhe_pedido.html', 
                               aocs=dados_aocs,
                               itens=itens_do_pedido,
                               unidades=unidades,
                               locais=locais,
                               responsaveis=responsaveis,
                               dotacoes=dotacoes,
                               tipos_documento=tipos_documento,
                               anexos=anexos,
                               cis_pagamento=cis_pagamento)

    except psycopg2.Error as e:
        traceback.print_exc()
        return f"Erro no banco de dados: {e}", 500
    finally:
        if conexao:
            conexao.close()
            
# --- Fluxo de Operação (Catálogo e Pedidos) ---

@app.route('/categoria/<int:id_categoria>/contratos')
@nivel_acesso_required(3)
@login_required
def contratos_por_categoria(id_categoria):
    """Serve a página de catálogo, com paginação, filtros e ordenação."""
    termo_busca = request.args.get('busca', '')
    pagina_atual = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'descricao')
    order = request.args.get('order', 'asc')

    categoria, itens, total_paginas, _, erro = _get_itens_por_categoria_com_saldo(
        id_categoria, termo_busca, pagina_atual, sort_by, order)
    if erro:
        return erro, 404 if "não encontrada" in erro else 500
        
    query_params = {'busca': termo_busca, 'sort_by': sort_by, 'order': order}
    query_params = {k: v for k, v in query_params.items() if v}
    
    return render_template('contratos_por_categoria.html', categoria=categoria, itens=itens, 
                           pagina_atual=pagina_atual, total_paginas=total_paginas,
                           query_params=query_params, sort_by=sort_by, order=order)

@app.route('/categoria/<int:id_categoria>/novo-pedido')
@nivel_acesso_required(2)
@login_required
def novo_pedido_pagina(id_categoria):
    """Serve a página de novo pedido, carregando APENAS os dados de domínio para os formulários."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute('SELECT * FROM Categorias WHERE id = %s', (id_categoria,))
        categoria = cursor.fetchone()
        if not categoria:
            return "Categoria não encontrada!", 404

        cursor.execute("SELECT nome FROM unidadesrequisitantes ORDER BY nome")
        unidades = [row['nome'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT descricao FROM locaisentrega ORDER BY descricao")
        locais = [row['descricao'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT nome FROM agentesresponsaveis ORDER BY nome")
        responsaveis = [row['nome'] for row in cursor.fetchall()]

        cursor.execute("SELECT info_orcamentaria FROM dotacao ORDER BY info_orcamentaria")
        dotacoes = [row['info_orcamentaria'] for row in cursor.fetchall()]

        return render_template('novo_pedido.html', 
                               categoria=categoria, 
                               termo_busca=request.args.get('busca', ''),
                               unidades=unidades,
                               locais=locais,
                               responsaveis=responsaveis,
                               dotacoes=dotacoes)
                               
    except psycopg2.Error as e:
        traceback.print_exc()
        return render_template('novo_pedido.html', categoria=None, 
                               unidades=[], locais=[], responsaveis=[], dotacoes=[],
                               erro=f"Erro no banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()

# --- Ferramentas de Importação e Geração de Documentos ---

@app.route('/importar-ui')
@nivel_acesso_required(2)
@login_required
def importar_ui():
    return render_template('importar.html')

@app.route('/contrato/<int:id_contrato>/importar-itens-ui')
@nivel_acesso_required(2)
@login_required
def importar_itens_ui(id_contrato):
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM Contratos WHERE id = %s', (id_contrato,))
        contrato = cursor.fetchone()
        if not contrato:
            return "Contrato não encontrado!", 404
        return render_template('importar_itens.html', contrato=contrato)
    except psycopg2.Error as e:
        return f"Erro no banco de dados: {e}", 500
    finally:
        if conexao:
            conexao.close()

@app.route('/pedido/<path:numero_aocs>/imprimir')
@nivel_acesso_required(2)
@login_required
def imprimir_aocs(numero_aocs):
    """Gera um PDF para a AOCS especificada, com dados das tabelas de domínio."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        sql = """
            SELECT 
                p.quantidade_pedida,
                ic.numero_item AS numero_item_contrato, ic.descricao, ic.marca, ic.unidade_medida, ic.valor_unitario,
                c.numero_contrato, c.fornecedor, c.cpf_cnpj, 
                inst.nome AS nome_instrumento,
                m.nome AS nome_modalidade,
                nm.numero_ano AS numero_modalidade_ano,
                pl.numero AS numero_processo,
                a.*,
                ur.nome AS nome_unidade,
                le.descricao AS desc_local_entrega,
                ar.nome AS nome_agente,
                d.info_orcamentaria AS info_dotacao
            FROM Pedidos p
            JOIN ItensContrato ic ON p.id_item_contrato = ic.id
            JOIN Contratos c ON ic.id_contrato = c.id
            JOIN AOCS a ON p.id_aocs = a.id
            LEFT JOIN instrumentocontratual inst ON c.id_instrumento_contratual = inst.id
            LEFT JOIN modalidade m ON c.id_modalidade = m.id
            LEFT JOIN numeromodalidade nm ON c.id_numero_modalidade = nm.id
            LEFT JOIN processoslicitatorios pl ON c.id_processo_licitatorio = pl.id
            LEFT JOIN unidadesrequisitantes ur ON a.id_unidade_requisitante = ur.id
            LEFT JOIN locaisentrega le ON a.id_local_entrega = le.id
            LEFT JOIN agentesresponsaveis ar ON a.id_agente_responsavel = ar.id
            LEFT JOIN dotacao d ON a.id_dotacao = d.id
            WHERE a.numero_aocs = %s
        """
        cursor.execute(sql, (numero_aocs,))
        itens_db = cursor.fetchall()

        if not itens_db:
            return "Pedido não encontrado!", 404

        total_geral = sum(float(item['quantidade_pedida']) * float(item['valor_unitario']) for item in itens_db)
        
        itens_para_template = []
        for item in itens_db:
            item_dict = dict(item)
            item_dict['subtotal'] = float(item_dict['quantidade_pedida']) * float(item_dict['valor_unitario'])
            itens_para_template.append(item_dict)
        
        primeiro_item = itens_para_template[0]
        instrumento = f"{primeiro_item['nome_instrumento']} nº {primeiro_item['numero_contrato']} - {primeiro_item['nome_modalidade']} nº {primeiro_item['numero_modalidade_ano']}"
        
        aocs_context = {
            "numero_aocs": primeiro_item['numero_aocs'],
            "unidade_requisitante": primeiro_item['nome_unidade'],
            "justificativa": primeiro_item['justificativa'],
            "instrumento_contratual": instrumento,
            "fornecedor": primeiro_item['fornecedor'],
            "cnpj": primeiro_item['cpf_cnpj'],
            "info_orcamentaria": primeiro_item['info_dotacao'],
            "local_entrega": primeiro_item['desc_local_entrega'],
            "local_data": f"Braúnas/MG, {primeiro_item['data_criacao'].strftime('%d de %B de %Y')}",
            "agente_responsavel": primeiro_item['nome_agente']
        }

        logo_url = url_for('static', filename='images/brasao.png', _external=True)

        html_renderizado = render_template(
            'aocs_template.html', 
            aocs=aocs_context,
            itens=itens_para_template, 
            total_geral=total_geral,
            logo_url=logo_url
        )

        pdf = HTML(string=html_renderizado, base_url=request.base_url).write_pdf()

        return Response(pdf, mimetype='application/pdf', headers={
            'Content-Disposition': f'inline; filename=AOCS_{numero_aocs.replace("/", "-")}.pdf'
        })

    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro ao gerar o PDF: {e}", 500
    finally:
        if conexao:
            conexao.close()

@app.route('/pedido/<path:numero_aocs>/imprimir-pendentes')
@nivel_acesso_required(2)
@login_required
def imprimir_pendentes_aocs(numero_aocs):
    """Gera um PDF contendo apenas os itens com entrega pendente de uma AOCS."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        sql = """
            SELECT 
                (p.quantidade_pedida - p.quantidade_entregue) AS saldo_pendente,
                p.quantidade_pedida, p.quantidade_entregue,
                ic.numero_item AS numero_item_contrato, ic.descricao, ic.marca, ic.unidade_medida, ic.valor_unitario,
                c.numero_contrato, c.fornecedor, c.cpf_cnpj, 
                inst.nome AS nome_instrumento, a.*, ur.nome AS nome_unidade,
                le.descricao AS desc_local_entrega, ar.nome AS nome_agente, d.info_orcamentaria AS info_dotacao
            FROM Pedidos p
            JOIN ItensContrato ic ON p.id_item_contrato = ic.id
            JOIN Contratos c ON ic.id_contrato = c.id
            JOIN AOCS a ON p.id_aocs = a.id
            LEFT JOIN instrumentocontratual inst ON c.id_instrumento_contratual = inst.id
            LEFT JOIN unidadesrequisitantes ur ON a.id_unidade_requisitante = ur.id
            LEFT JOIN locaisentrega le ON a.id_local_entrega = le.id
            LEFT JOIN agentesresponsaveis ar ON a.id_agente_responsavel = ar.id
            LEFT JOIN dotacao d ON a.id_dotacao = d.id
            WHERE a.numero_aocs = %s AND p.quantidade_entregue < p.quantidade_pedida
        """
        cursor.execute(sql, (numero_aocs,))
        itens_pendentes_db = cursor.fetchall()

        if not itens_pendentes_db:
            flash('Não há itens pendentes para esta AOCS.', 'success')
            return redirect(url_for('detalhe_pedido', numero_aocs=numero_aocs))

        total_geral_pendente = sum(float(item['saldo_pendente']) * float(item['valor_unitario']) for item in itens_pendentes_db)
        
        primeiro_item = dict(itens_pendentes_db[0])
        
        aocs_context = {
            "numero_aocs": primeiro_item['numero_aocs'],
            "numero_pedido": primeiro_item['numero_pedido'], 
            "unidade_requisitante": primeiro_item['nome_unidade'],
            "fornecedor": primeiro_item['fornecedor'],
            "cnpj": primeiro_item['cpf_cnpj'],
            "local_data": f"Braúnas/MG, {datetime.now().strftime('%d de %B de %Y')}"
        }

        logo_url = url_for('static', filename='images/brasao.png', _external=True)

        html_renderizado = render_template(
            'aocs_pendentes_template.html', 
            aocs=aocs_context,
            itens=itens_pendentes_db, 
            total_geral_pendente=total_geral_pendente,
            logo_url=logo_url
        )

        pdf = HTML(string=html_renderizado, base_url=request.base_url).write_pdf()

        return Response(pdf, mimetype='application/pdf', headers={
            'Content-Disposition': f'inline; filename=PENDENTES_AOCS_{numero_aocs.replace("/", "-")}.pdf'
        })

    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro ao gerar o PDF de pendentes: {e}", 500
    finally:
        if conexao: conexao.close()

@app.route('/pedido/<path:numero_aocs>/nova-ci', methods=['GET', 'POST'])
@nivel_acesso_required(2)
@login_required
def nova_ci_ui(numero_aocs):
    """
    Serve a página do formulário para criar uma nova CI (GET)
    e processa o salvamento da CI no banco de dados (POST).
    """
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        sql_aocs = """
            SELECT a.id, a.justificativa, c.fornecedor, c.cpf_cnpj,
                   a.id_unidade_requisitante, a.id_agente_responsavel, a.id_dotacao
            FROM AOCS a
            JOIN Pedidos p ON a.id = p.id_aocs JOIN ItensContrato ic ON p.id_item_contrato = ic.id
            JOIN Contratos c ON ic.id_contrato = c.id
            WHERE a.numero_aocs = %s GROUP BY a.id, c.fornecedor, c.cpf_cnpj
        """
        cursor.execute(sql_aocs, (numero_aocs,))
        aocs_data = cursor.fetchone()
        if not aocs_data: return "AOCS não encontrada!", 404

        if request.method == 'POST':
            form = request.form
            valor_nf = Decimal(form['valor_nota_fiscal'].replace('.', '').replace(',', '.'))

            sql_insert_ci = """
                INSERT INTO ci_pagamento (id_aocs, numero_ci, data_ci, numero_nota_fiscal, serie_nota_fiscal, 
                                          data_nota_fiscal, valor_nota_fiscal, id_dotacao_pagamento, 
                                          observacoes_pagamento, id_solicitante, id_secretaria)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert_ci, (
                aocs_data['id'], form['numero_ci'], form['data_ci'], form['numero_nota_fiscal'],
                form.get('serie_nota_fiscal'), form['data_nota_fiscal'], valor_nf,
                form['id_dotacao_pagamento'], form.get('observacoes_pagamento'),
                form['id_solicitante'], form['id_secretaria']
            ))
            conexao.commit()
            flash('CI de Pagamento criada com sucesso!', 'success')
            return redirect(url_for('detalhe_pedido', numero_aocs=numero_aocs))

        cursor.execute("SELECT id, info_orcamentaria FROM dotacao ORDER BY info_orcamentaria")
        dotacoes = cursor.fetchall()
        cursor.execute("SELECT id, nome FROM agentesresponsaveis ORDER BY nome")
        solicitantes = cursor.fetchall()
        cursor.execute("SELECT id, nome FROM unidadesrequisitantes ORDER BY nome")
        secretarias = cursor.fetchall()
        
        return render_template('nova_ci.html', aocs=aocs_data, dotacoes=dotacoes,
                               solicitantes=solicitantes, secretarias=secretarias,
                               numero_aocs=numero_aocs)

    except psycopg2.IntegrityError as e:
        if conexao: conexao.rollback()
        flash(f"Erro: O número da CI ou da Nota Fiscal já existe no banco de dados.", "error")
        return redirect(url_for('nova_ci_ui', numero_aocs=numero_aocs))
    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('detalhe_pedido', numero_aocs=numero_aocs))
    finally:
        if conexao: conexao.close()

def _gerar_pdf_ci(id_ci, cursor):
    """Função auxiliar que busca dados de uma CI e renderiza o PDF."""
    # SQL CORRIGIDO: Usa os JOINs corretos para chegar ao contrato
    sql_ci = """
        SELECT 
            ci.*, 
            a.justificativa, 
            c.fornecedor, 
            c.cpf_cnpj,
            sec.nome as nome_secretaria, 
            sol.nome as nome_solicitante
        FROM ci_pagamento ci
        JOIN aocs a ON ci.id_aocs = a.id
        -- Junta com pedidos para encontrar *um* item (precisamos do contrato)
        JOIN pedidos p ON a.id = p.id_aocs
        -- Junta com itenscontrato para chegar ao contrato
        JOIN itenscontrato ic ON p.id_item_contrato = ic.id
        -- Junta com contratos para pegar fornecedor/cnpj
        JOIN contratos c ON ic.id_contrato = c.id
        -- Junta com as tabelas de domínio da CI
        LEFT JOIN unidadesrequisitantes sec ON ci.id_secretaria = sec.id
        LEFT JOIN agentesresponsaveis sol ON ci.id_solicitante = sol.id
        WHERE ci.id = %s
        -- Limita a 1, pois só precisamos dos dados do fornecedor uma vez
        LIMIT 1 
    """
    cursor.execute(sql_ci, (id_ci,))
    ci_data = cursor.fetchone()
    if not ci_data: raise ValueError("CI não encontrada.")

    valor_nf = ci_data['valor_nota_fiscal']
    valor_por_extenso = num2words(valor_nf, lang='pt_BR', to='currency')

    logo_url = url_for('static', filename='images/brasao.png', _external=True)
    html = render_template(
        'ci_pagamento_template.html', # Usa o template que você atualizou
        numero_ci=ci_data['numero_ci'],
        data_ci=ci_data['data_ci'].strftime('%d/%m/%Y'),
        secretaria=ci_data['nome_secretaria'],
        valor_nf=valor_nf,
        valor_por_extenso=valor_por_extenso.capitalize(),
        numero_nf=ci_data['numero_nota_fiscal'],
        data_nf=ci_data['data_nota_fiscal'].strftime('%d/%m/%Y'),
        fornecedor=ci_data['fornecedor'],
        cnpj=ci_data['cpf_cnpj'],
        referencia=ci_data['justificativa'], # Usa a justificativa da AOCS
        observacoes=ci_data['observacoes_pagamento'],
        solicitante=ci_data['nome_solicitante'],
        logo_url=logo_url
    )
    return HTML(string=html, base_url=request.base_url).write_pdf()

@app.route('/ci/<int:id_ci>/imprimir')
@login_required
def imprimir_ci(id_ci):
    """Gera o PDF de uma CI de pagamento existente."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        pdf = _gerar_pdf_ci(id_ci, cursor)
        nome_arquivo = f"CI_Pagamento_{id_ci}.pdf"
        return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': f'inline; filename={nome_arquivo}'})
    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro ao gerar o PDF da CI: {e}", 500
    finally:
        if conexao: conexao.close()

@app.route('/ci/<int:id_ci>/editar', methods=['GET', 'POST'])
@nivel_acesso_required(2)
@login_required
def editar_ci_ui(id_ci):
    """Serve a página para editar uma CI (GET) e salva as alterações (POST)."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        if request.method == 'POST':
            form = request.form
            valor_nf = Decimal(form['valor_nota_fiscal'].replace('.', '').replace(',', '.'))
            sql_update = """
                UPDATE ci_pagamento SET
                    numero_ci=%s, data_ci=%s, numero_nota_fiscal=%s, serie_nota_fiscal=%s, data_nota_fiscal=%s,
                    valor_nota_fiscal=%s, id_dotacao_pagamento=%s, observacoes_pagamento=%s,
                    id_solicitante=%s, id_secretaria=%s
                WHERE id=%s
            """
            cursor.execute(sql_update, (
                form['numero_ci'], form['data_ci'], form['numero_nota_fiscal'], form.get('serie_nota_fiscal'),
                form['data_nota_fiscal'], valor_nf, form['id_dotacao_pagamento'],
                form.get('observacoes_pagamento'), form['id_solicitante'], form['id_secretaria'], id_ci
            ))
            conexao.commit()
            flash('CI de Pagamento atualizada com sucesso!', 'success')
            
            cursor.execute("SELECT a.numero_aocs FROM aocs a JOIN ci_pagamento ci ON a.id = ci.id_aocs WHERE ci.id = %s", (id_ci,))
            numero_aocs = cursor.fetchone()['numero_aocs']
            return redirect(url_for('detalhe_pedido', numero_aocs=numero_aocs))

        cursor.execute("SELECT * FROM ci_pagamento WHERE id = %s", (id_ci,))
        ci_data = cursor.fetchone()
        if not ci_data: return "CI não encontrada!", 404
        
        cursor.execute("SELECT numero_aocs FROM aocs WHERE id = %s", (ci_data['id_aocs'],))
        aocs = cursor.fetchone() # Armazena como 'aocs'
        if not aocs:
            raise ValueError("AOCS associada à CI não encontrada.")
        cursor.execute("SELECT id, info_orcamentaria FROM dotacao ORDER BY info_orcamentaria")
        dotacoes = cursor.fetchall()
        cursor.execute("SELECT id, nome FROM agentesresponsaveis ORDER BY nome")
        solicitantes = cursor.fetchall()
        cursor.execute("SELECT id, nome FROM unidadesrequisitantes ORDER BY nome")
        secretarias = cursor.fetchall()

        return render_template('editar_ci.html', ci=ci_data, dotacoes=dotacoes,
                               solicitantes=solicitantes, secretarias=secretarias,
                               aocs=aocs)
    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('home')) 
    finally:
        if conexao: conexao.close()

@app.route('/gerenciar-tabelas')
@nivel_acesso_required(2)
@login_required
def gerenciar_tabelas_ui():
    """Serve a página de gerenciamento das tabelas de domínio do sistema."""
    return render_template('gerenciar_tabelas.html', tabelas=TABELAS_GERENCIAVEIS)

# --- 3.5. Rotas de Serviço e Arquivos ---

@app.route('/uploads/<path:filename>')
@nivel_acesso_required(2)
@login_required
def uploaded_file(filename):
    """Serve um arquivo da pasta de uploads, agora com suporte a subdiretórios."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def _salvar_e_registrar_anexo(arquivo, tipo_documento_final, tipo_entidade, id_entidade, identificador_entidade, cursor):
    """
    Função auxiliar interna que centraliza a lógica de salvar um anexo no disco
    e registrar no banco de dados. Retorna True em caso de sucesso.
    Lança uma exceção (raise) em caso de erro para ser tratada pela rota que a chamou.
    """

    subpasta = tipo_entidade if tipo_entidade == 'aocs' else str(id_entidade)
    caminho_completo_pasta = os.path.join(app.config['UPLOAD_FOLDER'], subpasta)
    if tipo_entidade == 'aocs':
        caminho_completo_pasta = os.path.join(app.config['UPLOAD_FOLDER'], 'aocs', str(id_entidade))
    
    os.makedirs(caminho_completo_pasta, exist_ok=True)


    nome_original = secure_filename(arquivo.filename)
    _, extensao = os.path.splitext(nome_original)
    tipo_doc_limpo = _limpar_e_truncar(tipo_documento_final, 15)
    identificador_limpo = _limpar_e_truncar(identificador_entidade, 10)
    timestamp = int(datetime.now().timestamp())
    nome_arquivo_final = f"{timestamp}_{tipo_doc_limpo}_{identificador_limpo}{extensao}"
    
    caminho_completo_arquivo = os.path.join(caminho_completo_pasta, nome_arquivo_final)
    arquivo.save(caminho_completo_arquivo)

    nome_seguro_db = os.path.join(subpasta, nome_arquivo_final).replace("\\", "/")
    if tipo_entidade == 'aocs':
        nome_seguro_db = os.path.join('aocs', str(id_entidade), nome_arquivo_final).replace("\\", "/")

    sql_insert = """
        INSERT INTO Anexos (id_entidade, tipo_entidade, nome_original, nome_seguro, data_upload, tipo_documento) 
        VALUES (%s, %s, %s, %s, CURRENT_DATE, %s)
    """
    cursor.execute(sql_insert, (id_entidade, tipo_entidade, nome_original, nome_seguro_db, tipo_documento_final))
    return True

@app.route('/contrato/<int:id_contrato>/upload', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def upload_anexo(id_contrato):
    """Rota para upload de anexos de CONTRATOS."""
    redirect_url = url_for('detalhe_contrato', id_contrato=id_contrato)
    
    if 'anexo' not in request.files or not request.files['anexo'].filename:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(redirect_url)
    
    tipo_documento_selecionado = request.form.get('tipo_documento_select')
    tipo_documento_novo = request.form.get('tipo_documento_novo', '').strip()
    
    if tipo_documento_selecionado == 'NOVO' and not tipo_documento_novo:
        flash('Você selecionou "NOVO TIPO", mas não digitou um nome.', 'error')
        return redirect(redirect_url)
    
    tipo_documento_final = tipo_documento_novo if tipo_documento_selecionado == 'NOVO' else tipo_documento_selecionado
    if not tipo_documento_final:
        flash('Por favor, selecione o tipo do documento.', 'error')
        return redirect(redirect_url)

    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        if tipo_documento_selecionado == 'NOVO':
            cursor.execute("INSERT INTO tipos_documento (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", (tipo_documento_final,))
        
        cursor.execute("SELECT numero_contrato FROM Contratos WHERE id = %s", (id_contrato,))
        dados_contrato = cursor.fetchone()
        if not dados_contrato:
            raise ValueError("Contrato não encontrado.")

        _salvar_e_registrar_anexo(
            arquivo=request.files['anexo'],
            tipo_documento_final=tipo_documento_final,
            tipo_entidade='contrato',
            id_entidade=id_contrato,
            identificador_entidade=dados_contrato['numero_contrato'],
            cursor=cursor
        )
        
        conexao.commit()
        flash('Anexo enviado com sucesso!', 'success')
    
    except (psycopg2.Error, OSError, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'error')
    
    finally:
        if conexao: conexao.close()
            
    return redirect(redirect_url)

@app.route('/aocs/<path:numero_aocs>/upload', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def upload_anexo_aocs(numero_aocs):
    """Rota para upload de anexos de AOCS (Pedidos)."""
    
    # --- 1. Validação de Entrada ---
    if 'anexo' not in request.files or not request.files['anexo'].filename:
        # Retorna JSON de erro, status 400 (Bad Request)
        return jsonify({'erro': 'Nenhum arquivo selecionado.'}), 400

    tipo_documento_selecionado = request.form.get('tipo_documento_select')
    tipo_documento_novo = request.form.get('tipo_documento_novo', '').strip()
    
    if tipo_documento_selecionado == 'NOVO' and not tipo_documento_novo:
        # Retorna JSON de erro
        return jsonify({'erro': 'Você selecionou "NOVO TIPO", mas não digitou um nome.'}), 400
        
    tipo_documento_final = tipo_documento_novo if tipo_documento_selecionado == 'NOVO' else tipo_documento_selecionado
    if not tipo_documento_final:
        # Retorna JSON de erro
        return jsonify({'erro': 'Por favor, selecione o tipo do documento.'}), 400

    # --- 2. Processamento (Banco e Disco) ---
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        if tipo_documento_selecionado == 'NOVO':
            cursor.execute("INSERT INTO tipos_documento (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", (tipo_documento_final,))

        cursor.execute("SELECT id FROM aocs WHERE numero_aocs = %s", (numero_aocs,))
        dados_aocs = cursor.fetchone()
        if not dados_aocs:
            # Lança um erro para ser pego pelo except
            raise ValueError("AOCS não encontrada.")
        
        _salvar_e_registrar_anexo(
            arquivo=request.files['anexo'],
            tipo_documento_final=tipo_documento_final,
            tipo_entidade='aocs',
            id_entidade=dados_aocs['id'],
            identificador_entidade=numero_aocs,
            cursor=cursor
        )
        
        conexao.commit()
        # Retorna JSON de sucesso, status 201 (Created)
        return jsonify({'mensagem': 'Anexo da AOCS enviado com sucesso!'}), 201
    
    except (psycopg2.Error, OSError, ValueError, Exception) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        # Retorna JSON de erro, status 500 (Internal Server Error)
        return jsonify({'erro': f'Ocorreu um erro ao processar o arquivo: {e}'}), 500
    
    finally:
        if conexao: conexao.close()
            
    # O redirect final foi removido. A função agora SÓ retorna JSON.

@app.route('/consultas')
@nivel_acesso_required(3)
@login_required
def consultas_ui():
    """Serve a página de consultas avançadas, pré-carregando as opções de filtro."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute("SELECT id, numero FROM processoslicitatorios ORDER BY numero")
        processos = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT id, nome FROM unidadesrequisitantes ORDER BY nome")
        unidades = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT id, descricao as texto FROM locaisentrega ORDER BY descricao")
        locais = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT id, info_orcamentaria as texto FROM dotacao ORDER BY info_orcamentaria")
        dotacoes = [dict(row) for row in cursor.fetchall()]

        return render_template('consultas.html', 
                               processos=processos, 
                               unidades=unidades,
                               locais=locais,         
                               dotacoes=dotacoes,       
                               entidades_pesquisaveis=ENTIDADES_PESQUISAVEIS)

    except Exception as e:
        traceback.print_exc()
        return render_template('consultas.html', entidades_pesquisaveis={}, erro=str(e))
    finally:
        if conexao:
            conexao.close()

@app.route('/relatorios')
@nivel_acesso_required(3)
@login_required
def relatorios_ui():
    """Serve o hub principal para a geração de relatórios."""
    try:
        return render_template('relatorios.html', relatorios=RELATORIOS_DISPONIVEIS)
    except Exception as e:
        traceback.print_exc()
        return render_template('relatorios.html', erro=str(e))

@app.route('/admin/usuarios')
@nivel_acesso_required(1)
@login_required
def gerenciar_usuarios_ui():
    """Serve a página de gerenciamento de usuários, acessível apenas por Admins."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, username, nivel_acesso, ativo FROM usuarios ORDER BY username")
        usuarios = cursor.fetchall()
        
        return render_template('gerenciar_usuarios.html', usuarios=usuarios)
    except Exception as e:
        traceback.print_exc()
        return render_template('gerenciar_usuarios.html', usuarios=[], erro=str(e))
    finally:
        if conexao:
            conexao.close()

# --- 4. Rotas de API (JSON) ---

TABELAS_GERENCIAVEIS = {
    'instrumento-contratual': {'tabela': 'instrumentocontratual', 'coluna': 'nome', 'fk_tabela': 'contratos', 'fk_coluna': 'id_instrumento_contratual'},
    'modalidade': {'tabela': 'modalidade', 'coluna': 'nome', 'fk_tabela': 'contratos', 'fk_coluna': 'id_modalidade'},
    'numero-modalidade': {'tabela': 'numeromodalidade', 'coluna': 'numero_ano', 'fk_tabela': 'contratos', 'fk_coluna': 'id_numero_modalidade'},
    'processo-licitatorio': {'tabela': 'processoslicitatorios', 'coluna': 'numero', 'fk_tabela': 'contratos', 'fk_coluna': 'id_processo_licitatorio'},
    'unidade-requisitante': {'tabela': 'unidadesrequisitantes', 'coluna': 'nome', 'fk_tabela': 'aocs', 'fk_coluna': 'id_unidade_requisitante'},
    'local-entrega': {'tabela': 'locaisentrega', 'coluna': 'descricao', 'fk_tabela': 'aocs', 'fk_coluna': 'id_local_entrega'},
    'agente-responsavel': {'tabela': 'agentesresponsaveis', 'coluna': 'nome', 'fk_tabela': 'aocs', 'fk_coluna': 'id_agente_responsavel'},
    'dotacao': {'tabela': 'dotacao', 'coluna': 'info_orcamentaria', 'fk_tabela': 'aocs', 'fk_coluna': 'id_dotacao'},
    'tipo-documento': {'tabela': 'tipos_documento', 'coluna': 'nome', 'fk_tabela': 'anexos', 'fk_coluna': 'tipo_documento'}
}

ENTIDADES_PESQUISAVEIS = {
    'processo_licitatorio': {
        'label': 'Contratos por Processo Licitatório',
        'tabela_principal': 'processoslicitatorios',
        'coluna_texto': 'numero',
        'vinculos': [
            {
                'titulo_resultado': 'Contratos Vinculados',
                'tabela_alvo': 'Contratos',
                'sql': """
                    SELECT c.id, c.numero_contrato, c.fornecedor, c.ativo, cat.nome AS nome_categoria
                    FROM Contratos c JOIN Categorias cat ON c.id_categoria = cat.id
                    WHERE c.id_processo_licitatorio = %s ORDER BY c.numero_contrato
                """
            }
        ]
    },
    'unidade_requisitante': {
        'label': 'AOCS por Unidade Requisitante',
        'tabela_principal': 'unidadesrequisitantes',
        'coluna_texto': 'nome',
        'vinculos': [
            {
                'titulo_resultado': 'AOCS Vinculadas',
                'tabela_alvo': 'AOCS',
                'sql': """
                    SELECT
                        a.numero_aocs,
                        TO_CHAR(a.data_criacao, 'DD/MM/YYYY') AS data_criacao,
                        c.fornecedor,
                        CASE 
                            WHEN SUM(CASE WHEN p.status_entrega = 'Entregue' THEN 1 ELSE 0 END) = COUNT(p.id) THEN 'Entregue'
                            WHEN SUM(CASE WHEN p.status_entrega = 'Pendente' THEN 1 ELSE 0 END) = COUNT(p.id) THEN 'Pendente'
                            ELSE 'Entrega Parcial'
                        END as status_entrega
                    FROM AOCS a
                    JOIN Pedidos p ON a.id = p.id_aocs
                    JOIN ItensContrato ic ON p.id_item_contrato = ic.id
                    JOIN Contratos c ON ic.id_contrato = c.id
                    WHERE a.id_unidade_requisitante = %s
                    GROUP BY a.id, c.fornecedor ORDER BY a.data_criacao DESC
                """
            }
        ]
    },
    'local_entrega': {
        'label': 'AOCS por Local de Entrega',
        'tabela_principal': 'locaisentrega',
        'coluna_texto': 'descricao',
        'vinculos': [
            {
                'titulo_resultado': 'AOCS Vinculadas',
                'tabela_alvo': 'AOCS',
                'sql': """
                    SELECT
                        a.numero_aocs,
                        TO_CHAR(a.data_criacao, 'DD/MM/YYYY') AS data_criacao,
                        c.fornecedor,
                        CASE 
                            WHEN SUM(CASE WHEN p.status_entrega = 'Entregue' THEN 1 ELSE 0 END) = COUNT(p.id) THEN 'Entregue'
                            WHEN SUM(CASE WHEN p.status_entrega = 'Pendente' THEN 1 ELSE 0 END) = COUNT(p.id) THEN 'Pendente'
                            ELSE 'Entrega Parcial'
                        END as status_entrega
                    FROM AOCS a
                    JOIN Pedidos p ON a.id = p.id_aocs
                    JOIN ItensContrato ic ON p.id_item_contrato = ic.id
                    JOIN Contratos c ON ic.id_contrato = c.id
                    WHERE a.id_local_entrega = %s
                    GROUP BY a.id, c.fornecedor ORDER BY a.data_criacao DESC
                """
            }
        ]
    },
    'dotacao': {
        'label': 'AOCS por Dotação Orçamentária',
        'tabela_principal': 'dotacao',
        'coluna_texto': 'info_orcamentaria',
        'vinculos': [
            {
                'titulo_resultado': 'AOCS Vinculadas',
                'tabela_alvo': 'AOCS',
                'sql': """
                    SELECT
                        a.numero_aocs,
                        TO_CHAR(a.data_criacao, 'DD/MM/YYYY') AS data_criacao,
                        c.fornecedor,
                        CASE 
                            WHEN SUM(CASE WHEN p.status_entrega = 'Entregue' THEN 1 ELSE 0 END) = COUNT(p.id) THEN 'Entregue'
                            WHEN SUM(CASE WHEN p.status_entrega = 'Pendente' THEN 1 ELSE 0 END) = COUNT(p.id) THEN 'Pendente'
                            ELSE 'Entrega Parcial'
                        END as status_entrega
                    FROM AOCS a
                    JOIN Pedidos p ON a.id = p.id_aocs
                    JOIN ItensContrato ic ON p.id_item_contrato = ic.id
                    JOIN Contratos c ON ic.id_contrato = c.id
                    WHERE a.id_dotacao = %s
                    GROUP BY a.id, c.fornecedor ORDER BY a.data_criacao DESC
                """
            }
        ]
    }
}

RELATORIOS_DISPONIVEIS = {
    'lista_fornecedores': {
        'titulo': 'Lista de Fornecedores',
        'descricao': 'Gera uma lista de todos os fornecedores únicos com seus respectivos CNPJs.',
        'sql': """
            SELECT DISTINCT fornecedor, cpf_cnpj 
            FROM Contratos
        """,
        'colunas': [
            {'key': 'fornecedor', 'header': 'Fornecedor'},
            {'key': 'cpf_cnpj', 'header': 'CPF/CNPJ'}
        ],
        'ordenacao_opcoes': {
            'fornecedor_asc': {'label': 'Fornecedor (A-Z)', 'sql': 'ORDER BY fornecedor ASC'},
            'fornecedor_desc': {'label': 'Fornecedor (Z-A)', 'sql': 'ORDER BY fornecedor DESC'}
        }
    },
    'lista_contratos': {
        'titulo': 'Lista de Contratos Ativos',
        'descricao': 'Relação completa de todos os contratos ativos no sistema, com suas categorias e datas de vencimento.',
        'sql': """
            SELECT 
                c.numero_contrato, 
                c.fornecedor, 
                cat.nome AS nome_categoria, 
                TO_CHAR(c.data_fim, 'DD/MM/YYYY') AS data_fim_br,
                c.data_fim
            FROM Contratos c
            JOIN Categorias cat ON c.id_categoria = cat.id
            WHERE c.ativo = TRUE
        """,
        'colunas': [
            {'key': 'numero_contrato', 'header': 'Número'},
            {'key': 'fornecedor', 'header': 'Fornecedor'},
            {'key': 'nome_categoria', 'header': 'Categoria'},
            {'key': 'data_fim_br', 'header': 'Data de Vencimento'}
        ],
        'ordenacao_opcoes': {
            'data_fim_asc': {'label': 'Vencimento (Mais Próximo)', 'sql': 'ORDER BY c.data_fim ASC'},
            'data_fim_desc': {'label': 'Vencimento (Mais Distante)', 'sql': 'ORDER BY c.data_fim DESC'},
            'fornecedor_asc': {'label': 'Fornecedor (A-Z)', 'sql': 'ORDER BY c.fornecedor ASC'}
        }
    }
}

# --- API: Gestão de Categorias ---
@app.route('/api/categorias', methods=['GET', 'POST'])
@nivel_acesso_required(2)
@login_required
def api_gerenciar_categorias():
    """API para listar (GET) ou criar (POST) categorias."""
    conexao = None
    try:
        if request.method == 'GET':
            conexao = get_db_connection()
            cursor = conexao.cursor()
            
            mostrar_inativos = request.args.get('mostrar_inativos') == 'true'
            where_clause = "" if mostrar_inativos else "WHERE ativo = TRUE"
            
            sql = f'SELECT * FROM Categorias {where_clause} ORDER BY nome'
            cursor.execute(sql)
            
            return jsonify([dict(cat) for cat in cursor.fetchall()])

        elif request.method == 'POST':
            dados = request.get_json()
            if not dados or not dados.get('nome', '').strip():
                return jsonify({'erro': 'O nome da categoria é obrigatório.'}), 400
            
            conexao = get_db_connection()
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO Categorias (nome) VALUES (%s) RETURNING id", (dados['nome'].strip(),))
            id_nova_categoria = cursor.fetchone()['id']
            conexao.commit()
            
            return jsonify({'mensagem': 'Categoria criada com sucesso!', 'id_categoria': id_nova_categoria}), 201

    except psycopg2.IntegrityError:
        if conexao: conexao.rollback()
        return jsonify({'erro': 'Esta categoria já existe.'}), 409
    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/categorias/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@nivel_acesso_required(2)
@login_required
def api_gerenciar_categoria_individual(id):
    """API para buscar (GET), atualizar (PUT) ou excluir (DELETE) uma categoria."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        if request.method == 'GET':
            cursor.execute('SELECT * FROM Categorias WHERE id = %s', (id,))
            categoria = cursor.fetchone()
            if not categoria: 
                return jsonify({'erro': 'Categoria não encontrada'}), 404
            return jsonify(dict(categoria))

        elif request.method == 'PUT':
            dados = request.get_json()
            if not dados or not dados.get('nome', '').strip():
                return jsonify({'erro': 'O nome da categoria é obrigatório.'}), 400
            
            cursor.execute('UPDATE Categorias SET nome = %s WHERE id = %s', (dados['nome'].strip(), id))
            conexao.commit()
            return jsonify({'mensagem': 'Categoria atualizada com sucesso!'})

        elif request.method == 'DELETE':
            cursor.execute('SELECT COUNT(id) FROM Contratos WHERE id_categoria = %s', (id,))
            if cursor.fetchone()[0] > 0:
                return jsonify({'erro': 'Não é possível excluir. Categoria vinculada a contratos.'}), 409
            
            cursor.execute('DELETE FROM Categorias WHERE id = %s', (id,))
            conexao.commit()
            return jsonify({'mensagem': 'Categoria excluída com sucesso!'})

    except psycopg2.IntegrityError:
        if conexao: conexao.rollback()
        return jsonify({'erro': 'Já existe uma categoria com este nome.'}), 409
    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/categorias/<int:id>/status', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def toggle_categoria_status(id):
    """Inverte o status 'ativo' de uma categoria com uma única query."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute('UPDATE Categorias SET ativo = NOT ativo WHERE id = %s RETURNING ativo', (id,))
        
        resultado = cursor.fetchone()
        if not resultado:
            return jsonify({"erro": "Categoria não encontrada."}), 404
            
        conexao.commit()
        return jsonify({"mensagem": "Status da categoria alterado com sucesso!"})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/categorias/<int:id_categoria>/itens')
@nivel_acesso_required(2)
@login_required
def api_itens_por_categoria(id_categoria):
    """API que retorna uma lista PAGINADA e ORDENADA de itens de uma categoria em JSON."""
    pagina_atual = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')
    sort_by = request.args.get('sort_by', 'descricao')
    order = request.args.get('order', 'asc')

    _, itens, total_paginas, _, erro = _get_itens_por_categoria_com_saldo(
        id_categoria, termo_busca, page=pagina_atual, sort_by=sort_by, order=order
    )
    
    if erro:
        return jsonify({"erro": erro}), 500
        
    return jsonify({
        'itens': [dict(item) for item in itens],
        'total_paginas': total_paginas,
        'pagina_atual': pagina_atual
    })

# --- API: Gestão de Contratos e Itens ---
@app.route('/api/contratos', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def cadastrar_contrato():
    """API para cadastrar um novo contrato usando a estrutura de dados normalizada."""
    dados = request.get_json()
    campos_obrigatorios = ['id_categoria', 'numero_contrato', 'fornecedor', 'cpf_cnpj', 
                           'numero_processo', 'modalidade', 'numero_modalidade', 
                           'data_inicio', 'data_fim', 'tipo_contrato']
    if not all(k in dados for k in campos_obrigatorios):
        return jsonify({'erro': 'Dados obrigatórios incompletos.'}), 400
    
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;") 

        id_instrumento = _get_or_create_id(cursor, 'instrumentocontratual', 'nome', dados.get('tipo_contrato'))
        id_modalidade = _get_or_create_id(cursor, 'modalidade', 'nome', dados.get('modalidade'))
        id_num_modalidade = _get_or_create_id(cursor, 'numeromodalidade', 'numero_ano', dados.get('numero_modalidade'))
        id_processo = _get_or_create_id(cursor, 'processoslicitatorios', 'numero', dados.get('numero_processo'))
    
        sql = """
            INSERT INTO Contratos (
                id_categoria, numero_contrato, fornecedor, cpf_cnpj, 
                data_inicio, data_fim, data_criacao, email, telefone,
                id_instrumento_contratual, id_modalidade, id_numero_modalidade, id_processo_licitatorio
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            dados.get('id_categoria'), dados.get('numero_contrato'), dados.get('fornecedor'), 
            dados.get('cpf_cnpj'), dados.get('data_inicio'), dados.get('data_fim'), 
            date.today().strftime('%Y-%m-%d'), dados.get('email'), dados.get('telefone'),
            id_instrumento, id_modalidade, id_num_modalidade, id_processo
        ))
    
        conexao.commit()
        return jsonify({'mensagem': 'Contrato criado com sucesso!'}), 201
    
    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/contratos/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@nivel_acesso_required(2)
@login_required
def api_gerenciar_contrato_individual(id):
    """API para buscar (GET), atualizar (PUT) ou excluir (DELETE) um contrato."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        if request.method == 'GET':
            sql_get = """
                SELECT c.*, inst.nome as tipo_contrato, m.nome as modalidade, 
                       nm.numero_ano as numero_modalidade, pl.numero as numero_processo
                FROM Contratos c
                LEFT JOIN instrumentocontratual inst ON c.id_instrumento_contratual = inst.id
                LEFT JOIN modalidade m ON c.id_modalidade = m.id
                LEFT JOIN numeromodalidade nm ON c.id_numero_modalidade = nm.id
                LEFT JOIN processoslicitatorios pl ON c.id_processo_licitatorio = pl.id
                WHERE c.id = %s
            """
            cursor.execute(sql_get, (id,))
            contrato = cursor.fetchone()
            if not contrato: 
                return jsonify({'erro': 'Contrato não encontrado'}), 404
            return jsonify(dict(contrato))

        elif request.method == 'PUT':
            dados = request.get_json()
            cursor.execute("BEGIN;")

            id_instrumento = _get_or_create_id(cursor, 'instrumentocontratual', 'nome', dados.get('tipo_contrato'))
            id_modalidade = _get_or_create_id(cursor, 'modalidade', 'nome', dados.get('modalidade'))
            id_num_modalidade = _get_or_create_id(cursor, 'numeromodalidade', 'numero_ano', dados.get('numero_modalidade'))
            id_processo = _get_or_create_id(cursor, 'processoslicitatorios', 'numero', dados.get('numero_processo'))
            
            sql_update = """
                UPDATE Contratos SET 
                    id_categoria=%s, numero_contrato=%s, fornecedor=%s, cpf_cnpj=%s, 
                    data_inicio=%s, data_fim=%s, email=%s, telefone=%s,
                    id_instrumento_contratual=%s, id_modalidade=%s, 
                    id_numero_modalidade=%s, id_processo_licitatorio=%s
                WHERE id=%s
            """
            cursor.execute(sql_update, (
                dados.get('id_categoria'), dados.get('numero_contrato'), dados.get('fornecedor'), 
                dados.get('cpf_cnpj'), dados.get('data_inicio'), dados.get('data_fim'),
                dados.get('email'), dados.get('telefone'),
                id_instrumento, id_modalidade, id_num_modalidade, id_processo,
                id
            ))
            conexao.commit()
            return jsonify({'mensagem': 'Contrato atualizado com sucesso!'})

        elif request.method == 'DELETE':
            cursor.execute('SELECT COUNT(id) FROM ItensContrato WHERE id_contrato = %s', (id,))
            if cursor.fetchone()[0] > 0:
                return jsonify({'erro': 'Não é possível excluir. Contrato possui itens.'}), 409
            
            cursor.execute('DELETE FROM Contratos WHERE id = %s', (id,))
            conexao.commit()
            return jsonify({'mensagem': 'Contrato excluído com sucesso!'})

    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/contratos/<int:id>/status', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def toggle_contrato_status(id):
    """Inverte o status 'ativo' de um contrato com uma única query."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute('UPDATE Contratos SET ativo = NOT ativo WHERE id = %s RETURNING id', (id,))
        
        resultado = cursor.fetchone()
        if not resultado:
            return jsonify({"erro": "Contrato não encontrado."}), 404
            
        conexao.commit()
        return jsonify({"mensagem": "Status do contrato alterado com sucesso!"})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/contratos/<int:id_contrato>/itens', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def cadastrar_item_contrato(id_contrato):
    """Cadastra um novo item em um contrato com validação de tipos de dados."""
    dados = request.get_json()
    conexao = None
    try:
        campos_obrigatorios = ['numero_item', 'descricao', 'unidade_medida', 'quantidade', 'valor_unitario']
        if not all(dados.get(k) for k in campos_obrigatorios):
            return jsonify({'erro': 'Dados obrigatórios incompletos.'}), 400

        try:
            quantidade = float(str(dados['quantidade']).replace(',', '.'))
            valor_unitario = float(str(dados['valor_unitario']).replace(',', '.'))
        except (ValueError, TypeError):
            return jsonify({'erro': 'Os campos Quantidade e Valor Unitário devem ser números válidos.'}), 400

        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        sql = """
            INSERT INTO ItensContrato (id_contrato, numero_item, descricao, unidade_medida, 
                                     quantidade, valor_unitario, marca) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            id_contrato, dados['numero_item'], dados['descricao'], 
            dados['unidade_medida'], quantidade, valor_unitario, dados.get('marca')
        ))
        
        conexao.commit()
        return jsonify({'mensagem': 'Item cadastrado com sucesso!'}), 201

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/itens/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@nivel_acesso_required(2)
@login_required
def api_gerenciar_item_individual(id):
    """API para buscar (GET), atualizar (PUT) ou excluir (DELETE) um item."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        if request.method == 'GET':
            cursor.execute('SELECT * FROM ItensContrato WHERE id = %s', (id,))
            item = cursor.fetchone()
            if not item: 
                return jsonify({'erro': 'Item não encontrado'}), 404
            return jsonify(dict(item))

        elif request.method == 'PUT':
            dados = request.get_json()
            
            campos_obrigatorios = ['numero_item', 'descricao', 'unidade_medida', 'quantidade', 'valor_unitario']
            if not all(dados.get(k) for k in campos_obrigatorios):
                return jsonify({'erro': 'Dados obrigatórios incompletos.'}), 400

            try:
                quantidade = float(str(dados['quantidade']).replace(',', '.'))
                valor_unitario = float(str(dados['valor_unitario']).replace(',', '.'))
            except (ValueError, TypeError):
                return jsonify({'erro': 'Os campos Quantidade e Valor Unitário devem ser números válidos.'}), 400
                
            sql = """
                UPDATE ItensContrato SET numero_item=%s, descricao=%s, unidade_medida=%s, 
                quantidade=%s, valor_unitario=%s, marca=%s WHERE id=%s
            """
            cursor.execute(sql, (
                dados['numero_item'], dados['descricao'], dados['unidade_medida'], 
                quantidade, valor_unitario, dados.get('marca'), id
            ))
            conexao.commit()
            return jsonify({'mensagem': 'Item atualizado com sucesso!'})

        elif request.method == 'DELETE':
            cursor.execute('SELECT COUNT(id) FROM Pedidos WHERE id_item_contrato = %s', (id,))
            if cursor.fetchone()[0] > 0:
                return jsonify({'erro': 'Não é possível excluir. Item possui pedidos.'}), 409
            
            cursor.execute('DELETE FROM ItensContrato WHERE id = %s', (id,))
            conexao.commit()
            return jsonify({'mensagem': 'Item excluído com sucesso!'})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/itens/<int:id>/status', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def toggle_item_status(id):
    """Inverte o status 'ativo' de um item com uma única query."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute('UPDATE ItensContrato SET ativo = NOT ativo WHERE id = %s RETURNING id', (id,))
        
        resultado = cursor.fetchone()
        if not resultado:
            return jsonify({"erro": "Item não encontrado."}), 404
            
        conexao.commit()
        return jsonify({"mensagem": "Status do item alterado com sucesso!"})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

# --- API: Gestão de AOCS ---
@app.route('/api/aocs', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def api_criar_aocs_completa():
    """Cria uma AOCS completa usando a estrutura de dados normalizada."""
    dados_requisicao = request.get_json()
    conexao = None
    try:
        aocs_dados = dados_requisicao.get('aocs_dados')
        itens_pedido = dados_requisicao.get('itens_pedido')

        if not aocs_dados or not itens_pedido:
            return jsonify({'erro': 'Estrutura de dados inválida. Faltam aocs_dados ou itens_pedido.'}), 400

        campos_obrigatorios_aocs = ['numero_aocs', 'unidade_requisitante', 'justificativa', 
                                    'info_orcamentaria', 'local_entrega', 'agente_responsavel']
        if not all(aocs_dados.get(k) for k in campos_obrigatorios_aocs):
            return jsonify({'erro': 'Dados obrigatórios da AOCS incompletos.'}), 400

        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        id_unidade = _get_or_create_id(cursor, 'unidadesrequisitantes', 'nome', aocs_dados.get('unidade_requisitante'))
        id_local = _get_or_create_id(cursor, 'locaisentrega', 'descricao', aocs_dados.get('local_entrega'))
        id_responsavel = _get_or_create_id(cursor, 'agentesresponsaveis', 'nome', aocs_dados.get('agente_responsavel'))
        id_dotacao = _get_or_create_id(cursor, 'dotacao', 'info_orcamentaria', aocs_dados.get('info_orcamentaria'))

        sql_aocs = """
            INSERT INTO AOCS (
                numero_aocs, justificativa, local_data, 
                id_unidade_requisitante, id_local_entrega, id_agente_responsavel, id_dotacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        cursor.execute(sql_aocs, (
            aocs_dados.get('numero_aocs'), aocs_dados.get('justificativa'),
            aocs_dados.get('local_data'), id_unidade, id_local, id_responsavel, id_dotacao
        ))
        id_aocs = cursor.fetchone()['id']
        
        for item in itens_pedido:
            sql_pedido = "INSERT INTO Pedidos (id_item_contrato, id_aocs, quantidade_pedida) VALUES (%s, %s, %s);"
            cursor.execute(sql_pedido, (item.get('id'), id_aocs, item.get('quantidade')))
        
        conexao.commit()
        return jsonify({'mensagem': f'AOCS {aocs_dados.get("numero_aocs")} criada com sucesso!', 'id_aocs': id_aocs}), 201
    
    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()
        
# --- API: Ferramentas de Importação ---
@app.route('/api/importar/contratos/preview', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def importar_contratos_preview():
    if 'arquivo_excel' not in request.files: return jsonify({"erro": "Nenhum arquivo enviado."}), 400
    arquivo = request.files['arquivo_excel']
    if not arquivo.filename: return jsonify({"erro": "Nenhum arquivo selecionado."}), 400
    if not arquivo.filename.endswith('.xlsx'): return jsonify({"erro": "Formato inválido. Envie um .xlsx"}), 400
    try:
        df = pd.read_excel(arquivo)
        colunas_obrigatorias = ['id_categoria', 'numero_contrato', 'fornecedor', 'cpf_cnpj', 'numero_processo', 'modalidade', 'numero_modalidade', 'data_inicio', 'data_fim']
        if not all(c in df.columns for c in colunas_obrigatorias):
            return jsonify({"erro": f"Colunas obrigatórias faltantes: {list(set(colunas_obrigatorias) - set(df.columns))}"}), 400
        colunas_opcionais = ['tipo_contrato', 'email', 'telefone']
        for col in colunas_opcionais:
            if col not in df.columns: df[col] = None
        df = df.where(pd.notnull(df), None)
        return df.to_json(orient='records', date_format='iso')
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar o arquivo: {e}"}), 500

@app.route('/api/importar/contratos/salvar', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def importar_contratos_salvar():
    dados = request.get_json()
    if not dados: return jsonify({"erro": "Nenhum dado recebido."}), 400
    
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;") 

        hoje = date.today().strftime('%Y-%m-%d')
        
        for contrato_excel in dados:
            id_categoria = contrato_excel.get('id_categoria')
            cursor.execute('SELECT id FROM Categorias WHERE id = %s', (id_categoria,))
            if not cursor.fetchone():
                raise ValueError(f"Categoria com ID {id_categoria} não encontrada no banco.")

            id_instrumento = _get_or_create_id(cursor, 'instrumentocontratual', 'nome', contrato_excel.get('tipo_contrato'))
            id_modalidade = _get_or_create_id(cursor, 'modalidade', 'nome', contrato_excel.get('modalidade'))
            id_num_modalidade = _get_or_create_id(cursor, 'numeromodalidade', 'numero_ano', contrato_excel.get('numero_modalidade'))
            id_processo = _get_or_create_id(cursor, 'processoslicitatorios', 'numero', contrato_excel.get('numero_processo'))
            
            sql = """
                INSERT INTO Contratos (
                    id_categoria, numero_contrato, fornecedor, cpf_cnpj, 
                    data_inicio, data_fim, data_criacao, email, telefone,
                    id_instrumento_contratual, id_modalidade, id_numero_modalidade, id_processo_licitatorio
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                id_categoria, contrato_excel.get('numero_contrato'), contrato_excel.get('fornecedor'), 
                contrato_excel.get('cpf_cnpj'), contrato_excel.get('data_inicio'), contrato_excel.get('data_fim'), 
                hoje, contrato_excel.get('email'), contrato_excel.get('telefone'),
                id_instrumento, id_modalidade, id_num_modalidade, id_processo
            ))

        conexao.commit()
        return jsonify({"mensagem": f"{len(dados)} contratos importados com sucesso!"}), 201
        
    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback() 
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao salvar dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/importar/itens/global/preview', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def importar_itens_global_preview():
    if 'arquivo_excel' not in request.files: return jsonify({"erro": "Nenhum arquivo enviado."}), 400
    arquivo = request.files['arquivo_excel']
    if not arquivo.filename: return jsonify({"erro": "Nenhum arquivo selecionado."}), 400
    if not arquivo.filename.endswith('.xlsx'): return jsonify({"erro": "Formato inválido. Envie um .xlsx"}), 400
    try:
        df = pd.read_excel(arquivo)
        colunas_obrigatorias = ['numero_contrato', 'tipo_contrato', 'numero_item', 'descricao', 'unidade_medida', 'quantidade', 'valor_unitario']
        colunas_faltantes = list(set(colunas_obrigatorias) - set(df.columns))
        if colunas_faltantes:
            return jsonify({"erro": f"Colunas obrigatórias faltantes: {', '.join(colunas_faltantes)}"}), 400
        df = df.where(pd.notnull(df), None)
        return df.to_json(orient='records')
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar o arquivo: {e}"}), 500

@app.route('/api/importar/itens/global/salvar', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def importar_itens_global_salvar():
    """Recebe uma lista de itens de múltiplos contratos e os salva no banco."""
    conexao = None
    try:
        dados_para_salvar = request.get_json()
        if not dados_para_salvar: return jsonify({"erro": "Nenhum dado recebido."}), 400
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")
        for i, item in enumerate(dados_para_salvar):
            num_contrato_raw = item.get('numero_contrato')
            tipo_contrato_raw = item.get('tipo_contrato')
            num_contrato = str(num_contrato_raw).strip() if num_contrato_raw is not None else None
            tipo_contrato = str(tipo_contrato_raw).strip() if tipo_contrato_raw is not None else None
            if not num_contrato or not tipo_contrato:
                raise ValueError(f"Linha {i+1}: 'numero_contrato' e 'tipo_contrato' não podem estar vazias.")
            cursor.execute("SELECT id FROM Contratos WHERE numero_contrato = %s AND tipo_contrato = %s", (num_contrato, tipo_contrato))
            contrato_encontrado = cursor.fetchone()
            if not contrato_encontrado:
                raise ValueError(f"Linha {i+1}: Contrato '{num_contrato}' com tipo '{tipo_contrato}' não encontrado.")
            id_contrato = contrato_encontrado['id']
            try:
                quantidade_raw = item.get('quantidade')
                quantidade_limpa = float(str(quantidade_raw).replace(',', '.').strip()) if quantidade_raw is not None else 0.0
                valor_unitario_raw = item.get('valor_unitario')
                valor_unitario_limpo = float(str(valor_unitario_raw).replace('R$', '').replace(',', '.').strip()) if valor_unitario_raw is not None else 0.0
            except (ValueError, TypeError):
                raise ValueError(f"Linha {i+1}: Verifique os valores de 'quantidade' ({quantidade_raw}) e 'valor_unitario' ({valor_unitario_raw}). Devem ser números.")
            sql_insert = """
                INSERT INTO ItensContrato (id_contrato, numero_item, descricao, unidade_medida, 
                                         quantidade, valor_unitario, marca) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (id_contrato, item.get('numero_item'), item.get('descricao'), 
                                         item.get('unidade_medida'), quantidade_limpa, 
                                         valor_unitario_limpo, item.get('marca')))
        conexao.commit()
        return jsonify({"mensagem": f"{len(dados_para_salvar)} itens importados com sucesso!"}), 201
    except Exception as e:
        if conexao: conexao.rollback()
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write("Ocorreu um erro durante a importação de itens (versão de debug):\n\n")
            traceback.print_exc(file=f)
        print("!!! ERRO CAPTURADO. Verifique o arquivo error_log.txt !!!")
        return jsonify({"erro": str(e)}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/anexos/<int:id_anexo>', methods=['DELETE'])
@nivel_acesso_required(2)
@login_required
def api_excluir_anexo(id_anexo):
    """Exclui o registro de um anexo do banco de dados."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT nome_seguro FROM Anexos WHERE id = %s", (id_anexo,))
        anexo = cursor.fetchone()
        if not anexo:
            return jsonify({'erro': 'Anexo não encontrado.'}), 404

        cursor.execute("DELETE FROM Anexos WHERE id = %s", (id_anexo,))
        conexao.commit()
        
        return jsonify({'mensagem': 'Registro do anexo excluído com sucesso.'})

    except psycopg2.Error as e:
        if conexao:
            conexao.rollback()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao:
            conexao.close()
            
@app.route('/api/tabelas-sistema/<string:nome_tabela>', methods=['GET'])
@nivel_acesso_required(2)
@login_required
def api_get_tabela_sistema(nome_tabela):
    """API genérica para listar itens de uma tabela de domínio do sistema."""
    if nome_tabela not in TABELAS_GERENCIAVEIS:
        return jsonify({'erro': 'Tabela não gerenciável.'}), 404

    config = TABELAS_GERENCIAVEIS[nome_tabela]
    tabela = config['tabela']
    coluna = config['coluna']
    
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute(f"SELECT id, {coluna} AS nome FROM public.{tabela} ORDER BY {coluna}")
        itens = cursor.fetchall()
        return jsonify([dict(item) for item in itens])
    except psycopg2.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao:
            conexao.close()

@app.route('/api/tabelas-sistema/<string:nome_tabela>', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def api_create_item_tabela_sistema(nome_tabela):
    """API genérica para criar um novo item em uma tabela de domínio."""
    conexao = None
    try:
        if nome_tabela not in TABELAS_GERENCIAVEIS:
            return jsonify({'erro': 'Tabela não gerenciável.'}), 404

        config = TABELAS_GERENCIAVEIS[nome_tabela]
        tabela = config['tabela']
        coluna = config['coluna']
        
        dados = request.get_json()
        novo_valor = dados.get('nome', '').strip()
        if not novo_valor:
            return jsonify({'erro': 'O valor não pode estar vazio.'}), 400

        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute(f"INSERT INTO public.{tabela} ({coluna}) VALUES (%s) RETURNING id", (novo_valor,))
        novo_id = cursor.fetchone()['id']
        conexao.commit()
        
        return jsonify({'mensagem': 'Item criado com sucesso!', 'id': novo_id, 'nome': novo_valor}), 201

    except psycopg2.IntegrityError:
        if conexao: conexao.rollback()
        return jsonify({'erro': 'Este valor já existe.'}), 409
    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/tabelas-sistema/<string:nome_tabela>/<int:item_id>', methods=['PUT'])
@nivel_acesso_required(2)
@login_required
def api_update_item_tabela_sistema(nome_tabela, item_id):
    """API genérica para atualizar um item em uma tabela de domínio."""
    conexao = None
    try:
        if nome_tabela not in TABELAS_GERENCIAVEIS:
            return jsonify({'erro': 'Tabela não gerenciável.'}), 404

        config = TABELAS_GERENCIAVEIS[nome_tabela]
        tabela = config['tabela']
        coluna = config['coluna']

        dados = request.get_json()
        novo_valor = dados.get('nome', '').strip()
        if not novo_valor:
            return jsonify({'erro': 'O valor não pode estar vazio.'}), 400

        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute(f"UPDATE public.{tabela} SET {coluna} = %s WHERE id = %s", (novo_valor, item_id))
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'Item não encontrado para atualização.'}), 404
            
        conexao.commit()
        return jsonify({'mensagem': 'Item atualizado com sucesso!'})

    except psycopg2.IntegrityError:
        if conexao: conexao.rollback()
        return jsonify({'erro': 'Este valor já existe.'}), 409
    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/tabelas-sistema/<string:nome_tabela>/<int:item_id>', methods=['DELETE'])
@nivel_acesso_required(2)
@login_required
def api_delete_item_tabela_sistema(nome_tabela, item_id):
    """API genérica para excluir um item de uma tabela de domínio, com verificação de vínculo corrigida."""
    conexao = None
    try:
        if nome_tabela not in TABELAS_GERENCIAVEIS:
            return jsonify({'erro': 'Tabela não gerenciável.'}), 404

        config = TABELAS_GERENCIAVEIS[nome_tabela]
        tabela_dominio = config['tabela']
        fk_tabela_uso = config.get('fk_tabela')
        fk_coluna_uso = config.get('fk_coluna')

        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        if fk_tabela_uso and fk_coluna_uso:
            if nome_tabela == 'tipo-documento':
                cursor.execute(f"SELECT {config['coluna']} FROM public.{tabela_dominio} WHERE id = %s", (item_id,))
                registro = cursor.fetchone()
                if registro:
                    nome_a_verificar = registro[0]
                    cursor.execute(f"SELECT COUNT(*) FROM public.{fk_tabela_uso} WHERE {fk_coluna_uso} = %s", (nome_a_verificar,))
            else:
                cursor.execute(f"SELECT COUNT(*) FROM public.{fk_tabela_uso} WHERE {fk_coluna_uso} = %s", (item_id,))
            
            contagem = cursor.fetchone()[0]
            if contagem > 0:
                return jsonify({'erro': f'Não é possível excluir. Este item está vinculado a {contagem} registro(s).'}), 409

        cursor.execute(f"DELETE FROM public.{tabela_dominio} WHERE id = %s", (item_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'Item não encontrado para exclusão.'}), 404
            
        conexao.commit()
        return jsonify({'mensagem': 'Item excluído com sucesso!'})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro de banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()
        
@app.route('/api/aocs/<path:numero_aocs>/status', methods=['PUT'])
@nivel_acesso_required(2)
@login_required
def update_aocs_status(numero_aocs):
    """Atualiza o status de entrega de todos os itens de uma AOCS."""
    dados = request.get_json()
    novo_status = dados.get('status')
    
    status_validos = ['Pendente', 'Entrega Parcial', 'Entregue']
    if not novo_status or novo_status not in status_validos:
        return jsonify({'erro': 'Status inválido.'}), 400

    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        sql = """
            UPDATE Pedidos SET status_entrega = %s 
            WHERE id_aocs = (SELECT id FROM AOCS WHERE numero_aocs = %s)
        """
        cursor.execute(sql, (novo_status, numero_aocs))
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'Nenhum pedido encontrado para esta AOCS.'}), 404

        conexao.commit()
        return jsonify({'mensagem': f'Status da AOCS {numero_aocs} atualizado para "{novo_status}" com sucesso!'})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()        

@app.route('/api/aocs/<path:numero_aocs>', methods=['DELETE'])
@nivel_acesso_required(2)
@login_required
def api_delete_aocs(numero_aocs):
    """Exclui uma AOCS e todos os seus itens de pedido associados (via CASCADE)."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
    
        cursor.execute("DELETE FROM AOCS WHERE numero_aocs = %s", (numero_aocs,))
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'AOCS não encontrada.'}), 404
            
        conexao.commit()
        return jsonify({'mensagem': f'AOCS {numero_aocs} e todos os seus itens foram excluídos com sucesso. O saldo dos itens foi restaurado.'})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/aocs/<path:numero_aocs>/data', methods=['PUT'])
@nivel_acesso_required(2)
@login_required
def update_aocs_data(numero_aocs):
    """Atualiza a data de criação de uma AOCS."""
    dados = request.get_json()
    nova_data = dados.get('data')
    if not nova_data:
        return jsonify({'erro': 'Nova data não fornecida.'}), 400

    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute("UPDATE aocs SET data_criacao = %s WHERE numero_aocs = %s", (nova_data, numero_aocs))
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'AOCS não encontrada.'}), 404

        conexao.commit()
        return jsonify({'mensagem': f'Data da AOCS {numero_aocs} atualizada com sucesso!'})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/aocs/<path:numero_aocs>/dados-gerais', methods=['PUT'])
@nivel_acesso_required(2)
@login_required
def update_aocs_dados_gerais(numero_aocs):
    """Atualiza campos de dados gerais (como numero_pedido, empenho) de uma AOCS."""
    dados = request.get_json()
    
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        campos_permitidos = ['numero_pedido', 'empenho']
        campos_para_atualizar = []
        valores = []

        for campo in campos_permitidos:
            if campo in dados:
                campos_para_atualizar.append(f"{campo} = %s")
                valores.append(dados[campo].strip())
            
        if not campos_para_atualizar:
            return jsonify({'erro': 'Nenhum dado válido para atualizar.'}), 400

        valores.append(numero_aocs)
        sql = f"UPDATE aocs SET {', '.join(campos_para_atualizar)} WHERE numero_aocs = %s"
        
        cursor.execute(sql, valores)
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'AOCS não encontrada.'}), 404

        conexao.commit()
        return jsonify({'mensagem': 'Dados da AOCS atualizados com sucesso!'})

    except psycopg2.Error as e:
        if conexao: conexao.rollback()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()
        
@app.route('/api/aocs/<path:numero_aocs>', methods=['PUT'])
@nivel_acesso_required(2)
@login_required
def api_update_aocs_completa(numero_aocs):
    """Atualiza os dados mestres de uma AOCS de forma transacional."""
    dados = request.get_json()
    if not dados:
        return jsonify({'erro': 'Nenhum dado recebido.'}), 400

    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        id_unidade = _get_or_create_id(cursor, 'unidadesrequisitantes', 'nome', dados.get('unidade_requisitante'))
        id_local = _get_or_create_id(cursor, 'locaisentrega', 'descricao', dados.get('local_entrega'))
        id_responsavel = _get_or_create_id(cursor, 'agentesresponsaveis', 'nome', dados.get('agente_responsavel'))
        id_dotacao = _get_or_create_id(cursor, 'dotacao', 'info_orcamentaria', dados.get('info_orcamentaria'))

        sql = """
            UPDATE AOCS SET
                justificativa = %s,
                id_unidade_requisitante = %s,
                id_local_entrega = %s,
                id_agente_responsavel = %s,
                id_dotacao = %s
            WHERE numero_aocs = %s
        """
        cursor.execute(sql, (
            dados.get('justificativa'),
            id_unidade,
            id_local,
            id_responsavel,
            id_dotacao,
            numero_aocs
        ))

        if cursor.rowcount == 0:
            return jsonify({'erro': 'AOCS não encontrada para atualização.'}), 404

        conexao.commit()
        return jsonify({'mensagem': 'Dados da AOCS atualizados com sucesso!'})

    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/aocs/<path:numero_aocs>', methods=['GET'])
@nivel_acesso_required(2)
@login_required
def api_get_aocs_detalhes(numero_aocs):
    """Retorna os dados detalhados de uma AOCS específica em formato JSON."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        sql = """
            SELECT a.*, ur.nome AS nome_unidade, le.descricao AS desc_local_entrega,
                   ar.nome AS nome_agente, d.info_orcamentaria AS info_dotacao
            FROM AOCS a
            LEFT JOIN unidadesrequisitantes ur ON a.id_unidade_requisitante = ur.id
            LEFT JOIN locaisentrega le ON a.id_local_entrega = le.id
            LEFT JOIN agentesresponsaveis ar ON a.id_agente_responsavel = ar.id
            LEFT JOIN dotacao d ON a.id_dotacao = d.id
            WHERE a.numero_aocs = %s
        """
        cursor.execute(sql, (numero_aocs,))
        aocs = cursor.fetchone()

        if not aocs:
            return jsonify({'erro': 'AOCS não encontrada.'}), 404

        return jsonify(dict(aocs))

    except psycopg2.Error as e:
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    finally:
        if conexao:
            conexao.close()

@app.route('/api/importar/itens/<int:id_contrato>/preview', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def importar_itens_preview(id_contrato):
    """API para pré-visualizar itens de um Excel para um contrato específico."""
    if 'arquivo_excel' not in request.files: return jsonify({"erro": "Nenhum arquivo enviado."}), 400
    arquivo = request.files['arquivo_excel']
    if not arquivo.filename.endswith('.xlsx'): return jsonify({"erro": "Formato inválido. Envie um .xlsx"}), 400
    
    try:
        df = pd.read_excel(arquivo)
        colunas_obrigatorias = ['numero_item', 'descricao', 'unidade_medida', 'quantidade', 'valor_unitario']
        colunas_faltantes = list(set(colunas_obrigatorias) - set(df.columns))
        if colunas_faltantes:
            return jsonify({"erro": f"Colunas obrigatórias faltantes: {', '.join(colunas_faltantes)}"}), 400
        
        if 'marca' not in df.columns:
            df['marca'] = None
            
        df = df.where(pd.notnull(df), None)
        return df.to_json(orient='records')
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao processar o arquivo: {e}"}), 500

@app.route('/api/importar/itens/<int:id_contrato>/salvar', methods=['POST'])
@nivel_acesso_required(2)
@login_required
def importar_itens_salvar(id_contrato):
    """API para salvar em massa os itens de um Excel em um contrato específico."""
    dados_para_salvar = request.get_json()
    if not dados_para_salvar: return jsonify({"erro": "Nenhum dado recebido."}), 400

    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        for item in dados_para_salvar:
            try:
                quantidade = float(str(item.get('quantidade')).replace(',', '.'))
                valor_unitario = float(str(item.get('valor_unitario')).replace(',', '.'))
            except (ValueError, TypeError):
                raise ValueError("Verifique os valores de 'quantidade' e 'valor_unitario'. Devem ser números.")

            sql_insert = """
                INSERT INTO ItensContrato (id_contrato, numero_item, descricao, unidade_medida, 
                                         quantidade, valor_unitario, marca) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (
                id_contrato, item.get('numero_item'), item.get('descricao'),
                item.get('unidade_medida'), quantidade, valor_unitario, item.get('marca')
            ))
            
        conexao.commit()
        return jsonify({"mensagem": f"{len(dados_para_salvar)} itens importados com sucesso!"}), 201

    except (psycopg2.Error, ValueError) as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao salvar: {str(e)}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/pedidos/<int:id_pedido>/registrar-entrega', methods=['PUT'])
@nivel_acesso_required(2)
@login_required
def api_registrar_entrega(id_pedido):
    """
    Registra a entrega de uma quantidade para um item de pedido específico (linha da AOCS).
    Atualiza a quantidade_entregue e o status_entrega do item.
    """
    dados = request.get_json()
    conexao = None
    try:
        try:
            quantidade_recebida = Decimal(str(dados['quantidade']).replace(',', '.'))
            if quantidade_recebida < 0:
                raise ValueError("Quantidade não pode ser negativa.")
        except Exception: 
            return jsonify({'erro': 'Quantidade fornecida é inválida.'}), 400

        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("BEGIN;")

        cursor.execute("SELECT quantidade_pedida, quantidade_entregue FROM Pedidos WHERE id = %s FOR UPDATE", (id_pedido,))
        pedido_item = cursor.fetchone()
        if not pedido_item:
            return jsonify({'erro': 'Item do pedido não encontrado.'}), 404

        quantidade_total_entregue = pedido_item['quantidade_entregue'] + quantidade_recebida
        if quantidade_total_entregue > pedido_item['quantidade_pedida']:
            saldo_restante = pedido_item['quantidade_pedida'] - pedido_item['quantidade_entregue']
            return jsonify({'erro': f'Entrega excede a quantidade pedida. Restam apenas {saldo_restante} unidades.'}), 400
            
        if quantidade_total_entregue >= pedido_item['quantidade_pedida']:
            novo_status = 'Entregue'
        elif quantidade_total_entregue > 0:
            novo_status = 'Entrega Parcial'
        else:
            novo_status = 'Pendente'
            
        sql_update = "UPDATE Pedidos SET quantidade_entregue = %s, status_entrega = %s WHERE id = %s"
        cursor.execute(sql_update, (quantidade_total_entregue, novo_status, id_pedido))
        
        conexao.commit()
        return jsonify({'mensagem': 'Entrega registrada com sucesso!'})

    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Ocorreu um erro inesperado: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/consultas', methods=['GET'])
@nivel_acesso_required(2)
@login_required
def api_consultas():
    """API genérica que usa o dicionário ENTIDADES_PESQUISAVEIS para executar buscas."""
    conexao = None
    try:
        tipo_consulta = request.args.get('tipo')
        valor_id = request.args.get('valor', type=int)

        if not tipo_consulta or not valor_id:
            return jsonify({'erro': 'Parâmetros "tipo" e "valor" são obrigatórios.'}), 400
        
        if tipo_consulta not in ENTIDADES_PESQUISAVEIS:
            return jsonify({'erro': 'Tipo de consulta desconhecido.'}), 400

        config = ENTIDADES_PESQUISAVEIS[tipo_consulta]
        
        vinculo_config = config['vinculos'][0]
        sql_query = vinculo_config['sql']
        titulo_resultado = vinculo_config['titulo_resultado']
        
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        cursor.execute(sql_query, (valor_id,))
        resultados = cursor.fetchall()
        
        return jsonify({
            'tipo': tipo_consulta,
            'titulo': titulo_resultado, 
            'resultados': [dict(row) for row in resultados]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'erro': f'Ocorreu um erro no servidor: {e}'}), 500
    finally:
        if conexao:
            conexao.close()

@app.route('/api/consultas/entidades/<string:nome_entidade>')
@nivel_acesso_required(2)
@login_required
def api_get_valores_entidade(nome_entidade):
    """
    API genérica para buscar a lista de valores de uma entidade pesquisável.
    Ex: Retorna todos os Processos Licitatórios.
    """
    conexao = None
    try:
        if nome_entidade not in ENTIDADES_PESQUISAVEIS:
            return jsonify({'erro': 'Entidade não pesquisável.'}), 404

        config = ENTIDADES_PESQUISAVEIS[nome_entidade]
        tabela = config['tabela_principal']
        coluna_texto = config['coluna_texto']

        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute(f"SELECT id, {coluna_texto} AS texto FROM public.{tabela} ORDER BY {coluna_texto}")
        
        resultados = cursor.fetchall()
        return jsonify([dict(row) for row in resultados])

    except Exception as e:
        traceback.print_exc()
        return jsonify({'erro': f'Ocorreu um erro no servidor: {e}'}), 500
    finally:
        if conexao:
            conexao.close()

@app.route('/api/relatorios/<string:nome_relatorio>')
@nivel_acesso_required(3)
@login_required
def api_gerar_relatorio(nome_relatorio):
    """
    API genérica para gerar relatórios em PDF com base na configuração 
    do dicionário RELATORIOS_DISPONIVEIS.
    """
    conexao = None
    try:
        if nome_relatorio not in RELATORIOS_DISPONIVEIS:
            return "Relatório não encontrado ou não permitido.", 404

        config = RELATORIOS_DISPONIVEIS[nome_relatorio]
        ordenacao_selecionada = request.args.get('ordenacao', '')

        sql_base = config['sql']
        
        ordenacao_sql = ""
        if ordenacao_selecionada in config['ordenacao_opcoes']:
            ordenacao_sql = config['ordenacao_opcoes'][ordenacao_selecionada]['sql']
        
        sql_final = f"{sql_base} {ordenacao_sql}"

        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute(sql_final)
        resultados = cursor.fetchall()

        logo_url = url_for('static', filename='images/brasao.png', _external=True)
        data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')

        html_renderizado = render_template(
            'relatorio_generico_template.html', 
            titulo_relatorio=config['titulo'],
            data_geracao=data_geracao,
            colunas=config['colunas'],
            resultados=resultados,
            logo_url=logo_url
        )

        pdf = HTML(string=html_renderizado, base_url=request.base_url).write_pdf()

        nome_arquivo = f"{nome_relatorio.upper()}_{date.today().strftime('%Y-%m-%d')}.pdf"
        return Response(pdf, mimetype='application/pdf', headers={
            'Content-Disposition': f'inline; filename={nome_arquivo}'
        })

    except Exception as e:
        traceback.print_exc()
        return f"Ocorreu um erro ao gerar o relatório: {e}", 500
    finally:
        if conexao:
            conexao.close()

@app.route('/api/admin/usuarios', methods=['POST'])
@nivel_acesso_required(1)
@login_required
def api_criar_usuario():
    """API para criar um novo usuário. Acessível apenas por Admins."""
    dados = request.get_json()
    conexao = None
    try:
        username = dados.get('username', '').strip()
        password = dados.get('password', '').strip()
        nivel_acesso = dados.get('nivel_acesso')

        if not username or not password:
            return jsonify({'erro': 'Nome de usuário e senha são obrigatórios.'}), 400
        
        try:
            nivel_acesso = int(nivel_acesso)
            if nivel_acesso not in [1, 2, 3]:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({'erro': 'Nível de acesso inválido.'}), 400

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        sql = "INSERT INTO usuarios (username, password_hash, nivel_acesso) VALUES (%s, %s, %s) RETURNING id"
        cursor.execute(sql, (username, password_hash, nivel_acesso))
        
        novo_id = cursor.fetchone()['id']
        conexao.commit()
        
        return jsonify({
            'mensagem': 'Usuário criado com sucesso!',
            'usuario': {'id': novo_id, 'username': username, 'nivel_acesso': nivel_acesso, 'ativo': True}
        }), 201

    except psycopg2.IntegrityError:
        if conexao: conexao.rollback()
        return jsonify({'erro': 'Este nome de usuário já está em uso.'}), 409
    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Ocorreu um erro inesperado: {e}"}), 500
    finally:
        if conexao: conexao.close()
      
@app.route('/api/admin/usuarios/<int:id>', methods=['GET', 'PUT'])
@nivel_acesso_required(1)
@login_required
def api_gerenciar_usuario_individual(id):
    """API para buscar (GET) ou atualizar (PUT) um usuário específico."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        if request.method == 'GET':
            cursor.execute("SELECT id, username, nivel_acesso FROM usuarios WHERE id = %s", (id,))
            usuario = cursor.fetchone()
            if not usuario:
                return jsonify({'erro': 'Usuário não encontrado.'}), 404
            return jsonify(dict(usuario))

        elif request.method == 'PUT':
            dados = request.get_json()
            username = dados.get('username', '').strip()
            nivel_acesso = dados.get('nivel_acesso')

            if not username or not nivel_acesso:
                return jsonify({'erro': 'Nome de usuário e nível de acesso são obrigatórios.'}), 400

            cursor.execute("UPDATE usuarios SET username = %s, nivel_acesso = %s WHERE id = %s", (username, nivel_acesso, id))
            conexao.commit()
            return jsonify({'mensagem': 'Usuário atualizado com sucesso!'})

    except psycopg2.IntegrityError:
        if conexao: conexao.rollback()
        return jsonify({'erro': 'Este nome de usuário já está em uso.'}), 409
    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Ocorreu um erro inesperado: {e}"}), 500
    finally:
        if conexao: conexao.close()

@app.route('/api/admin/usuarios/<int:id>/status', methods=['POST'])
@nivel_acesso_required(1)
@login_required
def api_toggle_user_status(id):
    """Inverte o status 'ativo' de um usuário."""
    conexao = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuarios SET ativo = NOT ativo WHERE id = %s RETURNING id, ativo", (id,))
        resultado = cursor.fetchone()
        if not resultado:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        conexao.commit()
        return jsonify({
            'mensagem': 'Status do usuário alterado com sucesso!',
            'novo_status': resultado['ativo']
        })
    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Ocorreu um erro inesperado: {e}"}), 500
    finally:
        if conexao: conexao.close()
 
@app.route('/api/admin/usuarios/<int:id>/reset-password', methods=['POST'])
@nivel_acesso_required(1)
@login_required
def api_reset_user_password(id):
    """Gera uma nova senha segura, a atualiza no banco e a retorna para o admin."""
    conexao = None
    try:
        # Gera uma senha aleatória segura de 12 caracteres
        alfabeto = string.ascii_letters + string.digits
        nova_senha = ''.join(secrets.choice(alfabeto) for i in range(12))
        novo_hash = generate_password_hash(nova_senha, method='pbkdf2:sha256')

        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s", (novo_hash, id))
        
        if cursor.rowcount == 0:
            return jsonify({'erro': 'Usuário não encontrado.'}), 404
        
        conexao.commit()
        return jsonify({
            'mensagem': 'Senha redefinida com sucesso!',
            'nova_senha': nova_senha
        })
    except Exception as e:
        if conexao: conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": f"Ocorreu um erro inesperado: {e}"}), 500
    finally:
        if conexao: conexao.close()
            
# --- 5. Bloco de Execução ---

if __name__ == '__main__':
    app.run(debug=True)