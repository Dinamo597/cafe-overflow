'use strict';
// Presentación: solo renderiza, captura formularios y valida sintaxis.
// Todo valor de negocio (totales, descuentos, niveles, DevPoints) viene de la API.

const $app = document.getElementById('app');
const montar = (...nodos) => $app.replaceChildren(...nodos.flat(Infinity).filter((n) => n != null && n !== false));
const COP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
const formatoFecha = new Intl.DateTimeFormat('es-CO', {
  timeZone: 'America/Bogota', dateStyle: 'medium', timeStyle: 'short',
});
const fecha = (iso) => formatoFecha.format(new Date(iso));
const PASOS = ['Pendiente de pago', 'En Preparación', 'Listo', 'Entregado']; // solo para dibujar el avance
const REGEX_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ---------- utilidades ----------
function el(tag, attrs = {}, ...hijos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'class') e.className = v;
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const h of hijos.flat()) {
    if (h == null || h === false) continue;
    e.append(typeof h === 'object' ? h : document.createTextNode(String(h)));
  }
  return e;
}

const guardar = {
  leer(clave, defecto) {
    try { const v = localStorage.getItem(clave); return v == null ? defecto : JSON.parse(v); } catch { return defecto; }
  },
  escribir(clave, valor) {
    try { localStorage.setItem(clave, JSON.stringify(valor)); } catch { /* sin almacenamiento */ }
  },
  borrar(clave) {
    try { localStorage.removeItem(clave); } catch { /* sin almacenamiento */ }
  },
};

function aviso(texto, error = false) {
  const t = el('div', { class: 'toast' + (error ? ' err' : ''), role: error ? 'alert' : 'status' }, texto);
  document.getElementById('toasts').append(t);
  setTimeout(() => t.remove(), error ? 6000 : 3500);
}

