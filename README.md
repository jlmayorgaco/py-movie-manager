# PyMovieManager

Organiza carpetas de películas para Plex: detecta el género en la etiqueta
`[g-…]` de una carpeta de RAW, la prepara en TEMP, quita las etiquetas
`[g-…]` y `[d-…]` del nombre y la lleva a VOSE bajo el género correspondiente.
Conserva los nombres de edición, las películas, subtítulos, imágenes y otros
archivos de la carpeta. Un traslado conserva también los directorios reales
`@eaDir` de Synology dentro de la película, incluidos los anidados en `.actors`
o `extrathumbs`. Todo su contenido pasa por las mismas comprobaciones: se
rechazan enlaces, archivos especiales, montajes anidados y marcas de traslados
interrumpidos. También exporta un inventario local independiente.

El CLI (`main.py`) configura los casos de uso `MovieManager` e `Inventory`.
El dominio trabaja contra puertos en `src/domain/interfaces`. Los adaptadores
de Synology, macOS y Windows conservan sus puntos de entrada y comparten la
implementación local en `src/adapters`.

## Instalación y configuración

Se requiere Python 3.9 o posterior. El programa usa solo la biblioteca estándar.
Para una instalación nueva en Synology:

```bash
ssh tu_usuario@tu_nas
cd ~/services
git clone https://github.com/jlmayorgaco/py-movie-manager.git
cd py-movie-manager
python3 -m venv venv
source venv/bin/activate
python --version
cp config/config.json config/synology.local.json
```

Edita `config/synology.local.json` con tus rutas absolutas. Usa un archivo
`config/*.local.json` para cada máquina; Git lo ignora. En Windows se aceptan rutas
absolutas con letra de unidad o UNC, escapando las barras en el JSON.

```json
{
  "directory_raw": "/ruta/a/RAW",
  "directory_temp": "/ruta/a/__TMM_TEMP__",
  "directory_vose": "/ruta/a/VOSE",
  "dry_run": false,
  "inventory_roots": {
    "Dobladas": "/ruta/a/Dobladas",
    "Pendientes": "/ruta/a/Pendientes"
  }
}
```

RAW y VOSE deben existir para organizar. Si se omite TEMP, se usa
`__TMM_TEMP__` junto a RAW. TEMP puede faltar si su directorio padre existe.
Las raíces deben ser distintas y no se pueden anidar, apuntar a la raíz del
sistema ni pasar por enlaces o junctions. Las raíces extra son opcionales y
solo se usan en el inventario. `dry_run: false` permite solicitar `--apply`;
sin esa opción, el CLI siempre simula. `dry_run: true` bloquea `--apply`.

`--sandbox` selecciona únicamente la carpeta `__sandbox__` del repositorio
y no se puede combinar con `--config`. En Bash,
`bash scripts/reset_sandbox.sh` crea datos sintéticos una sola vez y se niega a
reemplazar un sandbox existente. `--sandbox` también requiere `--apply` para
mover archivos. Usa `--os mac` o `--os windows` según corresponda.

## Inventario

```bash
python main.py --os synology --config config/synology.local.json \
  --inventory --output "$HOME/filmoteca.csv"
```

Escanea RAW, VOSE y las raíces adicionales configuradas. Se puede configurar
solo VOSE, o solo raíces adicionales, si únicamente se quiere inventariar.
El escaneo es recursivo y no usa IMDb, credenciales ni red. Ignora TEMP,
directorios de sistema como `@eaDir` y `#recycle`, enlaces y nombres habituales
de tráilers, extras y muestras. Cada archivo de vídeo cuenta por separado;
dos ediciones o copias aparecen en filas distintas.

El CSV tiene BOM UTF-8 para Excel. Incluye nombre de archivo y carpeta, título,
año, género, director, biblioteca, ruta completa, extensión, edición y una
marca de revisión. Los datos desconocidos quedan vacíos. Los campos que Excel
podría tratar como fórmulas se prefijan con un apóstrofo; el resto se conserva
literalmente. Para un listado de lectura rápida, usa una salida `.txt`.
La presencia en la biblioteca no registra si alguien vio o disfrutó la película.

## Etiquetas de género

La organización acepta los nombres de `GenresEnum` y los alias explícitos de
[`config/GenresConfig.py`](config/GenresConfig.py). Ignora mayúsculas, acentos y
diferencias de espacios, guiones y guiones bajos. Por ejemplo, `Bélica`,
`BÉLICA`, `belica` y `War` van a `WAR`; `Ciencia Ficción` y
`science_fiction` van a `SCIENCE_FICTION`. La etiqueta de director no interviene
en esa decisión. Ambas etiquetas se quitan del nombre de la carpeta de destino.

Una etiqueta desconocida, como `Película de Televisión`, queda en su carpeta
original y aparece en el informe como `unknown_genre_tag`, sin destino. El
informe puede sugerir géneros para errores de escritura cercanos —por ejemplo,
`THRILLER` para `Thriler`—; las sugerencias nunca generan operaciones de traslado.
Con `--resume`, si una etiqueta conservada en TEMP contradice el género de la
carpeta que la contiene, el informe indica `temp_genre_mismatch` y no la mueve.

## Simular, revisar y aplicar

