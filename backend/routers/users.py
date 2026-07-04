from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.core.database import get_db
from backend.core.security import get_current_user, get_password_hash, require_roles
from backend.models.models import CompUser
from backend.schemas.schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/api/users", tags=["Usuários"])

@router.get("/", response_model=List[UserOut], summary="Listar usuários")
def list_users(db: Session = Depends(get_db), _=Depends(require_roles("admin", "gestor"))):
    return db.query(CompUser).order_by(CompUser.nome).all()

@router.post("/", response_model=UserOut, summary="Criar usuário")
def create_user(data: UserCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    if db.query(CompUser).filter(CompUser.email == data.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = CompUser(
        nome=data.nome, email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role, cargo=data.cargo, telefone=data.telefone, matricula=data.matricula
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserOut, summary="Editar usuário")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    user = db.query(CompUser).filter(CompUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", summary="Desativar usuário")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: CompUser = Depends(require_roles("admin"))):
    user = db.query(CompUser).filter(CompUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode desativar sua própria conta")
    user.is_active = False
    db.commit()
    return {"message": "Usuário desativado"}
