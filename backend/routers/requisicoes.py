from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.models import CompRequisicao, CompRequisicaoItem, CompItem, CompUser, CompCotacao, CompFornecedor
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/api/requisicoes", tags=["Requisições"])

# ─── Schemas inline ───────────────────────────────────────────────────────────

class ItemReqIn(BaseModel):
    item_id: int
    quantidade: float
    observacao: Optional[str] = None

class RequisicaoCreate(BaseModel):
    urgencia: str = "media"
    justificativa: Optional[str] = None
    data_necessidade: Optional[date] = None
    observacoes: Optional[str] = None
    itens: List[ItemReqIn]

class RequisicaoItemOut(BaseModel):
    id: int
    item_id: int
    item_nome: str
    item_unidade: str
    item_codigo: Optional[str]
    quantidade: float
    observacao: Optional[str]
    status: str
    class Config:
        from_attributes = True

class RequisicaoOut(BaseModel):
    id: int
    numero: str
    urgencia: str
    justificativa: Optional[str]
    solicitante_id: int
    solicitante_nome: str
    status: str
    data_necessidade: Optional[date]
    observacoes: Optional[str]
    created_at: datetime
    updated_at: datetime
    itens: List[RequisicaoItemOut] = []
    class Config:
        from_attributes = True

class CotacaoCreate(BaseModel):
    requisicao_id: int
    requisicao_item_id: int
    fornecedor_id: int
    preco_unitario: float
    quantidade: float
    prazo_entrega_dias: Optional[int] = None
    condicao_pagamento: Optional[str] = None
    validade_proposta: Optional[date] = None
    observacoes: Optional[str] = None

class CotacaoOut(BaseModel):
    id: int
    requisicao_id: int
    requisicao_item_id: Optional[int]
    fornecedor_id: int
    fornecedor_nome: str
    item_id: Optional[int]
    item_nome: Optional[str]
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

# ─── Helpers ──────────────────────────────────────────────────────────────────

