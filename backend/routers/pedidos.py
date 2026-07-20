from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.core.database import get_db
from backend.core.security import get_current_user, require_roles
from backend.models.models import CompPedido, CompRequisicao, CompRequisicaoItem, CompFornecedor, CompCotacao, CompHistorico, CompUser
from backend.schemas.schemas import PedidoCreate, PedidoUpdate, PedidoAprovar, PedidoPagamento, PedidoRecebimento, PedidoOut, HistoricoOut

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos de Compra"])

def next_numero_pc(db: Session) -> str:
    last = db.query(CompPedido).order_by(CompPedido.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"PC-{n:04d}"

def registrar_historico(db: Session, pedido: CompPedido, status_novo: str, usuario: CompUser, obs: Optional[str] = None):
    hist = CompHistorico(
        pedido_id=pedido.id,
        pedido_numero=pedido.numero,
        status_anterior=pedido.status,
        status_novo=status_novo,
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        observacao=obs
    )
    db.add(hist)

@router.get("/", response_model=List[PedidoOut], summary="Listar pedidos de compra")
def list_pedidos(
    status: Optional[str] = None,
    fornecedor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(CompPedido)
    if status:
        q = q.filter(CompPedido.status == status)
    if fornecedor_id:
        q = q.filter(CompPedido.fornecedor_id == fornecedor_id)
    return q.order_by(CompPedido.created_at.desc()).all()

@router.post("/", response_model=PedidoOut, summary="Criar pedido de compra")
def create_pedido(data: PedidoCreate, db: Session = Depends(get_db), current_user: CompUser = Depends(require_roles("admin", "gestor"))):
    req = db.query(CompRequisicao).filter(CompRequisicao.id == data.requisicao_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisição não encontrada")
    forn = db.query(CompFornecedor).filter(CompFornecedor.id == data.fornecedor_id).first()
    if not forn:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    # Pega dados do item: prioriza o item específico da requisição
    req_item = None
    if data.requisicao_item_id:
        req_item = db.query(CompRequisicaoItem).filter(CompRequisicaoItem.id == data.requisicao_item_id).first()

    item_id = req_item.item_id if req_item else getattr(req, 'item_id', 0)
    item_nome = req_item.item_nome if req_item else getattr(req, 'item_nome', '')
    item_unidade = req_item.item_unidade if req_item else getattr(req, 'item_unidade', 'UN')

    pedido = CompPedido(
        numero=next_numero_pc(db),
        requisicao_id=req.id,
        requisicao_numero=req.numero,
        requisicao_item_id=data.requisicao_item_id,
        item_id=item_id,
        item_nome=item_nome,
        item_unidade=item_unidade,
        quantidade=data.quantidade,
        fornecedor_id=forn.id,
        fornecedor_nome=forn.razao_social,
        cotacao_id=data.cotacao_id,
        preco_unitario=data.preco_unitario,
        preco_total=data.preco_unitario * data.quantidade,
        condicao_pagamento=data.condicao_pagamento,
        prazo_entrega_dias=data.prazo_entrega_dias,
        previsao_entrega=data.previsao_entrega,
        observacoes=data.observacoes,
        status="aguardando_aprovacao",
        created_by=current_user.id,
        created_by_nome=current_user.nome
    )
    db.add(pedido)

    # marca cotação como selecionada
    if data.cotacao_id:
        cot = db.query(CompCotacao).filter(CompCotacao.id == data.cotacao_id).first()
        if cot:
            cot.selecionada = True

    # atualiza status do item da req e da req geral
    if req_item:
        req_item.status = "pedido_gerado"
    # verifica se todos os itens têm pedido
    from backend.models.models import CompRequisicaoItem as CRI
    todos = db.query(CRI).filter(CRI.requisicao_id == req.id).all()
    if all(i.status == "pedido_gerado" for i in todos):
        req.status = "pedido_gerado"
    elif any(i.status in ("cotado","pedido_gerado") for i in todos):
        req.status = "cotando"
    db.flush()

    registrar_historico(db, pedido, "aguardando_aprovacao", current_user, "Pedido criado")
    db.commit()
    db.refresh(pedido)
    return pedido

@router.get("/{pedido_id}", response_model=PedidoOut, summary="Detalhe do pedido")
def get_pedido(pedido_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido

@router.put("/{pedido_id}", response_model=PedidoOut, summary="Editar dados do pedido")
def update_pedido(pedido_id: int, data: PedidoUpdate, db: Session = Depends(get_db), _=Depends(require_roles("admin", "gestor"))):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status not in ("aguardando_aprovacao", "reprovado"):
        raise HTTPException(status_code=400, detail="Pedido não pode ser editado neste status")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(pedido, field, value)
    db.commit()
    db.refresh(pedido)
    return pedido

@router.post("/{pedido_id}/aprovar", response_model=PedidoOut, summary="Aprovar ou reprovar pedido")
def aprovar_pedido(pedido_id: int, data: PedidoAprovar, db: Session = Depends(get_db), current_user: CompUser = Depends(require_roles("admin", "gestor"))):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status != "aguardando_aprovacao":
        raise HTTPException(status_code=400, detail="Pedido não está aguardando aprovação")

    novo_status = "aprovado" if data.aprovado else "reprovado"
    registrar_historico(db, pedido, novo_status, current_user, data.motivo_reprovacao)

    pedido.status = novo_status
    pedido.aprovado_por_id = current_user.id
    pedido.aprovado_por_nome = current_user.nome
    pedido.data_aprovacao = datetime.utcnow()
    if not data.aprovado:
        pedido.motivo_reprovacao = data.motivo_reprovacao
    db.commit()
    db.refresh(pedido)
    return pedido

@router.post("/{pedido_id}/pagamento", response_model=PedidoOut, summary="Registrar pagamento")
def registrar_pagamento(pedido_id: int, data: PedidoPagamento, db: Session = Depends(get_db), current_user: CompUser = Depends(require_roles("admin", "gestor"))):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status not in ("aprovado", "aguardando_pagamento"):
        raise HTTPException(status_code=400, detail="Pedido precisa estar aprovado para registrar pagamento")

    registrar_historico(db, pedido, "pago", current_user, f"Pagamento: {data.forma_pagamento or ''}")
    pedido.status = "pago"
    pedido.data_pagamento = data.data_pagamento
    pedido.valor_pago = data.valor_pago
    pedido.forma_pagamento = data.forma_pagamento
    pedido.comprovante_obs = data.comprovante_obs
    db.commit()
    db.refresh(pedido)
    return pedido

@router.post("/{pedido_id}/recebimento", response_model=PedidoOut, summary="Registrar recebimento")
def registrar_recebimento(pedido_id: int, data: PedidoRecebimento, db: Session = Depends(get_db), current_user: CompUser = Depends(get_current_user)):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status not in ("aprovado", "aguardando_pagamento", "pago"):
        raise HTTPException(status_code=400, detail="Pedido precisa estar aprovado ou pago para registrar recebimento")

    recebido_total = data.quantidade_recebida >= pedido.quantidade
    novo_status = "recebido_total" if recebido_total else "recebido_parcial"

    registrar_historico(db, pedido, novo_status, current_user, f"NF: {data.numero_nf or 'não informada'} | Qtd: {data.quantidade_recebida}")
    pedido.status = novo_status
    pedido.data_recebimento = data.data_recebimento
    pedido.quantidade_recebida = data.quantidade_recebida
    pedido.numero_nf = data.numero_nf
    pedido.recebido_por_id = current_user.id
    pedido.recebido_por_nome = current_user.nome
    pedido.obs_recebimento = data.obs_recebimento
    db.commit()
    db.refresh(pedido)
    return pedido

@router.post("/{pedido_id}/reenviar", response_model=PedidoOut, summary="Reenviar pedido reprovado para aprovação")
def reenviar_pedido(pedido_id: int, db: Session = Depends(get_db), current_user: CompUser = Depends(require_roles("admin", "gestor"))):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status != "reprovado":
        raise HTTPException(status_code=400, detail="Apenas pedidos reprovados podem ser reenviados")
    registrar_historico(db, pedido, "aguardando_aprovacao", current_user, "Pedido reenviado para aprovação")
    pedido.status = "aguardando_aprovacao"
    pedido.motivo_reprovacao = None
    db.commit()
    db.refresh(pedido)
    return pedido

@router.get("/{pedido_id}/historico", response_model=List[HistoricoOut], summary="Histórico do pedido")
def get_historico(pedido_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(CompHistorico).filter(CompHistorico.pedido_id == pedido_id).order_by(CompHistorico.data.asc()).all()

@router.delete("/{pedido_id}", summary="Cancelar pedido")
def cancelar_pedido(pedido_id: int, db: Session = Depends(get_db), current_user: CompUser = Depends(require_roles("admin"))):
    pedido = db.query(CompPedido).filter(CompPedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status in ("recebido_total", "recebido_parcial"):
        raise HTTPException(status_code=400, detail="Pedido já recebido não pode ser cancelado")
    registrar_historico(db, pedido, "cancelado", current_user, "Pedido cancelado")
    pedido.status = "cancelado"
    db.commit()
    return {"message": "Pedido cancelado"}
