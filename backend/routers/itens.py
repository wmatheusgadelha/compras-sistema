from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.core.database import get_db
from backend.core.security import get_current_user, require_roles
from backend.models.models import CompItem, CompCategoria, CompCotacao, CompPedido
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/itens", tags=["Itens"])

class ItemCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    unidade: str = "UN"
    categoria_id: Optional[int] = None
    estoque_minimo: Optional[float] = None
    observacoes: Optional[str] = None

class ItemUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    categoria_id: Optional[int] = None
    estoque_minimo: Optional[float] = None
    observacoes: Optional[str] = None
    is_active: Optional[bool] = None

class ItemOut(BaseModel):
    id: int
    codigo: str
    nome: str
    descricao: Optional[str]
    unidade: str
    categoria_id: Optional[int]
    categoria_nome: Optional[str]
    estoque_minimo: Optional[float]
    observacoes: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

def next_codigo(db: Session) -> str:
    last = db.query(CompItem).order_by(CompItem.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"ITEM-{n:04d}"

@router.get("/", response_model=List[ItemOut])
def list_itens(busca: Optional[str] = None, categoria_id: Optional[int] = None,
               apenas_ativos: bool = True, db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(CompItem)
    if apenas_ativos: q = q.filter(CompItem.is_active == True)
    if busca: q = q.filter(CompItem.nome.ilike(f"%{busca}%") | CompItem.codigo.ilike(f"%{busca}%"))
    if categoria_id: q = q.filter(CompItem.categoria_id == categoria_id)
    return q.order_by(CompItem.nome).all()

@router.post("/", response_model=ItemOut)
def create_item(data: ItemCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    cat_nome = None
    if data.categoria_id:
        cat = db.query(CompCategoria).filter(CompCategoria.id == data.categoria_id).first()
        if cat: cat_nome = cat.nome
    item = CompItem(codigo=next_codigo(db), nome=data.nome, descricao=data.descricao,
                    unidade=data.unidade, categoria_id=data.categoria_id, categoria_nome=cat_nome,
                    estoque_minimo=data.estoque_minimo, observacoes=data.observacoes)
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    item = db.query(CompItem).filter(CompItem.id == item_id).first()
    if not item: raise HTTPException(404, "Item não encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    if data.categoria_id:
        cat = db.query(CompCategoria).filter(CompCategoria.id == data.categoria_id).first()
        item.categoria_nome = cat.nome if cat else None
    db.commit(); db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    item = db.query(CompItem).filter(CompItem.id == item_id).first()
    if not item: raise HTTPException(404, "Item não encontrado")
    item.is_active = False; db.commit()
    return {"message": "Item desativado"}

@router.get("/{item_id}/historico")
def get_historico_item(item_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Retorna histórico de compras do item: pedidos e cotações onde apareceu"""
    item = db.query(CompItem).filter(CompItem.id == item_id).first()
    if not item: raise HTTPException(404, "Item não encontrado")

    pedidos = db.query(CompPedido).filter(CompPedido.item_id == item_id).order_by(CompPedido.created_at.desc()).all()
    cotacoes = db.query(CompCotacao).join(
        CompPedido, CompCotacao.requisicao_id == CompPedido.requisicao_id, isouter=True
    ).filter(CompPedido.item_id == item_id).order_by(CompCotacao.created_at.desc()).limit(20).all()

    # última compra
    ultima = pedidos[0] if pedidos else None

    historico_pedidos = [{
        "numero": p.numero,
        "fornecedor": p.fornecedor_nome,
        "quantidade": p.quantidade,
        "unidade": p.item_unidade,
        "preco_unitario": p.preco_unitario,
        "preco_total": p.preco_total,
        "status": p.status,
        "data": p.created_at.isoformat() if p.created_at else None,
        "data_recebimento": p.data_recebimento.isoformat() if p.data_recebimento else None,
        "numero_nf": p.numero_nf,
    } for p in pedidos]

    return {
        "item": {"id": item.id, "codigo": item.codigo, "nome": item.nome, "unidade": item.unidade},
        "total_pedidos": len(pedidos),
        "ultima_compra": {
            "numero": ultima.numero,
            "fornecedor": ultima.fornecedor_nome,
            "preco_unitario": ultima.preco_unitario,
            "preco_total": ultima.preco_total,
            "data": ultima.created_at.isoformat() if ultima else None,
            "status": ultima.status,
        } if ultima else None,
        "pedidos": historico_pedidos,
    }
