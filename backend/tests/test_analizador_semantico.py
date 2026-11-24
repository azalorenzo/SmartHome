from pathlib import Path

import pytest

from backend.compiler.analizador_semantico import validate
from backend.compiler.tabla_simbolos import tabla_inicial
from backend.language import parse


def _validar(fuente: str):
    programa = parse(fuente)
    assert not isinstance(programa, list), programa
    return validate(programa, tabla_inicial())


def test_el_programa_de_demostracion_no_tiene_errores_semanticos():
    demostracion = Path(__file__).resolve().parents[2] / "examples" / "demo.smarthome.txt"
    assert _validar(demostracion.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "fuente",
    [
        "ENCENDER luz_sala\nAPAGAR luz_sala",
        "ENCENDER ventilador1\nAPAGAR ventilador1",
        "ABRIR puerta_principal\nCERRAR puerta_principal",
        "ACTIVAR alarma1\nDESACTIVAR alarma1",
        "CONSULTAR alarma1\nLISTAR DISPOSITIVOS",
        "SI alarma1 == DESACTIVADA ENTONCES ACTIVAR alarma1",
    ],
)
def test_acepta_operaciones_compatibles(fuente):
    assert _validar(fuente) == []


@pytest.mark.parametrize(
    ("fuente", "linea", "columna", "fragmento"),
    [
        ("ENCENDER dispositivo99", 1, 1, "no existe"),
        ("CONSULTAR dispositivo99", 1, 1, "no existe"),
        ("SI dispositivo99 == ENCENDIDO ENTONCES LISTAR DISPOSITIVOS", 1, 1, "no existe"),
        ("ENCENDER alarma1", 1, 1, "operación ENCENDER"),
        ("ABRIR luz_sala", 1, 1, "operación ABRIR"),
        ("SI luz_sala == ENCENDIDO ENTONCES ACTIVAR luz_sala", 1, 35, "operación ACTIVAR"),
        (
            "SI puerta_principal == ENCENDIDO ENTONCES CERRAR puerta_principal",
            1, 1, "estado ENCENDIDO",
        ),
    ],
)
def test_informa_errores_semanticos(fuente, linea, columna, fragmento):
    (diagnostico,) = _validar(fuente)
    assert (diagnostico.fase, diagnostico.linea, diagnostico.columna) == (
        "semantica", linea, columna,
    )
    assert fragmento in diagnostico.mensaje


def test_reune_todos_los_errores_del_programa_en_orden():
    diagnosticos = _validar(
        "ENCENDER luz_sala\n"
        "ENCENDER dispositivo99\n"
        "ACTIVAR ventilador1\n"
        "SI alarma1 == ABIERTA ENTONCES APAGAR puerta_principal\n"
    )
    assert [(d.linea, d.columna) for d in diagnosticos] == [(2, 1), (3, 1), (4, 1), (4, 32)]


@pytest.mark.parametrize(
    "direccion",
    ["demo@example.com", "ana.lopez+casa@correo.itoaxaca.edu.mx", "a_b-c@sub-dominio.mx"],
)
def test_acepta_destinatarios_validos(direccion):
    assert _validar(f'ENVIAR CORREO A "{direccion}" MENSAJE "Hola"') == []


@pytest.mark.parametrize(
    "direccion",
    [
        "", "demo", "demo@", "@example.com", "demo@example", "demo@@example.com",
        "de mo@example.com", "demo@example.c", "demo..x@example.com",
        ".demo@example.com", "demo.@example.com", "demo@-example.com",
        "demo@example..com", "a" * 250 + "@ex.com",
    ],
)
def test_rechaza_destinatarios_invalidos(direccion):
    (diagnostico,) = _validar(f'ENVIAR CORREO A "{direccion}" MENSAJE "Hola"')
    assert diagnostico.fase == "semantica"
    assert "correo válido" in diagnostico.mensaje


@pytest.mark.parametrize(
    "fuente",
    [
        'NOTIFICAR ""',
        'NOTIFICAR "   "',
        'ENVIAR CORREO A "demo@example.com" MENSAJE ""',
        'SI luz_sala == APAGADO ENTONCES NOTIFICAR "\t"',
    ],
)
def test_rechaza_mensajes_vacios(fuente):
    (diagnostico,) = _validar(fuente)
    assert "vacío" in diagnostico.mensaje


def test_un_correo_puede_tener_destinatario_y_mensaje_invalidos():
    diagnosticos = _validar('ENVIAR CORREO A "demo" MENSAJE " "')
    assert len(diagnosticos) == 2
