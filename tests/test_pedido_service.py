import pytest

from negocio.descuento_service import DescuentoService
from negocio.entidades import Cliente, EstadoPedido, Producto
from negocio.excepciones import PedidoPendienteExistente, StockInsuficiente
from negocio.fidelidad_service import FidelidadService
from negocio.pedido_service import PedidoService
from tests.fakes import ClienteDAOMemoria, PedidoDAOMemoria, ProductoDAOMemoria


def construir_servicio(productos, clientes):
    return PedidoService(
        producto_dao=ProductoDAOMemoria(productos),
        cliente_dao=ClienteDAOMemoria(clientes),
        pedido_dao=PedidoDAOMemoria(),
        descuento_service=DescuentoService(),
        fidelidad_service=FidelidadService(),
    )


def test_crear_pedido_con_stock_insuficiente_lanza_excepcion():
    producto = Producto(id=1, nombre="Espresso StackTrace", precio_base=8_000, stock=2)
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com")
    servicio = construir_servicio([producto], [cliente])

    with pytest.raises(StockInsuficiente):
        servicio.crear_pedido(1, [{"producto_id": 1, "cantidad": 5}])


def test_no_se_puede_crear_pedido_si_hay_uno_pendiente():
    producto = Producto(id=1, nombre="Espresso StackTrace", precio_base=8_000, stock=10)
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com")
    servicio = construir_servicio([producto], [cliente])

    servicio.crear_pedido(1, [{"producto_id": 1, "cantidad": 1}])

    with pytest.raises(PedidoPendienteExistente):
        servicio.crear_pedido(1, [{"producto_id": 1, "cantidad": 1}])


def test_crear_pedido_descuenta_stock():
    producto = Producto(id=1, nombre="Espresso StackTrace", precio_base=8_000, stock=10)
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com")
    servicio = construir_servicio([producto], [cliente])

    servicio.crear_pedido(1, [{"producto_id": 1, "cantidad": 3}])

    assert servicio.producto_dao.obtener(1).stock == 7


def test_pagar_pedido_acumula_monto_y_devpoints():
    producto = Producto(id=1, nombre="Combo BugHunter", precio_base=25_000, stock=10)
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com")
    servicio = construir_servicio([producto], [cliente])

    pedido = servicio.crear_pedido(1, [{"producto_id": 1, "cantidad": 2}])
    servicio.pagar_pedido(pedido.id)

    cliente_actualizado = servicio.cliente_dao.obtener(1)
    assert cliente_actualizado.monto_acumulado == pedido.total
    assert cliente_actualizado.dev_points == pedido.total // 20_000
    assert servicio.pedido_dao.obtener(pedido.id).estado == EstadoPedido.EN_PREPARACION


def test_avanzar_estado_sigue_el_flujo_completo():
    producto = Producto(id=1, nombre="Té Async/Await", precio_base=7_000, stock=10)
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com")
    servicio = construir_servicio([producto], [cliente])

    pedido = servicio.crear_pedido(1, [{"producto_id": 1, "cantidad": 1}])
    servicio.pagar_pedido(pedido.id)

    servicio.avanzar_estado(pedido.id)
    assert servicio.pedido_dao.obtener(pedido.id).estado == EstadoPedido.LISTO

    servicio.avanzar_estado(pedido.id)
    assert servicio.pedido_dao.obtener(pedido.id).estado == EstadoPedido.ENTREGADO
