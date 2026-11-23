from pathlib import Path

import pytest

from backend.language.analizador_lexico import ErrorLexico, tokenizar
from backend.language.componentes_lexicos import ComponenteLexico, TipoComponente


def test_tokeniza_demostracion():
    demostracion = Path(__file__).resolve().parents[2] / "examples" / "demo.smarthome.txt"
    componentes = tokenizar(demostracion.read_text(encoding="utf-8"))
    assert componentes[:2] == [
        ComponenteLexico(TipoComponente.ENCENDER, "ENCENDER", 1, 1),
        ComponenteLexico(TipoComponente.ID, "luz_sala", 1, 10),
    ]
    cadenas = [
        componente.valor
        for componente in componentes
        if componente.tipo is TipoComponente.CADENA
    ]
    assert cadenas == [
        "Puerta cerrada y alarma activada",
        "demo@example.com",
        "Revisión completada",
    ]
    assert componentes[-1].tipo is TipoComponente.FIN


def test_conserva_saltos_y_decodifica_escapes():
    componentes = tokenizar('\r\n\tNOTIFICAR "a\\"b\\\\c"\n\n')
    assert componentes == [
        ComponenteLexico(TipoComponente.SALTO, "\n", 1, 1),
        ComponenteLexico(TipoComponente.NOTIFICAR, "NOTIFICAR", 2, 2),
        ComponenteLexico(TipoComponente.CADENA, 'a"b\\c', 2, 12),
        ComponenteLexico(TipoComponente.SALTO, "\n", 2, 21),
        ComponenteLexico(TipoComponente.SALTO, "\n", 3, 1),
        ComponenteLexico(TipoComponente.FIN, "", 4, 1),
    ]


@pytest.mark.parametrize(
    ("fuente", "linea", "columna"),
    [
        ("ENCENDER luz_sala@", 1, 18),
        ("ENCENDER\r\nSI luz_sala = ENCENDIDO", 2, 13),
        ("ENCENDER Luz_sala", 1, 10),
        ('NOTIFICAR "sin cierre\n', 1, 11),
        (r'NOTIFICAR "a\q"', 1, 13),
    ],
)
def test_informa_errores_lexicos(fuente, linea, columna):
    with pytest.raises(ErrorLexico) as error:
        tokenizar(fuente)
    diagnostico = error.value.diagnostico
    assert (diagnostico.fase, diagnostico.linea, diagnostico.columna) == (
        "lexica", linea, columna,
    )


def test_admite_instruccion_incompleta():
    assert [componente.tipo for componente in tokenizar("ENCENDER")] == [
        TipoComponente.ENCENDER, TipoComponente.FIN,
    ]
