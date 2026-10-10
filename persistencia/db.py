import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def conectar(ruta_db: str = "cafe_overflow.db") -> sqlite3.Connection:
    conexion = sqlite3.connect(ruta_db)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar(conexion: sqlite3.Connection) -> None:
    conexion.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conexion.commit()
