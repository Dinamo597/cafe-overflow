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
    def crear(self, cliente: Cliente) -> Cliente: ...

    @abstractmethod
    def obtener(self, cliente_id: int) -> Optional[Cliente]: ...

    @abstractmethod
    def actualizar(self, cliente: Cliente) -> None: ...


class PedidoDAO(ABC):
    @abstractmethod
    def guardar(self, pedido: Pedido) -> Pedido: ...

    @abstractmethod
    def obtener(self, pedido_id: int) -> Optional[Pedido]: ...

    @abstractmethod
    def pendiente_de(self, cliente_id: int) -> Optional[Pedido]: ...

    @abstractmethod
    def actualizar_estado(self, pedido_id: int, estado: EstadoPedido) -> None: ...
