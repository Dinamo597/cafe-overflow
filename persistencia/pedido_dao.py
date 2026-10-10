import sqlite3
from datetime import datetime
from typing import Optional

from negocio.entidades import EstadoPedido, ItemPedido, Pedido
from negocio.daos import PedidoDAO


class PedidoDAOSQLite(PedidoDAO):
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def _items_de(self, pedido_id: int) -> list[ItemPedido]:
        filas = self.conexion.execute(
            "SELECT * FROM items_pedido WHERE pedido_id = ?", (pedido_id,)
        ).fetchall()
        return [
            ItemPedido(
                producto_id=f["producto_id"],
                cantidad=f["cantidad"],
                precio_unitario=f["precio_unitario"],
            )
            for f in filas
        ]

    def _mapear(self, fila: sqlite3.Row) -> Pedido:
        return Pedido(
            id=fila["id"],
            cliente_id=fila["cliente_id"],
            items=self._items_de(fila["id"]),
            estado=EstadoPedido(fila["estado"]),
            total=fila["total"],
            fecha=datetime.fromisoformat(fila["fecha"]),
            dev_points_redimidos=fila["dev_points_redimidos"],
            dev_points_otorgados=fila["dev_points_otorgados"],
        )

    def guardar(self, pedido: Pedido) -> Pedido:
        cursor = self.conexion.execute(
            "INSERT INTO pedidos (cliente_id, estado, total, dev_points_redimidos, "
            "dev_points_otorgados, fecha) VALUES (?, ?, ?, ?, ?, ?)",
            (
                pedido.cliente_id,
                pedido.estado.value,
                pedido.total,
                pedido.dev_points_redimidos,
                pedido.dev_points_otorgados,
                pedido.fecha.isoformat(),
            ),
        )
        pedido.id = cursor.lastrowid
        for item in pedido.items:
            self.conexion.execute(
                "INSERT INTO items_pedido (pedido_id, producto_id, cantidad, precio_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido.id, item.producto_id, item.cantidad, item.precio_unitario),
            )
        self.conexion.commit()
        return pedido

    def obtener(self, pedido_id: int) -> Optional[Pedido]:
        fila = self.conexion.execute(
            "SELECT * FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        return self._mapear(fila) if fila else None

    def pendiente_de(self, cliente_id: int) -> Optional[Pedido]:
        fila = self.conexion.execute(
            "SELECT * FROM pedidos WHERE cliente_id = ? AND estado = ?",
            (cliente_id, EstadoPedido.PENDIENTE_PAGO.value),
        ).fetchone()
        return self._mapear(fila) if fila else None

    def actualizar_estado(self, pedido_id: int, estado: EstadoPedido) -> None:
        self.conexion.execute(
            "UPDATE pedidos SET estado = ? WHERE id = ?", (estado.value, pedido_id)
        )
        self.conexion.commit()

    def listar_por_cliente(self, cliente_id: int) -> list[Pedido]:
        filas = self.conexion.execute(
            "SELECT * FROM pedidos WHERE cliente_id = ? ORDER BY fecha", (cliente_id,)
        ).fetchall()
        return [self._mapear(f) for f in filas]

    def listar(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]:
        if estado is None:
            filas = self.conexion.execute("SELECT * FROM pedidos ORDER BY fecha").fetchall()
        else:
            filas = self.conexion.execute(
                "SELECT * FROM pedidos WHERE estado = ? ORDER BY fecha", (estado.value,)
            ).fetchall()
        return [self._mapear(f) for f in filas]
