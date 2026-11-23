# SmartHome — Plan de desarrollo e integración

**Proyecto:** SmartHome — Sistema de automatización de dispositivos inteligentes  
**Materia:** Lenguajes y Autómatas II  
**Equipo:** cinco integrantes

El desarrollo se divide en cinco entregas consecutivas. Cada integrante termina su bloque, comprueba sus pruebas de aceptación e integra sus ramas en `develop` antes de pasar el turno. La primera entrega es la gramática, el lexer, el parser y el AST.

## 1. Alcance y dispositivos

La aplicación web tendrá una consola multilínea, un panel de dispositivos simulados, una vista de resultados, un historial y una lista de notificaciones. Los correos de prueba serán visibles en Mailpit.

| Identificador | Nombre | Tipo | Estado inicial | Estados válidos | Comandos |
|---|---|---|---|---|---|
| `luz_sala` | Luz de la sala | `LUZ` | `APAGADO` | `ENCENDIDO`, `APAGADO` | `ENCENDER`, `APAGAR`, `CONSULTAR` |
| `ventilador1` | Ventilador | `VENTILADOR` | `APAGADO` | `ENCENDIDO`, `APAGADO` | `ENCENDER`, `APAGAR`, `CONSULTAR` |
| `puerta_principal` | Puerta principal | `PUERTA` | `CERRADA` | `ABIERTA`, `CERRADA` | `ABRIR`, `CERRAR`, `CONSULTAR` |
| `alarma1` | Alarma | `ALARMA` | `DESACTIVADA` | `ACTIVADA`, `DESACTIVADA` | `ACTIVAR`, `DESACTIVAR`, `CONSULTAR` |

Una migración carga los dispositivos al instalar. PostgreSQL conserva sus estados al reiniciar.

## 2. Tecnologías

| Parte | Herramientas |
|---|---|
| Lenguaje de instrucciones | EBNF, Python 3.12 y `dataclasses` para el AST. |
| Semántica, código intermedio y ejecución | Python 3.12. |
| API REST | FastAPI, Pydantic y JSON. |
| Persistencia | PostgreSQL, SQLAlchemy y Alembic. |
| Correo de pruebas | `smtplib` y Mailpit. |
| Interfaz web | React, TypeScript, Vite y CSS. |
| Pruebas | Pytest y Vitest. |
| Colaboración | Git, GitHub, Pull Requests y GitHub Projects. |
| Despliegue | Docker Compose con `frontend`, `backend`, `postgres` y `mailpit`. |

## 3. Gramática

```ebnf
programa     = { SALTO }, instruccion, { SALTO, { SALTO }, instruccion }, { SALTO } ;
instruccion  = simple | condicional ;
simple       = control | consulta | listado | notificacion | correo ;
control      = ( "ENCENDER" | "APAGAR" | "ABRIR" | "CERRAR" |
                 "ACTIVAR" | "DESACTIVAR" ), ID ;
consulta     = "CONSULTAR", ID ;
listado      = "LISTAR", "DISPOSITIVOS" ;
notificacion = "NOTIFICAR", CADENA ;
correo       = "ENVIAR", "CORREO", "A", CADENA, "MENSAJE", CADENA ;
condicional  = "SI", ID, "==", estado, "ENTONCES", simple ;
estado       = "ENCENDIDO" | "APAGADO" | "ABIERTA" | "CERRADA" |
               "ACTIVADA" | "DESACTIVADA" ;
```

- Una instrucción por línea y al menos una por programa. Se permiten líneas vacías, espacios y tabulaciones fuera de las cadenas, y saltos LF o CRLF.
- Las palabras reservadas y estados van en mayúsculas. Los identificadores siguen `[a-z][a-z0-9_]*`. Las cadenas usan comillas dobles, ocupan una línea y admiten comillas y barras invertidas escapadas.
- `SI … ENTONCES` compara el estado actual y ejecuta un comando simple si coincide. `REPETIR`, `SINO`, variables y condiciones anidadas quedan fuera del alcance.
- El AST incorpora `Program`, `Control`, `Query`, `ListDevices`, `Notify`, `SendEmail` e `If`, con posiciones de origen. Los diagnósticos tienen `phase`, `line`, `column` y `message`. Las posiciones empiezan en 1.

