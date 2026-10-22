# P03h · Alta reanudable y primera obra

Revisión local del 22-10-2026 en `gpt/dk2-p03h-asistente-reanudable`.
Completa la interfaz de P03a–g; la fusión de la fase requiere los cuatro
controles de cada PR. No activa servicios de producción.

## Recorrido y límites de la evidencia

`catalog-setup.spec.ts` recorre los cinco pasos con Magic Link/TOTP,
PostgreSQL, almacenamiento y APIs reales. La fixture crea una serie desde la
plantilla PVC con perfiles y compras **sintéticos**, sin lista de costos activa.
Las dos respuestas documentales son simuladas. Esta evidencia no certifica
datos de Proline ni mide cuánto tarda una persona en leer su manual real.

El recorrido publica una discrepancia citada, conserva su revisión al cambiar
de paso, carga `p03-alta-precios-sinteticos.xlsx` y guarda sus 12 precios tras
la revisión humana. El archivo sigue seleccionado al volver de Manual.
Cierra/reabre en el paso cuatro, compara 1206 → 1208 mm y elige la adición
de soldadura entre las soluciones exactas del motor. La confirmación guarda
una salida esperada inmutable de 1208,00 mm y habilita las capacidades
de cotización y fabricación, sin valores sugeridos pendientes.

El botón final abre una obra nueva con esa serie. La respuesta HTTP guarda
`design_defaults.system_id` y el primer editor hereda la selección. La obra
no altera las preferencias de la empresa. Los precios automáticos pertenecen
a P04; aquí se prepara su entrada.

## Revisión de interfaz

Comparación con `mockups/Prueba.dc.html`: cinco pasos numerados, título de la
prueba y dibujo de la apertura, piezas/cantidades/medidas/ángulos del motor,
columna editable «Según tu manual» y confirmación humana al final. Las piezas
reales se enumeran por SKU y dimensión; una tabla local permite revisar toda
la salida, con paginación de 50 filas. Los números de ese mockup son referencia
visual, nunca datos de catálogo.

| Antes | Después | Motivo |
|---|---|---|
| Un estilo de `.catalog` mostraba Manual tras cambiar de paso | Los pasos `[hidden]` tienen una regla explícita; conservan el borrador sin mostrarlo | Evitar dos tareas simultáneas y contenido ajeno al paso actual |
| Cinco filas de navegación en móvil | Dos columnas flexibles y texto distribuible | Acercar la acción al contenido conservando los nombres completos |
| Reabrir podía mostrar el paso de una caché anterior | Se espera el progreso vigente; cada escritura usa la revisión de la anterior | Evitar sobrescribir el trabajo de otra pantalla |
| La creación de obra aceptaba preferencias pero no las persistía | Valida y guarda las preferencias en la misma inserción | La primera ventana debe heredar la serie elegida |
| El foco podía recorrer un paso oculto o un fieldset deshabilitado | El diálogo filtra esos controles y hace accesible su cuerpo desplazable | Teclado y lectura de la tarea visible |
| Un botón del fondo desbordaba a 320 px y texto al 200 % | Sus etiquetas pueden distribuirse y respetan el ancho disponible | Mantener el tamaño de página sin desplazamiento horizontal |

No se añadió movimiento. El cambio de paso restablece el inicio del contenido;
el trabajo sin publicar permanece montado. Cerrar o recuperar pide confirmar
el descarte de archivos/revisiones locales. Los costos solo se montan para el
dueño y conservan la autorización del servidor.

## Extremos, accesibilidad y rendimiento

`catalog-setup-stress.spec.ts` cambia la respuesta de lectura, sin escribir
catálogo: nombres Unicode de 150/255 caracteres, código de 50, 0/1/500 perfiles
y pendientes, 1440/390/320 px y texto al 100/200 %. Comprueba ausencia de
desborde de página, axe A/AA/2.1AA, último pendiente accesible mediante End y
cotización deshabilitada mientras faltan datos. La lista tiene altura acotada
y desplazamiento propio; no se ocultan los pendientes ni se inventa un total.

Los tiempos se registran en el log E2E: `readyMs` incluye navegación y edición
de reglas; `wizardMs` mide desde abrir hasta recuperar el primer paso. Son
mediciones de Vite/stack local, sin limitación de red, y no son Core Web Vitals
ni una medición de producción. La ficha recarga sus datos vigentes; los pasos
visitados conservan el estado sin remontarse.

| Medición local | 1440 × 900 | 390 × 844 |
|---|---:|---:|
| Navegación y edición de reglas (`readyMs`) | 6286 ms | 6942 ms |
| Abrir y recuperar el primer paso (`wizardMs`) | 3844 ms | 3819 ms |

La recuperación sigue superando tres segundos en este servidor de desarrollo;
el estado de carga aparece mientras espera. No se declara resuelto el objetivo
de rendimiento de P11. El editor existente es de lectura por debajo de 1024 px;
el ensayo móvil verifica la serie heredada, sin declarar edición móvil completa.

## Verificación

- Frontend completo: 1.218 pruebas aprobadas; 43 regresiones dirigidas tras
  el último ajuste del asistente y el diálogo.
- Backend unitario: 1.702 aprobadas. Motor: 1.086 aprobadas y dos xfail previos.
  Comprobación de bytes dorados aprobada, sin regeneración.
- PostgreSQL: 16 integraciones de referencia y creación de obra aprobadas.
  La prueba de otra empresa rechaza la serie sin insertar una obra parcial.
- Tres E2E finales aprobados en 2,6 minutos: dos recorridos reales y un ensayo
  de extremos. Todas sus capturas comprueban axe y ancho de página.
- ESLint, TypeScript, Prettier, Ruff, mypy, Django check, guardas y build aprobados.
  OpenAPI/orval reproducibles. Database Gate se exige en CI.

## Capturas seleccionadas

Cada paso: [Serie 1440](alta-serie-1440.png) / [390](alta-serie-390.png),
[Manual 1440](alta-manual-1440.png) / [390](alta-manual-390.png),
[Precios 1440](alta-precios-1440.png) / [390](alta-precios-390.png),
[Prueba 1440](alta-ventana-1440.png) / [390](alta-ventana-390.png),
[Primera cotización 1440](alta-cotizacion-1440.png) / [390](alta-cotizacion-390.png).
Primer editor: [1440](alta-primera-ventana-1440.png) / [390](alta-primera-ventana-390.png).
Extremos al 200 %: [1440](alta-extremos-1440.png), [390](alta-extremos-390.png)
y [320](alta-extremos-320.png).
