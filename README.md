# Short Video Generator

MVP local de un pipeline modular de generación de video vertical con aprobación humana.

## Límites del primer hito

- FastAPI, worker y scheduler son procesos distintos.
- SQLite conserva estado; los binarios viven en `storage/`.
- El dominio no depende de FastAPI, SQLAlchemy, FFmpeg ni proveedores externos.
- Sólo existen contratos, persistencia, máquina de estados, puertos y proveedores
  deterministas. Aún no hay generación externa ni renderizado FFmpeg.

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
