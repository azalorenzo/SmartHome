import re

from .diagnosticos import Diagnostico
from .componentes_lexicos import ComponenteLexico, TipoComponente


_PALABRAS_RESERVADAS = {
    tipo.value: tipo
    for tipo in TipoComponente
    if tipo not in {
        TipoComponente.ID, TipoComponente.CADENA, TipoComponente.SALTO,
        TipoComponente.IGUALDAD, TipoComponente.FIN,
    }
}
_PALABRA = re.compile(r"\w+")
_IDENTIFICADOR = re.compile(r"[a-z][a-z0-9_]*")


class ErrorLexico(ValueError):
    def __init__(self, linea: int, columna: int, mensaje: str) -> None:
        self.diagnostico = Diagnostico("lexical", linea, columna, mensaje)
        super().__init__(f"{linea}:{columna}: {mensaje}")


def _leer_cadena(fuente: str, inicio: int, linea: int, columna: int) -> tuple[str, int]:
    caracteres: list[str] = []
    indice = inicio + 1

    while indice < len(fuente):
        caracter = fuente[indice]
        if caracter == '"':
            return "".join(caracteres), indice + 1
        if caracter in "\r\n":
            break
        if caracter == "\\":
            columna_escape = columna + indice - inicio
            indice += 1
            if indice == len(fuente) or fuente[indice] in "\r\n":
                break
            caracter = fuente[indice]
            if caracter not in ('"', "\\"):
                raise ErrorLexico(linea, columna_escape, "Secuencia de escape no válida.")
        caracteres.append(caracter)
        indice += 1

    raise ErrorLexico(linea, columna, "Cadena sin comillas de cierre.")


def tokenizar(fuente: str) -> list[ComponenteLexico]:
    """Convierte el texto en componentes y agrega FIN en la posición final."""
    componentes: list[ComponenteLexico] = []
    indice = 0
    linea = 1
    inicio_linea = 0

    while indice < len(fuente):
        caracter = fuente[indice]
        columna = indice - inicio_linea + 1
        if caracter in " \t":
            indice += 1
            continue
        if caracter == "\n" or fuente.startswith("\r\n", indice):
            componentes.append(ComponenteLexico(TipoComponente.SALTO, "\n", linea, columna))
            indice += 2 if caracter == "\r" else 1
            linea += 1
            inicio_linea = indice
            continue
        if fuente.startswith("==", indice):
            tipo, valor, indice = TipoComponente.IGUALDAD, "==", indice + 2
        elif caracter == '"':
            valor, indice = _leer_cadena(fuente, indice, linea, columna)
            tipo = TipoComponente.CADENA
        else:
            palabra = _PALABRA.match(fuente, indice)
            if palabra is None:
                raise ErrorLexico(linea, columna, f"Carácter no válido: {caracter!r}.")
            valor = palabra.group()
            if valor in _PALABRAS_RESERVADAS:
                tipo = _PALABRAS_RESERVADAS[valor]
            elif _IDENTIFICADOR.fullmatch(valor):
                tipo = TipoComponente.ID
            else:
                raise ErrorLexico(linea, columna, f"Palabra no válida: {valor!r}.")
            indice = palabra.end()

        componentes.append(ComponenteLexico(tipo, valor, linea, columna))

    componentes.append(ComponenteLexico(TipoComponente.FIN, "", linea, indice - inicio_linea + 1))
    return componentes
