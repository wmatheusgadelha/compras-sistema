from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.core.database import Base, engine, SessionLocal
from backend.core.security import get_password_hash
from backend.core.config import settings
from backend.models.models import (
    CompUser, CompCategoria, CompItem, CompFornecedor,
    CompRequisicao, CompRequisicaoItem, CompCotacao, CompPedido, CompHistorico
)
from backend.routers import auth, users, itens, fornecedores, requisicoes, pedidos, dashboard
from backend.routers import categorias

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.RESET_SEED:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if settings.RESET_SEED:
            pass  # tabelas já foram recriadas pelo drop_all + create_all

        if db.query(CompUser).count() == 0:
            # Usuários
            admin = CompUser(nome="Administrador", email="admin@compras.com",
                             hashed_password=get_password_hash("admin123"), role="admin", cargo="Administrador")
            gestor = CompUser(nome="Carlos Mendes", email="gestor@compras.com",
                              hashed_password=get_password_hash("gestor123"), role="gestor", cargo="Gerente de Compras")
            tecnico = CompUser(nome="Ana Lima", email="tecnico@compras.com",
                               hashed_password=get_password_hash("tecnico123"), role="tecnico", cargo="Analista de Compras")
            db.add_all([admin, gestor, tecnico])
            db.flush()

            # Categorias
            cats = [
                CompCategoria(nome="EPI", descricao="Equipamentos de Proteção Individual"),
                CompCategoria(nome="Matéria-Prima", descricao="Insumos para produção"),
                CompCategoria(nome="Embalagem", descricao="Embalagens e materiais de envase"),
                CompCategoria(nome="Manutenção", descricao="Peças e materiais de manutenção"),
                CompCategoria(nome="Escritório", descricao="Material de escritório e papelaria"),
                CompCategoria(nome="Químicos", descricao="Produtos químicos em geral"),
                CompCategoria(nome="Limpeza", descricao="Produtos de limpeza e higiene"),
            ]
            db.add_all(cats)
            db.flush()
            cat_map = {c.nome: c for c in cats}

            # Itens
            itens_seed = [
                CompItem(codigo="ITEM-0001", nome="Luva de Nitrila M", unidade="CX",
                         categoria_id=cat_map["EPI"].id, categoria_nome="EPI", estoque_minimo=5),
                CompItem(codigo="ITEM-0002", nome="Óculos de Proteção", unidade="UN",
                         categoria_id=cat_map["EPI"].id, categoria_nome="EPI", estoque_minimo=10),
                CompItem(codigo="ITEM-0003", nome="Soda Cáustica 50KG", unidade="SC",
                         categoria_id=cat_map["Matéria-Prima"].id, categoria_nome="Matéria-Prima", estoque_minimo=2),
                CompItem(codigo="ITEM-0004", nome="Ácido Cítrico 25KG", unidade="SC",
                         categoria_id=cat_map["Matéria-Prima"].id, categoria_nome="Matéria-Prima", estoque_minimo=3),
                CompItem(codigo="ITEM-0005", nome="Frasco HDPE 1L", unidade="CX",
                         categoria_id=cat_map["Embalagem"].id, categoria_nome="Embalagem", estoque_minimo=10),
                CompItem(codigo="ITEM-0006", nome="Óleo Lubrificante 20L", unidade="LT",
                         categoria_id=cat_map["Manutenção"].id, categoria_nome="Manutenção"),
                CompItem(codigo="ITEM-0007", nome="Papel A4 Resma", unidade="RS",
                         categoria_id=cat_map["Escritório"].id, categoria_nome="Escritório"),
            ]
            db.add_all(itens_seed)
            db.flush()

            # Fornecedores
            forn_seed = [
                CompFornecedor(razao_social="Distribuidora EPI Segurança Ltda", nome_fantasia="EPI Segurança",
                               cnpj="12.345.678/0001-90", email="vendas@episeguranca.com.br",
                               telefone="(11) 3456-7890", contato="Ricardo Alves",
                               categoria_id=cat_map["EPI"].id, categoria_nome="EPI", cidade="São Paulo", estado="SP"),
                CompFornecedor(razao_social="Química Industrial Brasil S/A", nome_fantasia="QuimBrasil",
                               cnpj="98.765.432/0001-10", email="comercial@quimbrasil.com.br",
                               telefone="(11) 4567-8901", contato="Fernanda Costa",
                               categoria_id=cat_map["Matéria-Prima"].id, categoria_nome="Matéria-Prima",
                               cidade="Guarulhos", estado="SP"),
                CompFornecedor(razao_social="Embapack Embalagens Ltda", nome_fantasia="Embapack",
                               cnpj="11.222.333/0001-44", email="pedidos@embapack.com.br",
                               telefone="(19) 3333-4444", contato="João Silva",
                               categoria_id=cat_map["Embalagem"].id, categoria_nome="Embalagem",
                               cidade="Campinas", estado="SP"),
                CompFornecedor(razao_social="Papelaria Central Ltda", nome_fantasia="PapCentral",
                               cnpj="55.666.777/0001-88", email="vendas@papcentral.com.br",
                               telefone="(11) 2222-3333", contato="Marcia Souza",
                               categoria_id=cat_map["Escritório"].id, categoria_nome="Escritório",
                               cidade="São Paulo", estado="SP"),
            ]
            db.add_all(forn_seed)
            db.flush()

            # Requisições demo
            from datetime import date, timedelta
            hoje = date.today()
            # Requisição 1 — múltiplos itens (luvas + óculos)
            req1 = CompRequisicao(numero="REQ-0001", urgencia="alta",
                                   justificativa="Reposição de EPIs urgente", solicitante_id=tecnico.id,
                                   solicitante_nome=tecnico.nome, status="pedido_gerado",
                                   data_necessidade=hoje + timedelta(days=7))
            db.add(req1); db.flush()
            ri1a = CompRequisicaoItem(requisicao_id=req1.id, item_id=itens_seed[0].id,
                item_nome=itens_seed[0].nome, item_unidade=itens_seed[0].unidade,
                item_codigo=itens_seed[0].codigo, quantidade=10, status="pedido_gerado")
            ri1b = CompRequisicaoItem(requisicao_id=req1.id, item_id=itens_seed[1].id,
                item_nome=itens_seed[1].nome, item_unidade=itens_seed[1].unidade,
                item_codigo=itens_seed[1].codigo, quantidade=5, status="pedido_gerado")
            db.add_all([ri1a, ri1b]); db.flush()

            # Requisição 2 — item único cotado
            req2 = CompRequisicao(numero="REQ-0002", urgencia="media",
                                   justificativa="Reposição de estoque", solicitante_id=tecnico.id,
                                   solicitante_nome=tecnico.nome, status="cotando",
                                   data_necessidade=hoje + timedelta(days=15))
            db.add(req2); db.flush()
            ri2a = CompRequisicaoItem(requisicao_id=req2.id, item_id=itens_seed[2].id,
                item_nome=itens_seed[2].nome, item_unidade=itens_seed[2].unidade,
                item_codigo=itens_seed[2].codigo, quantidade=5, status="cotado")
            db.add(ri2a); db.flush()

            # Requisição 3 — aberta, 2 itens
            req3 = CompRequisicao(numero="REQ-0003", urgencia="baixa",
                                   solicitante_id=gestor.id, solicitante_nome=gestor.nome, status="aberta")
            db.add(req3); db.flush()
            ri3a = CompRequisicaoItem(requisicao_id=req3.id, item_id=itens_seed[4].id,
                item_nome=itens_seed[4].nome, item_unidade=itens_seed[4].unidade,
                item_codigo=itens_seed[4].codigo, quantidade=20, status="pendente")
            ri3b = CompRequisicaoItem(requisicao_id=req3.id, item_id=itens_seed[6].id,
                item_nome=itens_seed[6].nome, item_unidade=itens_seed[6].unidade,
                item_codigo=itens_seed[6].codigo, quantidade=3, status="pendente")
            db.add_all([ri3a, ri3b]); db.flush()

            # Cotação para req2
            cot1 = CompCotacao(requisicao_id=req2.id, requisicao_item_id=ri2a.id,
                                fornecedor_id=forn_seed[1].id, fornecedor_nome=forn_seed[1].razao_social,
                                item_id=itens_seed[2].id, item_nome=itens_seed[2].nome,
                                preco_unitario=180.00, quantidade=5, preco_total=900.00,
                                prazo_entrega_dias=10, condicao_pagamento="À vista",
                                selecionada=False, created_by=gestor.id)
            # Cotação selecionada para ri1a
            cot2 = CompCotacao(requisicao_id=req1.id, requisicao_item_id=ri1a.id,
                                fornecedor_id=forn_seed[0].id, fornecedor_nome=forn_seed[0].razao_social,
                                item_id=itens_seed[0].id, item_nome=itens_seed[0].nome,
                                preco_unitario=45.90, quantidade=10, preco_total=459.00,
                                prazo_entrega_dias=5, condicao_pagamento="30 dias",
                                selecionada=True, created_by=gestor.id)
            db.add_all([cot1, cot2]); db.flush()

            # Pedido de compra para ri1a
            pc1 = CompPedido(
                numero="PC-0001", requisicao_id=req1.id, requisicao_numero=req1.numero,
                requisicao_item_id=ri1a.id,
                item_id=itens_seed[0].id, item_nome=itens_seed[0].nome, item_unidade=itens_seed[0].unidade,
                quantidade=10, fornecedor_id=forn_seed[0].id, fornecedor_nome=forn_seed[0].razao_social,
                cotacao_id=cot2.id, preco_unitario=45.90, preco_total=459.00,
                condicao_pagamento="30 dias", prazo_entrega_dias=5,
                previsao_entrega=hoje + timedelta(days=5),
                status="aprovado", aprovado_por_id=admin.id, aprovado_por_nome=admin.nome,
                created_by=gestor.id, created_by_nome=gestor.nome
            )
            db.add(pc1); db.flush()
            db.add(CompHistorico(pedido_id=pc1.id, pedido_numero=pc1.numero,
                                  status_anterior="aguardando_aprovacao", status_novo="aprovado",
                                  usuario_id=admin.id, usuario_nome=admin.nome, observacao="Aprovado"))
            db.commit()
            print("✅ Seed criado com sucesso")
    finally:
        db.close()
    yield

app = FastAPI(title="Compras — Qualimpel ERP", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categorias.router)
app.include_router(itens.router)
app.include_router(fornecedores.router)
app.include_router(requisicoes.router)
app.include_router(pedidos.router)
app.include_router(dashboard.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
