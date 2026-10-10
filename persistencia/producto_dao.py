import sqlite3
from typing import Optional

from negocio.entidades import Producto
from negocio.interfaces import ProductoDAO


class ProductoDAOSQLite(ProductoDAO):
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def _mapear(self, fila: sqlite3.Row) -> Producto:
        return Producto(
            id=fila["id"],
            nombre=fila["nombre"],
            precio_base=fila["precio_base"],
            stock=fila["stock"],
        )

    def listar(self) -> list[Producto]:
        filas = self.conexion.execute("SELECT * FROM productos").fetchall()
        return [self._mapear(f) for f in filas]

    def obtener(self, producto_id: int) -> Optional[Producto]:
        fila = self.conexion.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()
        return self._mapear(fila) if fila else None

    def actualizar_stock(self, producto_id: int, nuevo_stock: int) -> None:
        self.conexion.execute(
            "UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id)
        )
        self.conexion.commit()
