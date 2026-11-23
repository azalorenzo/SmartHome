from dataclasses import dataclass

from .componentes_lexicos import TipoComponente


@dataclass(frozen=True)
class Nodo:
    linea: int
    columna: int


@dataclass(frozen=True)
class Control(Nodo):
    operacion: TipoComponente
    dispositivo: str


@dataclass(frozen=True)
class Consulta(Nodo):
    dispositivo: str


@dataclass(frozen=True)
class ListadoDispositivos(Nodo):
    pass


@dataclass(frozen=True)
class Notificacion(Nodo):
    mensaje: str


@dataclass(frozen=True)
class EnvioCorreo(Nodo):
    destinatario: str
    mensaje: str


InstruccionSimple = Control | Consulta | ListadoDispositivos | Notificacion | EnvioCorreo


@dataclass(frozen=True)
class Condicional(Nodo):
    dispositivo: str
    estado: TipoComponente
    instruccion: InstruccionSimple


Instruccion = InstruccionSimple | Condicional


@dataclass(frozen=True)
class Programa(Nodo):
    instrucciones: tuple[Instruccion, ...]