| Entrada | Resultado esperado |
|---|---|
| `ENCENDER luz_sala@` | Error léxico. |
| `ENCENDER` | Error sintáctico. |
| `ENCENDER dispositivo99` | Error semántico por dispositivo inexistente. |
| `ENCENDER alarma1` | Error semántico por operación incompatible. |
| `SI puerta_principal == ENCENDIDO ENTONCES CERRAR puerta_principal` | Error semántico por estado incompatible. |

## 4. Contratos de integración

| Función | Entrada y salida |
|---|---|
| `parse(source)` | Texto completo → AST o diagnósticos léxicos/sintácticos. |
| `compile_program(ast, symbols)` | AST y tabla de símbolos → código intermedio o diagnósticos semánticos. Valida dispositivos, tipos, operaciones, estados, mensajes con contenido y destinatarios con formato válido. |
| `optimize(ir)` | Código intermedio → código equivalente con destinos de salto válidos. |
| `execute(ir, services)` | Código intermedio y servicios de dispositivos, notificaciones y SMTP → resultados en orden y, si corresponde, un fallo de ejecución. |

La IR contiene `SET_STATE(device, state)`, `GET_STATE(device)`, `LIST_DEVICES`, `COMPARE_STATE(device, state)`, `JUMP_IF_FALSE(label)`, `NOTIFY(message)`, `SEND_EMAIL(recipient, message)` y `HALT`.

### Persistencia y ejecución

| Tabla | Campos |
|---|---|
| `devices` | `id`, `label`, `type`, `state`. La base valida los pares de tipo y estado. |
| `executions` | `id`, `source`, `status`, `diagnostics`, `results`, `created_at`, `finished_at`. Diagnósticos y resultados se guardan como JSONB. |
| `notifications` | `id`, `execution_id`, `message`, `created_at`. Cada notificación referencia su ejecución. |

La tabla de símbolos combina el catálogo de PostgreSQL con las operaciones permitidas por tipo en Python. Se valida el programa completo antes de ejecutarlo y se procesa un lote a la vez. Se registra el intento rechazado sin aplicar cambios. Si falla SMTP, se detiene el lote, se conservan los efectos confirmados y se registra el fallo sin reenvío automático. El correo usa el asunto fijo **Notificación SmartHome**.

### Optimizaciones

1. **Eliminar escrituras redundantes.** Dos `ENCENDER luz_sala` consecutivos pueden quedar en una escritura.
2. **Eliminar escrituras sobrescritas.** `ENCENDER luz_sala` seguido de `APAGAR luz_sala` puede quedar en la última escritura dentro de un tramo consecutivo de `SET_STATE`.

Cada tramo se confirma como una unidad. Las consultas, los listados, las condiciones, las notificaciones, el correo y las etiquetas de salto terminan el tramo. El historial guarda el texto original, los resultados observables y el resumen final de estados. Las pruebas comparan las ejecuciones con y sin optimización, incluida la secuencia `ENCENDER luz_sala → CONSULTAR luz_sala → APAGAR luz_sala`, que debe devolver `ENCENDIDO` en la consulta en ambos casos. Los efectos externos conservan su orden.

### API

| Ruta | Contrato |
|---|---|
| `POST /api/executions` | Recibe `{"source":"ENCENDER luz_sala"}`. Devuelve `id`, `status`, `diagnostics` y `results`. Estados finales: `succeeded`, `rejected` y `failed`. Cada resultado tiene `line`, `kind` y `data`. |
| `GET /api/devices` | Devuelve `id`, `label`, `type` y `state`, ordenados por identificador. |
| `GET /api/executions` | Devuelve hasta 50 ejecuciones, de la más reciente a la más antigua. |
| `GET /api/notifications` | Devuelve hasta 50 notificaciones, de la más reciente a la más antigua. |

## 5. Ramas y entregas consecutivas

La persona 1 inicializa `main` y crea `develop` desde ella. Las ramas de trabajo nacen de `develop` y vuelven a ella mediante Pull Requests. La versión final pasa de `develop` a `main` mediante un PR.

