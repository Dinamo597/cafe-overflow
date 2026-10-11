import sqlite3
from typing import Optional

from negocio.entidades import Cliente, NivelLealtad
from negocio.daos import ClienteDAO


class ClienteDAOSQLite(ClienteDAO):
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def _mapear(self, fila: sqlite3.Row) -> Cliente:
        return Cliente(
            id=fila["id"],
            nombre=fila["nombre"],
            correo=fila["correo"],
            nivel=NivelLealtad(fila["nivel"]),
            dev_points=fila["dev_points"],
            monto_acumulado=fila["monto_acumulado"],
        )

    def crear(self, cliente: Cliente) -> Cliente:
        cursor = self.conexion.execute(
            "INSERT INTO clientes (nombre, correo, nivel, dev_points, monto_acumulado) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                cliente.nombre,
                cliente.correo,
                cliente.nivel.value,
                cliente.dev_points,
                cliente.monto_acumulado,
            ),
        )
        self.conexion.commit()
        cliente.id = cursor.lastrowid
        return cliente

    def obtener(self, cliente_id: int) -> Optional[Cliente]:
        fila = self.conexion.execute(
            "SELECT * FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        return self._mapear(fila) if fila else None

    def actualizar(self, cliente: Cliente) -> None:
        self.conexion.execute(
            "UPDATE clientes SET nombre = ?, correo = ?, nivel = ?, dev_points = ?, "
            "monto_acumulado = ? WHERE id = ?",
            (
                cliente.nombre,
                cliente.correo,
                cliente.nivel.value,
                cliente.dev_points,
                cliente.monto_acumulado,
                cliente.id,
            ),
        )
        self.conexion.commit()
