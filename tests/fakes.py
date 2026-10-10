from datetime import datetime
from typing import Optional

from negocio.entidades import Cliente, EstadoPedido, Pedido, Producto
from negocio.interfaces import ClienteDAO, PedidoDAO, ProductoDAO


class ProductoDAOMemoria(ProductoDAO):
    def __init__(self, productos: Optional[list[Producto]] = None):
        self._productos = {p.id: p for p in (productos or [])}

    def listar(self) -> list[Producto]:
        return list(self._productos.values())

    def obtener(self, producto_id: int) -> Optional[Producto]:
        return self._productos.get(producto_id)

    def actualizar_stock(self, producto_id: int, nuevo_stock: int) -> None:
        self._productos[producto_id].stock = nuevo_stock


class ClienteDAOMemoria(ClienteDAO):
    def __init__(self, clientes: Optional[list[Cliente]] = None):
        self._clientes = {c.id: c for c in (clientes or [])}
        self._siguiente_id = max(self._clientes, default=0) + 1

    def crear(self, cliente: Cliente) -> Cliente:
        cliente.id = self._siguiente_id
        self._clientes[cliente.id] = cliente
        self._siguiente_id += 1
        return cliente

    def obtener(self, cliente_id: int) -> Optional[Cliente]:
        return self._clientes.get(cliente_id)

    def actualizar(self, cliente: Cliente) -> None:
        self._clientes[cliente.id] = cliente


class PedidoDAOMemoria(PedidoDAO):
    def __init__(self):
        self._pedidos: dict[int, Pedido] = {}
        self._siguiente_id = 1

    def guardar(self, pedido: Pedido) -> Pedido:
        pedido.id = self._siguiente_id
        self._pedidos[pedido.id] = pedido
        self._siguiente_id += 1
        return pedido

    def obtener(self, pedido_id: int) -> Optional[Pedido]:
        return self._pedidos.get(pedido_id)

    def pendiente_de(self, cliente_id: int) -> Optional[Pedido]:
        for pedido in self._pedidos.values():
            if pedido.cliente_id == cliente_id and pedido.estado == EstadoPedido.PENDIENTE_PAGO:
                return pedido
        return None

    def actualizar_estado(self, pedido_id: int, estado: EstadoPedido) -> None:
        self._pedidos[pedido_id].estado = estado
