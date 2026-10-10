import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from api.servicio_falso import PedidoServiceFalso


def _a_json(obj):
    """Hook de json.dumps para los tipos que no serializa por defecto."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"No serializable: {type(obj).__name__}")


def crear_handler(servicio):
    """Devuelve un handler que usa el `servicio` recibido desde fuera."""

    class Handler(BaseHTTPRequestHandler):
        def _responder(self, codigo: int, datos) -> None:
            cuerpo = json.dumps(datos, ensure_ascii=False, default=_a_json)
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(cuerpo.encode("utf-8"))

        def do_GET(self):
            ruta = urlparse(self.path).path
            partes = ruta.strip("/").split("/")

            if partes == ["api", "productos"]:
                productos = [asdict(p) for p in servicio.listar_menu()]
                self._responder(200, productos)
            elif partes[:2] == ["api", "clientes"] and len(partes) == 3:
                try:
                    cliente_id = int(partes[2])
                except ValueError:
                    self._responder(400, {"error": "El id debe ser un entero"})
                    return
                cliente = servicio.obtener_cliente(cliente_id)
                if cliente is None:
                    self._responder(404, {"error": "Cliente no encontrado"})
                else:
                    self._responder(200, asdict(cliente))
            else:
                self._responder(404, {"error": "Ruta no encontrada"})

        def do_POST(self):
            ruta = urlparse(self.path).path
            partes = ruta.strip("/").split("/")

            if partes == ["api", "clientes"]:
                try:
                    largo = int(self.headers.get("Content-Length", 0))
                    datos = json.loads(self.rfile.read(largo))
                except (ValueError, UnicodeDecodeError):
                    self._responder(400, {"error": "JSON inválido"})
                    return
                if not isinstance(datos, dict):
                    self._responder(400, {"error": "El cuerpo debe ser un objeto JSON"})
                    return
                nombre, correo = datos.get("nombre"), datos.get("correo")
                if not (isinstance(nombre, str) and nombre.strip()
                        and isinstance(correo, str) and correo.strip()):
                    self._responder(400, {"error": "Se requieren 'nombre' y 'correo'"})
                    return
                cliente = servicio.crear_cliente(nombre.strip(), correo.strip())
                self._responder(201, asdict(cliente))
            else:
                self._responder(404, {"error": "Ruta no encontrada"})

    return Handler


if __name__ == "__main__":
    servicio = PedidoServiceFalso()  # el día que exista el real, se cambia esta línea
    print("API en http://localhost:8000")
    HTTPServer(("localhost", 8000), crear_handler(servicio)).serve_forever()
