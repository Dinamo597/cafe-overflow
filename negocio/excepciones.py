class ErrorNegocio(Exception):
    """Base de todos los errores de reglas de negocio."""


class StockInsuficiente(ErrorNegocio):
    pass


class PedidoPendienteExistente(ErrorNegocio):
    pass


class DevPointsInsuficientes(ErrorNegocio):
    pass


class NoEncontrado(ErrorNegocio):
    """El cliente, producto o pedido referenciado no existe."""
