"""Interfaces de acceso a datos. Las implementa persistencia/ sobre sqlite3."""
from abc import ABC, abstractmethod
from typing import Optional

from negocio.entidades import Cliente, EstadoPedido, Pedido, Producto


class ProductoDAO(ABC):
    @abstractmethod
    def listar(self) -> list[Producto]: ...

    @abstractmethod
    def obtener(self, producto_id: int) -> Optional[Producto]: ...

    @abstractmethod
    def actualizar_stock(self, producto_id: int, nuevo_stock: int) -> None: ...


class ClienteDAO(ABC):
    @abstractmethod
    def crear(self, cliente: Cliente) -> Cliente:
        """Persiste y devuelve el cliente con su id asignado."""

    @abstractmethod
    def obtener(self, cliente_id: int) -> Optional[Cliente]: ...

    @abstractmethod
    def actualizar(self, cliente: Cliente) -> None: ...


class PedidoDAO(ABC):
    @abstractmethod
    def guardar(self, pedido: Pedido) -> Pedido:
        """Persiste el pedido (con sus ítems) y lo devuelve con su id asignado."""

    @abstractmethod
    def obtener(self, pedido_id: int) -> Optional[Pedido]: ...

    @abstractmethod
    def pendiente_de(self, cliente_id: int) -> Optional[Pedido]:
        """Pedido en 'Pendiente de pago' del cliente, o None."""

    @abstractmethod
    def actualizar_estado(self, pedido_id: int, estado: EstadoPedido) -> None: ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> list[Pedido]: ...

    @abstractmethod
    def listar(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]:
        """Todos los pedidos, o solo los del `estado` dado."""
