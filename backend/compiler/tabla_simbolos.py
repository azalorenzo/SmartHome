"""Tabla de símbolos de los dispositivos de SmartHome.

Combina el catálogo de dispositivos (en producción, las filas de la tabla
``devices`` de PostgreSQL) con las reglas de cada tipo, que viven en Python:
qué operaciones admite y qué estados son válidos.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from backend.language.componentes_lexicos import TipoComponente


class TipoDispositivo(StrEnum):
    LUZ = "LUZ"
    VENTILADOR = "VENTILADOR"
    PUERTA = "PUERTA"
    ALARMA = "ALARMA"


# Operación de control → estado que deja en el dispositivo.
ESTADO_RESULTANTE: dict[TipoComponente, TipoComponente] = {
    TipoComponente.ENCENDER: TipoComponente.ENCENDIDO,
    TipoComponente.APAGAR: TipoComponente.APAGADO,
    TipoComponente.ABRIR: TipoComponente.ABIERTA,
    TipoComponente.CERRAR: TipoComponente.CERRADA,
    TipoComponente.ACTIVAR: TipoComponente.ACTIVADA,
    TipoComponente.DESACTIVAR: TipoComponente.DESACTIVADA,
}

# Operaciones de control permitidas por tipo. CONSULTAR se admite en todos.
OPERACIONES_POR_TIPO: dict[TipoDispositivo, frozenset[TipoComponente]] = {
    TipoDispositivo.LUZ: frozenset({TipoComponente.ENCENDER, TipoComponente.APAGAR}),
    TipoDispositivo.VENTILADOR: frozenset({TipoComponente.ENCENDER, TipoComponente.APAGAR}),
    TipoDispositivo.PUERTA: frozenset({TipoComponente.ABRIR, TipoComponente.CERRAR}),
    TipoDispositivo.ALARMA: frozenset({TipoComponente.ACTIVAR, TipoComponente.DESACTIVAR}),
}

# Estados válidos por tipo: los que dejan sus operaciones.
ESTADOS_POR_TIPO: dict[TipoDispositivo, frozenset[TipoComponente]] = {
    tipo: frozenset(ESTADO_RESULTANTE[operacion] for operacion in operaciones)
    for tipo, operaciones in OPERACIONES_POR_TIPO.items()
}


@dataclass(frozen=True)
class Simbolo:
    identificador: str
    etiqueta: str
    tipo: TipoDispositivo
    estado: TipoComponente

    @property
    def operaciones(self) -> frozenset[TipoComponente]:
        return OPERACIONES_POR_TIPO[self.tipo]

    @property
    def estados(self) -> frozenset[TipoComponente]:
        return ESTADOS_POR_TIPO[self.tipo]


class TablaSimbolos:
    """Catálogo de dispositivos indexado por identificador."""

    def __init__(self, simbolos: Iterable[Simbolo]) -> None:
        self._simbolos: dict[str, Simbolo] = {}
        for simbolo in simbolos:
            if simbolo.identificador in self._simbolos:
                raise ValueError(f"Dispositivo duplicado: {simbolo.identificador!r}.")
            if simbolo.estado not in ESTADOS_POR_TIPO[simbolo.tipo]:
                raise ValueError(
                    f"El estado {simbolo.estado} no es válido para "
                    f"{simbolo.identificador!r} de tipo {simbolo.tipo}."
                )
            self._simbolos[simbolo.identificador] = simbolo

    @classmethod
    def desde_registros(cls, registros: Iterable[Mapping[str, str]]) -> "TablaSimbolos":
        """Construye la tabla con filas que tienen ``id``, ``label``, ``type`` y ``state``.

        Es el formato de la tabla ``devices`` y de ``GET /api/devices``.
        """
        return cls(
            Simbolo(
                registro["id"],
                registro["label"],
                TipoDispositivo(registro["type"]),
                TipoComponente(registro["state"]),
            )
            for registro in registros
        )

    def buscar(self, identificador: str) -> Simbolo | None:
        return self._simbolos.get(identificador)

    def __contains__(self, identificador: object) -> bool:
        return identificador in self._simbolos

    def __iter__(self):
        return iter(sorted(self._simbolos.values(), key=lambda simbolo: simbolo.identificador))

    def __len__(self) -> int:
        return len(self._simbolos)


CATALOGO_INICIAL: tuple[Simbolo, ...] = (
    Simbolo("luz_sala", "Luz de la sala", TipoDispositivo.LUZ, TipoComponente.APAGADO),
    Simbolo("ventilador1", "Ventilador", TipoDispositivo.VENTILADOR, TipoComponente.APAGADO),
    Simbolo("puerta_principal", "Puerta principal", TipoDispositivo.PUERTA, TipoComponente.CERRADA),
    Simbolo("alarma1", "Alarma", TipoDispositivo.ALARMA, TipoComponente.DESACTIVADA),
)


def tabla_inicial() -> TablaSimbolos:
    """Tabla con los cuatro dispositivos del plan en su estado inicial."""
    return TablaSimbolos(CATALOGO_INICIAL)
