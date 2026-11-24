# SmartHome

Plantilla inicial del Sistema de automatización de dispositivos inteligentes para Lenguajes y Autómatas II. El [plan de integración](docs/plan-integracion-smarthome.md) define el alcance, los contratos y las pruebas de aceptación.

## Estructura y responsables

| Ruta | Contenido | Responsable |
|---|---|---|
| `backend/language/` | Lexer, parser, AST y diagnósticos. | Persona 1 |
| `backend/compiler/` | Tabla de símbolos, validación semántica y generación de IR. | Persona 2 |
| `backend/runtime/` | Máquina virtual, optimizador y adaptador SMTP. | Persona 3 |
| `backend/db/` | Modelos, repositorios y migraciones Alembic. | Persona 4 |
| `backend/api/` | API REST e integración del motor. | Persona 4 |
| `backend/tests/` | Pruebas Pytest de los módulos del backend. | Personas 1 a 4 |
| `frontend/` | Aplicación React con TypeScript y Vite, más pruebas Vitest. | Persona 5 |
| `docs/` | Plan de integración y gramática EBNF. | Equipo |
| `examples/` | Programa de demostración. | Equipo |
| `compose.yaml` | Configuración local de los cuatro servicios. | Personas 4 y 5 |

## Arranque de la plantilla

Con Docker y Compose, ejecutar desde la raíz:

```sh
docker compose up --build
```

- Interfaz inicial: http://localhost:5173
- Verificación de la API: http://localhost:8000/api/health
- Bandeja de correo de pruebas: http://localhost:8025

Compose usa valores de desarrollo por defecto. Para cambiarlos, copiar `.env.example` a `.env`. El backend recibe las variables `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`, `SMTP_HOST` y `SMTP_PORT`.

La plantilla trae una pantalla inicial y una ruta de verificación de FastAPI. El lenguaje, los dispositivos, las migraciones, las pruebas funcionales y las rutas del proyecto se incorporan en sus respectivos turnos. El programa de `examples/demo.smarthome.txt` es la entrada de referencia para la aplicación terminada.

## Primer turno

Importar esta carpeta al repositorio de GitHub. La persona 1 crea `main` y `develop` y abre `feature/lexer` desde `develop`. Una vez integrado el lexer, abre `feature/parser` desde `develop` actualizado. Cada persona recibe su turno al quedar integradas las dos ramas del bloque anterior.

El punto de entrada del lenguaje es `from backend.language import parse`.
`parse(fuente)` devuelve un `Programa` con sus instrucciones en orden o una
lista con el primer diagnóstico léxico o sintáctico. Las posiciones del árbol
y de los diagnósticos empiezan en 1. Los nodos se definen en
[`arbol_sintactico.py`](backend/language/arbol_sintactico.py).

Para verificar el lexer y el parser desde la raíz del proyecto:

```sh
python -m pytest backend/tests
```

## Segundo turno: semántica

La tabla de símbolos está en
[`tabla_simbolos.py`](backend/compiler/tabla_simbolos.py). Combina el catálogo
de dispositivos con las reglas por tipo:

| Tipo | Operaciones | Estados |
|---|---|---|
| `LUZ`, `VENTILADOR` | `ENCENDER`, `APAGAR`, `CONSULTAR` | `ENCENDIDO`, `APAGADO` |
| `PUERTA` | `ABRIR`, `CERRAR`, `CONSULTAR` | `ABIERTA`, `CERRADA` |
| `ALARMA` | `ACTIVAR`, `DESACTIVAR`, `CONSULTAR` | `ACTIVADA`, `DESACTIVADA` |

`tabla_inicial()` devuelve los cuatro dispositivos del plan.
`TablaSimbolos.desde_registros(filas)` construye la tabla con filas que tienen
`id`, `label`, `type` y `state`, el formato de la tabla `devices`.

`validate(programa, tabla)` recorre el programa completo y devuelve todos los
diagnósticos con fase `semantica`, en orden. Detecta dispositivos inexistentes,
operaciones incompatibles con el tipo, estados de `SI` incompatibles con el
dispositivo, notificaciones y mensajes vacíos y destinatarios sin formato de
correo.
