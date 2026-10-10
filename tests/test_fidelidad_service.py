from negocio.entidades import Cliente, NivelLealtad
from negocio.excepciones import DevPointsInsuficientes
from negocio.fidelidad_service import FidelidadService
import pytest


def test_asciende_a_mid_en_el_umbral_exacto():
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com", monto_acumulado=499_000)
    servicio = FidelidadService()
    servicio.registrar_compra(cliente, 1_000)
    assert cliente.nivel == NivelLealtad.MID


def test_asciende_a_senior_en_el_umbral_exacto():
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com", monto_acumulado=1_499_000)
    servicio = FidelidadService()
    servicio.registrar_compra(cliente, 1_000)
    assert cliente.nivel == NivelLealtad.SENIOR


def test_no_asciende_por_debajo_del_umbral():
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com", monto_acumulado=100_000)
    servicio = FidelidadService()
    servicio.registrar_compra(cliente, 50_000)
    assert cliente.nivel == NivelLealtad.JUNIOR


def test_acumula_un_devpoint_por_cada_20000():
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com")
    servicio = FidelidadService()
    puntos = servicio.registrar_compra(cliente, 45_000)
    assert puntos == 2
    assert cliente.dev_points == 2


def test_redimir_devpoints_insuficientes_lanza_excepcion():
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com", dev_points=3)
    servicio = FidelidadService()
    with pytest.raises(DevPointsInsuficientes):
        servicio.redimir(cliente, 5)


def test_redimir_descuenta_saldo_y_devuelve_valor():
    cliente = Cliente(id=1, nombre="Ana", correo="ana@x.com", dev_points=10)
    servicio = FidelidadService()
    valor = servicio.redimir(cliente, 4)
    assert valor == 800
    assert cliente.dev_points == 6
