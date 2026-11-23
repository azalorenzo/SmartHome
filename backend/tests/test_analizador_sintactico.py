from pathlib import Path

import pytest

from backend.language import parse
from backend.language.arbol_sintactico import (
    Condicional,
    Consulta,
    Control,
    EnvioCorreo,
    ListadoDispositivos,
    Notificacion,
    Programa,
)
from backend.language.componentes_lexicos import TipoComponente


def test_construye_arbol_completo_de_la_demostracion():
    demostracion = Path(__file__).resolve().parents[2] / "examples" / "demo.smarthome.txt"

    assert parse(demostracion.read_text(encoding="utf-8")) == Programa(
        1,
        1,
        (
            Control(1, 1, TipoComponente.ENCENDER, "luz_sala"),
            Consulta(2, 1, "luz_sala"),
            Control(3, 1, TipoComponente.ENCENDER, "ventilador1"),
            Control(4, 1, TipoComponente.ABRIR, "puerta_principal"),
            Control(5, 1, TipoComponente.ACTIVAR, "alarma1"),
            Condicional(
                6,
                1,
                "puerta_principal",
                TipoComponente.ABIERTA,
                Control(6, 41, TipoComponente.CERRAR, "puerta_principal"),
            ),
            Notificacion(7, 1, "Puerta cerrada y alarma activada"),
            EnvioCorreo(8, 1, "demo@example.com", "Revisión completada"),
            ListadoDispositivos(9, 1),
        ),
    )


def test_acepta_un_estado_reservado_sin_validar_el_tipo_de_dispositivo():
    assert parse('SI puerta_principal == ENCENDIDO ENTONCES NOTIFICAR ""') == Programa(
        1,
        1,
        (
            Condicional(
                1, 1, "puerta_principal", TipoComponente.ENCENDIDO, Notificacion(1, 43, "")
            ),
        ),
    )


def test_analiza_instrucciones_simples_con_posiciones():
    fuente = (
        "\r\n\tENCENDER luz_sala\r\n\r\n"
        "CONSULTAR luz_sala\n"
        "LISTAR DISPOSITIVOS\n"
        'NOTIFICAR "Puerta cerrada"\n'
        'ENVIAR CORREO A "demo@example.com" MENSAJE "Revisión completada"\n'
    )
    assert parse(fuente) == Programa(
        2,
        2,
        (
            Control(2, 2, TipoComponente.ENCENDER, "luz_sala"),
            Consulta(4, 1, "luz_sala"),
            ListadoDispositivos(5, 1),
            Notificacion(6, 1, "Puerta cerrada"),
            EnvioCorreo(7, 1, "demo@example.com", "Revisión completada"),
        ),
    )


@pytest.mark.parametrize(
    ("fuente", "fase", "linea", "columna"),
    [
        ("", "sintactica", 1, 1),
        ("\r\n\n", "sintactica", 3, 1),
        ("ENCENDER", "sintactica", 1, 9),
        ("ENCENDER\nluz_sala", "sintactica", 1, 9),
        ("ENCENDER luz_sala@", "lexica", 1, 18),
        ("LISTAR", "sintactica", 1, 7),
        ("LISTAR DISPOSITIVOS CONSULTAR luz_sala", "sintactica", 1, 21),
        ('ENVIAR CORREO A "a@b.com" "hola"', "sintactica", 1, 27),
        ("SI luz_sala ENCENDIDO ENTONCES APAGAR luz_sala", "sintactica", 1, 13),
        ("SI luz_sala == encendido ENTONCES APAGAR luz_sala", "sintactica", 1, 16),
        ("SI luz_sala == ENCENDIDO APAGAR luz_sala", "sintactica", 1, 26),
        ("SI luz_sala == ENCENDIDO ENTONCES SI", "sintactica", 1, 35),
    ],
)
def test_informa_fase_y_posicion_del_error(fuente, fase, linea, columna):
    resultado = parse(fuente)
    assert isinstance(resultado, list)
    (diagnostico,) = resultado
    assert (diagnostico.fase, diagnostico.linea, diagnostico.columna) == (
        fase, linea, columna,
    )
    assert diagnostico.mensaje
