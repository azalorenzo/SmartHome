import pytest

from backend.language import parse
from backend.language.arbol_sintactico import (
    Consulta,
    Control,
    EnvioCorreo,
    ListadoDispositivos,
    Notificacion,
    Programa,
)
from backend.language.componentes_lexicos import TipoComponente


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
        ("", "syntactic", 1, 1),
        ("\r\n\n", "syntactic", 3, 1),
        ("ENCENDER", "syntactic", 1, 9),
        ("ENCENDER\nluz_sala", "syntactic", 1, 9),
        ("ENCENDER luz_sala@", "lexical", 1, 18),
        ("LISTAR", "syntactic", 1, 7),
        ("LISTAR DISPOSITIVOS CONSULTAR luz_sala", "syntactic", 1, 21),
        ('ENVIAR CORREO A "a@b.com" "hola"', "syntactic", 1, 27),
    ],
)
def test_informa_fase_y_posicion_del_error(fuente, fase, linea, columna):
    resultado = parse(fuente)
    assert isinstance(resultado, list)
    (diagnostico,) = resultado
    assert (diagnostico.phase, diagnostico.line, diagnostico.column) == (
        fase, linea, columna,
    )
    assert diagnostico.message
