# C1 — Diagrama de contexto

```mermaid
C4Context
    title Café Overflow — Diagrama de contexto (C1)

    Person(cliente, "Cliente", "Desarrollador que consulta el menú, arma su pedido y lo paga")
    Person(personal, "Personal de la cafetería", "Prepara los pedidos y actualiza su estado")

    System(cafe, "Café Overflow", "Sistema web de pedidos con niveles de fidelidad y DevPoints")

    System_Ext(pasarela, "Pasarela de pago (simulada)", "Aprueba o rechaza los cobros")

    Rel(cliente, cafe, "Consulta el menú, hace y paga pedidos", "HTTPS")
    Rel(personal, cafe, "Consulta la cola y avanza el estado de los pedidos", "HTTPS")
    Rel(cafe, pasarela, "Solicita el cobro de un pedido", "llamada interna (simulada)")
```

Notas:

- No hay API de inventario: el stock vive en la base de datos del propio sistema.
- La pasarela de pago es simulada (`PasarelaSimulada`, en `negocio/pasarela.py`).
- El personal apunta hacia el sistema (es quien lo usa), igual que el cliente.
