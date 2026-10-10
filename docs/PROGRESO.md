# Progreso

## Fase 0 — Contrato (Persona B)
- [x] Estructura de carpetas y .gitignore
- [x] Entidades y excepciones
- [x] docs/CONTRATO.md
- [x] Interfaces DAO (`negocio/daos.py`)
- [x] PasarelaPago / PasarelaSimulada (`negocio/pasarela.py`)

## Persona A (negocio + persistencia)
- [x] PasarelaSimulada
- [ ] Servicios (`listar_menu`, `crear_cliente`, `cotizar`, `crear_pedido`, `pagar_pedido`, `avanzar_estado`)
- [ ] DAOs sobre sqlite3
- [ ] `obtener_cliente` y `listar_pedidos` en PedidoService

## Persona B (api + presentation)
- [x] api/: GET /api/productos con servicio falso
- [x] api/: todos los endpoints del contrato (clientes, cotizar, pedidos, pagar, estado, listados) y mapeo de errores
- [x] api/servicio_falso.py completo en memoria
- [x] presentation/: servidor Node con proxy a /api/* y vistas (menú, cuenta, carrito/cotización, pedidos, personal)
- [x] Pruebas automáticas de la API (`tests/`)
- [x] Diagramas C1 y C2 (`docs/c4/`)
- [x] README
