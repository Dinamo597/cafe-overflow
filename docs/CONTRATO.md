# Contrato entre capas — Café Overflow

Este documento es la referencia para que `api/` y `presentation/` (Persona B) consuman la capa de negocio sin tener que leer el código de `negocio/` y `persistencia/`.

## Entidades (`negocio/entidades.py`)

- `Producto(id, nombre, precio_base, stock)`
- `Cliente(id, nombre, correo, nivel, dev_points, monto_acumulado)`
- `ItemPedido(producto_id, cantidad, precio_unitario)`
- `Pedido(id, cliente_id, items, estado, total, fecha, dev_points_redimidos, dev_points_otorgados)`
- `Cotizacion(subtotal, descuento_nivel, descuento_devpoints, total, devpoints_a_ganar)` — lo que devuelve `cotizar()`, para que la api lo serialice sin calcular nada.
- `NivelLealtad`: `Junior` / `Mid` / `Senior`
- `EstadoPedido`: `Pendiente de pago` / `En Preparación` / `Listo` / `Entregado`

## Excepciones (`negocio/excepciones.py`)

Todas heredan de `ErrorNegocio`. La capa api debe traducirlas así:

| Excepción | HTTP |
|---|---|
| `StockInsuficiente` | 409 |
| `PedidoPendienteExistente` | 409 |
| `DevPointsInsuficientes` | 400 |
| `PagoRechazado` | 402 |

## Interfaces de persistencia (`negocio/daos.py`)

- `ProductoDAO`: `listar()`, `obtener(id)`, `actualizar_stock(id, nuevo_stock)`
- `ClienteDAO`: `crear(cliente)`, `obtener(id)`, `actualizar(cliente)`
- `PedidoDAO`: `guardar(pedido)`, `obtener(id)`, `pendiente_de(cliente_id)`, `actualizar_estado(id, estado)`, `listar_por_cliente(cliente_id)`, `listar(estado=None)`

Implementadas sobre SQLite en `persistencia/`.

## Pasarela de pago (`negocio/pasarela.py`)

- `PasarelaPago.procesar(monto) -> bool`
- `PasarelaSimulada(aprueba=True)`: implementación de prueba, aprueba o rechaza según se configure al construirla. `pagar_pedido` la usa antes de confirmar el pago.

## Servicios y sus métodos (lo que consume la api)

- `CatalogoService.listar_menu() -> list[Producto]`
- `ClienteService.crear_cliente(nombre, correo) -> Cliente`
- `ClienteService.obtener_cliente(cliente_id) -> Optional[Cliente]`
- `PedidoService.cotizar(cliente_id, items, devpoints=0) -> Cotizacion`
- `PedidoService.crear_pedido(cliente_id, items, devpoints=0) -> Pedido`
- `PedidoService.pagar_pedido(pedido_id) -> Pedido`
- `PedidoService.avanzar_estado(pedido_id) -> Pedido`
- `PedidoService.listar_pedidos(cliente_id) -> list[Pedido]`

`items` es una lista de `{"producto_id": int, "cantidad": int}`. Ninguno de estos métodos recibe ni devuelve JSON ni diccionarios con forma HTTP: siempre entidades o excepciones.

## Endpoints propuestos para `api/`

(a confirmar nombre y forma exacta con Persona B)

- `GET /api/menu` → `listar_menu()`
- `POST /api/clientes` → `crear_cliente(nombre, correo)`
- `GET /api/clientes/{id}` → `obtener_cliente(id)`
- `GET /api/clientes/{id}/pedidos` → `listar_pedidos(id)`
- `POST /api/pedidos/cotizar` → `cotizar(cliente_id, items, devpoints)`
- `POST /api/pedidos` → `crear_pedido(cliente_id, items, devpoints)`
- `POST /api/pedidos/{id}/pagar` → `pagar_pedido(id)`
- `POST /api/pedidos/{id}/avanzar` → `avanzar_estado(id)`

## Decisiones acordadas

- La compra cuenta como completada cuando el pedido pasa a **Entregado**: ahí se acumula `monto_acumulado`, se evalúa el ascenso de nivel y se otorgan los DevPoints ganados. No al pagar.
- El stock se descuenta al **crear** el pedido, no al pagarlo.
- Orden de cálculo del total: subtotal → descuento por nivel → descuento por DevPoints redimidos → total mínimo 0.
- `pagar_pedido` pasa de `Pendiente de pago` a `En Preparación` solo si la pasarela aprueba el monto; si la rechaza, lanza `PagoRechazado` y el pedido queda igual.
- `avanzar_estado` sigue estrictamente `En Preparación → Listo → Entregado`; no permite saltos.
- Descuento por nivel: Junior 5 %, Mid 10 %, Senior 15 %, truncado hacia abajo con división entera (`subtotal * porcentaje // 100`). No se usan decimales en ningún monto.
- DevPoints: se ganan `total_pagado // 20_000` al entregar, se redimen a $200 cada uno.
- Ascenso: Mid a partir de $500.000 acumulados, Senior a partir de $1.500.000.

## Pendiente de confirmar con Persona B

- Forma exacta de las rutas y nombres de los campos JSON de cada endpoint.
- Qué devuelve la api cuando `avanzar_estado` se llama sobre un pedido `Entregado` (hoy el servicio simplemente no hace nada y devuelve el mismo pedido).
