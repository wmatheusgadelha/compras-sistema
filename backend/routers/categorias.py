from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.core.database import get_db
from backend.core.security import get_current_user, require_roles
from backend.models.models import CompCategoria
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/categorias", tags=["Categorias"])

class CategoriaCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None

class CategoriaOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    class Config:
        from_attributes = True

@router.get("/", response_model=List[CategoriaOut])
def list_categorias(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(CompCategoria).order_by(CompCategoria.nome).all()

@router.post("/", response_model=CategoriaOut)
def create_categoria(data: CategoriaCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    if db.query(CompCategoria).filter(CompCategoria.nome == data.nome).first():
        raise HTTPException(400, "Categoria já existe")
    c = CompCategoria(nome=data.nome, descricao=data.descricao)
    db.add(c); db.commit(); db.refresh(c)
    return c

@router.delete("/{cat_id}")
def delete_categoria(cat_id: int, db: Session = Depends(get_db), _=Depends(require_roles("admin","gestor"))):
    c = db.query(CompCategoria).filter(CompCategoria.id == cat_id).first()
    if not c: raise HTTPException(404, "Categoria não encontrada")
    db.delete(c); db.commit()
    return {"message": "Removida"}