def next_numero_req(db: Session) -> str:
    last = db.query(CompRequisicao).order_by(CompRequisicao.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"REQ-{n:04d}"

def enrich_req(req: CompRequisicao, db: Session) -> dict:
    itens = db.query(CompRequisicaoItem).filter(CompRequisicaoItem.requisicao_id == req.id).all()
    return {
        "id": req.id, "numero": req.numero, "urgencia": req.urgencia,
        "justificativa": req.justificativa, "solicitante_id": req.solicitante_id,
        "solicitante_nome": req.solicitante_nome, "status": req.status,
        "data_necessidade": req.data_necessidade, "observacoes": req.observacoes,
        "created_at": req.created_at, "updated_at": req.updated_at,
        "itens": [{"id": i.id, "item_id": i.item_id, "item_nome": i.item_nome,
                   "item_unidade": i.item_unidade, "item_codigo": i.item_codigo,
                   "quantidade": i.quantidade, "observacao": i.observacao,
                   "status": i.status} for i in itens]
    }

def compute_req_status(db: Session, req_id: int) -> str:
    itens = db.query(CompRequisicaoItem).filter(CompRequisicaoItem.requisicao_id == req_id).all()
    if not itens: return "aberta"
    statuses = [i.status for i in itens]
    if all(s == "pedido_gerado" for s in statuses): return "pedido_gerado"
    if any(s == "cotado" for s in statuses): return "cotando"
    return "aberta"

# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", summary="Listar requisições")
def list_requisicoes(status: Optional[str] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(CompRequisicao)
    if status: q = q.filter(CompRequisicao.status == status)
    reqs = q.order_by(CompRequisicao.created_at.desc()).all()
    return [enrich_req(r, db) for r in reqs]

@router.post("/", summary="Criar requisição com múltiplos itens")
def create_requisicao(data: RequisicaoCreate, db: Session = Depends(get_db), current_user: CompUser = Depends(get_current_user)):
    if not data.itens:
        raise HTTPException(400, "Adicione pelo menos um item")
    req = CompRequisicao(
        numero=next_numero_req(db), urgencia=data.urgencia,
        justificativa=data.justificativa, solicitante_id=current_user.id,
        solicitante_nome=current_user.nome, status="aberta",
        data_necessidade=data.data_necessidade, observacoes=data.observacoes
    )
    db.add(req); db.flush()
    for it in data.itens:
        item = db.query(CompItem).filter(CompItem.id == it.item_id, CompItem.is_active == True).first()
        if not item: raise HTTPException(404, f"Item {it.item_id} não encontrado")
        db.add(CompRequisicaoItem(
            requisicao_id=req.id, item_id=item.id, item_nome=item.nome,
            item_unidade=item.unidade, item_codigo=item.codigo,
            quantidade=it.quantidade, observacao=it.observacao, status="pendente"
        ))
    db.commit(); db.refresh(req)
    return enrich_req(req, db)

@router.get("/{req_id}", summary="Detalhe da requisição")
def get_requisicao(req_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == req_id).first()
    if not req: raise HTTPException(404, "Requisição não encontrada")
    return enrich_req(req, db)

@router.put("/{req_id}", summary="Atualizar status/dados da requisição")
def update_requisicao(req_id: int, data: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == req_id).first()
    if not req: raise HTTPException(404, "Requisição não encontrada")
    for field, value in data.items():
        if hasattr(req, field): setattr(req, field, value)
    db.commit(); db.refresh(req)
    return enrich_req(req, db)

# ─── Cotações por item da requisição ─────────────────────────────────────────

@router.get("/{req_id}/cotacoes", summary="Listar cotações da requisição")
def list_cotacoes(req_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(CompCotacao).filter(CompCotacao.requisicao_id == req_id).all()

@router.post("/{req_id}/cotacoes", summary="Adicionar cotação a um item da requisição")
def create_cotacao(req_id: int, data: CotacaoCreate, db: Session = Depends(get_db), current_user: CompUser = Depends(get_current_user)):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == req_id).first()
    if not req: raise HTTPException(404, "Requisição não encontrada")
    forn = db.query(CompFornecedor).filter(CompFornecedor.id == data.fornecedor_id).first()
    if not forn: raise HTTPException(404, "Fornecedor não encontrado")
    req_item = db.query(CompRequisicaoItem).filter(CompRequisicaoItem.id == data.requisicao_item_id).first()
    cotacao = CompCotacao(
        requisicao_id=req_id, requisicao_item_id=data.requisicao_item_id,
        fornecedor_id=forn.id, fornecedor_nome=forn.razao_social,
        item_id=req_item.item_id if req_item else None,
        item_nome=req_item.item_nome if req_item else None,
        preco_unitario=data.preco_unitario, quantidade=data.quantidade,
        preco_total=data.preco_unitario * data.quantidade,
        prazo_entrega_dias=data.prazo_entrega_dias, condicao_pagamento=data.condicao_pagamento,
        validade_proposta=data.validade_proposta, observacoes=data.observacoes,
        created_by=current_user.id
    )
    db.add(cotacao)
    # atualiza status do item da req
    if req_item and req_item.status == "pendente":
        req_item.status = "cotado"
    # atualiza status geral da req
    req.status = compute_req_status(db, req_id)
    db.commit(); db.refresh(cotacao)
    return cotacao

@router.put("/{req_id}/cotacoes/{cot_id}", summary="Editar cotação")
def update_cotacao(req_id: int, cot_id: int, data: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cot = db.query(CompCotacao).filter(CompCotacao.id == cot_id, CompCotacao.requisicao_id == req_id).first()
    if not cot: raise HTTPException(404, "Cotação não encontrada")
    for field, value in data.items():
        if hasattr(cot, field): setattr(cot, field, value)
    if cot.preco_unitario and cot.quantidade:
        cot.preco_total = cot.preco_unitario * cot.quantidade
    db.commit(); db.refresh(cot)
    return cot

@router.delete("/{req_id}/cotacoes/{cot_id}", summary="Remover cotação")
def delete_cotacao(req_id: int, cot_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cot = db.query(CompCotacao).filter(CompCotacao.id == cot_id, CompCotacao.requisicao_id == req_id).first()
    if not cot: raise HTTPException(404, "Cotação não encontrada")
    db.delete(cot); db.commit()
    return {"message": "Cotação removida"}
