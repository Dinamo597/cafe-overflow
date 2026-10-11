from datetime import datetime, timezone

from negocio.daos import ClienteDAO, PedidoDAO, ProductoDAO
from negocio.descuento_service import DescuentoService
from negocio.entidades import Cotizacion, EstadoPedido, ItemPedido, Pedido
from negocio.excepciones import ErrorNegocio, PagoRechazado, PedidoPendienteExistente, StockInsuficiente
from negocio.fidelidad_service import PESOS_POR_DEVPOINT, FidelidadService
from negocio.pasarela import PasarelaPago


class PedidoService:
    def __init__(
        self,
        producto_dao: ProductoDAO,
        cliente_dao: ClienteDAO,
        pedido_dao: PedidoDAO,
        descuento_service: DescuentoService,
        fidelidad_service: FidelidadService,
        pasarela_pago: PasarelaPago,
    ):
        self.producto_dao = producto_dao
        self.cliente_dao = cliente_dao
        self.pedido_dao = pedido_dao
        self.descuento_service = descuento_service
        self.fidelidad_service = fidelidad_service
        self.pasarela_pago = pasarela_pago

    def _armar_items(self, items: list[dict]) -> tuple[list[ItemPedido], int]:
        armados = []
        subtotal = 0
        for entrada in items:
            producto = self.producto_dao.obtener(entrada["producto_id"])
            cantidad = entrada["cantidad"]
            if cantidad > producto.stock:
                raise StockInsuficiente(producto.id, cantidad, producto.stock)
            armados.append(ItemPedido(producto.id, cantidad, producto.precio_base))
            subtotal += producto.precio_base * cantidad
        return armados, subtotal

    def cotizar(self, cliente_id: int, items: list[dict], devpoints: int = 0) -> Cotizacion:
        cliente = self.cliente_dao.obtener(cliente_id)
        _, subtotal = self._armar_items(items)
        descuento_nivel = self.descuento_service.calcular_descuento(cliente.nivel, subtotal)
        if devpoints:
            self.fidelidad_service.validar_redencion(cliente, devpoints)
        descuento_devpoints = self.fidelidad_service.valor_redencion(devpoints)
        total = max(subtotal - descuento_nivel - descuento_devpoints, 0)
        return Cotizacion(
            subtotal=subtotal,
            descuento_nivel=descuento_nivel,
            descuento_devpoints=descuento_devpoints,
            total=total,
            devpoints_a_ganar=total // PESOS_POR_DEVPOINT,
        )

    def crear_pedido(self, cliente_id: int, items: list[dict], devpoints: int = 0) -> Pedido:
        pendiente = self.pedido_dao.pendiente_de(cliente_id)
        if pendiente:
            raise PedidoPendienteExistente(cliente_id, pendiente.id)

        items_armados, _ = self._armar_items(items)
        cotizacion = self.cotizar(cliente_id, items, devpoints)

        for item in items_armados:
            producto = self.producto_dao.obtener(item.producto_id)
            self.producto_dao.actualizar_stock(producto.id, producto.stock - item.cantidad)

        pedido = Pedido(
            id=None,
            cliente_id=cliente_id,
            items=items_armados,
            estado=EstadoPedido.PENDIENTE_PAGO,
            total=cotizacion.total,
            fecha=datetime.now(timezone.utc),
            dev_points_redimidos=devpoints,
        )
        return self.pedido_dao.guardar(pedido)

    def pagar_pedido(self, pedido_id: int) -> Pedido:
        pedido = self.pedido_dao.obtener(pedido_id)
        if pedido.estado != EstadoPedido.PENDIENTE_PAGO:
            raise ErrorNegocio(f"El pedido {pedido.id} no está pendiente de pago")
        if not self.pasarela_pago.procesar(pedido.total):
            raise PagoRechazado(pedido.id, pedido.total)

        if pedido.dev_points_redimidos:
            cliente = self.cliente_dao.obtener(pedido.cliente_id)
            self.fidelidad_service.redimir(cliente, pedido.dev_points_redimidos)
            self.cliente_dao.actualizar(cliente)

        pedido.estado = EstadoPedido.EN_PREPARACION
        self.pedido_dao.actualizar_estado(pedido.id, pedido.estado)
        return pedido

    def avanzar_estado(self, pedido_id: int) -> Pedido:
        siguiente = {
            EstadoPedido.EN_PREPARACION: EstadoPedido.LISTO,
            EstadoPedido.LISTO: EstadoPedido.ENTREGADO,
        }
        pedido = self.pedido_dao.obtener(pedido_id)
        nuevo_estado = siguiente.get(pedido.estado)
        if nuevo_estado is None:
            return pedido

        pedido.estado = nuevo_estado
        self.pedido_dao.actualizar_estado(pedido.id, nuevo_estado)

        if nuevo_estado == EstadoPedido.ENTREGADO:
            cliente = self.cliente_dao.obtener(pedido.cliente_id)
            pedido.dev_points_otorgados = self.fidelidad_service.registrar_compra(cliente, pedido.total)
            self.cliente_dao.actualizar(cliente)

        return pedido

    def listar_pedidos(self, cliente_id: int) -> list[Pedido]:
        return self.pedido_dao.listar_por_cliente(cliente_id)
