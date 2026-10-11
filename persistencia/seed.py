import sqlite3

PRODUCTOS_INICIALES = [
    ("Espresso StackTrace", 8_000, 50),
    ("Combo BugHunter", 25_000, 30),
    ("Té Async/Await", 7_000, 40),
]


def sembrar(conexion: sqlite3.Connection) -> None:
    existentes = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if existentes:
        return
    conexion.executemany(
        "INSERT INTO productos (nombre, precio_base, stock) VALUES (?, ?, ?)",
        PRODUCTOS_INICIALES,
    )
    conexion.commit()
