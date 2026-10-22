# P06a · Mesa de la obra e inspector móvil

Verificación local del 22-10-2026 en `gpt/dk2-p06a-obra-unica`, sobre P05k
`1e1ead31`. API 8010, preview de producción 5175 y PostgreSQL propio aislado.
Se conservan el checkout del dueño y REVIEW. Los catálogos y clientes usados
son sintéticos; los cálculos, operaciones, guardados y lecturas son reales.

## Alcance

La propuesta `VITE_OBRA_VISTA_UNICA` está activa por defecto; `false`, `off` o
`0` restauran las vistas anteriores. En el borrador editable, la lista de
ventanas permanece al lado del dibujo y del inspector. La cabecera reúne
obra, cliente, total con IVA y preparación de cotización. «Pedir a DEKOPEN»
abre el compositor y requiere la acción posterior de enviar. «Enviar
cotización» abre la preparación existente; no envía ni emite un documento.

Serie, color y cantidad comparten el inspector con medidas, apertura y vidrio.
Los datos avanzados quedan plegados y el precio guardado permanece visible,
con el desglose comercial del motor a un clic. El material se abre desde el
inspector. 2D/3D ocupan el mismo lienzo; Interior/Exterior comparten la cara.
Los permisos y los bloqueos de revisiones conservan la autoridad del servidor.

A 390 px la lista y el dibujo se apilan y el inspector se abre abajo. Se
permite editar y guardar; dividir con precisión y acoplar requieren una
pantalla mayor. Los controles de historial y guardado siguen disponibles.
Escape cancela una cota sin que blur la aplique ni despache una simulación.

## Regresiones corregidas y pruebas conservadas

Guardar refresca la consulta compartida de obra antes de seleccionar el id
nuevo. Se evita perder la selección contra una lista anterior o dejar el total
obsoleto. Actividad y las otras secciones conservan la sesión y el historial,
incluido el borrador nuevo. Cambiar de ventana o salir conserva el guardián.

«Más → Organizar ventanas» conserva la colección con operaciones de lote.
Las pruebas usan esta entrada explícita y recargan para verificar la persistencia
cuando la sesión sigue montada; conservan BOM, tenant, duplicación y clonación.
La prueba móvil sustituye la expectativa antigua de solo lectura por cantidad
editada y guardada con el servidor. Las aserciones de geometría, precio,
rollback, propuestas y respuestas obsoletas se conservan.

Las pruebas de rutas compilan las mismas pantallas diferidas durante su setup:
sus cuatro fallos de la suite concurrente eran esperas de transformación de Vite
en Suspense. No se aumentan timeouts ni se simulan destinos. La suite completa
del frontend pasa con 1.257 pruebas; 89 regresiones finales de las superficies
tocadas también pasan. ESLint, TypeScript, guardianes y build aprobados.

La corrida completa final usa `vitest run --maxWorkers=4` (120 archivos,
103,56 s), conservando todas las aserciones y los límites de tiempo. La
concurrencia automática junto a Chromium/TypeScript saturó una prueba ajena
de 100 filas de llamadas IA; con cuatro workers pasa toda la suite. Ocho
pruebas de miembros incluyen la regresión de cara sin muestra de acabado.

Los recorridos de editor, proyecto y mesa comprueban once casos; los dos de
precio conservan emisión, PDF y extremos de la colección. Después de los
ajustes de Escape y cara, ambos recorridos finales de la mesa pasan sin
reintentos; el móvil repite la captura con el dibujo dentro de la pantalla.

## Revisión visual, rendimiento y movimiento

La composición sigue `Main.dc.html`: navegación compacta, cabecera, lista,
dibujo dominante e inspector simple. Se conserva la búsqueda global y la
capacidad profesional del editor. La revisión final de P06 todavía debe
comprobar extremos, avisos y el recorrido completo de tres tipologías.

| Superficie         | 1440 × 900                       | 390 × 844                  |
| ------------------ | -------------------------------- | -------------------------- |
| Obra vacía         | [Escritorio](empty-1440.png)     | [Móvil](empty-390.png)     |
| Dibujo e inspector | [Escritorio](inspector-1440.png) | [Móvil](inspector-390.png) |
| Mesa y dibujo      | [Escritorio](workbench-1440.png) | [Móvil](workbench-390.png) |
| 3D en la mesa      | [Escritorio](3d-1440.png)        | [Móvil](3d-390.png)        |

Móvil verificado con emulación Chromium, sin dispositivo físico. Los recorridos
comprueban ancho sin desborde y axe WCAG A/AA en la mesa. El editor conserva
sus verificaciones de encaje a 1440, 1280 y 1024 y pan extremo.

No se añaden animaciones a acciones frecuentes ni se interpola geometría. Los
cambios 2D/3D son inmediatos; el 3D conserva carga diferida y su límite de
hardware. El desplazamiento a los avisos respeta `prefers-reduced-motion`.
El chunk 3D de 752 kB conserva la deuda existente de P11.

La mesa vacía cargó en 929 ms a 1440 px y 944 ms a 390 px en la corrida final
de ambos tamaños. [Mediciones](tiempos.json). Es carga local de una obra;
no acredita todavía respuesta menor de 100 ms al editar.

Escape en el desglose de precio cierra solo el popover y conserva el inspector
móvil. Los gestos del editor escuchan después de las capas internas; el E2E
comprueba la permanencia de la hoja y la sincronización de cara en 3D.

Los dos recorridos conservados de precio, emisión, PDF y 500 filas visuales
pasan. Carga de obra 1.460–1.540 ms; 500 filas 2.077–2.084 ms; búsqueda 57 ms.
Esas filas pertenecen a la colección avanzada; no acreditan todavía el
rendimiento de la nueva lista persistente.

## Pendiente de P06b

- Precio simple vivo de la ventana sin guardar, con desglose del mismo motor.
- Respuesta del dibujo menor de 100 ms mientras el motor valida en segundo plano.
- Chips de aviso con corrección y deshacer sobre la ventana afectada.
- Flujo de fija, abatible doble y corredera mediante catálogos compatibles.
- Extremos de 120/500 ventanas y nombres/medidas en la lista persistente.

P06 sigue en curso. Esta entrega no acredita fabricación Proline, proveedor IA
real, teléfono físico ni aceptación visual final del dueño.
