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

- `entidades.py`: Producto, Cliente, Pedido, ItemPedido, NivelLealtad, EstadoPedido.
- `excepciones.py`: StockInsuficiente, PedidoPendienteExistente, DevPointsInsuficientes.
- `interfaces.py`: contratos de ProductoDAO, ClienteDAO y PedidoDAO (los implementa la capa de persistencia).
- `descuento_service.py`: 5/10/15% según nivel.
- `fidelidad_service.py`: ascenso Junior → Mid ($500.000) → Senior ($1.500.000), acumulación y redención de DevPoints ($20.000 = 1 punto, 1 punto = $200).
- `pedido_service.py`: cotizar, crear_pedido, pagar_pedido, avanzar_estado. Valida stock y pedido pendiente antes de crear.
- `catalogo_service.py` / `cliente_service.py`: listar_menu, crear_cliente.

Todos los montos se manejan en pesos enteros (sin decimales), con redondeo half-up donde aplica.

## Capa de persistencia

DAOs sobre SQLite (`producto_dao.py`, `cliente_dao.py`, `pedido_dao.py`) que implementan las interfaces de `negocio/interfaces.py`. `db.py` crea el esquema (`schema.sql`) y `seed.py` carga el menú inicial (Espresso StackTrace, Combo BugHunter, Té Async/Await).

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
from negocio.pedido_service import PedidoService

con = conectar("cafe_overflow.db")
inicializar(con)
sembrar(con)

pedido_service = PedidoService(
    ProductoDAOSQLite(con), ClienteDAOSQLite(con), PedidoDAOSQLite(con),
    DescuentoService(), FidelidadService(),
)
```
