from negocio.entidades import Producto


class PedidoServiceFalso:
    def listar_menu(self) -> list[Producto]:
        return [
            Producto(id=1, nombre="Espresso StackTrace", precio_base=6000, stock=20),
            Producto(id=2, nombre="Combo BugHunter", precio_base=18000, stock=10),
            Producto(id=3, nombre="Té Async/Await", precio_base=5000, stock=15),
        ]
