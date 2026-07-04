from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# ─── Auth ─────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_role: str
    user_id: int

class ChangePassword(BaseModel):
    senha_atual: str
    nova_senha: str

# ─── Usuários ─────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    password: str
    role: str = "tecnico"
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    matricula: Optional[str] = None

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    role: Optional[str] = None
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    matricula: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    nome: str
    email: str
    role: str
    cargo: Optional[str]
    telefone: Optional[str]
    matricula: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# ─── Itens ────────────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    codigo: str
    nome: str
    descricao: Optional[str] = None
    unidade: str = "UN"
    categoria: Optional[str] = None
    estoque_minimo: Optional[float] = None
    observacoes: Optional[str] = None

class ItemUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    categoria: Optional[str] = None
    estoque_minimo: Optional[float] = None
    observacoes: Optional[str] = None
    is_active: Optional[bool] = None

class ItemOut(BaseModel):
    id: int
    codigo: str
    nome: str
    descricao: Optional[str]
    unidade: str
    categoria: Optional[str]
    estoque_minimo: Optional[float]
    observacoes: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# ─── Fornecedores ─────────────────────────────────────────────────────────────

class FornecedorCreate(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    contato: Optional[str] = None
    categoria: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None

class FornecedorUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    contato: Optional[str] = None
    categoria: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None
    is_active: Optional[bool] = None

class FornecedorOut(BaseModel):
    id: int
    razao_social: str
    nome_fantasia: Optional[str]
    cnpj: Optional[str]
    email: Optional[str]
    telefone: Optional[str]
    contato: Optional[str]
    categoria: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    observacoes: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# ─── Requisições ──────────────────────────────────────────────────────────────

class RequisicaoCreate(BaseModel):
    item_id: int
    quantidade: float
    urgencia: str = "media"
    justificativa: Optional[str] = None
    data_necessidade: Optional[date] = None
    observacoes: Optional[str] = None

class RequisicaoUpdate(BaseModel):
    quantidade: Optional[float] = None
    urgencia: Optional[str] = None
    justificativa: Optional[str] = None
    data_necessidade: Optional[date] = None
    observacoes: Optional[str] = None
    status: Optional[str] = None

class RequisicaoOut(BaseModel):
    id: int
    numero: str
    item_id: int
    item_nome: str
    item_unidade: str
    quantidade: float
    urgencia: str
    justificativa: Optional[str]
    solicitante_id: int
    solicitante_nome: str
    status: str
    data_necessidade: Optional[date]
    observacoes: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ─── Cotações ─────────────────────────────────────────────────────────────────

class CotacaoCreate(BaseModel):
    requisicao_id: int
    fornecedor_id: int
    preco_unitario: float
    quantidade: float
    prazo_entrega_dias: Optional[int] = None
    condicao_pagamento: Optional[str] = None
    validade_proposta: Optional[date] = None
    observacoes: Optional[str] = None

class CotacaoUpdate(BaseModel):
    preco_unitario: Optional[float] = None
    quantidade: Optional[float] = None
    prazo_entrega_dias: Optional[int] = None
    condicao_pagamento: Optional[str] = None
    validade_proposta: Optional[date] = None
    observacoes: Optional[str] = None
    selecionada: Optional[bool] = None

class CotacaoOut(BaseModel):
    id: int
    requisicao_id: int
    fornecedor_id: int
    fornecedor_nome: str
    preco_unitario: float
    quantidade: float
    preco_total: float
    prazo_entrega_dias: Optional[int]
    condicao_pagamento: Optional[str]
    validade_proposta: Optional[date]
    observacoes: Optional[str]
    selecionada: bool
    created_at: datetime
    class Config:
        from_attributes = True

# ─── Pedidos ──────────────────────────────────────────────────────────────────

class PedidoCreate(BaseModel):
    requisicao_id: int
    cotacao_id: Optional[int] = None
    fornecedor_id: int
    quantidade: float
    preco_unitario: float
    condicao_pagamento: Optional[str] = None
    prazo_entrega_dias: Optional[int] = None
    previsao_entrega: Optional[date] = None
    observacoes: Optional[str] = None

class PedidoAprovar(BaseModel):
    aprovado: bool
    motivo_reprovacao: Optional[str] = None

class PedidoPagamento(BaseModel):
    data_pagamento: date
    valor_pago: float
    forma_pagamento: Optional[str] = None
    comprovante_obs: Optional[str] = None

class PedidoRecebimento(BaseModel):
    data_recebimento: date
    quantidade_recebida: float
    numero_nf: Optional[str] = None
    obs_recebimento: Optional[str] = None

class PedidoUpdate(BaseModel):
    condicao_pagamento: Optional[str] = None
    prazo_entrega_dias: Optional[int] = None
    previsao_entrega: Optional[date] = None
    observacoes: Optional[str] = None

class PedidoOut(BaseModel):
    id: int
    numero: str
    requisicao_id: int
    requisicao_numero: str
    item_id: int
    item_nome: str
    item_unidade: str
    quantidade: float
    fornecedor_id: int
    fornecedor_nome: str
    cotacao_id: Optional[int]
    preco_unitario: float
    preco_total: float
    condicao_pagamento: Optional[str]
    prazo_entrega_dias: Optional[int]
    previsao_entrega: Optional[date]
    status: str
    aprovado_por_id: Optional[int]
    aprovado_por_nome: Optional[str]
    data_aprovacao: Optional[datetime]
    motivo_reprovacao: Optional[str]
    data_pagamento: Optional[date]
    valor_pago: Optional[float]
    forma_pagamento: Optional[str]
    comprovante_obs: Optional[str]
    data_recebimento: Optional[date]
    quantidade_recebida: Optional[float]
    numero_nf: Optional[str]
    recebido_por_nome: Optional[str]
    obs_recebimento: Optional[str]
    observacoes: Optional[str]
    created_by: int
    created_by_nome: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class HistoricoOut(BaseModel):
    id: int
    pedido_id: int
    pedido_numero: str
    status_anterior: Optional[str]
    status_novo: str
    usuario_nome: Optional[str]
    observacao: Optional[str]
    data: datetime
    class Config:
        from_attributes = True

# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_requisicoes: int
    requisicoes_abertas: int
    total_pedidos: int
    pedidos_aguardando_aprovacao: int
    pedidos_aprovados: int
    pedidos_recebidos: int
    valor_total_pedidos: float
    valor_pedidos_mes: float
