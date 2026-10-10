from negocio.entidades import Producto
from negocio.interfaces import ProductoDAO


class CatalogoService:
    def __init__(self, producto_dao: ProductoDAO):
        self.producto_dao = producto_dao

    def listar_menu(self) -> list[Producto]:
        return self.producto_dao.listar()
