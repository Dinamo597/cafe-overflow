class ErrorNegocio(Exception):
    pass


class StockInsuficiente(ErrorNegocio):
    def __init__(self, producto_id: int, solicitado: int, disponible: int):
        self.producto_id = producto_id
        self.solicitado = solicitado
        self.disponible = disponible
        super().__init__(
            f"Stock insuficiente para el producto {producto_id}: "
            f"solicitado {solicitado}, disponible {disponible}"
        )


class PedidoPendienteExistente(ErrorNegocio):
    def __init__(self, cliente_id: int, pedido_id: int):
        self.cliente_id = cliente_id
        self.pedido_id = pedido_id
        super().__init__(
            f"El cliente {cliente_id} ya tiene el pedido {pedido_id} pendiente de pago"
        )


class DevPointsInsuficientes(ErrorNegocio):
    def __init__(self, cliente_id: int, solicitados: int, disponibles: int):
        self.cliente_id = cliente_id
        self.solicitados = solicitados
        self.disponibles = disponibles
        super().__init__(
            f"El cliente {cliente_id} solicitó redimir {solicitados} DevPoints "
            f"pero solo tiene {disponibles}"
        )


class PagoRechazado(ErrorNegocio):
    def __init__(self, pedido_id: int, monto: int):
        self.pedido_id = pedido_id
        self.monto = monto
        super().__init__(f"La pasarela rechazó el pago del pedido {pedido_id} por {monto}")
