from decimal import ROUND_HALF_UP, Decimal


def redondear_pesos(valor: float) -> int:
    return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
