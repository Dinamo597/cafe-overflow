from negocio.entidades import NivelLealtad

PORCENTAJE_POR_NIVEL = {
    NivelLealtad.JUNIOR: 5,
    NivelLealtad.MID: 10,
    NivelLealtad.SENIOR: 15,
}


class DescuentoService:
    def porcentaje_para(self, nivel: NivelLealtad) -> int:
        return PORCENTAJE_POR_NIVEL[nivel]

    def calcular_descuento(self, nivel: NivelLealtad, subtotal: int) -> int:
        return subtotal * PORCENTAJE_POR_NIVEL[nivel] // 100
