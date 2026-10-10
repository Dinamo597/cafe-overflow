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
- [ ] API (`http.server`)
- [ ] Presentation (Node + HTML/JS)
