from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import verify_password, get_password_hash, create_access_token, get_current_user
from backend.models.models import CompUser
from backend.schemas.schemas import Token, ChangePassword

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])

@router.post("/token", response_model=Token, summary="Login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(CompUser).filter(CompUser.email == form_data.username, CompUser.is_active == True).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    token = create_access_token({"sub": user.email})
    return Token(access_token=token, token_type="bearer", user_name=user.nome, user_role=user.role, user_id=user.id)

@router.post("/change-password", summary="Trocar senha")
def change_password(data: ChangePassword, db: Session = Depends(get_db), current_user: CompUser = Depends(get_current_user)):
    if not verify_password(data.senha_atual, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    current_user.hashed_password = get_password_hash(data.nova_senha)
    db.commit()
    return {"message": "Senha alterada com sucesso"}
