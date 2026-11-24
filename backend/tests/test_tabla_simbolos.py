import pytest

from backend.compiler.tabla_simbolos import (
    ESTADOS_POR_TIPO,
    Simbolo,
    TablaSimbolos,
    TipoDispositivo,
    tabla_inicial,
)
from backend.language.componentes_lexicos import TipoComponente


def test_tabla_inicial_contiene_los_cuatro_dispositivos_del_plan():
    tabla = tabla_inicial()
    assert [simbolo.identificador for simbolo in tabla] == [
        "alarma1", "luz_sala", "puerta_principal", "ventilador1",
    ]
    assert tabla.buscar("puerta_principal") == Simbolo(
        "puerta_principal", "Puerta principal", TipoDispositivo.PUERTA, TipoComponente.CERRADA
    )
    assert "dispositivo99" not in tabla
    assert tabla.buscar("dispositivo99") is None


@pytest.mark.parametrize(
    ("tipo", "operaciones", "estados"),
    [
        (TipoDispositivo.LUZ, {"ENCENDER", "APAGAR"}, {"ENCENDIDO", "APAGADO"}),
        (TipoDispositivo.VENTILADOR, {"ENCENDER", "APAGAR"}, {"ENCENDIDO", "APAGADO"}),
        (TipoDispositivo.PUERTA, {"ABRIR", "CERRAR"}, {"ABIERTA", "CERRADA"}),
        (TipoDispositivo.ALARMA, {"ACTIVAR", "DESACTIVAR"}, {"ACTIVADA", "DESACTIVADA"}),
    ],
)
def test_reglas_por_tipo(tipo, operaciones, estados):
    simbolo = Simbolo("x", "X", tipo, next(iter(ESTADOS_POR_TIPO[tipo])))
    assert {operacion.value for operacion in simbolo.operaciones} == operaciones
    assert {estado.value for estado in simbolo.estados} == estados


def test_construye_la_tabla_desde_registros_de_la_base():
    tabla = TablaSimbolos.desde_registros(
        [{"id": "luz_sala", "label": "Luz de la sala", "type": "LUZ", "state": "ENCENDIDO"}]
    )
    assert tabla.buscar("luz_sala").estado is TipoComponente.ENCENDIDO
    assert len(tabla) == 1


def test_rechaza_estado_incompatible_con_el_tipo():
    with pytest.raises(ValueError):
        TablaSimbolos([Simbolo("puerta", "Puerta", TipoDispositivo.PUERTA, TipoComponente.ENCENDIDO)])


def test_rechaza_identificadores_duplicados():
    simbolo = Simbolo("luz_sala", "Luz", TipoDispositivo.LUZ, TipoComponente.APAGADO)
    with pytest.raises(ValueError):
        TablaSimbolos([simbolo, simbolo])
