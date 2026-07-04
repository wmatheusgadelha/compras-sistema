from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.core.database import get_db
from backend.core.security import get_current_user, require_roles
from backend.models.models import CompFornecedor, CompCategoria
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/fornecedores", tags=["Fornecedores"])

class FornecedorCreate(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    contato: Optional[str] = None
    categoria_id: Optional[int] = None
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
    categoria_id: Optional[int] = None
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
    categoria_id: Optional[int]
    categoria_nome: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    observacoes: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

@router.get("/", response_model=List[FornecedorOut])
def list_fornecedores(busca: Optional[str] = None, apenas_ativos: bool = True,
                      db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(CompFornecedor)
    if apenas_ativos: q = q.filter(CompFornecedor.is_active == True)
    if busca:
        q = q.filter(CompFornecedor.razao_social.ilike(f"%{busca}%") |
                     CompFornecedor.nome_fantasia.ilike(f"%{busca}%") |
                     CompFornecedor.cnpj.ilike(f"%{busca}%"))
    return q.order_by(CompFornecedor.razao_social).all()

@router.post("/", response_model=FornecedorOut)
def create_fornecedor(data: FornecedorCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    if data.cnpj and db.query(CompFornecedor).filter(CompFornecedor.cnpj == data.cnpj).first():
        raise HTTPException(400, "CNPJ já cadastrado")
    cat_nome = None
    if data.categoria_id:
        cat = db.query(CompCategoria).filter(CompCategoria.id == data.categoria_id).first()
        if cat: cat_nome = cat.nome
    forn = CompFornecedor(**{**data.model_dump(), "categoria_nome": cat_nome})
    db.add(forn); db.commit(); db.refresh(forn)
    return forn

@router.put("/{forn_id}", response_model=FornecedorOut)
def update_fornecedor(forn_id: int, data: FornecedorUpdate, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    forn = db.query(CompFornecedor).filter(CompFornecedor.id == forn_id).first()
    if not forn: raise HTTPException(404, "Fornecedor não encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(forn, field, value)
    if data.categoria_id is not None:
        cat = db.query(CompCategoria).filter(CompCategoria.id == data.categoria_id).first()
        forn.categoria_nome = cat.nome if cat else None
    db.commit(); db.refresh(forn)
    return forn

@router.delete("/{forn_id}")
def delete_fornecedor(forn_id: int, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    forn = db.query(CompFornecedor).filter(CompFornecedor.id == forn_id).first()
    if not forn: raise HTTPException(404, "Fornecedor não encontrado")
    forn.is_active = False; db.commit()
    return {"message": "Fornecedor desativado"}
