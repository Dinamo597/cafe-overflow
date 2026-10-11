"""Composición de la capa de negocio para la API.

Reúne CatalogoService, ClienteService y PedidoService en una sola fachada con
las firmas que consume `api/servidor.py`. No contiene reglas de negocio: solo
cablea servicios y traduce "no existe" a NoEncontrado.
"""
from typing import Optional

from negocio.catalogo_service import CatalogoService
from negocio.cliente_service import ClienteService
from negocio.daos import ClienteDAO, PedidoDAO, ProductoDAO
from negocio.descuento_service import DescuentoService
from negocio.entidades import Cliente, Cotizacion, EstadoPedido, Pedido, Producto
from negocio.excepciones import NoEncontrado
from negocio.fidelidad_service import FidelidadService
from negocio.pasarela import PasarelaPago, PasarelaSimulada
from negocio.pedido_service import PedidoService
from persistencia.cliente_dao import ClienteDAOSQLite
from persistencia.db import conectar, inicializar
from persistencia.pedido_dao import PedidoDAOSQLite
from persistencia.producto_dao import ProductoDAOSQLite
from persistencia.seed import sembrar


class ServicioApi:
    def __init__(self, producto_dao: ProductoDAO, cliente_dao: ClienteDAO, pedido_dao: PedidoDAO,
                 pasarela: PasarelaPago):
        self._productos = producto_dao
        self._clientes = cliente_dao
        self._pedidos = pedido_dao
        self._catalogo = CatalogoService(producto_dao)
        self._cliente_service = ClienteService(cliente_dao)
        self._pedido_service = PedidoService(
            producto_dao, cliente_dao, pedido_dao, DescuentoService(), FidelidadService(), pasarela)

    def listar_menu(self) -> list[Producto]:
        return self._catalogo.listar_menu()

    def crear_cliente(self, nombre: str, correo: str) -> Cliente:
        return self._cliente_service.crear_cliente(nombre, correo)

    def obtener_cliente(self, cliente_id: int) -> Optional[Cliente]:
        return self._cliente_service.obtener_cliente(cliente_id)

    def cotizar(self, cliente_id: int, items: list[dict], devpoints_a_redimir: int = 0) -> Cotizacion:
        self._exigir_cliente(cliente_id)
        return self._pedido_service.cotizar(cliente_id, self._a_dicts(items), devpoints_a_redimir)

    def crear_pedido(self, cliente_id: int, items: list[dict], devpoints_a_redimir: int = 0) -> Pedido:
        self._exigir_cliente(cliente_id)
        return self._pedido_service.crear_pedido(cliente_id, self._a_dicts(items), devpoints_a_redimir)

    def pagar_pedido(self, pedido_id: int) -> Pedido:
        self._exigir_pedido(pedido_id)
        return self._pedido_service.pagar_pedido(pedido_id)

    def avanzar_estado(self, pedido_id: int) -> Pedido:
        self._exigir_pedido(pedido_id)
        return self._pedido_service.avanzar_estado(pedido_id)

    def listar_pedidos(self, cliente_id: int) -> list[Pedido]:
        self._exigir_cliente(cliente_id)
        return self._pedido_service.listar_pedidos(cliente_id)

    def listar_todos(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]:
        return self._pedidos.listar(estado)

    # --- adaptación ------------------------------------------------------
    def _a_dicts(self, items: list[dict]) -> list[dict]:
        for item in items:
            if self._productos.obtener(item["producto_id"]) is None:
                raise NoEncontrado(f"Producto {item['producto_id']} no encontrado")
        return items

    def _exigir_cliente(self, cliente_id: int) -> None:
        if self._clientes.obtener(cliente_id) is None:
            raise NoEncontrado("Cliente no encontrado")

    def _exigir_pedido(self, pedido_id: int) -> None:
        if self._pedidos.obtener(pedido_id) is None:
            raise NoEncontrado("Pedido no encontrado")


def crear_servicio(ruta_db: str = "cafe_overflow.db", pasarela: Optional[PasarelaPago] = None) -> ServicioApi:
    """Abre (o crea) la base SQLite, siembra el menú y arma el servicio."""
    con = conectar(ruta_db, check_same_thread=False)
    inicializar(con)
    sembrar(con)
    return ServicioApi(ProductoDAOSQLite(con), ClienteDAOSQLite(con), PedidoDAOSQLite(con),
                       pasarela or PasarelaSimulada())
