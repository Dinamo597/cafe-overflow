"""Servicio en memoria con las mismas firmas que tendrá PedidoService.

Sirve para desarrollar y probar api/ y presentation/ sin esperar a negocio/
y persistencia/. Devuelve entidades de negocio.entidades, nunca JSON.
"""
from typing import Optional

from negocio.entidades import (
    Cliente, Cotizacion, EstadoPedido, ItemPedido, Nivel, Pedido, Producto,
)
from negocio.excepciones import (
    DevPointsInsuficientes, ErrorNegocio, NoEncontrado,
    PedidoPendienteExistente, StockInsuficiente,
)
from negocio.pasarela import PasarelaPago, PasarelaSimulada

DESCUENTO_NIVEL = {Nivel.JUNIOR: 5, Nivel.MID: 10, Nivel.SENIOR: 15}
VALOR_DEVPOINT = 200
PESOS_POR_DEVPOINT = 20000
UMBRAL_MID = 500_000
UMBRAL_SENIOR = 1_500_000
SIGUIENTE_ESTADO = {
    EstadoPedido.EN_PREPARACION: EstadoPedido.LISTO,
    EstadoPedido.LISTO: EstadoPedido.ENTREGADO,
}


class PedidoServiceFalso:
    def __init__(self, pasarela: Optional[PasarelaPago] = None):
        self._pasarela = pasarela or PasarelaSimulada()
        self._productos = {
            p.id: p for p in [
                Producto(id=1, nombre="Espresso StackTrace", precio_base=6000, stock=20),
                Producto(id=2, nombre="Combo BugHunter", precio_base=18000, stock=10),
                Producto(id=3, nombre="Té Async/Await", precio_base=5000, stock=15),
            ]
        }
        self._clientes: dict[int, Cliente] = {}
        self._pedidos: dict[int, Pedido] = {}
        self._sig_cliente = 1
        self._sig_pedido = 1

    # --- consultas -------------------------------------------------------
    def listar_menu(self) -> list[Producto]:
        return list(self._productos.values())

    def obtener_cliente(self, cliente_id: int) -> Optional[Cliente]:
        return self._clientes.get(cliente_id)

    def listar_pedidos(self, cliente_id: int) -> list[Pedido]:
        self._cliente(cliente_id)
        return [p for p in self._pedidos.values() if p.cliente_id == cliente_id]

    def listar_todos(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]:
        return [p for p in self._pedidos.values() if estado is None or p.estado == estado]

    # --- comandos --------------------------------------------------------
    def crear_cliente(self, nombre: str, correo: str) -> Cliente:
        cliente = Cliente(nombre=nombre, correo=correo, id=self._sig_cliente)
        self._clientes[cliente.id] = cliente
        self._sig_cliente += 1
        return cliente

    def cotizar(self, cliente_id: int, items: list[ItemPedido],
                devpoints_a_redimir: int = 0) -> Cotizacion:
        cliente = self._cliente(cliente_id)
        return self._calcular(cliente, self._fusionar(items), devpoints_a_redimir)

    def crear_pedido(self, cliente_id: int, items: list[ItemPedido],
                     devpoints_a_redimir: int = 0) -> Pedido:
        cliente = self._cliente(cliente_id)
        if any(p.cliente_id == cliente_id and p.estado == EstadoPedido.PENDIENTE_PAGO
               for p in self._pedidos.values()):
            raise PedidoPendienteExistente("Ya tienes un pedido pendiente de pago")
        fusionados = self._fusionar(items)
        cot = self._calcular(cliente, fusionados, devpoints_a_redimir)
        for item in fusionados:
            self._productos[item.producto_id].stock -= item.cantidad
        cliente.devpoints -= devpoints_a_redimir
        pedido = Pedido(cliente_id=cliente_id, id=self._sig_pedido,
                        items=fusionados, total=cot.total)
        self._pedidos[pedido.id] = pedido
        self._sig_pedido += 1
        return pedido

    def pagar_pedido(self, pedido_id: int) -> Pedido:
        pedido = self._pedido(pedido_id)
        if pedido.estado != EstadoPedido.PENDIENTE_PAGO:
            raise ErrorNegocio("El pedido no está pendiente de pago")
        if not self._pasarela.cobrar(pedido.id, pedido.total):
            raise ErrorNegocio("Pago rechazado")
        pedido.estado = EstadoPedido.EN_PREPARACION
        return pedido

    def avanzar_estado(self, pedido_id: int) -> Pedido:
        pedido = self._pedido(pedido_id)
        if pedido.estado == EstadoPedido.PENDIENTE_PAGO:
            raise ErrorNegocio("El pedido debe pagarse antes de avanzar")
        siguiente = SIGUIENTE_ESTADO.get(pedido.estado)
        if siguiente is None:
            raise ErrorNegocio("El pedido ya fue entregado")
        pedido.estado = siguiente
        if siguiente == EstadoPedido.ENTREGADO:
            self._completar_compra(pedido)
        return pedido

    # --- internos --------------------------------------------------------
    def _cliente(self, cliente_id: int) -> Cliente:
        cliente = self._clientes.get(cliente_id)
        if cliente is None:
            raise NoEncontrado("Cliente no encontrado")
        return cliente

    def _pedido(self, pedido_id: int) -> Pedido:
        pedido = self._pedidos.get(pedido_id)
        if pedido is None:
            raise NoEncontrado("Pedido no encontrado")
        return pedido

    def _fusionar(self, items: list[ItemPedido]) -> list[ItemPedido]:
        if not items:
            raise ErrorNegocio("El pedido debe tener al menos un producto")
        cantidades: dict[int, int] = {}
        for item in items:
            if item.producto_id not in self._productos:
                raise NoEncontrado(f"Producto {item.producto_id} no encontrado")
            if item.cantidad <= 0:
                raise ErrorNegocio("La cantidad debe ser mayor que cero")
            cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad
        return [ItemPedido(pid, c) for pid, c in cantidades.items()]

    def _calcular(self, cliente: Cliente, items: list[ItemPedido],
                  devpoints: int) -> Cotizacion:
        if devpoints < 0:
            raise ErrorNegocio("Los DevPoints a redimir no pueden ser negativos")
        subtotal = 0
        for item in items:
            producto = self._productos[item.producto_id]
            if item.cantidad > producto.stock:
                raise StockInsuficiente(
                    f"Stock insuficiente de {producto.nombre}: quedan {producto.stock}")
            subtotal += producto.precio_base * item.cantidad
        if devpoints > cliente.devpoints:
            raise DevPointsInsuficientes(
                f"Solo tienes {cliente.devpoints} DevPoints disponibles")
        desc_nivel = subtotal * DESCUENTO_NIVEL[cliente.nivel] // 100
        desc_dev = devpoints * VALOR_DEVPOINT
        total = max(0, subtotal - desc_nivel - desc_dev)
        return Cotizacion(subtotal, desc_nivel, desc_dev, total, total // PESOS_POR_DEVPOINT)

    def _completar_compra(self, pedido: Pedido) -> None:
        cliente = self._clientes[pedido.cliente_id]
        cliente.monto_acumulado += pedido.total
        cliente.devpoints += pedido.total // PESOS_POR_DEVPOINT
        if cliente.monto_acumulado >= UMBRAL_SENIOR:
            cliente.nivel = Nivel.SENIOR
        elif cliente.monto_acumulado >= UMBRAL_MID:
            cliente.nivel = Nivel.MID
