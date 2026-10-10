from typing import Optional

from negocio.entidades import Cliente, Producto


class PedidoServiceFalso:
    def __init__(self):
        self._clientes: dict[int, Cliente] = {}
        self._siguiente_id = 1

    def listar_menu(self) -> list[Producto]:
        return [
            Producto(id=1, nombre="Espresso StackTrace", precio_base=6000, stock=20),
            Producto(id=2, nombre="Combo BugHunter", precio_base=18000, stock=10),
            Producto(id=3, nombre="Té Async/Await", precio_base=5000, stock=15),
        ]

    def crear_cliente(self, nombre: str, correo: str) -> Cliente:
        cliente = Cliente(nombre=nombre, correo=correo, id=self._siguiente_id)
        self._clientes[cliente.id] = cliente
        self._siguiente_id += 1
        return cliente

    def obtener_cliente(self, cliente_id: int) -> Optional[Cliente]:
        return self._clientes.get(cliente_id)
