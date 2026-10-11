# Progreso — Café Overflow

## Persona A (negocio + persistencia)

- [x] `entidades.py`, `excepciones.py`, `daos.py`, `pasarela.py`
- [x] `descuento_service.py`, `fidelidad_service.py`, `pedido_service.py`, `catalogo_service.py`, `cliente_service.py`
- [x] `persistencia/` sobre SQLite (schema, seed, DAOs)
- [x] Pruebas unitarias con DAOs en memoria
- [x] `docs/c4/c3-backend.svg`

## Persona B (api + presentation)

- [x] `api/`: todos los endpoints del contrato y mapeo de errores
- [x] `api/servicio_real.py`: fachada sobre los servicios de negocio y SQLite
- [x] `presentation/`: servidor Node con proxy a `/api/*` y vistas (menú, cuenta, carrito/cotización, pedidos, personal)
- [x] Pruebas de la API (`tests/test_api.py`) contra el servicio real con SQLite en memoria
- [x] `docs/c4`: C1 y C2
- [x] README

## Integración

- [x] Rutas y formato JSON acordados (ver `docs/CONTRATO.md`)
- [x] Integración api + negocio + persistencia
- [ ] Pull request de `feature/persona-a` y `feature/persona-b` hacia `main`
- [ ] Revisión cruzada de diagramas (C1/C2 de B con C3 de A)
