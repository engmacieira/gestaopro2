--
-- PostgreSQL database dump
--

\restrict XxbYpeIOi57DdPhA3fuaiVuMCt3AsHT6ywqmRzxY59IAjmgfHNZDcaNwC1qwQmc

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

-- Started on 2025-11-13 15:05:36

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 25318)
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;


--
-- TOC entry 5107 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 25355)
-- Name: agentesresponsaveis; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agentesresponsaveis (
    id integer NOT NULL,
    nome character varying(255) NOT NULL
);


ALTER TABLE public.agentesresponsaveis OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 25358)
-- Name: agentesresponsaveis_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.agentesresponsaveis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agentesresponsaveis_id_seq OWNER TO postgres;

--
-- TOC entry 5108 (class 0 OID 0)
-- Dependencies: 221
-- Name: agentesresponsaveis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.agentesresponsaveis_id_seq OWNED BY public.agentesresponsaveis.id;


--
-- TOC entry 222 (class 1259 OID 25359)
-- Name: anexos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.anexos (
    id integer NOT NULL,
    id_entidade integer NOT NULL,
    nome_original character varying(255) NOT NULL,
    nome_seguro character varying(255) NOT NULL,
    data_upload date DEFAULT CURRENT_DATE NOT NULL,
    tipo_documento character varying(100),
    tipo_entidade character varying(100) NOT NULL
);


ALTER TABLE public.anexos OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 25365)
-- Name: anexos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.anexos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anexos_id_seq OWNER TO postgres;

--
-- TOC entry 5109 (class 0 OID 0)
-- Dependencies: 223
-- Name: anexos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.anexos_id_seq OWNED BY public.anexos.id;


--
-- TOC entry 224 (class 1259 OID 25366)
-- Name: aocs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.aocs (
    id integer NOT NULL,
    numero_aocs character varying(100) NOT NULL,
    data_criacao date DEFAULT CURRENT_DATE NOT NULL,
    justificativa text,
    local_data character varying(100),
    id_unidade_requisitante integer,
    id_local_entrega integer,
    id_agente_responsavel integer,
    id_dotacao integer,
    numero_pedido character varying(100),
    tipo_pedido character varying(100),
    empenho character varying(100)
);


ALTER TABLE public.aocs OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 25372)
-- Name: aocs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.aocs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.aocs_id_seq OWNER TO postgres;

--
-- TOC entry 5110 (class 0 OID 0)
-- Dependencies: 225
-- Name: aocs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.aocs_id_seq OWNED BY public.aocs.id;


--
-- TOC entry 226 (class 1259 OID 25373)
-- Name: categorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    ativo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.categorias OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 25377)
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_id_seq OWNER TO postgres;

--
-- TOC entry 5111 (class 0 OID 0)
-- Dependencies: 227
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- TOC entry 228 (class 1259 OID 25378)
-- Name: ci_pagamento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ci_pagamento (
    id integer NOT NULL,
    id_aocs integer NOT NULL,
    numero_ci character varying(50) NOT NULL,
    data_ci date NOT NULL,
    numero_nota_fiscal character varying(100) NOT NULL,
    serie_nota_fiscal character varying(50),
    codigo_acesso_nota character varying(255),
    data_nota_fiscal date NOT NULL,
    valor_nota_fiscal numeric(15,2) NOT NULL,
    id_dotacao_pagamento integer,
    observacoes_pagamento text,
    id_solicitante integer,
    id_secretaria integer
);


ALTER TABLE public.ci_pagamento OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 25383)
-- Name: ci_pagamento_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ci_pagamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ci_pagamento_id_seq OWNER TO postgres;

--
-- TOC entry 5112 (class 0 OID 0)
-- Dependencies: 229
-- Name: ci_pagamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ci_pagamento_id_seq OWNED BY public.ci_pagamento.id;


