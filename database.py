import os
import sqlite3

DB_PATH = "data/orcamentos.db"
PASTA_IMAGENS = "data/imagens"


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(PASTA_IMAGENS, exist_ok=True)

    conn = conectar()
    cursor = conn.cursor()

    # 1. Tabela de Equipamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            imagem TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE equipamentos ADD COLUMN imagem TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # 2. Tabela de Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            cidade TEXT,
            observacoes TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Tabela de Fotos de Serviços (Portfólio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotos_servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT,
            caminho_arquivo TEXT NOT NULL,
            descricao TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Tabela de Orçamentos Fechados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orcamentos_fechados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            cliente_fone TEXT,
            data_evento TEXT,
            local_evento TEXT,
            subtotal REAL,
            frete REAL,
            desconto REAL,
            total REAL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Popula equipamentos iniciais
    cursor.execute("SELECT COUNT(*) FROM equipamentos")
    if cursor.fetchone()[0] == 0:
        itens_iniciais = [
            ("Estrutura Grid Q25 4x4m", 450.00, None),
            ("Par LED RGBW 3W (Par)", 120.00, None),
            ("Moving Head Beam 230W (Par)", 350.00, None),
            ('Caixa Alta RCF ART 715 (Par)', 300.00, None),
            ('Subwoofer Ativo 18" (Par)', 400.00, None),
            ("Máquina de Fumaça 1500W", 100.00, None),
        ]
        cursor.executemany(
            "INSERT INTO equipamentos (nome, preco, imagem) VALUES (?, ?, ?)",
            itens_iniciais,
        )
        conn.commit()

    conn.close()


# --- CLIENTES ---


def salvar_cliente(nome, telefone, email, cidade, obs):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO clientes (nome, telefone, email, cidade, observacoes)
        VALUES (?, ?, ?, ?, ?)
    """,
        (nome, telefone, email, cidade, obs),
    )
    conn.commit()
    conn.close()


def listar_clientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, telefone, email, cidade, observacoes FROM clientes"
        " ORDER BY nome ASC"
    )
    clientes = cursor.fetchall()
    conn.close()
    return [dict(cli) for cli in clientes]


# --- EQUIPAMENTOS ---


def listar_equipamentos_completos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, preco, imagem FROM equipamentos ORDER BY nome ASC"
    )
    equipamentos = cursor.fetchall()
    conn.close()
    return [dict(eq) for eq in equipamentos]


def salvar_novo_equipamento(
    nome, preco, arquivo_bytes=None, nome_original=None
):
    caminho_relativo = None
    if arquivo_bytes and nome_original:
        caminho_relativo = os.path.join(
            PASTA_IMAGENS, f"eq_new_{nome_original}"
        )
        with open(caminho_relativo, "wb") as f:
            f.write(arquivo_bytes)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO equipamentos (nome, preco, imagem) VALUES (?, ?, ?)",
        (nome, preco, caminho_relativo),
    )
    conn.commit()
    conn.close()


def atualizar_imagem_equipamento(
    equipamento_id, arquivo_bytes, nome_original
):
    caminho_relativo = os.path.join(
        PASTA_IMAGENS, f"eq_{equipamento_id}_{nome_original}"
    )
    with open(caminho_relativo, "wb") as f:
        f.write(arquivo_bytes)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE equipamentos SET imagem = ? WHERE id = ?",
        (caminho_relativo, equipamento_id),
    )
    conn.commit()
    conn.close()


# --- PORTFÓLIO ---


def salvar_foto_servico(
    titulo, categoria, arquivo_bytes, nome_original, descricao
):
    caminho_relativo = os.path.join(PASTA_IMAGENS, f"srv_{nome_original}")
    with open(caminho_relativo, "wb") as f:
        f.write(arquivo_bytes)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO fotos_servicos (titulo, categoria, caminho_arquivo, descricao)
        VALUES (?, ?, ?, ?)
    """,
        (titulo, categoria, caminho_relativo, descricao),
    )
    conn.commit()
    conn.close()


def listar_fotos_servicos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, titulo, categoria, caminho_arquivo, descricao FROM"
        " fotos_servicos ORDER BY id DESC"
    )
    fotos = cursor.fetchall()
    conn.close()
    return [dict(foto) for foto in fotos]


# --- ORÇAMENTOS ---


def salvar_orcamento_fechado(
    cliente, fone, data_ev, local_ev, subtotal, frete, desconto, total
):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orcamentos_fechados 
        (cliente_nome, cliente_fone, data_evento, local_evento, subtotal, frete, desconto, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (cliente, fone, data_ev, local_ev, subtotal, frete, desconto, total),
    )
    conn.commit()
    orc_id = cursor.lastrowid
    conn.close()
    return orc_id


def listar_orcamentos_fechados():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, cliente_nome, cliente_fone, data_evento, local_evento, 
               subtotal, frete, desconto, total, criado_em 
        FROM orcamentos_fechados 
        ORDER BY id DESC
    """)
    orcamentos = cursor.fetchall()
    conn.close()
    return [dict(orc) for orc in orcamentos]