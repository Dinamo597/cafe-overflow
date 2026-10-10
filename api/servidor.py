"""Capa API: traduce HTTP/JSON <-> llamadas al servicio. Sin reglas de negocio."""
import json
import os
import re
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from api.servicio_falso import PedidoServiceFalso
from negocio.entidades import EstadoPedido, ItemPedido
from negocio.excepciones import (
    ErrorNegocio, NoEncontrado, PedidoPendienteExistente, StockInsuficiente,
)

MAX_CUERPO = 1_000_000


class ErrorSolicitud(Exception):
    """Solicitud mal formada (JSON inválido, campos faltantes o mal tipados)."""


def _a_json(obj):
    """Hook de json.dumps para los tipos que no serializa por defecto."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"No serializable: {type(obj).__name__}")


def _codigo_http(error: ErrorNegocio) -> int:
    if isinstance(error, NoEncontrado):
        return 404
    if isinstance(error, (StockInsuficiente, PedidoPendienteExistente)):
        return 409
    return 400


def _entero(valor, campo: str, minimo: int = None) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ErrorSolicitud(f"'{campo}' debe ser un entero")
    if minimo is not None and valor < minimo:
        raise ErrorSolicitud(f"'{campo}' debe ser >= {minimo}")
    return valor


def _id_de_ruta(texto: str) -> int:
    try:
        return int(texto)
    except ValueError:
        raise ErrorSolicitud("El id debe ser un entero")


def _datos_pedido(datos: dict):
    """Valida la sintaxis del cuerpo de cotizar / crear pedido."""
    cliente_id = _entero(datos.get("cliente_id"), "cliente_id")
    crudos = datos.get("items")
    if not isinstance(crudos, list) or not crudos:
        raise ErrorSolicitud("'items' debe ser una lista no vacía")
    items = []
    for crudo in crudos:
        if not isinstance(crudo, dict):
            raise ErrorSolicitud("Cada ítem debe ser un objeto")
        items.append(ItemPedido(
            producto_id=_entero(crudo.get("producto_id"), "producto_id"),
            cantidad=_entero(crudo.get("cantidad"), "cantidad", minimo=1),
        ))
    devpoints = _entero(datos.get("devpoints_a_redimir", 0), "devpoints_a_redimir", minimo=0)
    return cliente_id, items, devpoints


def crear_handler(servicio, silencioso: bool = False):
    """Devuelve un handler que usa el `servicio` recibido desde fuera."""

    class Handler(BaseHTTPRequestHandler):
        # ---- utilidades -------------------------------------------------
        def log_message(self, formato, *args):
            if not silencioso:
                super().log_message(formato, *args)

        def _responder(self, codigo: int, datos) -> None:
            cuerpo = json.dumps(datos, ensure_ascii=False, default=_a_json).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def _leer_json(self) -> dict:
            try:
                largo = int(self.headers.get("Content-Length", 0))
                if largo > MAX_CUERPO:
                    raise ErrorSolicitud("Cuerpo demasiado grande")
                datos = json.loads(self.rfile.read(largo))
            except (ValueError, UnicodeDecodeError):
                raise ErrorSolicitud("JSON inválido")
            if not isinstance(datos, dict):
                raise ErrorSolicitud("El cuerpo debe ser un objeto JSON")
            return datos

        # ---- endpoints --------------------------------------------------
        def _get_productos(self, consulta):
            return 200, [asdict(p) for p in servicio.listar_menu()]

        def _post_clientes(self, consulta):
            datos = self._leer_json()
            nombre, correo = datos.get("nombre"), datos.get("correo")
            if not (isinstance(nombre, str) and nombre.strip()
                    and isinstance(correo, str) and correo.strip()):
                raise ErrorSolicitud("Se requieren 'nombre' y 'correo'")
            return 201, asdict(servicio.crear_cliente(nombre.strip(), correo.strip()))

        def _get_cliente(self, consulta, cliente_id):
            cliente = servicio.obtener_cliente(_id_de_ruta(cliente_id))
            if cliente is None:
                return 404, {"error": "Cliente no encontrado"}
            return 200, asdict(cliente)

        def _post_cotizar(self, consulta):
            cliente_id, items, devpoints = _datos_pedido(self._leer_json())
            return 200, asdict(servicio.cotizar(cliente_id, items, devpoints))

        def _post_pedidos(self, consulta):
            cliente_id, items, devpoints = _datos_pedido(self._leer_json())
            return 201, asdict(servicio.crear_pedido(cliente_id, items, devpoints))

        def _post_pagar(self, consulta, pedido_id):
            return 200, asdict(servicio.pagar_pedido(_id_de_ruta(pedido_id)))

        def _post_estado(self, consulta, pedido_id):
            return 200, asdict(servicio.avanzar_estado(_id_de_ruta(pedido_id)))

        def _get_pedidos(self, consulta):
            cliente = consulta.get("cliente_id", [None])[0]
            estado = consulta.get("estado", [None])[0]
            if cliente is not None and estado is not None:
                raise ErrorSolicitud("Use 'cliente_id' o 'estado', no ambos")
            if cliente is not None:
                pedidos = servicio.listar_pedidos(_id_de_ruta(cliente))
            else:
                try:
                    filtro = EstadoPedido(estado) if estado is not None else None
                except ValueError:
                    raise ErrorSolicitud("Estado inválido")
                pedidos = servicio.listar_todos(filtro)
            return 200, [asdict(p) for p in pedidos]

        RUTAS = [
            ("GET", r"/api/productos", "_get_productos"),
            ("POST", r"/api/clientes", "_post_clientes"),
            ("GET", r"/api/clientes/([^/]+)", "_get_cliente"),
            ("POST", r"/api/pedidos/cotizar", "_post_cotizar"),
            ("POST", r"/api/pedidos", "_post_pedidos"),
            ("GET", r"/api/pedidos", "_get_pedidos"),
            ("POST", r"/api/pedidos/([^/]+)/pagar", "_post_pagar"),
            ("POST", r"/api/pedidos/([^/]+)/estado", "_post_estado"),
        ]

        # ---- despacho ---------------------------------------------------
        def _despachar(self, metodo: str) -> None:
            url = urlparse(self.path)
            ruta = url.path.rstrip("/") or "/"
            coincide_ruta = False
            try:
                for m, patron, nombre in self.RUTAS:
                    encontrado = re.fullmatch(patron, ruta)
                    if not encontrado:
                        continue
                    coincide_ruta = True
                    if m == metodo:
                        codigo, cuerpo = getattr(self, nombre)(
                            parse_qs(url.query), *encontrado.groups())
                        return self._responder(codigo, cuerpo)
                if coincide_ruta:
                    return self._responder(405, {"error": "Método no permitido"})
                return self._responder(404, {"error": "Ruta no encontrada"})
            except ErrorSolicitud as e:
                self._responder(400, {"error": str(e)})
            except ErrorNegocio as e:
                self._responder(_codigo_http(e), {"error": str(e)})
            except Exception:
                self._responder(500, {"error": "Error interno del servidor"})

        def do_GET(self):
            self._despachar("GET")

        def do_POST(self):
            self._despachar("POST")

    return Handler


if __name__ == "__main__":
    servicio = PedidoServiceFalso()  # el día que exista el real, se cambia esta línea
    puerto = int(os.environ.get("API_PORT", 8000))
    print(f"API en http://localhost:{puerto}")
    HTTPServer(("localhost", puerto), crear_handler(servicio)).serve_forever()
