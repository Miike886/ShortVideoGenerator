# Short Video Generator

MVP local de un pipeline modular de generación de video vertical con aprobación humana.

## Límites del primer hito

- FastAPI, worker y scheduler son procesos distintos.
- SQLite conserva estado; los binarios viven en `storage/`.
- El dominio no depende de FastAPI, SQLAlchemy, FFmpeg ni proveedores externos.
- El primer flujo ejecutable usa únicamente contratos, persistencia, máquina de estados,
  FFmpeg y proveedores deterministas locales. No hay generación externa.

## Principios del MVP

### Costo operativo obligatorio cero

El vertical slice de referencia debe poder ejecutarse localmente sin suscripciones,
créditos de API ni cuentas de pago. Sus dependencias base serán gratuitas y, cuando
aplique, de código abierto. Los proveedores externos con costo o cuota podrán añadirse
después como integraciones opcionales, pero nunca serán necesarios para ejecutar el
flujo local de referencia.

"Gratuito" significa que el sistema no introduce un costo obligatorio por ejecución.
El equipo sigue siendo responsable de comprobar las licencias de modelos, voces y
recursos audiovisuales antes de usarlos o distribuir el contenido generado.

### Proveedores reemplazables

Fuentes, generación editorial, TTS, media y renderizado se consumen únicamente mediante
interfaces pequeñas. El pipeline no conoce SDKs, credenciales ni detalles de un proveedor
concreto. Cada integración debe:

- recibir y devolver contratos propios del proyecto;
- encapsular su configuración y sus errores;
- poder sustituirse mediante configuración, sin modificar el dominio ni el pipeline;
- contar con un proveedor determinista para pruebas;
- no escribir directamente en SQLite ni controlar transiciones de estado.

La implementación local y gratuita será la configuración predeterminada. Los adaptadores
remotos, si se incorporan, serán alternativas explícitas.

## Desarrollo con uv

```powershell
uv python install 3.12
uv sync --dev
uv run pytest
```

`uv` administra el intérprete, el entorno virtual, las dependencias y el archivo
`uv.lock`. No se requiere activar `.venv` ni instalar paquetes con `pip`.

Procesos previstos:

```powershell
uv run svg-api
uv run svg-worker
uv run svg-scheduler
```

El worker y el scheduler son deliberadamente esqueletos en este hito.

## Vertical slice determinista

El comando manual crea un nicho y un candidato fixture, los evalúa, genera brief y guion,
crea imágenes PPM, audio WAV y subtítulos SRT, renderiza un MP4 vertical y lo coloca en la
bandeja de revisión.

Con FFmpeg y `ffprobe` disponibles en `PATH`:

```powershell
uv run svg-run-manual
```

Si la terminal todavía no heredó las rutas, se pueden indicar explícitamente:

```powershell
uv run svg-run-manual --ffmpeg C:\ruta\a\ffmpeg.exe --ffprobe C:\ruta\a\ffprobe.exe
```

El identificador predeterminado `manual-fixture-v1` hace que repetir el comando devuelva la
misma ejecución y producción sin duplicar artefactos. Para crear otra ejecución:

```powershell
uv run svg-run-manual --idempotency-key manual-fixture-v2
```

Inicia la API en otro proceso:

```powershell
uv run svg-api
```

Endpoints disponibles:

- `GET /review-queue`
- `GET /productions/{production_id}`
- `POST /productions/{production_id}/reviews`
- `GET /files/{relative_path}`

Una decisión humana utiliza uno de estos valores:

```json
{
  "decision": "approved",
  "comment": "Revisión humana completada"
}
```

También se aceptan `rejected` y `changes_requested`; ambas decisiones requieren comentario.
El audio actual es un tono de prueba reproducible, no una voz sintética real.

## Quality gate de desarrollo

El flujo automático de cierre de desarrollo es:

```text
Implementación
    → architecture-guardian
    → code-quality-gate
    → feature-documenter
    → commit y pull request autorizados
```

`architecture-guardian` revisa límites, dirección de dependencias, cohesión y propiedad de
la lógica. Sólo corrige automáticamente hallazgos pequeños y seguros; un resultado `blocked`
detiene QA y publicación hasta autorizar una refactorización amplia.

`code-quality-gate` verifica lockfile, dependencias, Ruff, pruebas aplicables, whitespace,
artefactos temporales y FFmpeg cuando el cambio afecta renderizado. Su resultado es `passed`,
`passed-with-warnings` o `failed`; un resultado `failed` bloquea la publicación.
