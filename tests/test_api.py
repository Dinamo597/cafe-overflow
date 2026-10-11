import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer

from api.servicio_real import crear_servicio
from api.servidor import crear_handler
from negocio.pasarela import PasarelaSimulada


class BaseApi(unittest.TestCase):
    pasarela_aprueba = True

    def setUp(self):
        self.servicio = crear_servicio(":memory:", PasarelaSimulada(aprueba=self.pasarela_aprueba))
        self.servidor = HTTPServer(("127.0.0.1", 0), crear_handler(self.servicio, silencioso=True))
        self.base = f"http://127.0.0.1:{self.servidor.server_address[1]}"
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def ajustar_cliente(self, cliente_id, **campos):
        """Fija datos del cliente directamente en la BD de prueba (p. ej. monto acumulado)."""
        cliente = self.servicio._clientes.obtener(cliente_id)
        for campo, valor in campos.items():
            setattr(cliente, campo, valor)
        self.servicio._clientes.actualizar(cliente)

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()

    def pedir(self, metodo, ruta, cuerpo=None, crudo=None):
        datos = crudo if crudo is not None else (json.dumps(cuerpo).encode() if cuerpo is not None else None)
        req = urllib.request.Request(self.base + ruta, data=datos, method=metodo)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def cliente(self, nombre="Ana", correo="ana@x.co"):
        return self.pedir("POST", "/api/clientes", {"nombre": nombre, "correo": correo})[1]

    def pedido(self, cliente_id, items=None, devpoints=0):
        items = items or [{"producto_id": 1, "cantidad": 1}]
        return self.pedir("POST", "/api/pedidos", {
            "cliente_id": cliente_id, "items": items, "devpoints_a_redimir": devpoints})

    def entregar(self, pedido_id):
        self.pedir("POST", f"/api/pedidos/{pedido_id}/pagar")
        self.pedir("POST", f"/api/pedidos/{pedido_id}/estado")
        return self.pedir("POST", f"/api/pedidos/{pedido_id}/estado")[1]

    def cotizar(self, cliente_id, items, devpoints=0):
        return self.pedir("POST", "/api/pedidos/cotizar", {
            "cliente_id": cliente_id, "items": items, "devpoints_a_redimir": devpoints})


class TestProductosYClientes(BaseApi):
    def test_productos(self):
        codigo, cuerpo = self.pedir("GET", "/api/productos")
        self.assertEqual(codigo, 200)
        self.assertEqual(len(cuerpo), 3)
        self.assertEqual(set(cuerpo[0]), {"id", "nombre", "precio_base", "stock"})

    def test_crear_y_obtener_cliente(self):
        codigo, c = self.pedir("POST", "/api/clientes", {"nombre": " Ana ", "correo": "ana@x.co"})
        self.assertEqual(codigo, 201)
        self.assertEqual((c["nombre"], c["nivel"], c["dev_points"], c["monto_acumulado"]),
                         ("Ana", "Junior", 0, 0))
        codigo, c2 = self.pedir("GET", f"/api/clientes/{c['id']}")
        self.assertEqual((codigo, c2), (200, c))

    def test_cliente_inexistente_404(self):
        self.assertEqual(self.pedir("GET", "/api/clientes/99")[0], 404)

    def test_cliente_id_no_entero_400(self):
        self.assertEqual(self.pedir("GET", "/api/clientes/abc")[0], 400)

    def test_crear_cliente_invalido_400(self):
        self.assertEqual(self.pedir("POST", "/api/clientes", crudo=b"esto no es json")[0], 400)
        self.assertEqual(self.pedir("POST", "/api/clientes", crudo=b"[1,2]")[0], 400)
        self.assertEqual(self.pedir("POST", "/api/clientes", {"nombre": "Ana"})[0], 400)
        self.assertEqual(self.pedir("POST", "/api/clientes", {"nombre": "", "correo": "a@b.c"})[0], 400)
        self.assertEqual(self.pedir("POST", "/api/clientes", {"nombre": 5, "correo": "a@b.c"})[0], 400)

    def test_ruta_inexistente_404_y_metodo_405(self):
        self.assertEqual(self.pedir("GET", "/api/nada")[0], 404)
        self.assertEqual(self.pedir("POST", "/api/productos", {})[0], 405)