async function api(metodo, ruta, cuerpo) {
  let r;
  try {
    r = await fetch('/api' + ruta, {
      method: metodo,
      headers: cuerpo ? { 'Content-Type': 'application/json' } : {},
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new Error('No se pudo conectar con el servidor');
  }
  let datos = null;
  try { datos = await r.json(); } catch { /* sin cuerpo */ }
  if (!r.ok) throw Object.assign(new Error((datos && datos.error) || `Error ${r.status}`), { status: r.status });
  return datos;
}

async function accion(boton, fn) {
  if (boton) boton.disabled = true;
  try { await fn(); } catch (e) { aviso(e.message, true); } finally { if (boton) boton.disabled = false; }
}

// ---------- estado local (solo sesión del navegador) ----------
let carrito = guardar.leer('carrito', []);          // [{producto_id, cantidad}]
const idCliente = () => guardar.leer('clienteId', null);

function guardarCarrito() {
  guardar.escribir('carrito', carrito);
  const total = carrito.reduce((s, i) => s + i.cantidad, 0);
  const badge = document.getElementById('badge');
  badge.textContent = total;
  badge.hidden = total === 0;
}

async function cargarCliente() {
  const id = idCliente();
  if (id == null) return null;
  try {
    return await api('GET', `/clientes/${id}`);
  } catch (e) {
    if (e.status === 404) guardar.borrar('clienteId');
    else throw e;
    return null;
  }
}

const insigniaNivel = (nivel) => el('span', { class: `nivel ${nivel}` }, nivel);
const enlaceCuenta = () => el('a', { href: '#/cliente' }, 'cuenta');

// ---------- vistas ----------
async function vistaMenu() {
  const productos = await api('GET', '/productos');
  montar(
    el('h1', {}, 'menu'),
    el('p', { class: 'sub' }, 'Combustible para tu próximo commit.'),
    el('div', { class: 'rejilla' }, productos.map((p) => {
      const enCarrito = (carrito.find((i) => i.producto_id === p.id) || {}).cantidad || 0;
      return el('div', { class: 'tarjeta' },
        el('h2', {}, p.nombre),
        el('div', { class: 'precio' }, COP.format(p.precio_base)),
        el('div', { class: 'stock' + (p.stock === 0 ? ' agotado' : p.stock <= 5 ? ' bajo' : '') },
          p.stock === 0 ? 'agotado' : `stock: ${p.stock}`),
        el('button', {
          class: 'primario', disabled: p.stock === 0,
          onclick: (ev) => {
            const item = carrito.find((i) => i.producto_id === p.id);
            if (item) item.cantidad += 1; else carrito.push({ producto_id: p.id, cantidad: 1 });
            guardarCarrito();
            aviso(`${p.nombre} agregado al carrito`);
            ev.target.textContent = `+ agregar (${enCarrito + 1} en carrito)`;
          },
        }, enCarrito ? `+ agregar (${enCarrito} en carrito)` : '+ agregar'));
    })));
}

async function vistaCarrito() {
  const [productos, cliente] = await Promise.all([api('GET', '/productos'), cargarCliente()]);
  const porId = new Map(productos.map((p) => [p.id, p]));
  carrito = carrito.filter((i) => porId.has(i.producto_id));
  guardarCarrito();
  let dev_points = 0;
  let cotizacion = null;

  const zonaCot = el('div');
  const pintarCotizacion = () => {
    if (!cotizacion) { zonaCot.replaceChildren(); return; }
    const c = cotizacion;
    zonaCot.replaceChildren(el('div', { class: 'caja' },
      el('div', { class: 'desglose' },
        el('span', {}, 'subtotal'), el('span', {}, COP.format(c.subtotal)),
        el('span', {}, `descuento nivel ${cliente.nivel}`), el('span', { class: 'desc' }, '- ' + COP.format(c.descuento_nivel)),
        el('span', {}, 'descuento DevPoints'), el('span', { class: 'desc' }, '- ' + COP.format(c.descuento_devpoints)),
        el('div', { class: 'total' }, el('span', {}, 'total'), el('span', {}, COP.format(c.total)))),
      el('p', { class: 'meta' }, `Ganarás ${c.devpoints_a_ganar} DevPoints cuando recibas tu pedido.`),
      el('div', { class: 'acciones' },
        el('button', {
          class: 'primario',
          onclick: (ev) => accion(ev.target, async () => {
            const pedido = await api('POST', '/pedidos', cuerpoPedido());
            carrito = [];
            guardarCarrito();
            aviso(`Pedido #${pedido.id} creado. Págalo para enviarlo a preparación.`);
            location.hash = '#/pedidos';
          }),
        }, 'confirmar pedido'))));
  };

  const cuerpoPedido = () => ({ cliente_id: cliente.id, items: carrito, devpoints_a_redimir: dev_points });

  const dibujar = () => {
    cotizacion = null;
    if (carrito.length === 0) {
      montar(el('h1', {}, 'carrito'),
        el('p', { class: 'vacio' }, 'Tu carrito está vacío. ', el('a', { href: '#/menu' }, 'Ver el menú')));
      return;
    }
    if (!cliente) {
      montar(el('h1', {}, 'carrito'),
        el('p', { class: 'vacio' }, 'Necesitas una cuenta para cotizar. Ve a ', enlaceCuenta(), '.'));
      return;
    }
    const campoDev = el('input', {
      type: 'number', min: '0', step: '1', value: String(dev_points), id: 'dev_points',
      oninput: (ev) => {
        const n = Number(ev.target.value);
        dev_points = Number.isInteger(n) && n >= 0 ? n : 0;
        ev.target.classList.toggle('invalido', !(Number.isInteger(n) && n >= 0));
        cotizacion = null;
        pintarCotizacion();
      },
    });
    montar(
      el('h1', {}, 'carrito'),
      el('p', { class: 'sub' }, `Cliente: ${cliente.nombre} · nivel `, insigniaNivel(cliente.nivel),
        ` · ${cliente.dev_points} DevPoints`),
      el('div', { class: 'caja' }, carrito.map((item) => {
        const p = porId.get(item.producto_id);
        return el('div', { class: 'fila' },
          el('div', {}, el('b', {}, p.nombre), el('div', { class: 'meta' }, `${COP.format(p.precio_base)} c/u`)),
          el('div', { class: 'cant' },
            el('button', { class: 'mini', 'aria-label': 'menos', onclick: () => cambiar(item, -1) }, '−'),
            el('b', {}, item.cantidad),
            el('button', { class: 'mini', 'aria-label': 'más', onclick: () => cambiar(item, 1) }, '+'),
            el('button', { class: 'mini peligro', 'aria-label': 'quitar', onclick: () => cambiar(item, -item.cantidad) }, '✕')));
      })),
      el('div', { class: 'caja' },
        el('label', { for: 'dev_points' }, 'DevPoints a redimir (opcional)', campoDev)),
      el('div', { class: 'acciones' },
        el('button', {
          class: 'azul',
          onclick: (ev) => accion(ev.target, async () => {
            cotizacion = await api('POST', '/pedidos/cotizar', cuerpoPedido());
            pintarCotizacion();
          }),
        }, 'cotizar')),
      zonaCot);
  };

  const cambiar = (item, delta) => {
    item.cantidad += delta;
    carrito = carrito.filter((i) => i.cantidad > 0);
    guardarCarrito();
    dibujar();
  };
  dibujar();
}

function tarjetaPedido(pedido, nombres, { alPagar, alAvanzar, verCliente } = {}) {
  const idx = PASOS.indexOf(pedido.estado);
  return el('div', { class: 'caja' },
    el('div', { class: 'fila' },
      el('b', {}, `Pedido #${pedido.id}`),
      el('span', { class: 'precio' }, COP.format(pedido.total))),
    el('div', { class: 'pasos' }, PASOS.map((p, i) =>
      el('span', { class: 'paso' + (i < idx ? ' hecho' : i === idx ? ' actual' : '') }, p))),
    el('div', { class: 'items' }, pedido.items.map((i) => `${i.cantidad}× ${nombres.get(i.producto_id) || 'producto ' + i.producto_id}`).join(' · ')),
    el('div', { class: 'meta' }, fecha(pedido.fecha), verCliente ? ` · cliente #${pedido.cliente_id}` : ''),
    (alPagar && pedido.estado === 'Pendiente de pago') &&
      el('div', { class: 'acciones' }, el('button', {
        class: 'primario', onclick: (ev) => accion(ev.target, () => alPagar(pedido)),
      }, 'pagar')),
    alAvanzar && (pedido.estado === 'Pendiente de pago'
      ? el('div', { class: 'meta' }, 'esperando el pago del cliente')
      : pedido.estado !== 'Entregado' &&
        el('div', { class: 'acciones' }, el('button', {
          class: 'azul', onclick: (ev) => accion(ev.target, () => alAvanzar(pedido)),
        }, 'avanzar estado'))));
}

async function vistaPedidos() {
  if (idCliente() == null) {
    montar(el('h1', {}, 'mis_pedidos'),
      el('p', { class: 'vacio' }, 'Primero crea o consulta tu ', enlaceCuenta(), '.'));
    return;
  }
  const pintar = async () => {
    const id = idCliente();
    const [productos, pedidos] = await Promise.all([api('GET', '/productos'), api('GET', `/pedidos?cliente_id=${id}`)]);
    const nombres = new Map(productos.map((p) => [p.id, p.nombre]));
    const lista = [...pedidos].reverse();
    montar(
      el('h1', {}, 'mis_pedidos'),
      el('p', { class: 'sub' }, 'Se actualiza solo cada pocos segundos.'),
      lista.length === 0
        ? el('p', { class: 'vacio' }, 'Aún no tienes pedidos. ', el('a', { href: '#/menu' }, 'Ir al menú'))
        : lista.map((p) => tarjetaPedido(p, nombres, {
          alPagar: async (ped) => {
            await api('POST', `/pedidos/${ped.id}/pagar`);
            aviso(`Pedido #${ped.id} pagado`);
            await pintar();
          },
        })));
  };
  await pintar();
  temporizador = setInterval(() => pintar().catch(() => {}), 5000);
}

async function vistaCliente() {
  const cliente = await cargarCliente();
  const resultado = el('div');

  const errorNombre = el('div', { class: 'error-campo' });
  const errorCorreo = el('div', { class: 'error-campo' });
  const nombre = el('input', { id: 'nombre', required: true, maxlength: '80', autocomplete: 'name' });
  const correo = el('input', { id: 'correo', type: 'email', required: true, autocomplete: 'email' });
  const formRegistro = el('form', {
    novalidate: true,
    onsubmit: async (ev) => {
      ev.preventDefault();
      const n = nombre.value.trim(), c = correo.value.trim();
      errorNombre.textContent = n ? '' : 'El nombre es obligatorio';
      errorCorreo.textContent = REGEX_CORREO.test(c) ? '' : 'Ingresa un correo válido';
      nombre.classList.toggle('invalido', !n);
      correo.classList.toggle('invalido', !REGEX_CORREO.test(c));
      if (!n || !REGEX_CORREO.test(c)) return;
      await accion(ev.submitter, async () => {
        const nuevo = await api('POST', '/clientes', { nombre: n, correo: c });
        guardar.escribir('clienteId', nuevo.id);
        aviso(`Bienvenido, ${nuevo.nombre}. Tu id es ${nuevo.id}`);
        await vistaCliente();
      });
    },
  },
    el('label', { for: 'nombre' }, 'nombre', nombre), errorNombre,
    el('label', { for: 'correo' }, 'correo', correo), errorCorreo,
    el('button', { class: 'primario', type: 'submit' }, 'crear cuenta'));

  const errorId = el('div', { class: 'error-campo' });
  const campoId = el('input', { id: 'idc', type: 'number', min: '1', step: '1', required: true });
  const formConsulta = el('form', {
    novalidate: true,
    onsubmit: async (ev) => {
      ev.preventDefault();
      const n = Number(campoId.value);
      const valido = Number.isInteger(n) && n >= 1;
      errorId.textContent = valido ? '' : 'Ingresa un id entero positivo';
      campoId.classList.toggle('invalido', !valido);
      if (!valido) return;
      await accion(ev.submitter, async () => {
        const c = await api('GET', `/clientes/${n}`);
        guardar.escribir('clienteId', c.id);
        aviso(`Sesión iniciada como ${c.nombre}`);
        await vistaCliente();
      });
    },
  },
    el('label', { for: 'idc' }, 'tu id de cliente', campoId), errorId,
    el('button', { type: 'submit' }, 'consultar'));

  if (cliente) {
    montar(
      el('h1', {}, 'cuenta'),
      el('div', { class: 'caja' },
        el('div', { class: 'fila' },
          el('div', {}, el('b', {}, cliente.nombre), el('div', { class: 'meta' }, `${cliente.correo} · id ${cliente.id}`)),
          insigniaNivel(cliente.nivel)),
        el('div', { class: 'datos' },
          el('div', { class: 'dato' }, el('b', {}, cliente.dev_points), el('span', {}, 'DevPoints')),
          el('div', { class: 'dato' }, el('b', {}, COP.format(cliente.monto_acumulado)), el('span', {}, 'acumulado en compras')),
          el('div', { class: 'dato' }, el('b', {}, cliente.nivel), el('span', {}, 'nivel actual'))),
        el('div', { class: 'acciones' }, el('button', {
          class: 'peligro', onclick: () => { guardar.borrar('clienteId'); vistaCliente(); },
        }, 'cerrar sesión'))));
  } else {
    montar(
      el('h1', {}, 'cuenta'),
      el('p', { class: 'sub' }, 'Crea tu cuenta o consulta una existente con tu id.'),
      el('div', { class: 'caja' }, el('h2', {}, 'nuevo cliente'), formRegistro),
      el('div', { class: 'caja' }, el('h2', {}, 'ya tengo cuenta'), formConsulta),
      resultado);
  }
}

async function vistaPersonal() {
  let filtro = '';
  const pintar = async () => {
    const [productos, pedidos] = await Promise.all([
      api('GET', '/productos'),
      api('GET', '/pedidos' + (filtro ? `?estado=${encodeURIComponent(filtro)}` : '')),
    ]);
    const nombres = new Map(productos.map((p) => [p.id, p.nombre]));
    const selector = el('select', {
      id: 'filtro', onchange: (ev) => { filtro = ev.target.value; pintar().catch((e) => aviso(e.message, true)); },
    },
      el('option', { value: '' }, 'todos'),
      PASOS.map((p) => el('option', { value: p, selected: p === filtro }, p)));
    montar(
      el('h1', {}, 'personal'),
      el('p', { class: 'sub' }, 'Cola de pedidos. Avanza cada uno hasta entregarlo.'),
      el('div', { class: 'caja' }, el('label', { for: 'filtro' }, 'filtrar por estado', selector)),
      pedidos.length === 0
        ? el('p', { class: 'vacio' }, 'No hay pedidos.')
        : [...pedidos].reverse().map((p) => tarjetaPedido(p, nombres, {
          verCliente: true,
          alAvanzar: async (ped) => {
            const r = await api('POST', `/pedidos/${ped.id}/estado`);
            aviso(`Pedido #${r.id}: ${r.estado}`);
            await pintar();
          },
        })));
  };
  await pintar();
  temporizador = setInterval(() => pintar().catch(() => {}), 5000);
}

// ---------- enrutador ----------
const vistas = { menu: vistaMenu, carrito: vistaCarrito, pedidos: vistaPedidos, cliente: vistaCliente, personal: vistaPersonal };
let temporizador = null;

async function navegar() {
  clearInterval(temporizador);
  const nombre = location.hash.replace(/^#\//, '') || 'menu';
  const vista = vistas[nombre] || vistaMenu;
  document.querySelectorAll('nav a').forEach((a) => a.classList.toggle('activo', a.dataset.vista === nombre));
  montar(el('p', { class: 'cargando' }, 'cargando'));
  try {
    await vista();
  } catch (e) {
    montar(el('div', { class: 'error' }, e.message));
  }
}

window.addEventListener('hashchange', navegar);
guardarCarrito();
navegar();