--
-- TOC entry 230 (class 1259 OID 25384)
-- Name: contratos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contratos (
    id integer NOT NULL,
    id_categoria integer NOT NULL,
    numero_contrato character varying(100) NOT NULL,
    fornecedor character varying(255) NOT NULL,
    cpf_cnpj character varying(18) NOT NULL,
    email character varying(255),
    telefone character varying(20),
    data_inicio date NOT NULL,
    data_fim date NOT NULL,
    data_criacao date DEFAULT CURRENT_DATE NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    id_instrumento_contratual integer,
    id_modalidade integer,
    id_numero_modalidade integer,
    id_processo_licitatorio integer
);


ALTER TABLE public.contratos OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 25391)
-- Name: contratos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contratos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contratos_id_seq OWNER TO postgres;

--
-- TOC entry 5113 (class 0 OID 0)
-- Dependencies: 231
-- Name: contratos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contratos_id_seq OWNED BY public.contratos.id;


--
-- TOC entry 232 (class 1259 OID 25392)
-- Name: dotacao; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dotacao (
    id integer NOT NULL,
    info_orcamentaria text NOT NULL
);


ALTER TABLE public.dotacao OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 25397)
-- Name: dotacao_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dotacao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dotacao_id_seq OWNER TO postgres;

--
-- TOC entry 5114 (class 0 OID 0)
-- Dependencies: 233
-- Name: dotacao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dotacao_id_seq OWNED BY public.dotacao.id;


--
-- TOC entry 234 (class 1259 OID 25398)
-- Name: instrumentocontratual; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.instrumentocontratual (
    id integer NOT NULL,
    nome character varying(100) NOT NULL
);


ALTER TABLE public.instrumentocontratual OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 25401)
-- Name: instrumentocontratual_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.instrumentocontratual_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.instrumentocontratual_id_seq OWNER TO postgres;

--
-- TOC entry 5115 (class 0 OID 0)
-- Dependencies: 235
-- Name: instrumentocontratual_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.instrumentocontratual_id_seq OWNED BY public.instrumentocontratual.id;


--
-- TOC entry 236 (class 1259 OID 25402)
-- Name: itenscontrato; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itenscontrato (
    id integer NOT NULL,
    id_contrato integer NOT NULL,
    numero_item integer NOT NULL,
    descricao text NOT NULL,
    marca character varying(150),
    unidade_medida character varying(50) NOT NULL,
    quantidade numeric(15,3) NOT NULL,
    valor_unitario numeric(15,2) NOT NULL,
    ativo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.itenscontrato OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 25408)
-- Name: itenscontrato_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itenscontrato_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.itenscontrato_id_seq OWNER TO postgres;

--
-- TOC entry 5116 (class 0 OID 0)
-- Dependencies: 237
-- Name: itenscontrato_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itenscontrato_id_seq OWNED BY public.itenscontrato.id;


--
-- TOC entry 238 (class 1259 OID 25409)
-- Name: locaisentrega; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.locaisentrega (
    id integer NOT NULL,
    descricao text NOT NULL
);


ALTER TABLE public.locaisentrega OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 25414)
-- Name: locaisentrega_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.locaisentrega_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.locaisentrega_id_seq OWNER TO postgres;

--
-- TOC entry 5117 (class 0 OID 0)
-- Dependencies: 239
-- Name: locaisentrega_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.locaisentrega_id_seq OWNED BY public.locaisentrega.id;


--
-- TOC entry 240 (class 1259 OID 25415)
-- Name: logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.logs (
    id integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    id_usuario integer,
    acao character varying(255) NOT NULL,
    detalhes text
);


ALTER TABLE public.logs OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 25421)
-- Name: logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.logs_id_seq OWNER TO postgres;

--
-- TOC entry 5118 (class 0 OID 0)
-- Dependencies: 241
-- Name: logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.logs_id_seq OWNED BY public.logs.id;


