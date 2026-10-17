---
type: research
status: active
updated: 2026-10-17
volatility: medium
verified_ref: edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f
sources:
  - docs/ux/2026-10-17/README.md
  - docs/ux/2026-10-17/01-auditoria.md
  - docs/ux/2026-10-17/02-competencia.md
  - docs/wiki/sources/owner-ux-direction-2026-10-17.md
---

# Revisión de experiencia y competencia · 17-10-2026

## Resultado y estado

[Plan completo](../../ux/2026-10-17/README.md),
[auditoría](../../ux/2026-10-17/01-auditoria.md),
[fuentes/competencia](../../ux/2026-10-17/02-competencia.md),
[ejecución](../../ux/2026-10-17/07-ejecucion.md) y
[prompts](../../ux/2026-10-17/08-prompts.md).

La investigación comenzó como preparación documental. El dueño autorizó después
la construcción con «ahora empieza». Los hechos siguientes describen el ref
auditado; el [registro de implementación](../../ux/2026-10-17/10-implementacion.md)
documenta por separado el nuevo código y sus verificaciones.

## Hechos de código verificados en el ref indicado

- `navigation.ts` refleja permisos de lectura del API; eso no garantiza una
  navegación adecuada al trabajo frecuente de cada rol.
- Crear proyecto requiere nombre de obra y de cliente; nueve campos adicionales
  ya son opcionales/plegados. No afirmar que once campos son obligatorios.
- El renderer 3D omite deliberadamente ingletes en `memberBar`; el SVG 2D sí
  incluye lógica de uniones. Existe soporte parcial de texturas.
- El flujo de catálogo compila `source_lines` más una fuente que la pasarela
  resuelve de forma multimodal. El helper rasteriza páginas sin texto; si hay
  texto, lo envía y puede perder el gráfico de una página mixta. Límites de 20
  páginas/100 000 caracteres; sin modelo integral de layout/regiones/relaciones.
  Citas HIGH se verifican contra líneas locales. `vision_ocr` es otra capacidad
  de posiciones; no implica ausencia de transporte visual en el catálogo.
- `_unit_map_svg` de `backend/production/pack.py` es el punto de entrada para el
  problema observado de anotaciones de ensamblaje.

## Evidencia de producto y documentos, con límites

Se navegó REVIEW con estimador y encargado, se hizo una petición IA simple que
se descartó y se leyeron/renderizaron documentos existentes. **El SHA del build
REVIEW no se comprobó**; esas observaciones no se atribuyen automáticamente al
ref de inspección de código. Datos fixture/DEMO.

Ventanas desplazadas por cabeceras, nogal plano, importador orientado a plantilla,
materiales poco vinculados al dibujo y cola de OT/tareas repetida son hallazgos
de experiencia. Filas de stock parecidas no demuestran duplicación de BD.

El pack renderizado de una OT de cuatro unidades fijas tiene 24 páginas y códigos
cortados/solapados en su plano; el corte específico es más útil. No se emitió una
orden/revisión nueva. Doce imágenes propias se conservan con manifiesto en
[evidencia](../../ux/2026-10-17/evidencia/README.md).

## Investigación externa

La [segunda revisión](../../ux/2026-10-17/11-reconstruccion.md) amplía tareas de
Windowmaker, Klaes y A+W y estudia las fuentes oficiales de
[Grok Bot](https://x.ai/news/designing-grok-bot) y
[Dots](https://learn.chatgpt.com/docs/dots?nav=features), consultadas el 17-10-2026.
Se adopta continuidad del encargo, estado discreto y resultados interactivos.
Documentación pública no equivale a operar sus productos autenticados ni conocer
sus capacidades privadas. La matriz enlaza la evidencia y sus incógnitas.

Vídeos por tramos: dos de NuveraPRO, uno de Winart/Haustek, tres de Moxisys y
referencia oficial Logikal 12; además contexto histórico Logikal 10.1.0.45 de
WorkStation. El registro enlaza vídeos y tiempos aproximados. No se vieron
íntegros ni se operaron licencias comerciales.

Síntesis: rapidez de cotización/defaults de Nuvera/Winart; dibujo y presentación
de Moxisys; datos técnicos/continuidad industrial de Logikal. Windowmaker,
Klaes, A+W, RA Workshop, OpenJanela y Oknosoft aportan referencias complementarias.
El material de RA y Oknosoft incluye historia. Módulos Moxisys opcionales/en
desarrollo no se describen como ERP incluido y listo.

Las matrices distinguen observado, documentado, comercial e incógnita. No se
demostró una importación universal PDF→catálogo fabricable en un competidor y
no se concluye que no exista. No hay ranking operativo ni tiempos comparativos
medidos. No se redistribuyen vídeos/documentos externos.

## Intención y propuestas

[Fuente del dueño](../sources/owner-ux-direction-2026-10-17.md): un tema definitivo,
calidad/placer de uso, IA que quite trabajo, catálogo PDF y pruebas al final.
Propuestas del estudio: claro neutro, defaults, editor directo, IA con Deshacer,
pipeline multimodal y revisión por excepción, documentos por destinatario.

La [realidad vigente](../state/current-reality.md) separa la integración histórica
del trabajo nuevo en rama. La aceptación y el baseline IA del 12-10 conservan
fecha/ref y no se presentan como mediciones de esta investigación o de la rama.
