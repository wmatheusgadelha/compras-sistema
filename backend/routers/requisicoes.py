from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.models import CompRequisicao, CompItem, CompUser, CompCotacao
from backend.schemas.schemas import RequisicaoCreate, RequisicaoUpdate, RequisicaoOut, CotacaoCreate, CotacaoUpdate, CotacaoOut

router = APIRouter(prefix="/api/requisicoes", tags=["Requisições"])

def next_numero_req(db: Session) -> str:
    last = db.query(CompRequisicao).order_by(CompRequisicao.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"REQ-{n:04d}"

@router.get("/", response_model=List[RequisicaoOut], summary="Listar requisições")
def list_requisicoes(
    status: Optional[str] = None,
    urgencia: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(CompRequisicao)
    if status:
        q = q.filter(CompRequisicao.status == status)
    if urgencia:
        q = q.filter(CompRequisicao.urgencia == urgencia)
    return q.order_by(CompRequisicao.created_at.desc()).all()

@router.post("/", response_model=RequisicaoOut, summary="Criar requisição")
def create_requisicao(data: RequisicaoCreate, db: Session = Depends(get_db), current_user: CompUser = Depends(get_current_user)):
    item = db.query(CompItem).filter(CompItem.id == data.item_id, CompItem.is_active == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    req = CompRequisicao(
        numero=next_numero_req(db),
        item_id=data.item_id,
        item_nome=item.nome,
        item_unidade=item.unidade,
        quantidade=data.quantidade,
        urgencia=data.urgencia,
        justificativa=data.justificativa,
        solicitante_id=current_user.id,
        solicitante_nome=current_user.nome,
        data_necessidade=data.data_necessidade,
        observacoes=data.observacoes,
        status="aberta"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@router.get("/{req_id}", response_model=RequisicaoOut, summary="Detalhe da requisição")
def get_requisicao(req_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisição não encontrada")
    return req

@router.put("/{req_id}", response_model=RequisicaoOut, summary="Editar requisição")
def update_requisicao(req_id: int, data: RequisicaoUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisição não encontrada")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return req

# ─── Cotações vinculadas à requisição ────────────────────────────────────────

@router.get("/{req_id}/cotacoes", response_model=List[CotacaoOut], summary="Listar cotações da requisição")
def list_cotacoes(req_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(CompCotacao).filter(CompCotacao.requisicao_id == req_id).all()

@router.post("/{req_id}/cotacoes", response_model=CotacaoOut, summary="Adicionar cotação")
def create_cotacao(req_id: int, data: CotacaoCreate, db: Session = Depends(get_db), current_user: CompUser = Depends(get_current_user)):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisição não encontrada")
    from backend.models.models import CompFornecedor
    forn = db.query(CompFornecedor).filter(CompFornecedor.id == data.fornecedor_id).first()
    if not forn:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    cotacao = CompCotacao(
        requisicao_id=req_id,
        fornecedor_id=data.fornecedor_id,
        fornecedor_nome=forn.razao_social,
        preco_unitario=data.preco_unitario,
        quantidade=data.quantidade,
        preco_total=data.preco_unitario * data.quantidade,
        prazo_entrega_dias=data.prazo_entrega_dias,
        condicao_pagamento=data.condicao_pagamento,
        validade_proposta=data.validade_proposta,
        observacoes=data.observacoes,
        created_by=current_user.id
    )
    db.add(cotacao)
    # atualiza status da requisição
    if req.status == "aberta":
        req.status = "cotando"
    db.commit()
    db.refresh(cotacao)
    return cotacao

@router.put("/{req_id}/cotacoes/{cot_id}", response_model=CotacaoOut, summary="Editar cotação")
def update_cotacao(req_id: int, cot_id: int, data: CotacaoUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cot = db.query(CompCotacao).filter(CompCotacao.id == cot_id, CompCotacao.requisicao_id == req_id).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cot, field, value)
    if cot.preco_unitario and cot.quantidade:
        cot.preco_total = cot.preco_unitario * cot.quantidade
    db.commit()
    db.refresh(cot)
    return cot

@router.delete("/{req_id}/cotacoes/{cot_id}", summary="Remover cotação")
def delete_cotacao(req_id: int, cot_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cot = db.query(CompCotacao).filter(CompCotacao.id == cot_id, CompCotacao.requisicao_id == req_id).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    db.delete(cot)
    db.commit()
    return {"message": "Cotação removida"}