--
-- TOC entry 242 (class 1259 OID 25422)
-- Name: modalidade; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.modalidade (
    id integer NOT NULL,
    nome character varying(100) NOT NULL
);


ALTER TABLE public.modalidade OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 25425)
-- Name: modalidade_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.modalidade_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.modalidade_id_seq OWNER TO postgres;

--
-- TOC entry 5119 (class 0 OID 0)
-- Dependencies: 243
-- Name: modalidade_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.modalidade_id_seq OWNED BY public.modalidade.id;


--
-- TOC entry 244 (class 1259 OID 25426)
-- Name: numeromodalidade; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.numeromodalidade (
    id integer NOT NULL,
    numero_ano character varying(100) NOT NULL
);


ALTER TABLE public.numeromodalidade OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 25429)
-- Name: numeromodalidade_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.numeromodalidade_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.numeromodalidade_id_seq OWNER TO postgres;

--
-- TOC entry 5120 (class 0 OID 0)
-- Dependencies: 245
-- Name: numeromodalidade_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.numeromodalidade_id_seq OWNED BY public.numeromodalidade.id;


--
-- TOC entry 246 (class 1259 OID 25430)
-- Name: pedidos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pedidos (
    id integer NOT NULL,
    id_item_contrato integer NOT NULL,
    id_aocs integer NOT NULL,
    quantidade_pedida numeric(15,3) NOT NULL,
    data_pedido date DEFAULT CURRENT_DATE NOT NULL,
    status_entrega character varying(50) DEFAULT 'Pendente'::character varying NOT NULL,
    quantidade_entregue numeric(15,3) DEFAULT 0 NOT NULL
);


ALTER TABLE public.pedidos OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 25436)
-- Name: pedidos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pedidos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pedidos_id_seq OWNER TO postgres;

--
-- TOC entry 5121 (class 0 OID 0)
-- Dependencies: 247
-- Name: pedidos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pedidos_id_seq OWNED BY public.pedidos.id;


--
-- TOC entry 248 (class 1259 OID 25437)
-- Name: processoslicitatorios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.processoslicitatorios (
    id integer NOT NULL,
    numero character varying(100) NOT NULL
);


ALTER TABLE public.processoslicitatorios OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 25440)
-- Name: processoslicitatorios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.processoslicitatorios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.processoslicitatorios_id_seq OWNER TO postgres;

--
-- TOC entry 5122 (class 0 OID 0)
-- Dependencies: 249
-- Name: processoslicitatorios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.processoslicitatorios_id_seq OWNED BY public.processoslicitatorios.id;


--
-- TOC entry 250 (class 1259 OID 25441)
-- Name: tipos_documento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipos_documento (
    id integer NOT NULL,
    nome character varying(100) NOT NULL
);


ALTER TABLE public.tipos_documento OWNER TO postgres;

--
-- TOC entry 251 (class 1259 OID 25444)
-- Name: tipos_documento_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tipos_documento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_documento_id_seq OWNER TO postgres;

--
-- TOC entry 5123 (class 0 OID 0)
-- Dependencies: 251
-- Name: tipos_documento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tipos_documento_id_seq OWNED BY public.tipos_documento.id;


--
-- TOC entry 252 (class 1259 OID 25445)
-- Name: unidadesrequisitantes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.unidadesrequisitantes (
    id integer NOT NULL,
    nome character varying(255) NOT NULL
);


ALTER TABLE public.unidadesrequisitantes OWNER TO postgres;

--
-- TOC entry 253 (class 1259 OID 25448)
-- Name: unidadesrequisitantes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.unidadesrequisitantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unidadesrequisitantes_id_seq OWNER TO postgres;

--
-- TOC entry 5124 (class 0 OID 0)
-- Dependencies: 253
-- Name: unidadesrequisitantes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.unidadesrequisitantes_id_seq OWNED BY public.unidadesrequisitantes.id;


