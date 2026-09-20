import sqlite3
from datetime import datetime, timezone
from .config import DB_PATH
SCHEMA="""CREATE TABLE IF NOT EXISTS generations(
id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,path TEXT NOT NULL,model TEXT NOT NULL,
prompt TEXT NOT NULL,width INTEGER NOT NULL,height INTEGER NOT NULL,quality TEXT NOT NULL,output_format TEXT NOT NULL,
duration REAL NOT NULL,file_size INTEGER NOT NULL,input_tokens INTEGER,text_tokens INTEGER,image_input_tokens INTEGER,
output_tokens INTEGER,total_tokens INTEGER,cost_usd REAL,operation TEXT DEFAULT 'generate',source_path TEXT);"""
def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True); con=sqlite3.connect(DB_PATH); con.execute("PRAGMA journal_mode=WAL"); con.execute(SCHEMA)
    cols={r[1] for r in con.execute("PRAGMA table_info(generations)")}
    if "operation" not in cols: con.execute("ALTER TABLE generations ADD COLUMN operation TEXT DEFAULT 'generate'")
    if "source_path" not in cols: con.execute("ALTER TABLE generations ADD COLUMN source_path TEXT")
    return con
def add_generation(r):
    with connect() as con:
        con.execute("""INSERT INTO generations(created_at,path,model,prompt,width,height,quality,output_format,duration,file_size,
        input_tokens,text_tokens,image_input_tokens,output_tokens,total_tokens,cost_usd,operation,source_path)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (datetime.now(timezone.utc).isoformat(),r.path,r.model,r.prompt,r.width,r.height,r.quality,r.output_format,r.duration,
         r.file_size,r.input_tokens,r.text_tokens,r.image_input_tokens,r.output_tokens,r.total_tokens,r.cost_usd,r.operation,r.source_path))
def recent(limit=100):
    with connect() as con: con.row_factory=sqlite3.Row; return list(con.execute("SELECT * FROM generations ORDER BY id DESC LIMIT ?",(limit,)))
def totals():
    with connect() as con:
        r=con.execute("SELECT COUNT(*),COALESCE(SUM(cost_usd),0),COALESCE(SUM(total_tokens),0) FROM generations").fetchone()
        return {"count":r[0],"cost":r[1],"tokens":r[2]}
