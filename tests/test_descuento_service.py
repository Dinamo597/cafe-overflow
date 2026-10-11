from negocio.descuento_service import DescuentoService
from negocio.entidades import NivelLealtad


def test_descuento_junior():
    servicio = DescuentoService()
    assert servicio.calcular_descuento(NivelLealtad.JUNIOR, 100_000) == 5_000


def test_descuento_mid():
    servicio = DescuentoService()
    assert servicio.calcular_descuento(NivelLealtad.MID, 100_000) == 10_000


def test_descuento_senior():
    servicio = DescuentoService()
    assert servicio.calcular_descuento(NivelLealtad.SENIOR, 100_000) == 15_000


def test_descuento_trunca_decimales_hacia_abajo():
    servicio = DescuentoService()
    assert servicio.calcular_descuento(NivelLealtad.JUNIOR, 12_345) == 617


def test_descuento_no_redondea_hacia_arriba():
    servicio = DescuentoService()
    descuento = servicio.calcular_descuento(NivelLealtad.SENIOR, 7_777)
    assert isinstance(descuento, int)
    assert descuento == 1_166
