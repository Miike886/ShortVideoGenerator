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
`ASSET_PROVIDER`, `PEXELS_API_KEY` y `DEFAULT_CHARACTER_ID`; `.env.example` contiene la
plantilla. Edge TTS requiere conectividad, pero no una clave propia. Pexels requiere su clave
API y conserva atribución y metadatos de origen por asset. El flujo `fake` continúa siendo la
referencia gratuita, reproducible y offline para desarrollo y pruebas.

## ElevenLabs narration

Para probar la narracion de ElevenLabs durante desarrollo local, instala su dependencia
opcional y configura `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` y las variables de voz de
`.env.example`:

```powershell
uv sync --extra elevenlabs
$env:TTS_PROVIDER = "elevenlabs"
uv run svg-run-manual --topic "Why structured captions help" --language en
```

El modelo predeterminado es `eleven_multilingual_v2`, con la identidad versionada como
`byte_voice_v1`. Los resultados del plan gratuito son solo para desarrollo/pruebas; el
uso comercial o publico debe cumplir los terminos del plan activo y los derechos de la voz.
Esta slice no genera SFX ni musica.

## TTS credit-safe workflow

Para desarrollo visual, usa `TTS_MODE=cached`: los artifacts de narracion existentes se
reutilizan y un cache miss falla sin llamar a ElevenLabs. Usa `TTS_MODE=live` solo cuando la
narracion deba cambiar, genera una vez y vuelve a `cached`. El comando
`--byte-voice-stress-test` genera o reutiliza las dos referencias controladas de Byte Voice v1.

## Presenter reutilizable

El presenter Byte vive como asset compartido del proyecto en `assets/characters/byte/`.
`character.yaml` declara versión, pose predeterminada, poses disponibles, posición preferida
y escala. Las ejecuciones normales no llaman APIs de generación de imágenes para crear al
personaje; sólo validan y reutilizan PNGs transparentes existentes.

Para agregar otra pose, coloca `<pose>.png` en el directorio del personaje, agrégala a
`available_poses` y aumenta la versión del personaje si el cambio debe invalidar renders
previos. Para usar otro personaje en ejecuciones manuales, crea
`assets/characters/<id>/character.yaml` y configura `DEFAULT_CHARACTER_ID=<id>`.

## Captions dinámicos

El pipeline genera timestamps de palabra mediante `CaptionAlignmentProvider`. Las pruebas y
el camino offline usan `fake`, que alinea el texto conocido contra la duración real del audio
sin descargar modelos ni usar red. WhisperX queda detrás del mismo puerto como integración
opcional para ejecuciones manuales en entornos donde ya esté instalado.

```dotenv
CAPTION_ALIGNMENT_PROVIDER=fake
WHISPERX_MODEL=small
WHISPERX_DEVICE=cpu
```

Los subtítulos se escriben como `subtitles.ass`: grupos cortos de palabras, cambios
progresivos durante la narración y énfasis visual de la palabra activa. El objetivo actual es
sincronía y legibilidad; la tipografía cinética compleja queda para otro slice.

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
