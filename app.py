import os
import database as db
import pandas as pd
import streamlit as st

# Inicializa banco de dados
db.init_db()

st.set_page_config(
    page_title="Walls Vídeos | Sistema Pro",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa o estado do carrinho de compras na sessão
if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}

# Estilização CSS personalizada para miniaturas centralizadas (80x80)
st.markdown(
    """
    <style>
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    div[data-testid="stExpander"] {
        border-radius: 8px;
    }
    .thumb-80 img {
        width: 80px !important;
        height: 80px !important;
        object-fit: cover !important;
        object-position: center !important;
        border-radius: 8px !important;
        border: 1px solid #363b4e;
        display: block;
        margin: 0 auto;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# DIÁLOGOS E MODAIS (TELA DO EQUIPAMENTO)
# ==========================================
@st.dialog("📦 Detalhes do Equipamento")
def abrir_modal_detalhes_equipamento(eq):
    st.markdown(f"### {eq['nome']}")

    if eq["imagem"] and os.path.exists(eq["imagem"]):
        st.image(eq["imagem"], use_container_width=True)
    else:
        st.info("Equipamento sem foto cadastrada.")

    st.markdown(f"**Valor por diária:** `R$ {eq['preco']:.2f}`")

    qtd_atual = st.session_state.carrinho.get(eq["id"], {}).get("qtd", 1)

    qtd_modal = st.number_input(
        "Quantidade a adicionar:",
        min_value=1,
        max_value=50,
        value=qtd_atual if qtd_atual > 0 else 1,
        key=f"modal_qtd_{eq['id']}",
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button(
            "🛒 Adicionar ao Carrinho", type="primary", use_container_width=True
        ):
            st.session_state.carrinho[eq["id"]] = {
                "id": eq["id"],
                "nome": eq["nome"],
                "preco": eq["preco"],
                "qtd": qtd_modal,
                "subtotal": qtd_modal * eq["preco"],
            }
            st.success(f"{qtd_modal}x '{eq['nome']}' adicionado ao carrinho!")
            st.rerun()

    with col_m2:
        if eq["id"] in st.session_state.carrinho:
            if st.button("❌ Remover do Carrinho", use_container_width=True):
                del st.session_state.carrinho[eq["id"]]
                st.warning("Item removido do carrinho.")
                st.rerun()


# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

    st.title("Walls Vídeos")
    st.caption("Estruturas, Som & Iluminação")
    st.markdown("---")

    menu_opcao = st.radio(
        "Navegação",
        [
            "🛒 Criar Orçamento / Carrinho",
            "📋 Orçamentos Salvos",
            "📦 Catálogo de Equipamentos",
            "👤 Cadastro de Clientes",
            "📸 Portfólio de Serviços",
        ],
    )

    total_itens_cart = sum(
        item["qtd"] for item in st.session_state.carrinho.values()
    )
    st.markdown("---")
    st.metric("Itens no Carrinho", f"{total_itens_cart} un.")


# ==========================================
# TELA 1: CARRINHO E NOVO ORÇAMENTO
# ==========================================
if menu_opcao == "🛒 Criar Orçamento / Carrinho":
    st.header("🛒 Montar Orçamento")

    col_cli, col_info = st.columns([1, 1])

    with col_cli:
        clientes_cadastrados = db.listar_clientes()
        opcoes_clientes = ["-- Digitar Novo Cliente --"] + [
            c["nome"] for c in clientes_cadastrados
        ]
        cliente_selecionado = st.selectbox("Buscar Cliente", opcoes_clientes)

        if cliente_selecionado == "-- Digitar Novo Cliente --":
            cliente_nome = st.text_input("Nome do Cliente")
            cliente_fone = st.text_input("Telefone / WhatsApp")
        else:
            dados_cli = next(
                c for c in clientes_cadastrados if c["nome"] == cliente_selecionado
            )
            cliente_nome = st.text_input("Nome do Cliente", value=dados_cli["nome"])
            cliente_fone = st.text_input(
                "Telefone / WhatsApp", value=dados_cli["telefone"] or ""
            )

    with col_info:
        data_evento = st.date_input("Data do Evento")
        local_evento = st.text_input("Local / Chácara do Evento")

    st.markdown("---")
    st.subheader("📋 Seleção Rápida de Equipamentos")

    equipamentos = db.listar_equipamentos_completos()

    for eq in equipamentos:
        col_nome, col_preco, col_qtd = st.columns([3, 1.5, 1.5])

        with col_nome:
            st.markdown(f"**{eq['nome']}**")
        with col_preco:
            st.write(f"R$ {eq['preco']:.2f}")
        with col_qtd:
            val_iniciar = st.session_state.carrinho.get(eq["id"], {}).get(
                "qtd", 0
            )
            qtd = st.number_input(
                "Qtd",
                min_value=0,
                max_value=50,
                value=val_iniciar,
                key=f"fast_cart_{eq['id']}",
                label_visibility="collapsed",
            )

            if qtd > 0:
                st.session_state.carrinho[eq["id"]] = {
                    "id": eq["id"],
                    "nome": eq["nome"],
                    "preco": eq["preco"],
                    "qtd": qtd,
                    "subtotal": qtd * eq["preco"],
                }
            elif eq["id"] in st.session_state.carrinho and qtd == 0:
                del st.session_state.carrinho[eq["id"]]

    st.markdown("---")

    itens_lista = list(st.session_state.carrinho.values())
    subtotal = sum(item["subtotal"] for item in itens_lista)

    with st.expander(
        f"🛒 Carrinho de Compras ({len(itens_lista)} itens diferentes)",
        expanded=True,
    ):
        if not itens_lista:
            st.info("Nenhum equipamento adicionado ao carrinho ainda.")
        else:
            df_cart = pd.DataFrame(itens_lista)
            st.dataframe(
                df_cart[["nome", "qtd", "preco", "subtotal"]],
                use_container_width=True,
                column_config={
                    "nome": "Equipamento/Serviço",
                    "qtd": "Qtd",
                    "preco": st.column_config.NumberColumn(
                        "Valor Unit.", format="R$ %.2f"
                    ),
                    "subtotal": st.column_config.NumberColumn(
                        "Subtotal", format="R$ %.2f"
                    ),
                },
            )

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                frete = st.number_input(
                    "Frete / Transporte (R$)",
                    min_value=0.0,
                    step=20.0,
                    value=0.0,
                )
            with col_f2:
                desconto = st.number_input(
                    "Desconto (R$)", min_value=0.0, step=10.0, value=0.0
                )

            total_final = subtotal + frete - desconto
            st.markdown(f"### **Total Final: R$ {total_final:,.2f}**")

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button(
                    "✅ Fechar Pedido / Gerar Orçamento",
                    type="primary",
                    use_container_width=True,
                ):
                    if not cliente_nome.strip():
                        st.error("Por favor, preencha o nome do cliente!")
                    else:
                        orc_id = db.salvar_orcamento_fechado(
                            cliente=cliente_nome.strip(),
                            fone=cliente_fone.strip(),
                            data_ev=str(data_evento),
                            local_ev=local_evento.strip(),
                            subtotal=subtotal,
                            frete=frete,
                            desconto=desconto,
                            total=total_final,
                        )
                        st.success(
                            f"Orçamento #{orc_id} registrado com sucesso!"
                        )
                        st.session_state.carrinho = {}
                        st.balloons()
            with col_b2:
                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    st.session_state.carrinho = {}
                    st.rerun()


# ==========================================
# TELA 2: CONSULTAR ORÇAMENTOS SALVOS
# ==========================================
elif menu_opcao == "📋 Orçamentos Salvos":
    st.header("📋 Orçamentos Registrados")

    orcamentos = db.listar_orcamentos_fechados()

    if not orcamentos:
        st.info("Nenhum orçamento salvo no histórico ainda.")
    else:
        busca_cli = st.text_input("🔍 Buscar por nome do cliente:")
        if busca_cli:
            orcamentos = [
                o
                for o in orcamentos
                if busca_cli.lower() in o["cliente_nome"].lower()
            ]

        for orc in orcamentos:
            with st.expander(
                f"Orçamento #{orc['id']} - {orc['cliente_nome']} | R$"
                f" {orc['total']:,.2f}"
            ):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.write(f"**Cliente:** {orc['cliente_nome']}")
                    st.write(f"**Telefone:** {orc['cliente_fone'] or 'N/I'}")
                    st.write(f"**Data do Evento:** {orc['data_evento']}")
                with col_d2:
                    st.write(f"**Local:** {orc['local_evento'] or 'N/I'}")
                    st.write(f"**Data de Criação:** {orc['criado_em']}")

                st.markdown("---")
                col_v1, col_v2, col_v3, col_v4 = st.columns(4)
                col_v1.metric("Subtotal", f"R$ {orc['subtotal']:.2f}")
                col_v2.metric("Frete", f"R$ {orc['frete']:.2f}")
                col_v3.metric("Desconto", f"R$ {orc['desconto']:.2f}")
                col_v4.metric("TOTAL", f"R$ {orc['total']:.2f}")


# ==========================================
# TELA 3: CATÁLOGO DE EQUIPAMENTOS
# ==========================================
elif menu_opcao == "📦 Catálogo de Equipamentos":
    st.header("📦 Catálogo de Equipamentos e Serviços")

    with st.expander("➕ Cadastrar Novo Equipamento", expanded=False):
        with st.form("form_novo_eq_cat", clear_on_submit=True):
            nome_eq = st.text_input("Nome do Equipamento / Serviço *")
            preco_eq = st.number_input(
                "Preço da Diária (R$)", min_value=0.0, step=10.0
            )
            foto_eq = st.file_uploader(
                "Foto do Equipamento", type=["jpg", "jpeg", "png"]
            )

            if st.form_submit_button(
                "Salvar no Catálogo", use_container_width=True
            ):
                if not nome_eq.strip():
                    st.error("Informe o nome do equipamento!")
                else:
                    bytes_img = foto_eq.read() if foto_eq else None
                    nome_img = foto_eq.name if foto_eq else None
                    db.salvar_novo_equipamento(
                        nome=nome_eq.strip(),
                        preco=preco_eq,
                        arquivo_bytes=bytes_img,
                        nome_original=nome_img,
                    )
                    st.success(f"'{nome_eq}' adicionado ao catálogo!")
                    st.rerun()

    with st.expander("📷 Atualizar Foto de Item Existente", expanded=False):
        equipamentos_lista = db.listar_equipamentos_completos()
        if equipamentos_lista:
            item_sel = st.selectbox(
                "Selecione o equipamento:",
                options=equipamentos_lista,
                format_func=lambda x: x["nome"],
                key="sel_att_foto",
            )
            foto_nova = st.file_uploader(
                "Nova Foto", type=["jpg", "jpeg", "png"], key="up_att"
            )
            if st.button("Atualizar Foto", type="primary"):
                if foto_nova and item_sel:
                    db.atualizar_imagem_equipamento(
                        equipamento_id=item_sel["id"],
                        arquivo_bytes=foto_nova.read(),
                        nome_original=foto_nova.name,
                    )
                    st.success("Foto atualizada!")
                    st.rerun()

    st.markdown("---")

    col_tit, col_opt = st.columns([2, 1])
    with col_tit:
        st.subheader("Equipamentos Cadastrados")
    with col_opt:
        modo_cat = st.radio(
            "Modo de Exibição:",
            ["📋 Lista (sem foto)", "🖼️ Grade (com foto)"],
            horizontal=True,
            index=0,
            key="modo_cat_view",
        )

    equipamentos = db.listar_equipamentos_completos()

    if equipamentos:
        if modo_cat == "📋 Lista (sem foto)":
            for eq in equipamentos:
                with st.container(border=True):
                    col_nome_l, col_preco_l, col_btn_l = st.columns([4, 2, 2])
                    with col_nome_l:
                        st.markdown(f"**{eq['nome']}**")
                    with col_preco_l:
                        st.markdown(f"`R$ {eq['preco']:.2f}` / diária")
                    with col_btn_l:
                        if st.button(
                            "🔎 Detalhes / Adicionar",
                            key=f"btn_det_list_{eq['id']}",
                            use_container_width=True,
                        ):
                            abrir_modal_detalhes_equipamento(eq)

        else:
            cols = st.columns(4)
            for idx, eq in enumerate(equipamentos):
                col = cols[idx % 4]
                with col:
                    with st.container(border=True):
                        if eq["imagem"] and os.path.exists(eq["imagem"]):
                            st.markdown(
                                '<div class="thumb-80">', unsafe_allow_html=True
                            )
                            st.image(eq["imagem"])
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.caption("📷 *Sem foto*")

                        st.markdown(
                            f"<div style='text-align: center;'><b>{eq['nome']}</b><br><code>R$"
                            f" {eq['preco']:.2f}</code></div>",
                            unsafe_allow_html=True,
                        )

                        st.write("")
                        if st.button(
                            "🔎 Ver / Adicionar",
                            key=f"btn_det_grid_{eq['id']}",
                            use_container_width=True,
                        ):
                            abrir_modal_detalhes_equipamento(eq)

    else:
        st.info("Nenhum equipamento cadastrado no catálogo.")


# ==========================================
# TELA 4: CADASTRO DE CLIENTES
# ==========================================
elif menu_opcao == "👤 Cadastro de Clientes":
    st.header("👤 Gerenciamento de Clientes")

    with st.expander("➕ Cadastrar Novo Cliente", expanded=False):
        with st.form("form_novo_cliente", clear_on_submit=True):
            nome = st.text_input("Nome Completo *")
            telefone = st.text_input("Telefone / WhatsApp")
            email = st.text_input("E-mail")
            cidade = st.text_input("Cidade")
            obs = st.text_area("Observações")

            if st.form_submit_button(
                "Salvar Cliente", use_container_width=True
            ):
                if not nome.strip():
                    st.error("Informe o nome do cliente!")
                else:
                    db.salvar_cliente(
                        nome.strip(),
                        telefone.strip(),
                        email.strip(),
                        cidade.strip(),
                        obs.strip(),
                    )
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                    st.rerun()

    clientes = db.listar_clientes()
    if clientes:
        lista_dados = [
            {
                "Nome": c["nome"],
                "Telefone": c["telefone"],
                "Cidade": c["cidade"],
                "E-mail": c["email"],
                "Observações": c["observacoes"],
            }
            for c in clientes
        ]
        st.dataframe(pd.DataFrame(lista_dados), use_container_width=True)
    else:
        st.info("Nenhum cliente cadastrado.")


# ==========================================
# TELA 5: PORTFÓLIO DE SERVIÇOS
# ==========================================
elif menu_opcao == "📸 Portfólio de Serviços":
    st.header("📸 Portfólio de Fotos de Eventos")

    with st.expander("📸 Enviar Foto do Evento", expanded=False):
        with st.form("form_foto", clear_on_submit=True):
            titulo_foto = st.text_input("Título / Nome do Evento *")
            categoria = st.selectbox(
                "Categoria",
                [
                    "Som & Iluminação",
                    "Estruturas & Boates",
                    "Painel LED",
                    "Casamentos",
                    "Outros",
                ],
            )
            foto_upload = st.file_uploader(
                "Imagem (JPG / PNG)", type=["jpg", "jpeg", "png"]
            )
            descricao_foto = st.text_area("Descrição do Setup")

            if st.form_submit_button("Salvar Foto", use_container_width=True):
                if not titulo_foto.strip() or foto_upload is None:
                    st.error("Preencha o título e selecione uma foto!")
                else:
                    db.salvar_foto_servico(
                        titulo=titulo_foto.strip(),
                        categoria=categoria,
                        arquivo_bytes=foto_upload.read(),
                        nome_original=foto_upload.name,
                        descricao=descricao_foto.strip(),
                    )
                    st.success("Foto salva no portfólio!")
                    st.rerun()

    fotos = db.listar_fotos_servicos()
    if fotos:
        cols = st.columns(2)
        for idx, foto in enumerate(fotos):
            col = cols[idx % 2]
            with col:
                if os.path.exists(foto["caminho_arquivo"]):
                    st.image(foto["caminho_arquivo"], use_container_width=True)
                    st.caption(
                        f"**{foto['titulo']}**"
                        f" ({foto['categoria']})\n\n{foto['descricao']}"
                    )
    else:
        st.info("Nenhuma foto cadastrada no portfólio.")