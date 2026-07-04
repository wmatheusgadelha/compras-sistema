from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Date
from datetime import datetime
from backend.core.database import Base

# ─── Usuários ─────────────────────────────────────────────────────────────────

class CompUser(Base):
    __tablename__ = "comp_users"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="tecnico")
    cargo = Column(String(100), nullable=True)
    telefone = Column(String(20), nullable=True)
    matricula = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ─── Categorias (compartilhadas entre itens e fornecedores) ───────────────────

class CompCategoria(Base):
    __tablename__ = "comp_categorias"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ─── Itens ────────────────────────────────────────────────────────────────────

class CompItem(Base):
    __tablename__ = "comp_itens"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    unidade = Column(String(20), nullable=False, default="UN")
    categoria_id = Column(Integer, nullable=True)
    categoria_nome = Column(String(100), nullable=True)
    estoque_minimo = Column(Float, nullable=True)
    observacoes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ─── Fornecedores ─────────────────────────────────────────────────────────────

class CompFornecedor(Base):
    __tablename__ = "comp_fornecedores"
    id = Column(Integer, primary_key=True, index=True)
    razao_social = Column(String(200), nullable=False)
    nome_fantasia = Column(String(200), nullable=True)
    cnpj = Column(String(20), nullable=True, unique=True)
    email = Column(String(120), nullable=True)
    telefone = Column(String(20), nullable=True)
    contato = Column(String(120), nullable=True)
    categoria_id = Column(Integer, nullable=True)
    categoria_nome = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    observacoes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ─── Requisições ──────────────────────────────────────────────────────────────

class CompRequisicao(Base):
    __tablename__ = "comp_requisicoes"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(20), unique=True, nullable=False, index=True)
    item_id = Column(Integer, nullable=False)
    item_nome = Column(String(200), nullable=False)
    item_unidade = Column(String(20), nullable=False, default="UN")
    quantidade = Column(Float, nullable=False)
    urgencia = Column(String(20), nullable=False, default="media")
    justificativa = Column(Text, nullable=True)
    solicitante_id = Column(Integer, nullable=False)
    solicitante_nome = Column(String(120), nullable=False)
    status = Column(String(30), nullable=False, default="aberta")
    data_necessidade = Column(Date, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─── Cotações ─────────────────────────────────────────────────────────────────

class CompCotacao(Base):
    __tablename__ = "comp_cotacoes"
    id = Column(Integer, primary_key=True, index=True)
    requisicao_id = Column(Integer, nullable=False, index=True)
    fornecedor_id = Column(Integer, nullable=False)
    fornecedor_nome = Column(String(200), nullable=False)
    preco_unitario = Column(Float, nullable=False)
    quantidade = Column(Float, nullable=False)
    preco_total = Column(Float, nullable=False)
    prazo_entrega_dias = Column(Integer, nullable=True)
    condicao_pagamento = Column(String(100), nullable=True)
    validade_proposta = Column(Date, nullable=True)
    observacoes = Column(Text, nullable=True)
    selecionada = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

# ─── Pedidos ──────────────────────────────────────────────────────────────────

class CompPedido(Base):
    __tablename__ = "comp_pedidos"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(20), unique=True, nullable=False, index=True)
    requisicao_id = Column(Integer, nullable=False, index=True)
    requisicao_numero = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)
    item_nome = Column(String(200), nullable=False)
    item_unidade = Column(String(20), nullable=False, default="UN")
    quantidade = Column(Float, nullable=False)
    fornecedor_id = Column(Integer, nullable=False)
    fornecedor_nome = Column(String(200), nullable=False)
    cotacao_id = Column(Integer, nullable=True)
    preco_unitario = Column(Float, nullable=False)
    preco_total = Column(Float, nullable=False)
    condicao_pagamento = Column(String(100), nullable=True)
    prazo_entrega_dias = Column(Integer, nullable=True)
    previsao_entrega = Column(Date, nullable=True)
    status = Column(String(40), nullable=False, default="aguardando_aprovacao")
    # Aprovação
    aprovado_por_id = Column(Integer, nullable=True)
    aprovado_por_nome = Column(String(120), nullable=True)
    data_aprovacao = Column(DateTime, nullable=True)
    motivo_reprovacao = Column(Text, nullable=True)
    # Recebimento (simplificado — remove etapa de pagamento separada)
    data_recebimento = Column(Date, nullable=True)
    quantidade_recebida = Column(Float, nullable=True)
    numero_nf = Column(String(50), nullable=True)
    recebido_por_id = Column(Integer, nullable=True)
    recebido_por_nome = Column(String(120), nullable=True)
    obs_recebimento = Column(Text, nullable=True)
    # Pagamento (mantido para registro, mas não bloqueia fluxo)
    data_pagamento = Column(Date, nullable=True)
    valor_pago = Column(Float, nullable=True)
    forma_pagamento = Column(String(100), nullable=True)
    comprovante_obs = Column(Text, nullable=True)

    observacoes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_by_nome = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─── Histórico de pedidos ─────────────────────────────────────────────────────

class CompHistorico(Base):
    __tablename__ = "comp_historico"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    pedido_numero = Column(String(20), nullable=False)
    status_anterior = Column(String(40), nullable=True)
    status_novo = Column(String(40), nullable=False)
    usuario_id = Column(Integer, nullable=True)
    usuario_nome = Column(String(120), nullable=True)
    observacao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.utcnow)
