"""Validación semántica del AST contra la tabla de símbolos.

Recorre el programa completo y devuelve todos los diagnósticos encontrados,
para que ningún lote se ejecute si tiene un error en cualquier línea.
"""

import re

from backend.language.arbol_sintactico import (
    Condicional,
    Consulta,
    Control,
    EnvioCorreo,
    Instruccion,
    InstruccionSimple,
    Nodo,
    Notificacion,
    Programa,
)
from backend.language.diagnosticos import Diagnostico

from .tabla_simbolos import Simbolo, TablaSimbolos


# usuario@dominio.tld: sin espacios, con al menos un punto en el dominio.
_CORREO = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
    r"\.[A-Za-z]{2,}"
)
_LONGITUD_MAXIMA_CORREO = 254


def es_correo_valido(direccion: str) -> bool:
    return (
        len(direccion) <= _LONGITUD_MAXIMA_CORREO
        and _CORREO.fullmatch(direccion) is not None
        and ".." not in direccion
        and not direccion.startswith(".")
        and ".@" not in direccion
    )


class _Validador:
    def __init__(self, tabla: TablaSimbolos) -> None:
        self._tabla = tabla
        self.diagnosticos: list[Diagnostico] = []

    def _error(self, nodo: Nodo, mensaje: str) -> None:
        self.diagnosticos.append(Diagnostico("semantica", nodo.linea, nodo.columna, mensaje))

    def _dispositivo(self, nodo: Nodo, identificador: str) -> Simbolo | None:
        simbolo = self._tabla.buscar(identificador)
        if simbolo is None:
            self._error(nodo, f"El dispositivo {identificador!r} no existe.")
        return simbolo

    def instruccion(self, instruccion: Instruccion) -> None:
        if isinstance(instruccion, Condicional):
            self._condicional(instruccion)
        else:
            self._simple(instruccion)

    def _condicional(self, condicional: Condicional) -> None:
        simbolo = self._dispositivo(condicional, condicional.dispositivo)
        if simbolo is not None and condicional.estado not in simbolo.estados:
            validos = ", ".join(sorted(simbolo.estados))
            self._error(
                condicional,
                f"El estado {condicional.estado} no es compatible con "
                f"{simbolo.identificador!r} de tipo {simbolo.tipo}. "
                f"Estados válidos: {validos}.",
            )
        self._simple(condicional.instruccion)

    def _simple(self, instruccion: InstruccionSimple) -> None:
        match instruccion:
            case Control(operacion=operacion, dispositivo=identificador):
                simbolo = self._dispositivo(instruccion, identificador)
                if simbolo is not None and operacion not in simbolo.operaciones:
                    validas = ", ".join(sorted(simbolo.operaciones | {"CONSULTAR"}))
                    self._error(
                        instruccion,
                        f"La operación {operacion} no es compatible con "
                        f"{simbolo.identificador!r} de tipo {simbolo.tipo}. "
                        f"Operaciones válidas: {validas}.",
                    )
            case Consulta(dispositivo=identificador):
                self._dispositivo(instruccion, identificador)
            case Notificacion(mensaje=mensaje):
                self._mensaje(instruccion, mensaje, "La notificación")
            case EnvioCorreo(destinatario=destinatario, mensaje=mensaje):
                if not es_correo_valido(destinatario):
                    self._error(
                        instruccion,
                        f"El destinatario {destinatario!r} no es un correo válido.",
                    )
                self._mensaje(instruccion, mensaje, "El mensaje del correo")

    def _mensaje(self, nodo: Nodo, mensaje: str, sujeto: str) -> None:
        if not mensaje.strip():
            self._error(nodo, f"{sujeto} no puede estar vacío.")


def validate(programa: Programa, tabla: TablaSimbolos) -> list[Diagnostico]:
    """Devuelve los diagnósticos semánticos del programa, en orden de línea."""
    validador = _Validador(tabla)
    for instruccion in programa.instrucciones:
        validador.instruccion(instruccion)
    return validador.diagnosticos
