# Café Overflow — Dev & Coffee Lounge

Taller N-Tier (UNAB, Arquitectura de Software): sistema de pedidos en línea de un café temático, con niveles de fidelidad y DevPoints, en 3 capas con separación estricta de responsabilidades.

## Estructura

```
presentation/   Node (http) + HTML/CSS/JS plano. Renderiza y valida sintaxis; no calcula nada.
  server.js       sirve public/ y reenvía /api/* a la API
  public/         index.html, styles.css, app.js
api/            Python, http.server, JSON. Traduce HTTP/JSON <-> servicios. Sin reglas de negocio.
  servidor.py     handler y rutas (crear_handler(servicio))
  servicio_real.py  fachada que arma los servicios de negocio sobre SQLite
negocio/        Python puro (sin HTML/JSON/SQL): entidades, excepciones, servicios, interfaces DAO, pasarela.
persistencia/   DAOs sobre SQLite (schema.sql, seed.py).
tests/          Pruebas (API contra el servicio real; negocio con DAOs en memoria).
docs/           CONTRATO.md, PROGRESO.md y diagramas C4 (docs/c4/).
```

Dependencias: presentation -> api -> negocio -> persistencia (negocio define las interfaces DAO; persistencia las implementa). Todos los montos son pesos enteros.

## Requisitos

- Python 3.11+
- Node.js 18+
- `pytest` solo para las pruebas de negocio: `pip install -r requirements.txt`

## Ejecutar

Desde la raíz, en dos terminales:

```bash
python -m api.servidor
```

```bash
node presentation/server.js
```

Abre http://localhost:3000. La API queda en http://localhost:8000 y guarda los datos en `cafe_overflow.db` (se crea y siembra sola).

Variables opcionales: `API_PORT`, `DB_PATH` (archivo SQLite), `PORT` (presentación) y `API_URL` (a dónde reenvía Node, por defecto `http://127.0.0.1:8000`).

## Pruebas

```bash
python -m pytest tests -q
```

`tests/test_api.py` levanta la API en un puerto libre sobre SQLite en memoria y cubre cada endpoint, los códigos de error y el recorrido completo (cliente, cotizar, pedido, pago, preparación, listo, entregado, DevPoints y ascenso). El resto prueba la capa de negocio con DAOs en memoria (`tests/fakes.py`).

## Capas

- **negocio**: `descuento_service` (5/10/15 % por nivel), `fidelidad_service` (ascenso a $500.000 y $1.500.000; DevPoints: 1 por cada $20.000, cada uno vale $200), `pedido_service` (cotizar, crear, pagar, avanzar estado, listar), `catalogo_service`, `cliente_service`.
- **persistencia**: `producto_dao`, `cliente_dao`, `pedido_dao` sobre SQLite.
- **api**: contrato de endpoints y errores en `docs/CONTRATO.md`.

## Decisiones

Ver `docs/CONTRATO.md` (compra completada al entregar, stock al crear el pedido, orden de cálculo del total, etc.).
