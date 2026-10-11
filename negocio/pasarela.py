from abc import ABC, abstractmethod


class PasarelaPago(ABC):
    @abstractmethod
    def procesar(self, monto: int) -> bool: ...


class PasarelaSimulada(PasarelaPago):
    def __init__(self, aprueba: bool = True):
        self.aprueba = aprueba
        self.montos_procesados: list[int] = []

    def procesar(self, monto: int) -> bool:
        self.montos_procesados.append(monto)
        return self.aprueba