--
-- TOC entry 254 (class 1259 OID 25449)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    password_hash character varying(255) NOT NULL,
    nivel_acesso integer NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    data_criacao timestamp with time zone DEFAULT now()
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 255 (class 1259 OID 25454)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 5125 (class 0 OID 0)
-- Dependencies: 255
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 4837 (class 2604 OID 25455)
-- Name: agentesresponsaveis id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agentesresponsaveis ALTER COLUMN id SET DEFAULT nextval('public.agentesresponsaveis_id_seq'::regclass);


--
-- TOC entry 4838 (class 2604 OID 25456)
-- Name: anexos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos ALTER COLUMN id SET DEFAULT nextval('public.anexos_id_seq'::regclass);


--
-- TOC entry 4840 (class 2604 OID 25457)
-- Name: aocs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs ALTER COLUMN id SET DEFAULT nextval('public.aocs_id_seq'::regclass);


--
-- TOC entry 4842 (class 2604 OID 25458)
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- TOC entry 4844 (class 2604 OID 25459)
-- Name: ci_pagamento id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento ALTER COLUMN id SET DEFAULT nextval('public.ci_pagamento_id_seq'::regclass);


--
-- TOC entry 4845 (class 2604 OID 25460)
-- Name: contratos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos ALTER COLUMN id SET DEFAULT nextval('public.contratos_id_seq'::regclass);


--
-- TOC entry 4848 (class 2604 OID 25461)
-- Name: dotacao id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dotacao ALTER COLUMN id SET DEFAULT nextval('public.dotacao_id_seq'::regclass);


--
-- TOC entry 4849 (class 2604 OID 25462)
-- Name: instrumentocontratual id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instrumentocontratual ALTER COLUMN id SET DEFAULT nextval('public.instrumentocontratual_id_seq'::regclass);


--
-- TOC entry 4850 (class 2604 OID 25463)
-- Name: itenscontrato id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itenscontrato ALTER COLUMN id SET DEFAULT nextval('public.itenscontrato_id_seq'::regclass);


--
-- TOC entry 4852 (class 2604 OID 25464)
-- Name: locaisentrega id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locaisentrega ALTER COLUMN id SET DEFAULT nextval('public.locaisentrega_id_seq'::regclass);


--
-- TOC entry 4853 (class 2604 OID 25465)
-- Name: logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs ALTER COLUMN id SET DEFAULT nextval('public.logs_id_seq'::regclass);


--
-- TOC entry 4855 (class 2604 OID 25466)
-- Name: modalidade id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modalidade ALTER COLUMN id SET DEFAULT nextval('public.modalidade_id_seq'::regclass);


--
-- TOC entry 4856 (class 2604 OID 25467)
-- Name: numeromodalidade id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.numeromodalidade ALTER COLUMN id SET DEFAULT nextval('public.numeromodalidade_id_seq'::regclass);


--
-- TOC entry 4857 (class 2604 OID 25468)
-- Name: pedidos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos ALTER COLUMN id SET DEFAULT nextval('public.pedidos_id_seq'::regclass);


--
-- TOC entry 4861 (class 2604 OID 25469)
-- Name: processoslicitatorios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processoslicitatorios ALTER COLUMN id SET DEFAULT nextval('public.processoslicitatorios_id_seq'::regclass);


--
-- TOC entry 4862 (class 2604 OID 25470)
-- Name: tipos_documento id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_documento ALTER COLUMN id SET DEFAULT nextval('public.tipos_documento_id_seq'::regclass);


--
-- TOC entry 4863 (class 2604 OID 25471)
-- Name: unidadesrequisitantes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unidadesrequisitantes ALTER COLUMN id SET DEFAULT nextval('public.unidadesrequisitantes_id_seq'::regclass);


--
-- TOC entry 4864 (class 2604 OID 25472)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 4868 (class 2606 OID 25474)
-- Name: agentesresponsaveis agentesresponsaveis_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agentesresponsaveis
    ADD CONSTRAINT agentesresponsaveis_nome_key UNIQUE (nome);


