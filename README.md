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

El comando manual recibe un tema y un idioma, crea un candidato fixture, genera un brief y
un guion determinista de tres escenas, obtiene audio y recursos visuales mediante proveedores
reemplazables, renderiza un MP4 vertical y lo coloca en la bandeja de revisión.

Con FFmpeg y `ffprobe` disponibles en `PATH`:

```powershell
uv run svg-run-manual --topic "Why containers are useful" --language en
```

Si la terminal todavía no heredó las rutas, se pueden indicar explícitamente:

```powershell
uv run svg-run-manual --ffmpeg C:\ruta\a\ffmpeg.exe --ffprobe C:\ruta\a\ffprobe.exe
```

Si no se indica `--idempotency-key`, el comando la deriva de la entrada y la configuración.
Repetir la misma entrada devuelve la misma ejecución y producción sin volver a invocar TTS,
descargar assets ni renderizar. Para identificar explícitamente una ejecución:

```powershell
uv run svg-run-manual --topic "Why containers are useful" --language en `
  --idempotency-key containers-en-v1
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
Las pruebas usan proveedores `fake` reproducibles y no requieren red. Para una ejecución con
voz inteligible de Edge TTS y recursos gratuitos de Pexels:

```powershell
$env:PEXELS_API_KEY = "TU_API_KEY"
uv run svg-run-manual --topic "Why containers are useful" --language en `
  --tts-provider edge --asset-provider pexels
```

También se aceptan `TTS_PROVIDER`, `TTS_VOICE`, `TTS_RATE`, `TTS_VOLUME`,
`ASSET_PROVIDER` y `PEXELS_API_KEY`; `.env.example` contiene la plantilla. Edge TTS requiere
conectividad, pero no una clave propia. Pexels requiere su clave API y conserva atribución y
metadatos de origen por asset. El flujo `fake` continúa siendo la referencia gratuita,
reproducible y offline para desarrollo y pruebas.

## Quality gate de desarrollo

El flujo automático de cierre de desarrollo es:

```text
Implementación
    → vertical-slice-implementer
    → architecture-guardian
    → code-quality-gate
    → feature-documenter
    → commit y pull request autorizados
```

`architecture-guardian` revisa límites, dirección de dependencias, cohesión y propiedad de
la lógica. Sólo corrige automáticamente hallazgos pequeños y seguros; un resultado `blocked`
detiene QA y publicación hasta autorizar una refactorización amplia.

`vertical-slice-implementer` convierte una feature autorizada en el recorrido ejecutable y
verificable más pequeño, presenta el plan y los comandos de validación antes de editar, y
mantiene fuera del alcance las capacidades pospuestas. No autoriza acciones Git externas.

`code-quality-gate` verifica lockfile, dependencias, Ruff, pruebas aplicables, whitespace,
artefactos temporales y FFmpeg cuando el cambio afecta renderizado. Su resultado es `passed`,
`passed-with-warnings` o `failed`; un resultado `failed` bloquea la publicación.
