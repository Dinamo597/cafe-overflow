# Contrato entre capas — Café Overflow

Referencia común de Persona A (negocio + persistencia) y Persona B (api + presentation).

| Capa | Tecnología | Responsabilidad | Prohibido |
|---|---|---|---|
| `presentation/` | Node (`http`) + HTML/JS plano | UI; consume la API | Lógica de negocio, cálculos |
| `api/` | Python `http.server`, JSON | Traduce HTTP/JSON <-> servicios; mapea excepciones a HTTP | Reglas de negocio, SQL |
| `negocio/` | Python puro | Reglas, cálculos, estados | HTML, JSON, SQL |
| `persistencia/` | Python, DAOs sobre `sqlite3` | Acceso a datos | Reglas de negocio |

Los diagramas C4 están en `docs/c4/`.

## Entidades (`negocio/entidades.py`)

Montos en `int` COP.

- `Producto(id, nombre, precio_base, stock)`
- `Cliente(id, nombre, correo, nivel, dev_points, monto_acumulado)`
- `ItemPedido(producto_id, cantidad, precio_unitario)`
- `Pedido(id, cliente_id, items, estado, total, fecha, dev_points_redimidos, dev_points_otorgados)`
- `Cotizacion(subtotal, descuento_nivel, descuento_devpoints, total, devpoints_a_ganar)`
- `NivelLealtad`: `Junior` / `Mid` / `Senior`
- `EstadoPedido`: `Pendiente de pago` / `En Preparación` / `Listo` / `Entregado`

Una entidad nueva se crea con `id=None`; `ClienteDAO.crear` y `PedidoDAO.guardar` la devuelven con el id asignado.

## Excepciones (`negocio/excepciones.py`) y su traducción HTTP

Todas heredan de `ErrorNegocio`.

| Excepción | HTTP |
|---|---|
| `NoEncontrado` (cliente, producto o pedido inexistente) | 404 |
| `StockInsuficiente` | 409 |
| `PedidoPendienteExistente` | 409 |
| `DevPointsInsuficientes` | 400 |
| `PagoRechazado` | 402 |
| cualquier otro `ErrorNegocio` (p. ej. pagar un pedido que no está pendiente) | 400 |

## Interfaces de persistencia (`negocio/daos.py`)

- `ProductoDAO`: `listar()`, `obtener(id)`, `actualizar_stock(id, nuevo_stock)` (stock final, no delta)
- `ClienteDAO`: `crear(cliente)`, `obtener(id)`, `actualizar(cliente)`
- `PedidoDAO`: `guardar(pedido)`, `obtener(id)`, `pendiente_de(cliente_id)`, `actualizar_estado(id, estado)`, `listar_por_cliente(cliente_id)`, `listar(estado=None)`

`obtener` y `pendiente_de` devuelven `Optional[...]`. Implementadas sobre SQLite en `persistencia/`.

## Pasarela de pago (`negocio/pasarela.py`)

- `PasarelaPago.procesar(monto) -> bool`
- `PasarelaSimulada(aprueba=True)`: aprueba o rechaza según se configure.

## Servicios (negocio)

Devuelven **entidades**, nunca JSON ni diccionarios HTTP.

- `CatalogoService.listar_menu() -> list[Producto]`
- `ClienteService.crear_cliente(nombre, correo) -> Cliente`
- `ClienteService.obtener_cliente(cliente_id) -> Optional[Cliente]`
- `PedidoService.cotizar(cliente_id, items, devpoints=0) -> Cotizacion`
- `PedidoService.crear_pedido(cliente_id, items, devpoints=0) -> Pedido`
- `PedidoService.pagar_pedido(pedido_id) -> Pedido`
- `PedidoService.avanzar_estado(pedido_id) -> Pedido`
- `PedidoService.listar_pedidos(cliente_id) -> list[Pedido]`

`items` es una lista de `{"producto_id": int, "cantidad": int}`.

### Fachada de la API (`api/servicio_real.py`)

