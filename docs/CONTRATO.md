# Contrato — Café Overflow (N-Tier)

## Capas y responsabilidades

| Capa | Tecnología | Responsabilidad | Prohibido |
|---|---|---|---|
| `presentation/` | Node (`http`) + HTML/JS plano | UI; consume la API | Lógica de negocio |
| `api/` | Python `http.server`, JSON | Traduce HTTP/JSON <-> negocio; mapea excepciones a códigos HTTP | Reglas de negocio, SQL |
| `negocio/` | Python puro | Reglas, cálculos, estados | HTML, JSON, SQL |
| `persistencia/` | Python, DAOs sobre `sqlite3` | Acceso a datos | Reglas de negocio |

Dependencias: presentation -> api -> negocio; persistencia implementa las interfaces DAO definidas por negocio. Los diagramas C4 van en `docs/c4/`.

## Entidades (`negocio/entidades.py`)

Precios y montos en `int` COP.

- `Nivel`: JUNIOR="Junior", MID="Mid", SENIOR="Senior"
- `EstadoPedido`: PENDIENTE_PAGO="Pendiente de pago", EN_PREPARACION="En Preparación", LISTO="Listo", ENTREGADO="Entregado"
- `Producto(id, nombre, precio_base, stock)`
- `Cliente(nombre, correo, id=None, nivel=JUNIOR, devpoints=0, monto_acumulado=0)`
- `ItemPedido(producto_id, cantidad)`
- `Pedido(cliente_id, id=None, items=[], estado=PENDIENTE_PAGO, total=0, fecha=now UTC)`

### Criterio de ids

Una entidad nueva se crea con `id=None`. `ClienteDAO.crear` y `PedidoDAO.guardar` devuelven la entidad con el id asignado. Los campos obligatorios van antes que los que tienen default, por eso `id` no es el primer campo.

## Excepciones (`negocio/excepciones.py`)

`ErrorNegocio(Exception)` y, heredando de ella: `StockInsuficiente`, `PedidoPendienteExistente`, `DevPointsInsuficientes`.

## Reglas de negocio

- Compra "completada" = el pedido pasa a **Entregado**; ahí se acumulan monto, DevPoints y se evalúa el ascenso.
- El stock se descuenta **al crear el pedido**.

### Cálculo del total (en este orden)

1. **Subtotal** = suma de `precio_base * cantidad` de los ítems.
2. **Descuento por nivel**: Junior 5 %, Mid 10 %, Senior 15 % sobre el subtotal.
3. **DevPoints redimidos**: cada DevPoint = $200 de descuento directo. Requiere que el cliente tenga los puntos (si no, `DevPointsInsuficientes`).
4. **Total mínimo 0** (nunca negativo).

### DevPoints ganados

`devpoints_ganados = total_pagado // 20000`, y solo cuando el pedido pasa a **Entregado**.

### Ascenso de nivel

Se evalúa al pasar un pedido a Entregado, sobre `monto_acumulado` de compras completadas:

- Mid al llegar a >= $500.000
- Senior al llegar a >= $1.500.000

El descuento del nivel nuevo aplica **desde la siguiente compra**.

### Validaciones

- No registrar el pedido si alguna cantidad supera el stock -> `StockInsuficiente`.
- No registrar un pedido nuevo si el cliente tiene uno en "Pendiente de pago" -> `PedidoPendienteExistente`.

### Fechas

Todo en **UTC** internamente y en la BD; se convierte a hora de Bogotá solo al mostrarlas.

## Pasarela de pago (simulada) — a cargo de la Persona A

En `negocio/pasarela.py`:

- Interfaz `PasarelaPago` con `cobrar(pedido_id: int, monto: int) -> bool`.
- Implementación `PasarelaSimulada` (siempre aprueba).
- `PedidoService` recibe la pasarela **por constructor** (inyección de dependencias).

## Interfaces DAO (`negocio/daos.py`, implementadas en persistencia)

```python
class ProductoDAO(ABC):
    def listar(self) -> list[Producto]
    def obtener(self, producto_id: int) -> Optional[Producto]
    def actualizar_stock(self, producto_id: int, nuevo_stock: int) -> None  # stock final, no delta

class ClienteDAO(ABC):
    def crear(self, cliente: Cliente) -> Cliente          # devuelve con id asignado
    def obtener(self, cliente_id: int) -> Optional[Cliente]
    def actualizar(self, cliente: Cliente) -> None

class PedidoDAO(ABC):
    def guardar(self, pedido: Pedido) -> Pedido           # devuelve con id asignado
    def obtener(self, pedido_id: int) -> Optional[Pedido]
    def pendiente_de(self, cliente_id: int) -> Optional[Pedido]
    def actualizar_estado(self, pedido_id: int, estado: EstadoPedido) -> None
    def listar_por_cliente(self, cliente_id: int) -> list[Pedido]
    def listar(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]
```

- `listar_por_cliente` alimenta `GET /api/pedidos?cliente_id=`.
- `listar(estado)` alimenta la vista del personal.

## Servicios (negocio)

`listar_menu`, `crear_cliente`, `obtener_cliente`, `cotizar`, `crear_pedido`, `pagar_pedido`, `avanzar_estado`, `listar_pedidos`.

- `obtener_cliente(cliente_id) -> Optional[Cliente]`: alimenta `GET /api/clientes/{id}`.
- `listar_pedidos(cliente_id) -> list[Pedido]`: alimenta `GET /api/pedidos?cliente_id=` (usa `PedidoDAO.listar_por_cliente`).

## Endpoints (api)

| Método | Ruta | Servicio |
|---|---|---|
| GET | `/api/productos` | `listar_menu` |
| POST | `/api/clientes` | `crear_cliente` |
| GET | `/api/clientes/{id}` | `obtener_cliente` |
| POST | `/api/pedidos/cotizar` | `cotizar` |
| POST | `/api/pedidos` | `crear_pedido` |
| POST | `/api/pedidos/{id}/pagar` | `pagar_pedido` |
| POST | `/api/pedidos/{id}/estado` | `avanzar_estado` |
| GET | `/api/pedidos?cliente_id=` | `listar_pedidos` |

### Errores

`ErrorNegocio` -> 400 / 409:

- 409 Conflicto: `StockInsuficiente`, `PedidoPendienteExistente`
- 400 Solicitud inválida: `DevPointsInsuficientes` y cualquier otro `ErrorNegocio`
