from negocio.entidades import NivelLealtad
from negocio.redondeo import redondear_pesos

PORCENTAJE_POR_NIVEL = {
    NivelLealtad.JUNIOR: 0.05,
    NivelLealtad.MID: 0.10,
    NivelLealtad.SENIOR: 0.15,
}


class DescuentoService:
    def porcentaje_para(self, nivel: NivelLealtad) -> float:
        return PORCENTAJE_POR_NIVEL[nivel]

    def calcular_descuento(self, nivel: NivelLealtad, subtotal: int) -> int:
        return redondear_pesos(subtotal * PORCENTAJE_POR_NIVEL[nivel])