--
-- TOC entry 4870 (class 2606 OID 25476)
-- Name: agentesresponsaveis agentesresponsaveis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agentesresponsaveis
    ADD CONSTRAINT agentesresponsaveis_pkey PRIMARY KEY (id);


--
-- TOC entry 4872 (class 2606 OID 25478)
-- Name: anexos anexos_nome_seguro_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos
    ADD CONSTRAINT anexos_nome_seguro_key UNIQUE (nome_seguro);


--
-- TOC entry 4874 (class 2606 OID 25480)
-- Name: anexos anexos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos
    ADD CONSTRAINT anexos_pkey PRIMARY KEY (id);


--
-- TOC entry 4876 (class 2606 OID 25482)
-- Name: aocs aocs_numero_aocs_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs
    ADD CONSTRAINT aocs_numero_aocs_key UNIQUE (numero_aocs);


--
-- TOC entry 4878 (class 2606 OID 25484)
-- Name: aocs aocs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs
    ADD CONSTRAINT aocs_pkey PRIMARY KEY (id);


--
-- TOC entry 4881 (class 2606 OID 25486)
-- Name: categorias categorias_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_nome_key UNIQUE (nome);


--
-- TOC entry 4883 (class 2606 OID 25488)
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- TOC entry 4885 (class 2606 OID 25490)
-- Name: ci_pagamento ci_pagamento_numero_ci_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento
    ADD CONSTRAINT ci_pagamento_numero_ci_key UNIQUE (numero_ci);


--
-- TOC entry 4887 (class 2606 OID 25492)
-- Name: ci_pagamento ci_pagamento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento
    ADD CONSTRAINT ci_pagamento_pkey PRIMARY KEY (id);


--
-- TOC entry 4889 (class 2606 OID 25494)
-- Name: contratos contratos_numero_contrato_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_numero_contrato_key UNIQUE (numero_contrato);


--
-- TOC entry 4891 (class 2606 OID 25496)
-- Name: contratos contratos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_pkey PRIMARY KEY (id);


--
-- TOC entry 4893 (class 2606 OID 25498)
-- Name: dotacao dotacao_info_orcamentaria_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dotacao
    ADD CONSTRAINT dotacao_info_orcamentaria_key UNIQUE (info_orcamentaria);


--
-- TOC entry 4895 (class 2606 OID 25500)
-- Name: dotacao dotacao_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dotacao
    ADD CONSTRAINT dotacao_pkey PRIMARY KEY (id);


--
-- TOC entry 4897 (class 2606 OID 25502)
-- Name: instrumentocontratual instrumentocontratual_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instrumentocontratual
    ADD CONSTRAINT instrumentocontratual_nome_key UNIQUE (nome);


--
-- TOC entry 4899 (class 2606 OID 25504)
-- Name: instrumentocontratual instrumentocontratual_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instrumentocontratual
    ADD CONSTRAINT instrumentocontratual_pkey PRIMARY KEY (id);


--
-- TOC entry 4901 (class 2606 OID 25506)
-- Name: itenscontrato itenscontrato_id_contrato_numero_item_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itenscontrato
    ADD CONSTRAINT itenscontrato_id_contrato_numero_item_key UNIQUE (id_contrato, numero_item);


--
-- TOC entry 4903 (class 2606 OID 25508)
-- Name: itenscontrato itenscontrato_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itenscontrato
    ADD CONSTRAINT itenscontrato_pkey PRIMARY KEY (id);


--
-- TOC entry 4905 (class 2606 OID 25510)
-- Name: locaisentrega locaisentrega_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locaisentrega
    ADD CONSTRAINT locaisentrega_descricao_key UNIQUE (descricao);


--
-- TOC entry 4907 (class 2606 OID 25512)
-- Name: locaisentrega locaisentrega_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locaisentrega
    ADD CONSTRAINT locaisentrega_pkey PRIMARY KEY (id);


