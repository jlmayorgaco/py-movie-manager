# Auditoría de seguridad

| Área | Hallazgo en la versión anterior | Cambio |
| --- | --- | --- |
| CLI | `initialize_movie_manager_services()` aplicaba el valor `False` por defecto de argparse a `dry_run`. El flujo podía ejecutar movimientos sin autorización explícita. | El CLI requiere `--apply`, y la configuración puede vetar una ejecución real. |
| Synology | `move()` omitía dry-run. `deep_tree_move()` copiaba directamente a destino y luego borraba el origen de forma recursiva. | Un adaptador común valida rutas, usa un renombrado atómico sin reemplazo y solo copia en un área oculta cuando cruza dispositivos. |
| macOS y Windows | Algunos caminos de movimiento, copia y borrado ignoraban el modo de simulación o fusionaban directorios existentes. | Los tres adaptadores pasan por el mismo control de escritura. No se reemplazan destinos ni se eliminan directorios con contenido. |
| MovieManager | `start()` y `creating_temp_genres()` entraban en carpetas simuladas inexistentes. `moving_to_vose()` podía copiar sobre una migración parcial; la comprobación recurría a tamaños y muestreo. `deleting_temp()` usaba un borrado recursivo tras una comprobación incompleta de pendientes. | Un plan de solo lectura representa las etapas virtuales. Se conservan ambos lados ante colisiones, y TEMP solo se recupera explícitamente con `--resume`. |
| Configuración e informes | Se abrían logs y manifiestos antes de validar rutas. Un manifiesto anterior podía condicionar el siguiente intento por nombre de carpeta. | Los informes son opcionales, se escriben fuera de todas las raíces y no sustituyen la inspección del disco. |
| IMDb y scripts | El CLI en `main` ya no imprimía la clave directamente, pero `ScrapperServiceIMDB.__str__()` la exponía. Los scripts antiguos podían borrar o mover contenido en rutas fijas. | Se elimina la clave de la representación, y el CLI no inicializa IMDb. Las utilidades antiguas se archivan como texto; el generador de sandbox se niega a reutilizar carpetas existentes. |

La validación automatizada comprueba copias intactas ante colisiones, fallos de
E/S e interrupción de la limpieza; compara el contenido de las bibliotecas
antes y después de la simulación y del inventario. El fallback entre volúmenes
se prueba inyectando EXDEV y errores de copia, publicación y limpieza. Consulta
el [README](README.md) para desplegar, recuperar TEMP y revisar los límites.