`ServicioApi` reúne los tres servicios con las firmas que consume `api/servidor.py` (`cotizar`, `crear_pedido`, `pagar_pedido`, `avanzar_estado`, `listar_pedidos`, `listar_todos(estado=None)` sobre `PedidoDAO.listar`, etc.). No contiene reglas: solo cablea servicios y convierte "no existe" en `NoEncontrado` (404). `crear_servicio(ruta_db, pasarela)` abre la base SQLite, siembra el menú y arma todo.

La capa `api` convierte `Enum` (-> `.value`) y `datetime` (-> `isoformat()`) a JSON.

## Endpoints (api)

| Método | Ruta | Servicio | Éxito |
|---|---|---|---|
| GET | `/api/productos` | `listar_menu` | 200 |
| POST | `/api/clientes` | `crear_cliente` | 201 |
| GET | `/api/clientes/{id}` | `obtener_cliente` | 200 / 404 |
| POST | `/api/pedidos/cotizar` | `cotizar` | 200 |
| POST | `/api/pedidos` | `crear_pedido` | 201 |
| POST | `/api/pedidos/{id}/pagar` | `pagar_pedido` | 200 |
| POST | `/api/pedidos/{id}/estado` | `avanzar_estado` | 200 |
| GET | `/api/pedidos?cliente_id=` | `listar_pedidos` | 200 |
| GET | `/api/pedidos?estado=` (o sin filtro) | pedidos del personal | 200 |

Cuerpos de entrada:

- `POST /api/clientes`: `{"nombre": str, "correo": str}`
- `POST /api/pedidos/cotizar` y `POST /api/pedidos`: `{"cliente_id": int, "items": [{"producto_id": int, "cantidad": int >= 1}], "devpoints_a_redimir": int >= 0 (opcional)}`
- `/pagar` y `/estado`: sin cuerpo.
- `GET /api/pedidos`: `cliente_id` y `estado` son excluyentes; `estado` usa el valor del Enum (p. ej. `En Preparación`).

Errores: cuerpo `{"error": "mensaje"}`. Además de la tabla de excepciones: 400 por JSON inválido, campos faltantes o mal tipados e ids no enteros; 404 por ruta inexistente; 405 por método no permitido; 500 por error inesperado.

Fechas: ISO 8601 en UTC (`2026-10-10T21:42:00+00:00`); la presentación las muestra en hora de Bogotá.

## Decisiones acordadas

- La compra cuenta como completada cuando el pedido pasa a **Entregado**: ahí se acumula `monto_acumulado`, se evalúa el ascenso y se otorgan los DevPoints.
- El stock se descuenta al **crear** el pedido. Los DevPoints redimidos se descuentan al **pagar**.
- Orden de cálculo del total: subtotal -> descuento por nivel -> descuento por DevPoints redimidos -> total mínimo 0.
- Descuento por nivel: Junior 5 %, Mid 10 %, Senior 15 %, truncado con división entera (`subtotal * porcentaje // 100`).
- DevPoints: se ganan `total_pagado // 20_000` al entregar; se redimen a $200 cada uno.
- Ascenso: Mid desde $500.000 acumulados, Senior desde $1.500.000; el descuento nuevo aplica desde la siguiente compra.
- `pagar_pedido`: `Pendiente de pago` -> `En Preparación` solo si la pasarela aprueba (si no, `PagoRechazado` y el pedido queda igual). Pagar un pedido que no está pendiente lanza `ErrorNegocio`.
- `avanzar_estado` sigue `En Preparación -> Listo -> Entregado`; sobre un pedido sin pagar o ya entregado no hace nada y devuelve el mismo pedido (la API responde 200).
- No registrar pedido si la cantidad supera el stock; no registrar uno nuevo si el cliente tiene uno en "Pendiente de pago".
- Fechas en UTC internamente; se convierten a hora de Bogotá solo al mostrarlas.
- Rutas: se usan las de la tabla de arriba (`/api/productos`, `/api/pedidos?cliente_id=`, `/api/pedidos/{id}/estado`), no las propuestas iniciales (`/api/menu`, `/api/clientes/{id}/pedidos`, `/avanzar`).
