from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.models import CompRequisicao, CompPedido
from backend.schemas.schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats, summary="KPIs do dashboard")
def get_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    hoje = datetime.utcnow()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_req = db.query(func.count(CompRequisicao.id)).scalar() or 0
    req_abertas = db.query(func.count(CompRequisicao.id)).filter(
        CompRequisicao.status.in_(["aberta", "cotando"])
    ).scalar() or 0

    total_pedidos = db.query(func.count(CompPedido.id)).scalar() or 0
    aguardando_aprov = db.query(func.count(CompPedido.id)).filter(
        CompPedido.status == "aguardando_aprovacao"
    ).scalar() or 0
    aprovados = db.query(func.count(CompPedido.id)).filter(
        CompPedido.status.in_(["aprovado", "aguardando_pagamento", "pago"])
    ).scalar() or 0
    recebidos = db.query(func.count(CompPedido.id)).filter(
        CompPedido.status.in_(["recebido_total", "recebido_parcial"])
    ).scalar() or 0

    valor_total = db.query(func.coalesce(func.sum(CompPedido.preco_total), 0)).filter(
        CompPedido.status != "cancelado"
    ).scalar() or 0

    valor_mes = db.query(func.coalesce(func.sum(CompPedido.preco_total), 0)).filter(
        CompPedido.created_at >= inicio_mes,
        CompPedido.status != "cancelado"
    ).scalar() or 0

    return DashboardStats(
        total_requisicoes=total_req,
        requisicoes_abertas=req_abertas,
        total_pedidos=total_pedidos,
        pedidos_aguardando_aprovacao=aguardando_aprov,
        pedidos_aprovados=aprovados,
        pedidos_recebidos=recebidos,
        valor_total_pedidos=float(valor_total),
        valor_pedidos_mes=float(valor_mes),
    )
