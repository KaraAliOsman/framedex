---
type: concept
status: active
updated: 2026-10-22
volatility: high
verified_ref: gpt/dk2-p05i-mensajes-servidor
sources:
  - docs/research/2026-10-21-competencia/prompts/P05-navegacion-hoy-obras.md
  - docs/design/CONSTITUCION.md
  - frontend/scripts/check-catalog-copy.mjs
  - frontend/src/decimal.ts
  - frontend/src/ui/DomainValues.tsx
  - frontend/tests/e2e/product-language.spec.ts
  - engine/src/dekopen_engine/thermal.py
  - backend/analytics/today.py
  - backend/projects/ops_registry.py
  - backend/pricing/service.py
  - backend/pricing/workspace.py
  - backend/analytics/metrics.py
  - backend/search/service.py
  - docs/redesign/captures/dk2-p05i/aceptacion.md
  - docs/redesign/captures/dk2-p05g/aceptacion.md
---

# Lenguaje de la interfaz

## Hechos verificados en P05g

El guardián histórico de Catálogo analiza ahora todos los archivos TypeScript
del producto y todos los valores del diccionario. Incluye funciones avanzadas,
textos accesibles y templates. No interpreta comentarios, identificadores,
claves de contratos o relaciones DOM como texto visible. Pruebas del detector
conservan esa frontera y comprueban que un aria-label sí se revisa. Se excluyen
API generada, pruebas y pantallas de desarrollo, ausentes del build productivo.

El detector rechaza «Sin dato», «sellado», «autoridad», «fuente» y «procedencia»
en textos del producto. No usa una lista base de infracciones permitidas.
Los valores ausentes conservan null y piden completar; los formateadores
compartidos y sus componentes distinguen esa etiqueta de una cifra real.
Las pruebas siguen comprobando ceros, precisión, monedas y trazas existentes.

Los avisos térmicos y de Hoy se corrigen también donde se producen. El ensayo
de once pantallas espera contenido visible cargado antes de buscar las cinco
voces y capturar, a 1440/390 px. La prueba no inspecciona el estado pendiente
de un panel cerrado como si fuera contenido visible. Las pestañas móviles
conservan su ancho y el desplazamiento local; sus etiquetas ya no se solapan.

La revisión distingue documentos emitidos, precios guardados y revisiones
preparadas antes de emitir. Los datos físicos pertenecen a la orden: una
sección no se presenta como documento emitido. El servicio de aplicar sellante
y la junta de cierre mantienen su significado físico. Las tareas de IA usan
Resumen; un comprobante de pago conserva su significado financiero.

La regresión bow detectó lecturas repetidas de costos DEMO en el precio
indicativo. `sale_price` usa ahora el prefetch y repositorio propios del
cálculo; la siguiente consulta crea otro repositorio. Una integración compara
el resultado exacto sin caché, cuenta una sola lectura DEMO y comprueba nuevas
tarifas entre consultas. No cambia una fórmula ni introduce una caché global.

## Intención y trabajo pendiente

El encargo del dueño exige español de taller en todas las superficies.
P05g cubre las cinco voces iniciales y el lenguaje de tareas de IA. P05h amplía
el guardián a posición/vano, encargo y recibo, con la misma frontera entre texto
y contrato. Conserva los sinónimos antiguos de búsqueda y los enlaces DOM.

La revisión contextual de P05h distingue la ventana de la obra, el paño de su
dibujo y la coordenada de mecanizado. Las medidas de obra no se confunden con
las medidas de fabricación; una manilla tiene ubicación y un punto CNC no es
una ventana. Los cobros tienen comprobantes; las tareas del asistente, resumen.
Se corrigen también las etiquetas de espécimen térmico y acciones de Hoy.

P05i cubre diecinueve módulos de obras, precios, búsqueda e informes del servidor.
Los errores conservan códigos, monedas, selección y ausencia de precio. La
proyección actual usa textos humanos; los snapshots antiguos se reproducen sin
reescribirlos. Consultas SQL, claves y literales numéricos permanecen idénticos.

Los demás textos generados por backend, motor y documentos requieren las rondas
siguientes; el recuento cero de TypeScript no acredita esas respuestas.
No se reescribe evidencia emitida ni prosa aportada por clientes para conseguir
un recuento de cadenas. P05 sigue en curso hasta cerrar esa revisión y sus PR.

La enmienda del 22-10 en la constitución registra el glosario global. Las
capturas de fases anteriores describen sus propios refs y no se regeneran
para aparentar una aceptación nueva.