class TestCotizar(BaseApi):
    def test_cotizacion_junior(self):
        c = self.cliente()
        codigo, cot = self.cotizar(c["id"], [{"producto_id": 2, "cantidad": 2}])
        self.assertEqual(codigo, 200)
        self.assertEqual(cot, {"subtotal": 50000, "descuento_nivel": 2500,
                               "descuento_devpoints": 0, "total": 47500, "devpoints_a_ganar": 2})

    def test_errores(self):
        c = self.cliente()
        item = [{"producto_id": 1, "cantidad": 1}]
        self.assertEqual(self.cotizar(99, item)[0], 404)
        self.assertEqual(self.cotizar(c["id"], [{"producto_id": 77, "cantidad": 1}])[0], 404)
        self.assertEqual(self.cotizar(c["id"], [{"producto_id": 1, "cantidad": 999}])[0], 409)
        self.assertEqual(self.cotizar(c["id"], item, 5)[0], 400)           # DevPoints insuficientes
        self.assertEqual(self.cotizar(c["id"], [])[0], 400)
        self.assertEqual(self.cotizar(c["id"], [{"producto_id": 1, "cantidad": 0}])[0], 400)
        self.assertEqual(self.cotizar(c["id"], item, -1)[0], 400)
        self.assertEqual(self.cotizar("1", item)[0], 400)
        self.assertEqual(self.pedir("POST", "/api/pedidos/cotizar", crudo=b"{")[0], 400)

    def test_cotizar_no_descuenta_stock(self):
        c = self.cliente()
        self.cotizar(c["id"], [{"producto_id": 1, "cantidad": 5}])
        self.assertEqual(self.pedir("GET", "/api/productos")[1][0]["stock"], 50)

    def test_total_minimo_cero(self):
        c = self.cliente()
        self.ajustar_cliente(c["id"], dev_points=1000)
        cot = self.cotizar(c["id"], [{"producto_id": 3, "cantidad": 1}], 1000)[1]
        self.assertEqual((cot["total"], cot["devpoints_a_ganar"]), (0, 0))


class TestPedidos(BaseApi):
    def test_crear_pedido_descuenta_stock(self):
        c = self.cliente()
        codigo, p = self.pedido(c["id"], [{"producto_id": 1, "cantidad": 3}])
        self.assertEqual(codigo, 201)
        self.assertEqual((p["estado"], p["total"]), ("Pendiente de pago", 22800))
        self.assertTrue(p["fecha"].endswith("+00:00"))
        self.assertEqual(self.pedir("GET", "/api/productos")[1][0]["stock"], 47)

    def test_stock_insuficiente_409(self):
        c = self.cliente()
        codigo, cuerpo = self.pedido(c["id"], [{"producto_id": 2, "cantidad": 31}])
        self.assertEqual(codigo, 409)
        self.assertIn("error", cuerpo)

    def test_pedido_pendiente_existente_409(self):
        c = self.cliente()
        self.assertEqual(self.pedido(c["id"])[0], 201)
        self.assertEqual(self.pedido(c["id"])[0], 409)

    def test_otro_cliente_puede_pedir(self):
        a, b = self.cliente(), self.cliente("Beto", "b@x.co")
        self.assertEqual(self.pedido(a["id"])[0], 201)
        self.assertEqual(self.pedido(b["id"])[0], 201)

    def test_pagar_y_estados(self):
        c = self.cliente()
        p = self.pedido(c["id"])[1]
        ruta = f"/api/pedidos/{p['id']}"
        self.assertEqual(self.pedir("POST", ruta + "/estado")[1]["estado"], "Pendiente de pago")   # sin pagar no avanza
        self.assertEqual(self.pedir("POST", ruta + "/pagar")[1]["estado"], "En Preparación")
        self.assertEqual(self.pedir("POST", ruta + "/pagar")[0], 400)    # ya pagado
        self.assertEqual(self.pedir("POST", ruta + "/estado")[1]["estado"], "Listo")
        self.assertEqual(self.pedir("POST", ruta + "/estado")[1]["estado"], "Entregado")
        self.assertEqual(self.pedir("POST", ruta + "/estado")[1]["estado"], "Entregado")   # ya entregado no cambia

    def test_pedido_inexistente_y_id_invalido(self):
        self.assertEqual(self.pedir("POST", "/api/pedidos/99/pagar")[0], 404)
        self.assertEqual(self.pedir("POST", "/api/pedidos/99/estado")[0], 404)
        self.assertEqual(self.pedir("POST", "/api/pedidos/abc/pagar")[0], 400)

    def test_listar_por_cliente_y_estado(self):
        a, b = self.cliente(), self.cliente("Beto", "b@x.co")
        pa = self.pedido(a["id"])[1]
        self.pedido(b["id"])
        self.pedir("POST", f"/api/pedidos/{pa['id']}/pagar")
        codigo, lista = self.pedir("GET", f"/api/pedidos?cliente_id={a['id']}")
        self.assertEqual((codigo, [p["id"] for p in lista]), (200, [pa["id"]]))
        self.assertEqual(len(self.pedir("GET", "/api/pedidos")[1]), 2)
        self.assertEqual(len(self.pedir("GET", "/api/pedidos?estado=En%20Preparaci%C3%B3n")[1]), 1)
        self.assertEqual(len(self.pedir("GET", "/api/pedidos?estado=Pendiente%20de%20pago")[1]), 1)
        self.assertEqual(self.pedir("GET", "/api/pedidos?estado=Nada")[0], 400)
        self.assertEqual(self.pedir("GET", "/api/pedidos?cliente_id=x")[0], 400)
        self.assertEqual(self.pedir("GET", "/api/pedidos?cliente_id=99")[0], 404)
        self.assertEqual(self.pedir("GET", "/api/pedidos?cliente_id=1&estado=Listo")[0], 400)