| Turno | Responsable | Ramas, en orden | Entrega y prueba de aceptación |
|---|---|---|---|
| **1 · Primera jornada** | **Persona 1 — Lenguaje** | `feature/lexer` → `feature/parser` | En `backend/language/`, entrega EBNF, tokens, lexer, parser, AST y diagnósticos. El programa de demo genera un AST y se distinguen los errores léxico y sintáctico. |
| **2** | **Persona 2 — Semántica e IR** | `feature/semantic` → `feature/ir` | En `backend/compiler/`, entrega tabla de símbolos, validación y generación de IR. Rechaza identificadores, operaciones, estados y correos inválidos. Genera un salto correcto para el condicional. |
| **3** | **Persona 3 — Ejecutor y optimizador** | `feature/executor` → `feature/optimizer` | En `backend/runtime/`, entrega máquina virtual, servicios en memoria, SMTP y las dos optimizaciones. Demuestra condición verdadera y falsa, correo visible en Mailpit y equivalencia de resultados optimizados. |
| **4** | **Persona 4 — Persistencia y API** | `feature/persistence` → `feature/api` | En `backend/db/` y `backend/api/`, entrega migraciones, datos iniciales, repositorios, API e integración. Deja Compose con `backend`, `postgres` y `mailpit`. Ejecuta un lote por HTTP y verifica persistencia de estado e historial tras reiniciar. |
| **5** | **Persona 5 — Interfaz y despliegue** | `feature/frontend` → `feature/docker` | En `frontend/`, entrega consola, tarjetas, resultados, historial y notificaciones. Agrega el servicio `frontend` a Compose y completa el README. Demuestra la aplicación desde el navegador en una instalación limpia. |

### Reglas de traspaso

1. Crear la primera rama de cada turno desde `develop` actualizado. La persona 2 y las siguientes empiezan cuando las dos ramas del turno anterior estén integradas.
2. Subir commits descriptivos, pruebas y documentación del bloque. Abrir los PR hacia `develop`.
3. La persona del turno siguiente revisa el PR y comprueba la prueba de aceptación. La persona 4 revisa los PR de la persona 5.
4. Crear la segunda rama desde `develop` después de fusionar la primera.
5. La persona 5 abre el PR final a `main` tras la prueba de instalación limpia. El equipo comprueba el código, la documentación y las contribuciones antes de aprobarlo.

GitHub Projects tendrá las columnas **Pendiente**, **En progreso**, **En revisión** y **Hecho**. Cada rama tiene una tarjeta con descripción, responsable, criterio de aceptación y enlace al PR.

## 6. Demostración y cierre

Levantar la aplicación desde una copia limpia con `docker compose up --build`. Ejecutar en el navegador:

```text
ENCENDER luz_sala
CONSULTAR luz_sala
ENCENDER ventilador1
ABRIR puerta_principal
ACTIVAR alarma1
SI puerta_principal == ABIERTA ENTONCES CERRAR puerta_principal
NOTIFICAR "Puerta cerrada y alarma activada"
ENVIAR CORREO A "demo@example.com" MENSAJE "Revisión completada"
LISTAR DISPOSITIVOS
```

La consulta devuelve `ENCENDIDO`. Al cierre, la luz y el ventilador están encendidos, la puerta cerrada y la alarma activada. La notificación aparece en la aplicación y el correo en Mailpit. La evidencia también cubre `APAGAR`, `DESACTIVAR`, una condición falsa, los errores de las tres fases y las dos optimizaciones.

La entrega incluye la aplicación en `main`, README de instalación, pruebas automatizadas, evidencia funcional, tablero, contribuciones verificables y documentación técnica de arquitectura, gramática, tokens, AST, tabla de símbolos, validaciones, IR, optimizaciones, ejecutor y modelo de base de datos.

**Primer paso.** La persona 1 crea `main`, `develop`, el tablero y `feature/lexer`. Tras integrar el lexer, crea `feature/parser`. Cuando `parse(source)` pase las pruebas y quede en `develop`, entrega el turno a la persona 2.
