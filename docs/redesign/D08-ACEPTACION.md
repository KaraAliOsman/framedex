# D08 · Tipologías avanzadas

Verificado sobre código `9213655c`, rama `codex/D08-tipologias-avanzadas`, con
Supabase/Auth propios, Django, worker y Chromium. La evidencia se conserva en
[tipologías avanzadas](captures/tipologias-avanzadas/). Integrado por
[PR #150](https://github.com/KaraAliOsman/framedex/pull/150), squash
`d6921a893fcc3b303fcd693bd934380e7227f3d0`; CI 4/4 verde sobre `b66ba1c6`
en la corrida `38174351774`. La comprobación local completa terminó con salida 0.

## Resultado y autoridad

El catálogo aporta siete series v8 y catorce recetas: HST A/C, PSK XO,
plegable 3+0/2+1 con/sin hoja de paso, pivote vertical/horizontal,
guillotina simple/doble con muelles/contrapesos y puerta corredera XO.
Cada receta declara perfiles, holguras, encuentros, planos, recorrido,
herrajes y fuente. Los esquemas G/K no se inventan ni se ofrecen.
Todas las series, medidas y precios sintéticos están marcados DEMO y
no acreditan certificación ni un catálogo comercial de fabricante.

El motor calcula cortes/BOM/vidrio/peso/kit y la planta con Decimal.
Los doce enums históricos y las series v1–v7 conservan su autoridad y sus
goldens. Los movimientos avanzados usan el contrato `Opening` existente;
la receta tiene identidad propia y no agrega ramas de `BayOpeningType`.
Un fijo no recibe herrajes. La hoja de paso conserva cierre independiente.
Guardar, preciar y emitir emplean un contexto Decimal local de 80 dígitos;
la aritmética ambiental no cambia el snapshot ni su hash.

## Flujos verificados

- Biblioteca → serie compatible → receta → vidrio de seguridad → planta →
  kit/manilla → guardar → recargar: 14/14 PASA, BOM y diseño idénticos.
- Las 14 recetas en 1440×900, 1280×800 y 1024×768, claro/oscuro:
  84/84 PASA, precio calculado por el motor, herrajes móviles, sin desbordes
  ni errores de página. La revisión final añade la leyenda cerrada/abierta
  a las catorce capturas técnicas sobre una copia editable independiente.
- Sistema básico sin capacidad: HST ausente de los diseños seleccionables;
  causa y series que lo permiten en la biblioteca, con destino Catálogo.
- Vacío, carga y resolución, error 503 con reintento, operario sin permiso,
  medida fuera de rango y Ctrl+Z restaurando el estado: PASA.
- Catálogo: receta estructurada, fuente DEMO y elevación HST de 8 mm
  conservada desde su autoridad. No se publica una fuente de fabricante falsa.
- MiMo real: 2/2 propuestas, HST C y plegable 3+0 con paso; simulación del
  motor y operaciones tipadas sin rechazados. La marca pública del asistente
  continúa separada del proveedor y sus credenciales.
- Precio aplicado → preparación de emisión → revisión A → DOC-01 async →
  enlace público: PASA para 14 posiciones. La medición del ensayo es sintética
  explícita; no acredita un levantamiento en obra.
- Portal: 14 elevaciones selladas, precios y ficha; ocho tamaños/temas
  incluyendo 390×844, sin desborde ni errores. La navegación JSON/HTML está
  anonimizada. Después del ensayo se revocaron los enlaces locales del fixture:
  respuesta pública 410. El PDF emitido conserva su QR histórico y sus bytes,
  con una capacidad ya revocada, sin acceso a una cuenta productiva.

## Dibujo y evidencia

[Antes](captures/tipologias-avanzadas/antes/) conserva las seis vistas de la
serie básica previa. [Matriz](captures/tipologias-avanzadas/matriz/validacion.json)
registra los 84 ensayos y [estados](captures/tipologias-avanzadas/estados/)
los fallos deliberados y sus salidas. [Recorrido](captures/tipologias-avanzadas/recorrido/)
incluye captura técnica, planta y comercial de cada receta, los SVG comunes,
el PDF real emitido y su verificación SHA-256. Los PNG se comprimen sin
alterar sus píxeles. Las referencias históricas `s063`/`s064` se contrastaron
como gramática visual; no se usan como autoridad de cálculo.

DOC-01 tiene ocho páginas Carta; se verifican nombres, catorce posiciones,
DEMO, vista interior y geometría proveniente de la revisión inmutable.
El renderer técnico/comercial usa las mismas hojas/manillas, y omite cotas
en comercial. La planta distingue trazo cerrado discontinuo y abierto
continuo; contiene paquete plegado, elevación/carril HST y eje de pivote.
La vista interior/exterior refleja una vez y mantiene textos legibles.
P19 completa la cinemática de la vista 3D sobre esta autoridad.

`ux:capture`: editor/nueva posición 16 vistas, Catálogo ocho y portal ocho;
cero hallazgos, errores de consola/HTTP o desbordes en sus informes.

## Pase editorial, dos rondas

Primera ronda: se reemplazó la oferta genérica de movimientos por recetas
compatibles con fuente y previews del motor; se retiraron los kits de paños
fijos del inspector; el editor estructurado reúne herraje y recorrido sin
exponer un JSON que el estimador deba interpretar.

Segunda ronda: la ficha elige la primera hoja móvil y muestra mm con la
precisión de presentación común, sin colas decimales ni `.00`; la planta
explica los trazos cerrado/abierto; el PDF conserva coordenadas Decimal
al serializar, sin el redondeo implícito de `normalize()`. El cierre de la
hoja de paso deja de poder sobrescribirse con el kit general del paquete.

F5 se extiende al recorrido real de la receta. F6 permite consultar fuente,
esquema, carril/eje y recorrido. La idea del §8 compara en el lugar los
sistemas que habilitan la tipología y explica qué autoridad falta.

| Regla | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Mono tabular y formatos comunes; mm sin colas ni `.00`. |
| R2 | PASA | Tokens con radios ≤ 4 px; inglete del lienzo común. |
| R3 | PASA | Planta por líneas, una biblioteca, sin capas ornamentales. |
| R4 | PASA | Naranja en restricciones que requieren persona; CTA teal. |
| R5 | PASA | Cromo común en ambos temas. |
| R6 | PASA | Hoja, umbral, paso, carril, pivote; recetas con nombres humanos. |
| R7 | PASA | Ingeniería plegada, riel común compacto y lienzo principal. |
| R8 | PASA | Cinco estados y salidas probados en Chromium. |
| R9 | PASA | Elevación sobre papel; PDF Carta con cajetín y huella. |
| R10 | PASA | Selección común con contorno, tinte y manijas. |
| R11 | PASA | Gramática del motor, fixtures interior/exterior y manillas físicas. |
| R12 | PASA | Labels, foco tokenizado y Ctrl+Z ejercitado. |
| R13 | PASA | Sin animación añadida; reduce-motion común. |
| R14 | PASA | Elegir receta, guardar o emitir según la etapa. |
| R15 | PASA | Fuente/receta del catálogo; ausencia bloquea, sin cifras sustitutivas. |
| R16 | PASA | Sin degradados, blur, brillo ni morado IA. |
| R17 | PASA | 84 vistas de receta y matrices oficiales sin desbordes. |
| R18 | PASA | Guardado, recarga, precio, emisión y deshacer reales. |
| R19 | PASA | F5 muestra paquete/carril/eje calculado; F6 conserva autoridad. |
| R20 | PASA | Disponibilidad por serie y causa desde el catálogo y el motor. |

## Decisiones y límites

Las recetas se configuran en Catálogo, bajo permisos/fuente/validación de P16;
no existe una preferencia de Ajustes capaz de inventar capacidad física.
SQL rechaza recetas incompatibles, floats, fuente ausente y kits cruzados.
El catálogo v8 y las reglas mixtas nuevas se publican mediante migración;
un upgrade no necesita reproducir `seed.sql` ni reescribir autoridades previas.
El portal publica únicamente la proyección técnica permitida, sin costos,
fuentes privadas o credenciales. Se mantienen los adaptadores sandbox
existentes; D08 no introduce una integración externa nueva.

La cotización local no prueba carga de viento ni aptitud industrial real.
Se requieren catálogo, ensayos y políticas con fuentes del fabricante antes
de fabricar. Los fixtures sintéticos no sustituyen ese trabajo. No se
reescribe una revisión emitida para actualizar capturas o preferencias.
Véase [decisiones](../decisions/valores-por-defecto.md).

## Gates

Lint, typecheck, test y build locales PASA: motor 1006 (+2 xfail históricos),
backend 1544 y frontend 1076. Golden check byte a byte PASA.
Database Gate completo PASA: 95 archivos / 1451 pgTAP, 554 integraciones,
19 Auth E2E y trece programas de upgrade poblado PostgreSQL 16, incluido
D08 y la comprobación final de terreno. Teardown propio PASA, salida 0.
La primera corrida encontró una lista E2E de series anterior a v8 y una
regeneración API concurrente con Vite. Se actualizó la expectativa de las
siete series y se separaron ambos procesos; la corrida completa posterior
pasó sin debilitar checks ni timeouts. CI se registra al integrar.

La revisión del PR detectó dos regresiones: el formulario normalizaba cada
tecla y borraba decimales aún incompletos; el modo paso afectaba otros vanos.
Se conserva el borrador literal y se normaliza exactamente al salir, con error
en español cuando falta completarlo. La planta limita el paso al vano plegable.
Cuatro regresiones nuevas y seis pruebas focales pasan; los gates completos
posteriores conservan motor/backend y suman 1076 pruebas frontend. Mypy sin
caché verifica las 128 fuentes; el manifiesto v7 declara su retorno tipado.
En Chromium pasan seis vistas de escritura (fracción larga tecla a tecla,
signo, coma y borrador incompleto) sin publicar ninguna autoridad. El componente
común con tres vanos conserva el recorrido HST y el polígono de pivote cuando
se abre el paso. [Revisión](captures/tipologias-avanzadas/revision/validacion.json)
conserva los resultados y las capturas con sus estilos reales. Catálogo repite
ocho vistas `ux:capture` sin hallazgos. La evidencia total contiene 199 PNG.
