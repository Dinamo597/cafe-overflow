# Café Overflow — Dev & Coffee Lounge

Sistema de pedidos en línea para el café temático "Café Overflow", dividido en 3 capas (N-Tier) con separación estricta de responsabilidades.

## Estructura

```
/presentation   Node, http + HTML/JS plano (Persona B)
/api            Python, http.server, JSON (Persona B)
/negocio        Python, lógica pura (Persona A)
/persistencia   Python, DAOs sobre SQLite (Persona A)
/docs/c4        Diagramas C4
/tests          Pruebas unitarias con DAOs en memoria
```

## Capa de negocio

- `entidades.py`: Producto, Cliente, Pedido, ItemPedido, Cotizacion, NivelLealtad, EstadoPedido.
- `excepciones.py`: ErrorNegocio y sus subclases: StockInsuficiente, PedidoPendienteExistente, DevPointsInsuficientes, PagoRechazado.
- `daos.py`: contratos de ProductoDAO, ClienteDAO y PedidoDAO (los implementa la capa de persistencia).
- `pasarela.py`: PasarelaPago (contrato) y PasarelaSimulada (aprueba o rechaza el pago según se configure).
- `descuento_service.py`: 5/10/15% según nivel, truncado hacia abajo con división entera.
- `fidelidad_service.py`: ascenso Junior → Mid ($500.000) → Senior ($1.500.000), acumulación y redención de DevPoints ($20.000 = 1 punto, 1 punto = $200). Se acumula al llegar el pedido a Entregado, no al pagar.
- `pedido_service.py`: cotizar, crear_pedido, pagar_pedido, avanzar_estado, listar_pedidos. Valida stock y pedido pendiente antes de crear; pagar_pedido depende de que la pasarela apruebe.
- `catalogo_service.py` / `cliente_service.py`: listar_menu, crear_cliente, obtener_cliente.

Todos los montos se manejan en pesos enteros (sin decimales).

Ver `docs/CONTRATO.md` para el detalle de endpoints propuestos y decisiones acordadas con Persona B, y `docs/PROGRESO.md` para el estado de cada parte.

## Capa de persistencia

DAOs sobre SQLite (`producto_dao.py`, `cliente_dao.py`, `pedido_dao.py`) que implementan las interfaces de `negocio/daos.py`. `db.py` crea el esquema (`schema.sql`) y `seed.py` carga el menú inicial (Espresso StackTrace, Combo BugHunter, Té Async/Await).

## Pruebas

```
pip install -r requirements.txt
PYTHONPATH=. pytest tests/ -v
```

Cubren los umbrales de ascenso de nivel, el redondeo de descuentos y las dos validaciones de pedido (stock insuficiente y pedido pendiente existente), usando DAOs en memoria (`tests/fakes.py`).

## Uso rápido

```python
from persistencia.db import conectar, inicializar
from persistencia.seed import sembrar
from persistencia.producto_dao import ProductoDAOSQLite
from persistencia.cliente_dao import ClienteDAOSQLite
from persistencia.pedido_dao import PedidoDAOSQLite
from negocio.descuento_service import DescuentoService
from negocio.fidelidad_service import FidelidadService
from negocio.pasarela import PasarelaSimulada
from negocio.pedido_service import PedidoService

con = conectar("cafe_overflow.db")
inicializar(con)
sembrar(con)

pedido_service = PedidoService(
    ProductoDAOSQLite(con), ClienteDAOSQLite(con), PedidoDAOSQLite(con),
    DescuentoService(), FidelidadService(), PasarelaSimulada(),
)
```
