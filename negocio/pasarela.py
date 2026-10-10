from abc import ABC, abstractmethod


class PasarelaPago(ABC):
    @abstractmethod
    def cobrar(self, pedido_id: int, monto: int) -> bool:
        """Cobra `monto` (COP) del pedido. True si el pago fue aprobado."""


class PasarelaSimulada(PasarelaPago):
    def cobrar(self, pedido_id: int, monto: int) -> bool:
        return True
