# C2 — Diagrama de contenedores

```mermaid
C4Container
    title Café Overflow — Diagrama de contenedores (C2)

    Person(cliente, "Cliente", "Desarrollador que hace pedidos")
    Person(personal, "Personal", "Prepara y entrega pedidos")

    System_Boundary(cafe, "Café Overflow") {
        Container(presentacion, "Presentación", "Node.js (http) + HTML/CSS/JS", "Sirve la interfaz y reenvía /api/* a la API (evita CORS)")
        Container(api, "API", "Python, http.server", "Traduce HTTP/JSON a llamadas de negocio y mapea errores a códigos HTTP")
        Container(negocio, "Negocio", "Python", "Reglas: descuentos, DevPoints, niveles, estados del pedido, validaciones")
        Container(persistencia, "Persistencia", "Python, DAOs", "Acceso a datos tras interfaces DAO")
        ContainerDb(bd, "Base de datos", "SQLite", "Productos, clientes y pedidos")
    }

    System_Ext(pasarela, "Pasarela de pago (simulada)", "Aprueba o rechaza cobros")

    Rel(cliente, presentacion, "Usa el navegador", "HTTPS")
    Rel(personal, presentacion, "Gestiona la cola de pedidos", "HTTPS")
    Rel(presentacion, api, "Reenvía /api/*", "HTTP/JSON")
    Rel(api, negocio, "Invoca servicios", "llamada Python")
    Rel(negocio, persistencia, "Usa DAOs", "llamada Python")
    Rel(persistencia, bd, "Lee y escribe", "SQL")
    Rel(negocio, pasarela, "Cobra pedidos", "llamada Python (simulada)")
```

Notas:

- La base de datos es SQLite (no Redis).
- No hay API de inventario.
- `negocio` define las interfaces DAO y `persistencia` las implementa; `negocio` no contiene SQL, HTML ni JSON.
