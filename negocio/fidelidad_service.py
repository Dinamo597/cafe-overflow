from negocio.entidades import Cliente, NivelLealtad
from negocio.excepciones import DevPointsInsuficientes

UMBRAL_MID = 500_000
UMBRAL_SENIOR = 1_500_000
PESOS_POR_DEVPOINT = 20_000
VALOR_DEVPOINT = 200


class FidelidadService:
    def evaluar_ascenso(self, cliente: Cliente) -> NivelLealtad:
        if cliente.monto_acumulado >= UMBRAL_SENIOR:
            cliente.nivel = NivelLealtad.SENIOR
        elif cliente.monto_acumulado >= UMBRAL_MID:
            cliente.nivel = NivelLealtad.MID
        return cliente.nivel

    def registrar_compra(self, cliente: Cliente, monto_pagado: int) -> int:
        cliente.monto_acumulado += monto_pagado
        self.evaluar_ascenso(cliente)
        puntos_ganados = monto_pagado // PESOS_POR_DEVPOINT
        cliente.dev_points += puntos_ganados
        return puntos_ganados

    def valor_redencion(self, devpoints: int) -> int:
        return devpoints * VALOR_DEVPOINT

    def validar_redencion(self, cliente: Cliente, devpoints: int) -> None:
        if devpoints > cliente.dev_points:
            raise DevPointsInsuficientes(cliente.id, devpoints, cliente.dev_points)

    def redimir(self, cliente: Cliente, devpoints: int) -> int:
        self.validar_redencion(cliente, devpoints)
        cliente.dev_points -= devpoints
        return self.valor_redencion(devpoints)
