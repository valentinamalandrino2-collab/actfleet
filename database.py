"""
ActuarialFleet — database layer (SQLite via SQLAlchemy)
"""
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

DB_PATH = "actfleet.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS flotte (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                provincia TEXT NOT NULL,
                nveic INTEGER DEFAULT 50,
                cilindrata TEXT DEFAULT 'media',
                uso TEXT DEFAULT 'promiscuo',
                scadenza TEXT,
                referente TEXT,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sinistri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flotta_id INTEGER,
                targa TEXT NOT NULL,
                data_sinistro TEXT,
                tipo TEXT DEFAULT 'RCA',
                riserva REAL DEFAULT 0,
                pagato REAL DEFAULT 0,
                stato TEXT DEFAULT 'aperto',
                descrizione TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (flotta_id) REFERENCES flotte(id)
            )
        """))

# ── FLOTTE ──
def get_flotte() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM flotte ORDER BY created_at DESC", engine)

def add_flotta(data: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO flotte (nome, provincia, nveic, cilindrata, uso, scadenza, referente, note)
            VALUES (:nome, :provincia, :nveic, :cilindrata, :uso, :scadenza, :referente, :note)
        """), data)

def delete_flotta(fid: int):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sinistri WHERE flotta_id = :id"), {"id": fid})
        conn.execute(text("DELETE FROM flotte WHERE id = :id"), {"id": fid})

def import_flotte(df: pd.DataFrame):
    col_map = {
        "nome": ["nome", "name"],
        "provincia": ["provincia", "prov", "province"],
        "nveic": ["veicoli", "nveicoli", "n_veicoli", "vehicles", "nveic"],
        "cilindrata": ["cilindrata", "cil"],
        "uso": ["uso", "use"],
        "scadenza": ["scadenza", "scad", "expiry"],
        "referente": ["referente", "ref"],
        "note": ["note", "notes"],
    }
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    mapped = {}
    for field, aliases in col_map.items():
        for a in aliases:
            if a in df.columns:
                mapped[field] = df[a]
                break
        if field not in mapped:
            mapped[field] = ""
    result = pd.DataFrame(mapped)
    result["nveic"] = pd.to_numeric(result.get("nveic", 50), errors="coerce").fillna(50).astype(int)
    for _, row in result.iterrows():
        add_flotta({
            "nome": str(row.get("nome", "Importata")),
            "provincia": str(row.get("provincia", "GEN")).upper()[:3],
            "nveic": int(row.get("nveic", 50)),
            "cilindrata": str(row.get("cilindrata", "media")),
            "uso": str(row.get("uso", "promiscuo")),
            "scadenza": str(row.get("scadenza", "")),
            "referente": str(row.get("referente", "")),
            "note": str(row.get("note", "")),
        })
    return len(result)

# ── SINISTRI ──
def get_sinistri(flotta_id=None, stato=None) -> pd.DataFrame:
    q = "SELECT s.*, f.nome as flotta_nome FROM sinistri s LEFT JOIN flotte f ON s.flotta_id = f.id WHERE 1=1"
    params = {}
    if flotta_id:
        q += " AND s.flotta_id = :fid"
        params["fid"] = flotta_id
    if stato:
        q += " AND s.stato = :stato"
        params["stato"] = stato
    q += " ORDER BY s.created_at DESC"
    return pd.read_sql(text(q), engine, params=params)

def add_sinistro(data: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sinistri (flotta_id, targa, data_sinistro, tipo, riserva, pagato, stato, descrizione)
            VALUES (:flotta_id, :targa, :data_sinistro, :tipo, :riserva, :pagato, :stato, :descrizione)
        """), data)

def delete_sinistro(sid: int):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sinistri WHERE id = :id"), {"id": sid})

def import_sinistri(df: pd.DataFrame, flotte_df: pd.DataFrame):
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    count = 0
    for _, row in df.iterrows():
        nome_f = str(row.get("flotta", row.get("nome", "")))
        match = flotte_df[flotte_df["nome"].str.lower().str.contains(nome_f.lower(), na=False)]
        fid = int(match.iloc[0]["id"]) if not match.empty else None
        add_sinistro({
            "flotta_id": fid,
            "targa": str(row.get("targa", row.get("plate", ""))).upper(),
            "data_sinistro": str(row.get("data_sinistro", row.get("data", ""))),
            "tipo": str(row.get("tipo", row.get("type", "RCA"))),
            "riserva": float(row.get("riserva", row.get("reserve", 0)) or 0),
            "pagato": float(row.get("pagato", row.get("paid", 0)) or 0),
            "stato": str(row.get("stato", row.get("status", "aperto"))),
            "descrizione": str(row.get("descrizione", row.get("description", row.get("note", "")))),
        })
        count += 1
    return count

init_db()