class TestPagoRechazado(BaseApi):
    pasarela_aprueba = False

    def test_pago_rechazado_402(self):
        c = self.cliente()
        p = self.pedido(c["id"])[1]
        codigo, cuerpo = self.pedir("POST", f"/api/pedidos/{p['id']}/pagar")
        self.assertEqual(codigo, 402)
        self.assertIn("error", cuerpo)
        self.assertEqual(self.pedir("GET", f"/api/pedidos?cliente_id={c['id']}")[1][0]["estado"], "Pendiente de pago")


class TestRecorridoCompleto(BaseApi):
    def test_recorrido_con_devpoints(self):
        cid = self.cliente()["id"]
        # 10 combos = 250000; Junior 5 % -> 237500; gana 11 DevPoints al entregar
        self.assertEqual(self.cotizar(cid, [{"producto_id": 2, "cantidad": 10}])[1]["total"], 237500)
        p = self.pedido(cid, [{"producto_id": 2, "cantidad": 10}])[1]
        self.assertEqual(p["total"], 237500)
        self.assertEqual(self.pedir("GET", "/api/productos")[1][1]["stock"], 20)
        self.assertEqual(self.entregar(p["id"])["estado"], "Entregado")
        yo = self.pedir("GET", f"/api/clientes/{cid}")[1]
        self.assertEqual((yo["monto_acumulado"], yo["dev_points"], yo["nivel"]), (237500, 11, "Junior"))

        # Redime los 11 DevPoints = $2.200 de descuento directo
        items = [{"producto_id": 1, "cantidad": 20}]
        cot = self.cotizar(cid, items, 11)[1]
        self.assertEqual(cot, {"subtotal": 160000, "descuento_nivel": 8000,
                               "descuento_devpoints": 2200, "total": 149800, "devpoints_a_ganar": 7})
        p2 = self.pedido(cid, items, 11)[1]
        self.assertEqual(p2["total"], 149800)
        self.pedir("POST", f"/api/pedidos/{p2['id']}/pagar")   # los puntos se descuentan al pagar
        self.assertEqual(self.pedir("GET", f"/api/clientes/{cid}")[1]["dev_points"], 0)
        self.pedir("POST", f"/api/pedidos/{p2['id']}/estado")
        self.pedir("POST", f"/api/pedidos/{p2['id']}/estado")
        yo = self.pedir("GET", f"/api/clientes/{cid}")[1]
        self.assertEqual((yo["monto_acumulado"], yo["dev_points"]), (387300, 7))
        self.assertEqual(len(self.pedir("GET", f"/api/pedidos?cliente_id={cid}")[1]), 2)
        self.assertEqual(len(self.pedir("GET", "/api/pedidos?estado=Entregado")[1]), 2)

    def test_ascenso_a_mid_y_senior(self):
        cid = self.cliente()["id"]
        item = [{"producto_id": 1, "cantidad": 1}]
        self.ajustar_cliente(cid, monto_acumulado=499000)
        p = self.pedido(cid, item)[1]
        self.assertEqual(self.pedir("GET", f"/api/clientes/{cid}")[1]["nivel"], "Junior")
        self.entregar(p["id"])
        self.assertEqual(self.pedir("GET", f"/api/clientes/{cid}")[1]["nivel"], "Mid")
        # el descuento nuevo aplica desde la siguiente compra: 8000 - 10 %
        self.assertEqual(self.cotizar(cid, item)[1]["descuento_nivel"], 800)

        self.ajustar_cliente(cid, monto_acumulado=1_495_000)
        self.entregar(self.pedido(cid, item)[1]["id"])
        self.assertEqual(self.pedir("GET", f"/api/clientes/{cid}")[1]["nivel"], "Senior")
        self.assertEqual(self.cotizar(cid, item)[1]["descuento_nivel"], 1200)


if __name__ == "__main__":
    unittest.main()
