// Servidor de presentación: sirve los estáticos y reenvía /api/* a la API Python.
// Solo módulos de Node (sin Express). Reenviar evita problemas de CORS.
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT || 3000);
const API = new URL(process.env.API_URL || 'http://127.0.0.1:8000');
const PUBLIC = path.join(__dirname, 'public');

const TIPOS = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.png': 'image/png',
};

function json(res, codigo, cuerpo) {
  res.writeHead(codigo, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(cuerpo));
}

function reenviar(req, res) {
  const proxy = http.request(
    {
      hostname: API.hostname,
      port: API.port,
      path: req.url,
      method: req.method,
      headers: { ...req.headers, host: API.host },
    },
    (respuesta) => {
      res.writeHead(respuesta.statusCode, respuesta.headers);
      respuesta.pipe(res);
    }
  );
  proxy.on('error', () => json(res, 502, { error: 'La API no está disponible' }));
  req.pipe(proxy);
}

function estatico(req, res) {
  let ruta;
  try {
    ruta = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  } catch {
    return json(res, 400, { error: 'URL inválida' });
  }
  if (ruta === '/') ruta = '/index.html';
  const archivo = path.normalize(path.join(PUBLIC, ruta));
  if (!archivo.startsWith(PUBLIC + path.sep)) return json(res, 403, { error: 'Prohibido' });
  fs.readFile(archivo, (err, datos) => {
    if (err) return json(res, 404, { error: 'No encontrado' });
    res.writeHead(200, { 'Content-Type': TIPOS[path.extname(archivo)] || 'application/octet-stream' });
    res.end(datos);
  });
}

const servidor = http.createServer((req, res) => {
  if (req.url.startsWith('/api/')) return reenviar(req, res);
  if (req.method !== 'GET' && req.method !== 'HEAD') return json(res, 405, { error: 'Método no permitido' });
  estatico(req, res);
});

servidor.listen(PORT, () => {
  console.log(`Presentación en http://localhost:${PORT}  (API -> ${API.origin})`);
});
