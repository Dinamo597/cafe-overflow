from negocio.entidades import Cliente, NivelLealtad
from negocio.daos import ClienteDAO


class ClienteService:
    def __init__(self, cliente_dao: ClienteDAO):
        self.cliente_dao = cliente_dao

    def crear_cliente(self, nombre: str, correo: str) -> Cliente:
        cliente = Cliente(id=None, nombre=nombre, correo=correo, nivel=NivelLealtad.JUNIOR)
        return self.cliente_dao.crear(cliente)

    def obtener_cliente(self, cliente_id: int) -> Cliente:
        return self.cliente_dao.obtener(cliente_id)
