# Café Overflow

Taller N-Tier (UNAB, Arquitectura de Software): sistema de pedidos de una cafetería con niveles de fidelidad y DevPoints.

## Estructura por capas

```
presentation/   Node (http) + HTML/CSS/JS plano. Renderiza y valida sintaxis; no calcula nada.
  server.js       sirve public/ y reenvía /api/* a la API
  public/         index.html, styles.css, app.js
api/            Python, http.server, JSON. Traduce HTTP/JSON <-> servicio. Sin reglas de negocio.
  servidor.py     handler y rutas (crear_handler(servicio))
  servicio_falso.py  PedidoServiceFalso: servicio en memoria para desarrollar y probar
negocio/        Python puro (sin HTML/JSON/SQL): entidades, excepciones, interfaces DAO, pasarela.
persistencia/   Python, DAOs sobre sqlite3.
tests/          Pruebas automáticas de la API (unittest).
docs/           CONTRATO.md, PROGRESO.md y diagramas C4 (docs/c4/).
```

Dependencias: presentation -> api -> negocio -> persistencia (negocio define las interfaces DAO; persistencia las implementa).

## Requisitos

- Python 3.11+
- Node.js 18+

No hay dependencias externas (ni `pip install` ni `npm install`).

## Ejecutar

Desde la raíz del repositorio, en dos terminales:

```bash
python -m api.servidor
```

```bash
node presentation/server.js
```

Abre http://localhost:3000. La API queda en http://localhost:8000 (los endpoints están en `docs/CONTRATO.md`).

Variables opcionales: `API_PORT` (puerto de la API), `PORT` (puerto de presentación) y `API_URL` (a dónde reenvía Node, por defecto `http://127.0.0.1:8000`).

## Pruebas

```bash
python -m unittest discover -s tests -t .
```

Levantan la API en un puerto libre y cubren cada endpoint, los códigos de error y el recorrido completo (cliente, cotizar, pedido, pago, preparación, listo, entregado, DevPoints y ascenso).

## Cambiar el servicio falso por el real

`api/servidor.py` recibe el servicio desde fuera. En el bloque final del archivo hay una sola línea:

```python
servicio = PedidoServiceFalso()  # el día que exista el real, se cambia esta línea
```

Se reemplaza por el `PedidoService` real, construido con sus DAOs y la pasarela, por ejemplo:

```python
servicio = PedidoService(ProductoDAOSqlite(...), ClienteDAOSqlite(...), PedidoDAOSqlite(...), PasarelaSimulada())
```

El `PedidoService` real debe tener los mismos métodos que `PedidoServiceFalso` (ver `docs/CONTRATO.md`) y devolver entidades de `negocio/entidades.py`. Para comprobar la integración, las pruebas de `tests/` se pueden correr contra el servicio real cambiando la construcción en `BaseApi.setUp`.