--
-- TOC entry 4909 (class 2606 OID 25514)
-- Name: logs logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4911 (class 2606 OID 25516)
-- Name: modalidade modalidade_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modalidade
    ADD CONSTRAINT modalidade_nome_key UNIQUE (nome);


--
-- TOC entry 4913 (class 2606 OID 25518)
-- Name: modalidade modalidade_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modalidade
    ADD CONSTRAINT modalidade_pkey PRIMARY KEY (id);


--
-- TOC entry 4915 (class 2606 OID 25520)
-- Name: numeromodalidade numeromodalidade_numero_ano_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.numeromodalidade
    ADD CONSTRAINT numeromodalidade_numero_ano_key UNIQUE (numero_ano);


--
-- TOC entry 4917 (class 2606 OID 25522)
-- Name: numeromodalidade numeromodalidade_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.numeromodalidade
    ADD CONSTRAINT numeromodalidade_pkey PRIMARY KEY (id);


--
-- TOC entry 4920 (class 2606 OID 25524)
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id);


--
-- TOC entry 4922 (class 2606 OID 25526)
-- Name: processoslicitatorios processoslicitatorios_numero_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processoslicitatorios
    ADD CONSTRAINT processoslicitatorios_numero_key UNIQUE (numero);


--
-- TOC entry 4924 (class 2606 OID 25528)
-- Name: processoslicitatorios processoslicitatorios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processoslicitatorios
    ADD CONSTRAINT processoslicitatorios_pkey PRIMARY KEY (id);


--
-- TOC entry 4926 (class 2606 OID 25530)
-- Name: tipos_documento tipos_documento_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_documento
    ADD CONSTRAINT tipos_documento_nome_key UNIQUE (nome);


--
-- TOC entry 4928 (class 2606 OID 25532)
-- Name: tipos_documento tipos_documento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_documento
    ADD CONSTRAINT tipos_documento_pkey PRIMARY KEY (id);


--
-- TOC entry 4930 (class 2606 OID 25534)
-- Name: unidadesrequisitantes unidadesrequisitantes_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unidadesrequisitantes
    ADD CONSTRAINT unidadesrequisitantes_nome_key UNIQUE (nome);


--
-- TOC entry 4932 (class 2606 OID 25536)
-- Name: unidadesrequisitantes unidadesrequisitantes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unidadesrequisitantes
    ADD CONSTRAINT unidadesrequisitantes_pkey PRIMARY KEY (id);


--
-- TOC entry 4934 (class 2606 OID 25538)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 4936 (class 2606 OID 25540)
-- Name: usuarios usuarios_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);


--
-- TOC entry 4879 (class 1259 OID 25541)
-- Name: idx_aocs_numero_aocs; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_aocs_numero_aocs ON public.aocs USING btree (numero_aocs);


--
-- TOC entry 4918 (class 1259 OID 25542)
-- Name: idx_pedidos_id_aocs; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pedidos_id_aocs ON public.pedidos USING btree (id_aocs);


--
-- TOC entry 4938 (class 2606 OID 25543)
-- Name: aocs fk_agente_responsavel; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs
    ADD CONSTRAINT fk_agente_responsavel FOREIGN KEY (id_agente_responsavel) REFERENCES public.agentesresponsaveis(id);


--
-- TOC entry 4953 (class 2606 OID 25548)
-- Name: pedidos fk_aocs; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT fk_aocs FOREIGN KEY (id_aocs) REFERENCES public.aocs(id) ON DELETE CASCADE;


--
-- TOC entry 4942 (class 2606 OID 25553)
-- Name: ci_pagamento fk_aocs; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento
    ADD CONSTRAINT fk_aocs FOREIGN KEY (id_aocs) REFERENCES public.aocs(id);


