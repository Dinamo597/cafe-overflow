import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer

from api.servicio_falso import PedidoServiceFalso


def crear_handler(servicio):
    """Devuelve un handler que usa el `servicio` recibido desde fuera."""

    class Handler(BaseHTTPRequestHandler):
        def _responder(self, codigo: int, datos) -> None:
            cuerpo = json.dumps(datos, ensure_ascii=False)
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(cuerpo.encode("utf-8"))

        def do_GET(self):
            if self.path == "/api/productos":
                productos = [asdict(p) for p in servicio.listar_menu()]
                self._responder(200, productos)
            else:
                self._responder(404, {"error": "Ruta no encontrada"})

    return Handler


if __name__ == "__main__":
    servicio = PedidoServiceFalso()  # el día que exista el real, se cambia esta línea
    print("API en http://localhost:8000")
    HTTPServer(("localhost", 8000), crear_handler(servicio)).serve_forever()
