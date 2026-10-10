# Progreso — Café Overflow

## Persona A (negocio + persistencia)

- [x] `entidades.py`
- [x] `excepciones.py`
- [x] `daos.py` (interfaces de los DAO)
- [x] `pasarela.py` (`PasarelaPago` / `PasarelaSimulada`)
- [x] `descuento_service.py`
- [x] `fidelidad_service.py`
- [x] `pedido_service.py`
- [x] `catalogo_service.py` / `cliente_service.py`
- [x] `persistencia/` sobre SQLite (schema, seed, DAOs)
- [x] Pruebas unitarias con DAOs en memoria
- [x] `docs/c4/c3-backend.svg`

## Persona B (api + presentation)

- [ ] `api/` (endpoints HTTP sobre los servicios de negocio)
- [ ] `presentation/` (UI)
- [ ] `docs/c4` — C1 (contexto) y C2 (contenedores)

## Pendiente conjunto

- [ ] Confirmar rutas y formato JSON de la api (ver `docs/CONTRATO.md`)
- [ ] Integración api + negocio
- [ ] Pull request de `feature/persona-a` hacia `main`