--
-- TOC entry 4946 (class 2606 OID 25558)
-- Name: contratos fk_categoria; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT fk_categoria FOREIGN KEY (id_categoria) REFERENCES public.categorias(id) ON DELETE RESTRICT;


--
-- TOC entry 4951 (class 2606 OID 25563)
-- Name: itenscontrato fk_contrato; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itenscontrato
    ADD CONSTRAINT fk_contrato FOREIGN KEY (id_contrato) REFERENCES public.contratos(id) ON DELETE RESTRICT;


--
-- TOC entry 4937 (class 2606 OID 25568)
-- Name: anexos fk_contrato_anexo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos
    ADD CONSTRAINT fk_contrato_anexo FOREIGN KEY (id_entidade) REFERENCES public.contratos(id) ON DELETE CASCADE;


--
-- TOC entry 4939 (class 2606 OID 25573)
-- Name: aocs fk_dotacao; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs
    ADD CONSTRAINT fk_dotacao FOREIGN KEY (id_dotacao) REFERENCES public.dotacao(id);


--
-- TOC entry 4943 (class 2606 OID 25578)
-- Name: ci_pagamento fk_dotacao; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento
    ADD CONSTRAINT fk_dotacao FOREIGN KEY (id_dotacao_pagamento) REFERENCES public.dotacao(id);


--
-- TOC entry 4947 (class 2606 OID 25583)
-- Name: contratos fk_instrumento_contratual; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT fk_instrumento_contratual FOREIGN KEY (id_instrumento_contratual) REFERENCES public.instrumentocontratual(id);


--
-- TOC entry 4954 (class 2606 OID 25588)
-- Name: pedidos fk_item_contrato; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT fk_item_contrato FOREIGN KEY (id_item_contrato) REFERENCES public.itenscontrato(id) ON DELETE RESTRICT;


--
-- TOC entry 4940 (class 2606 OID 25593)
-- Name: aocs fk_local_entrega; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs
    ADD CONSTRAINT fk_local_entrega FOREIGN KEY (id_local_entrega) REFERENCES public.locaisentrega(id);


--
-- TOC entry 4948 (class 2606 OID 25598)
-- Name: contratos fk_modalidade; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT fk_modalidade FOREIGN KEY (id_modalidade) REFERENCES public.modalidade(id);


--
-- TOC entry 4949 (class 2606 OID 25603)
-- Name: contratos fk_numero_modalidade; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT fk_numero_modalidade FOREIGN KEY (id_numero_modalidade) REFERENCES public.numeromodalidade(id);


--
-- TOC entry 4950 (class 2606 OID 25608)
-- Name: contratos fk_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT fk_processo_licitatorio FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processoslicitatorios(id);


--
-- TOC entry 4944 (class 2606 OID 25613)
-- Name: ci_pagamento fk_secretaria; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento
    ADD CONSTRAINT fk_secretaria FOREIGN KEY (id_secretaria) REFERENCES public.unidadesrequisitantes(id);


--
-- TOC entry 4945 (class 2606 OID 25618)
-- Name: ci_pagamento fk_solicitante; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ci_pagamento
    ADD CONSTRAINT fk_solicitante FOREIGN KEY (id_solicitante) REFERENCES public.agentesresponsaveis(id);


--
-- TOC entry 4941 (class 2606 OID 25623)
-- Name: aocs fk_unidade_requisitante; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.aocs
    ADD CONSTRAINT fk_unidade_requisitante FOREIGN KEY (id_unidade_requisitante) REFERENCES public.unidadesrequisitantes(id);


--
-- TOC entry 4952 (class 2606 OID 25628)
-- Name: logs fk_usuario; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT fk_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id) ON DELETE SET NULL;


-- Completed on 2025-11-13 15:05:36

--
-- PostgreSQL database dump complete
--

\unrestrict XxbYpeIOi57DdPhA3fuaiVuMCt3AsHT6ywqmRzxY59IAjmgfHNZDcaNwC1qwQmc