```bash
python main.py --os synology --config config/synology.local.json --preflight
python main.py --os synology --config config/synology.local.json \
  --dry-run --report "$HOME/movie-plan.json"
python -m json.tool "$HOME/movie-plan.json"
```

El plan muestra las rutas, etapas, estados y motivos. Incluye los padres que se
prepararían para cada traslado. La simulación funciona aunque TEMP aún no exista.
`--plan` equivale a `--dry-run`. Los informes y exportaciones necesitan una ruta
nueva fuera de todas las raíces, en un directorio existente. Se puede usar
`--report-dir` con un directorio existente para generar un nombre único.

Después de revisar el plan y confirmar las rutas, empieza con una sola carpeta:

```bash
python main.py --os synology --config config/synology.local.json \
  --apply --limit 1 --report "$HOME/movie-apply-1.json"
python -m json.tool "$HOME/movie-apply-1.json"
```

Quita `--limit 1` cuando hayas verificado ese resultado. `--apply` calcula un
plan nuevo con el estado actual del disco. Si el destino existe o dos candidatos
del plan coinciden, se conservan ambos orígenes. El informe distingue contenido
idéntico, mismo nombre con contenido diferente, entradas adicionales, posible
traslado parcial y diferencias de edición o acompañantes. No fusiona ni
deduplica automáticamente. Usa `--stop-on-conflict` para detener la aplicación ante
un conflicto, o `--continue-on-error` para procesar otras carpetas tras un error de
E/S. `--limit` solo limita las nuevas carpetas de RAW. `--sort date` prioriza las
carpetas modificadas más recientemente. Códigos de salida: 0 si no hay errores
ni conflictos pendientes, 1 si hay un error, 2 si quedan conflictos o contenido
pendiente en TEMP, 130 si se interrumpe con Ctrl+C.

## Recuperar una ejecución interrumpida

TEMP nunca se vacía automáticamente. Inspecciona el informe y las carpetas de
RAW, TEMP y VOSE. Con `--resume` se incluyen las carpetas pendientes de TEMP
bajo géneros reconocidos, a partir del estado real del disco. Primero simula:

```bash
python main.py --os synology --config config/synology.local.json \
  --dry-run --resume --report "$HOME/movie-recovery-plan.json"
```

Si las rutas y operaciones son correctas, ejecuta `--apply --resume` con un
nuevo informe. Los archivos sueltos y carpetas desconocidas en TEMP quedan
para revisión manual. Un corte brusco puede dejar `.pymovie-manager.lock` en
RAW: verifica que ningún proceso siga activo antes de retirar ese archivo.
Las carpetas ocultas `.pymovie-transfer-*` son áreas de copia incompletas o
restos de una publicación. No se reanudan ni se limpian automáticamente;
un destino con una copia oculta pendiente se bloquea para evitar otro intento
sobre la misma carpeta. Compara RAW/TEMP/VOSE y el contenido oculto antes de
decidir qué conservar. Los restos del organizador anterior que contienen
`AlreadyCopied_…` también quedan para revisión manual. Una publicación interrumpida durante la limpieza puede dejar un
destino completo y parte del origen; el siguiente plan conserva ambos.

## Actualizar un Synology existente

Desde el NAS, confirma que estás en `main`, que no hay cambios locales y que
`config/config.json` aún contiene tus rutas Synology. Si hay cambios, revísalos
antes de continuar. Guarda la configuración **antes** del pull:

```bash
cd /volume1/homes/walla/services/py-movie-manager
git status --short --branch
python3 -m json.tool config/config.json
cp -n config/config.json "$HOME/py-movie-manager.synology.json"
git fetch origin
git pull --ff-only origin main
source venv/bin/activate
python --version
python main.py --help
python main.py --os synology --config "$HOME/py-movie-manager.synology.json" --preflight
```

Comprueba la copia si ya existía. Si el archivo trae rutas Windows, prepara la
configuración local con tus rutas reales antes de ejecutar `--preflight`. Para
usar la copia anterior en los ejemplos, cambia el argumento de `--config`.
No hay nuevas dependencias de ejecución que instalar.

## Pruebas y límites

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check
python -m pytest -q
```

Las pruebas usan películas sintéticas y directorios temporales. GitHub Actions
prueba Linux, Windows y macOS. La publicación de carpetas requiere una operación
atómica sin reemplazo del sistema de archivos. Si el kernel o la unidad de red
no la admite, el movimiento falla de forma conservadora. Entre volúmenes se
requiere espacio para la copia completa y se verifica SHA-256 antes de limpiar
el origen. Un traslado entre volúmenes se detiene si encuentra enlaces duros.
La copia no promete conservar ACL, propietarios ni atributos específicos de
todos los sistemas.

Mantén copias de seguridad y evita que otros procesos descarguen, renombren o
escriban en las carpetas que se están moviendo. La aplicación serializa sus
propias ejecuciones que compartan RAW; no coordina con clientes externos ni con
instancias configuradas con otro RAW. No se ha probado sobre el NAS de producción.
El inventario interpreta nombres, no el contenido del vídeo, y puede requerir
revisión para títulos poco convencionales, discos, extras o años ambiguos.
La organización conserva en RAW los vídeos sueltos y carpetas sin género; sí
aparecen en el inventario. El código histórico se conserva en
[`docs/legacy`](docs/legacy/README.md) como texto.
