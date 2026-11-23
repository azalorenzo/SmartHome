from .analizador_lexico import ErrorLexico, tokenizar
from .arbol_sintactico import (
    Condicional,
    Consulta,
    Control,
    EnvioCorreo,
    Instruccion,
    InstruccionSimple,
    ListadoDispositivos,
    Notificacion,
    Programa,
)
from .componentes_lexicos import ComponenteLexico, TipoComponente
from .diagnosticos import Diagnostico


_OPERACIONES = {
    TipoComponente.ENCENDER,
    TipoComponente.APAGAR,
    TipoComponente.ABRIR,
    TipoComponente.CERRAR,
    TipoComponente.ACTIVAR,
    TipoComponente.DESACTIVAR,
}
_ESTADOS = {
    TipoComponente.ENCENDIDO,
    TipoComponente.APAGADO,
    TipoComponente.ABIERTA,
    TipoComponente.CERRADA,
    TipoComponente.ACTIVADA,
    TipoComponente.DESACTIVADA,
}
_DESCRIPCIONES = {
    TipoComponente.ID: "un identificador de dispositivo",
    TipoComponente.CADENA: "una cadena entre comillas",
    TipoComponente.SALTO: "un salto de línea",
    TipoComponente.FIN: "el fin del programa",
}


class _ErrorSintactico(Exception):
    def __init__(self, componente: ComponenteLexico, esperado: str) -> None:
        encontrado = _DESCRIPCIONES.get(componente.tipo, repr(componente.valor))
        mensaje = f"Se esperaba {esperado}. Se encontró {encontrado}."
        self.diagnostico = Diagnostico(
            "sintactica", componente.linea, componente.columna, mensaje
        )
        super().__init__(mensaje)


class _AnalizadorSintactico:
    def __init__(self, componentes: list[ComponenteLexico]) -> None:
        self._componentes = componentes
        self._indice = 0

    @property
    def _actual(self) -> ComponenteLexico:
        return self._componentes[self._indice]

    def _avanzar(self) -> ComponenteLexico:
        componente = self._actual
        self._indice += 1
        return componente

    def _consumir(self, tipo: TipoComponente) -> ComponenteLexico:
        if self._actual.tipo is not tipo:
            esperado = _DESCRIPCIONES.get(tipo, repr(tipo.value))
            raise _ErrorSintactico(self._actual, esperado)
        return self._avanzar()

    def _omitir_saltos(self) -> None:
        while self._actual.tipo is TipoComponente.SALTO:
            self._avanzar()

    def programa(self) -> Programa:
        self._omitir_saltos()
        inicio = self._actual
        instrucciones = [self._instruccion()]

        while self._actual.tipo is not TipoComponente.FIN:
            self._consumir(TipoComponente.SALTO)
            self._omitir_saltos()
            if self._actual.tipo is TipoComponente.FIN:
                break
            instrucciones.append(self._instruccion())

        return Programa(inicio.linea, inicio.columna, tuple(instrucciones))

    def _instruccion(self) -> Instruccion:
        if self._actual.tipo is not TipoComponente.SI:
            return self._simple()

        inicio = self._avanzar()
        dispositivo = self._consumir(TipoComponente.ID)
        self._consumir(TipoComponente.IGUALDAD)
        if self._actual.tipo not in _ESTADOS:
            raise _ErrorSintactico(self._actual, "un estado")
        estado = self._avanzar()
        self._consumir(TipoComponente.ENTONCES)
        return Condicional(
            inicio.linea, inicio.columna, dispositivo.valor, estado.tipo, self._simple()
        )

    def _simple(self) -> InstruccionSimple:
        inicio = self._actual
        tipo = inicio.tipo
        if tipo in _OPERACIONES:
            self._avanzar()
            dispositivo = self._consumir(TipoComponente.ID)
            return Control(inicio.linea, inicio.columna, tipo, dispositivo.valor)

        match tipo:
            case TipoComponente.CONSULTAR:
                self._avanzar()
                dispositivo = self._consumir(TipoComponente.ID)
                return Consulta(inicio.linea, inicio.columna, dispositivo.valor)
            case TipoComponente.LISTAR:
                self._avanzar()
                self._consumir(TipoComponente.DISPOSITIVOS)
                return ListadoDispositivos(inicio.linea, inicio.columna)
            case TipoComponente.NOTIFICAR:
                self._avanzar()
                mensaje = self._consumir(TipoComponente.CADENA)
                return Notificacion(inicio.linea, inicio.columna, mensaje.valor)
            case TipoComponente.ENVIAR:
                self._avanzar()
                self._consumir(TipoComponente.CORREO)
                self._consumir(TipoComponente.A)
                destinatario = self._consumir(TipoComponente.CADENA)
                self._consumir(TipoComponente.MENSAJE)
                mensaje = self._consumir(TipoComponente.CADENA)
                return EnvioCorreo(
                    inicio.linea, inicio.columna, destinatario.valor, mensaje.valor
                )
            case _:
                raise _ErrorSintactico(inicio, "una instrucción simple")


def parse(fuente: str) -> Programa | list[Diagnostico]:
    """Devuelve el AST completo o una lista con el primer diagnóstico."""
    try:
        return _AnalizadorSintactico(tokenizar(fuente)).programa()
    except (ErrorLexico, _ErrorSintactico) as error:
        return [error.diagnostico]
