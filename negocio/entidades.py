from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Nivel(Enum):
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
    precio_base: int  # COP
    stock: int


@dataclass
class Cliente:
    nombre: str
    correo: str
    id: Optional[int] = None
    nivel: Nivel = Nivel.JUNIOR
    devpoints: int = 0
    monto_acumulado: int = 0  # COP


@dataclass
class ItemPedido:
    producto_id: int
    cantidad: int


@dataclass
class Pedido:
    cliente_id: int
    id: Optional[int] = None
    items: list[ItemPedido] = field(default_factory=list)
    estado: EstadoPedido = EstadoPedido.PENDIENTE_PAGO
    total: int = 0  # COP
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Cotizacion:
    subtotal: int
    descuento_nivel: int
    descuento_devpoints: int
    total: int
    devpoints_a_ganar: int
