from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NivelLealtad(Enum):
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"


class EstadoPedido(Enum):
    PENDIENTE_PAGO = "Pendiente de pago"
    EN_PREPARACION = "En Preparación"
    LISTO = "Listo"
    ENTREGADO = "Entregado"


@dataclass
class Producto:
    id: int
    nombre: str
    precio_base: int
    stock: int


@dataclass
class Cliente:
    id: int
    nombre: str
    correo: str
    nivel: NivelLealtad = NivelLealtad.JUNIOR
    dev_points: int = 0
    monto_acumulado: int = 0


@dataclass
class ItemPedido:
    producto_id: int
    cantidad: int
    precio_unitario: int


@dataclass
class Pedido:
    id: int
    cliente_id: int
    items: list[ItemPedido]
    estado: EstadoPedido
    total: int
    fecha: datetime
    dev_points_redimidos: int = 0
    dev_points_otorgados: int = 0


@dataclass
class Cotizacion:
    subtotal: int
    descuento_nivel: int
    descuento_devpoints: int
    total: int
    devpoints_a_ganar: int
