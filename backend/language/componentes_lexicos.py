from dataclasses import dataclass
from enum import StrEnum


class TipoComponente(StrEnum):
    ENCENDER = "ENCENDER"
    APAGAR = "APAGAR"
    ABRIR = "ABRIR"
    CERRAR = "CERRAR"
    ACTIVAR = "ACTIVAR"
    DESACTIVAR = "DESACTIVAR"
    CONSULTAR = "CONSULTAR"
    LISTAR = "LISTAR"
    DISPOSITIVOS = "DISPOSITIVOS"
    NOTIFICAR = "NOTIFICAR"
    ENVIAR = "ENVIAR"
    CORREO = "CORREO"
    A = "A"
    MENSAJE = "MENSAJE"
    SI = "SI"
    ENTONCES = "ENTONCES"
    ENCENDIDO = "ENCENDIDO"
    APAGADO = "APAGADO"
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"
    ACTIVADA = "ACTIVADA"
    DESACTIVADA = "DESACTIVADA"
    ID = "ID"
    CADENA = "CADENA"
    SALTO = "SALTO"
    IGUALDAD = "=="
    FIN = "EOF"


@dataclass(frozen=True)
class ComponenteLexico:
    tipo: TipoComponente
    valor: str
    linea: int
    columna: int
