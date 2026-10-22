# P02 · Aceptación integrada del catálogo

Verificada el 21-10-2026, rama `gpt/dk2-p02e-catalogo-integrado`, sobre
P02a–d (#169–#172). P02 sigue en curso hasta fusionar todas las sub-PR con
Lint & Typecheck, Test Suite, Frontend Build y Database Gate aprobados.

## Superficies y comparación

El inicio agrupa fabricante y serie, cuenta solo series del taller, permite
buscar y ofrece Agregar serie (biblioteca, plantilla o desde cero). Los ejemplos
se consultan al abrir la sección plegada. La biblioteca y las capacidades de
edición avanzada conservan enlaces propios. La ficha respeta la jerarquía,
espaciado, tipografía y textos de `Serie.dc.html`; la navegación general vigente
se reemplazará en P05. El detalle está en [ficha](aceptacion-ficha.md).

| Pantalla | 1440 × 900 | 390 × 844 |
|---|---|---|
| Catálogo | [captura](catalogo-1440.png) | [captura](catalogo-390.png) |
| 300 perfiles | [captura](serie-300-perfiles-1440.png) | [captura](serie-300-perfiles-390.png) |
| Prueba preliminar | [captura](ventana-prueba-1440.png) | [captura](ventana-prueba-390.png) |

Las [doce capturas de pestañas](aceptacion-ficha.md) completan la evidencia.
[Reglas móviles desplazadas hasta valores y origen](serie-reglas-valores-390.png)
demuestra la tabla horizontal contenida. Las 19 imágenes seleccionadas se
inspeccionaron visualmente. En móvil, la tabla se desplaza dentro de su región;
la página conserva el ancho de 390 px. Algunas capturas conservan el scroll
vertical de la operación anterior y muestran el contenido de la pestaña.

## Flujo real ejercitado

`catalog-series.spec.ts` aprobó dos ejecuciones (1440 y 390) en 1,4 minutos,
con Supabase aislado en 25421, Django en 8007 y Vite en 5173. Usa Magic Link y
TOTP reales; el navegador solo recibe la sesión ordinaria del usuario.

1. Abrir la PRO6004 sintética y pegar cinco filas desde el portapapeles nativo
   en Reglas. El lote real cambia DRAWABLE a QUOTABLE y actualiza la etiqueta.
2. Seleccionar y confirmar dos sugeridos. La franja baja exactamente dos sin
   recargar el documento; la ficha usa la respuesta canónica del servidor.
3. Abrir las seis pestañas. Axe A/AA/2.1 AA no reporta infracciones y se
   comprueba que no existe desbordamiento horizontal de la página.
4. Guardar el precio 1234,5678, consultar su evento y deshacer mediante un
   nuevo cambio auditado. No se borra historia ni se altera un documento emitido.
5. Elegir Abatible izquierda y calcular una ventana de 1200 × 1100 con el motor:
   HTTP 200 y despiece con PRO-F. Esta vista preliminar no registra verificación.
6. Abrir 300 perfiles, paginar 50 filas, conservar nombres de 80 caracteres y
   peso exacto 1,2345. Buscar sin coincidencias y abrir ejemplos bajo demanda,
   sin modificar el contador de dos series propias.
7. Crear desde una plantilla versionada y abrir la ficha devuelta. Los perfiles
   ausentes permanecen vacíos y la serie pide completar; no se inventan valores.

La regresión `catalog-advanced.spec.ts` mantiene el flujo anterior de alta,
edición y reapertura con API real; aprobó en la misma pila. El teclado completo,
pegado rectangular y deshacer están cubiertos en la [aceptación P02a](../dk2-p02a/aceptacion.md).

## Rendimiento y pruebas

Tiempos locales observados en la última ejecución: inicio 1,34–1,53 s, ficha
0,85–0,90 s y 300 perfiles 2,34–2,35 s. Son tiempos de navegación de esta pila,
no mediciones de producción ni Core Web Vitals. El inicio carga solo series
propias y pospone ejemplos, plantillas y biblioteca hasta necesitarlos.

La validación de fase incluye motor (1.071 aprobadas, dos xfail y goldens
idénticos), backend (1.642 aprobadas y un inventario de rutas corregido; las
cinco pruebas de OpenAPI pasan al repetir), frontend completo (1.173 aprobadas),
21 integraciones de catálogo, 18 unitarias de orígenes y 1.514 aserciones pgTAP
existentes más nueve del ordinal nuevo. Ruff, mypy, Django check, ESLint,
TypeScript, Prettier, guardas, reproducción API y build aprobados. La copia de
entrega vuelve a ejecutar frontend completo, tipos, guardas y build antes de
abrir la PR; CI es el gate obligatorio para cada commit que se fusione.

Todos los datos de aceptación son sintéticos explícitos. REVIEW conserva su
estado. Las historias inmutables impiden borrar las empresas sintéticas al
finalizar cada test; permanecen en la base aislada hasta terminar esa pila.
P03 sigue pendiente: asistente reanudable, doble lectura del manual, precios
por columnas, corrección/verificación de prueba y caso dorado por tenant.
