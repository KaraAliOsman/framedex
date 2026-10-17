# Construcción v1 · 17-10-2026

Autorizada por el dueño con «ahora empieza». Base: `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`.
Rama `codex/v1-experiencia`. El build REVIEW se reconstruyó desde este checkout
sin fixture/reset. Esta revisión no acredita aceptación definitiva del dueño ni
superioridad operativa sobre la competencia.

## Experiencia construida

| Área | Antes | Cambio implementado y propósito |
|---|---|---|
| Base visual | Dos temas y jerarquía muy densa | Tema claro único, papel blanco, mesa neutra, verde contenido y tipografía legible. Las preferencias antiguas no restauran oscuro. |
| Navegación | Herramientas organizadas como módulos internos | Trabajo habitual por rol y Más herramientas. Autorización del servidor conservada. |
| Obra | Cabecera, fases y datos antes de las ventanas | Ventanas primero; cuatro secciones principales; datos comerciales y herramientas adicionales plegados. Nueva obra sin cliente obligatorio. |
| Biblioteca | Repetición de serie, vidrio y acabado | Hereda decisiones de la obra y última serie por organización. Añade directamente con Deshacer; cantidad 1–9.999. |
| Editor | Detalle de hoja permanente y cabecera que crece | Propiedades habituales primero, ficha técnica plegada y cabecera compacta con nombres largos. El editor abre el mismo asistente contextual. |
| Representación | Extremos 3D rectos y acabados planos | Uniones 45/90 según cortes evaluados, veta por eje en SVG y UV longitudinal en 3D. Acabados ilustrativos, sin atribuirles fuente industrial. |
| IA | Entrada dividida y trazas que dominan | Una conversación contextual; resultados y muestras primero; fuentes plegadas. Se conserva continuidad, operaciones de dominio y Deshacer. |
| Cotización con IA | Muestra que lleva al formulario de precio | Calcula con preferencias reales; confirmar aplica el precio y prepara PDF privado. Un cambio de posición/importe requiere revisar la muestra nueva. No emite ni envía. |
| Presentación con IA | Sin operación de presentación | Propone título, introducción y composición del PDF, y textos de portal. Preview/apply/state/undo tipados, exclusivos del dueño, MFA, versión, firmas contra cambios concurrentes e idempotencia. |
| Catálogo PDF | Plantilla primero; límite de 20 páginas | PDF como entrada principal; bloques de cuatro páginas, hasta 1.000, texto e imagen de páginas mixtas, progreso y reintento del mismo trabajo. Revisión por dudas y fuente por página. |
| PDF comercial | Dibujos pequeños, cierre fragmentado | Composición Editorial/Compacta, título e introducción, miniaturas y dibujos mayores; resumen y aceptación juntos. Versiones antiguas conservan renderer sellado. |
| Visor | Acceso al documento fuera del trabajo; iframe en blanco en el navegador integrado | PDF.js local con páginas, zoom y texto accesible plegado; bytes privados, worker propio, descarga con blob revocable. En revisión de emisión se comprueban huella, tamaño y cabecera, y la confirmación se habilita tras renderizar. |
| Revisión de la propuesta | Formularios repetidos y falsos pendientes al recuperar un PDF de la IA | El PDF preparado ocupa la revisión. Ajustar datos abre la preparación real; no vuelve a exigir datos ya contenidos en el documento. |
| Materiales | BOM separada del dibujo | Ficha amplia con selección bidireccional por identidades reales de módulo/paño. Cantidades por unidad y explicación cuando no existe destino individual. |
| Taller | Anotaciones cortadas/solapadas y saltos excesivos | Callouts fuera del plano, menos saltos de sección y paquete renderizado de 19 páginas en el caso de referencia, frente a 24 anteriores. |
| Operación | Tareas repetidas y compras con faltante cero | Hoy agrupa causas y pagina; producción busca OT/obra/cliente y carga por bloques; compras prioriza faltantes, con opción de ver cubiertos. |
| Actualización web | Una pestaña puede conservar la entrada del bundle anterior | Entrada SPA/field-worker revalidables; assets con hash siguen inmutables. |

El recorrido no permite que un LLM fabrique cifras. Precio, medidas y BOM siguen
procediendo del motor y catálogo. Se preservan Decimal, organización/RLS,
revisiones emitidas, auditoría e idempotencia. Emitir, enviar, comprar, pagar y
liberar producción conservan su acción humana en el producto.

## Verificación de cierre

La campaña formal se ejecutó después de construir e integrar. Los logs completos
permanecen locales en `.run/v1-final/`; se versiona únicamente evidencia elegida.

| Comprobación | Resultado registrado |
|---|---|
| Motor | 1.064 pasan, 2 xfail esperados. Sin cambios de fórmulas. |
| Backend unitario | 1.583 pasan. |
| Frontend completo | 1.147 pasan en 213 suites antes del último cierre del flujo directo; las modificaciones posteriores tienen corridas afectadas separadas. |
| Integración PostgreSQL | 605 pasan. |
| pgTAP | 1.483 comprobaciones pasan en 97 archivos. |
| Flujo nuevo de precio/PDF | Ocho casos pasan: confirmación, concurrencia, importes cambiados, aprobación de dueño, recuperación, doble clic y serialización JSONB/fechas con precisión completa. |
| Materiales/dibujo | 38 pruebas afectadas pasan, incluyendo identidad entre módulos y destino ausente. |
| PDF/cotización | 20 pruebas afectadas pasan; documentos renderizados e inspeccionados. |
| Revisión y visor integrado | 41 casos afectados de obra/revisión pasan; el navegador integrado renderiza el PDF real, cambia de página y ajusta zoom. |
| Guarda del build | Cinco casos pasan; la excepción de diagnóstico upstream queda limitada al literal y chunk de PDF.js. |
| Comprobaciones estáticas | Ruff, mypy (135 archivos), Django check, ESLint/TypeScript, formato, guardas de fuentes, símbolos/aperturas y fixtures 3D. OpenAPI/orval reproducibles. |
| Build | Producción pasa; se conserva el aviso de tamaño de un chunk mayor de 500 kB. |
| PostgreSQL 16 | Migración limpia y actualizaciones pobladas pasan, conservando BOM, importes y bytes emitidos; recursos aislados detenidos al finalizar. |
| Navegador | 19 escenarios con resultado verde en su última ejecución: 16 en la corrida general y tres en repeticiones afectadas. El cierre de emisión y obra pasa (2/2), con recepción del PDF idéntico en Mailpit, revisiones inmutables y revisión a ancho completo. No se presenta como una nueva corrida completa de 19. |

El gate usa un proyecto Supabase aislado, con propiedad y puertos separados de
REVIEW. Su cierre detiene únicamente sus propios recursos. El estado y sesiones
del dueño se conservan. El cambio ajeno `engine/tests/golden_analytics.json` queda
fuera de esta entrega. Los bytes de `golden_extras.json` se normalizan a LF según
su generador, sin alterar valores.

La IA real se ejercitó con API, worker y proveedor configurados, como estimador,
en obras DEMO con/sin precio. Los primeros dos trabajos completaron en unos 15 s,
sin preguntas/rechazos, sin modificar borradores ni emitir revisiones. Son casos
de producto; no un resultado nuevo del harness ni una tasa de éxito general.

El dueño confirmó después que se usen las preferencias guardadas de la empresa
para cotizar y se pregunte solo por datos imprescindibles. El cálculo preparado
consulta esas preferencias en el servidor; no solicita de nuevo margen, moneda
o modo de precio ya definidos.

Un tercer encargo real preparó la propuesta de `P-000016`, obra sintética con
dos unidades: neto CLP 288.613, IVA 54.836 y total 343.449, procedentes del motor.
La muestra permitió aplicar el precio y preparar el PDF desde la conversación.
La lectura posterior del API confirmó `DRAFT`, precio vigente, **cero versiones
emitidas y cero registros de correo**. Se recuperó la revisión desde el historial
y se renderizó el documento de tres páginas sin emitirlo. No se atribuye a la IA
la creación de los antecedentes de ese fixture, preparados por APIs de dominio.

La dependencia nueva `pdfjs-dist` no aparece en los siete avisos de `npm audit`.
Los siete corresponden a versiones ya presentes en el lockfile base (cinco altos,
uno moderado y uno bajo); este trabajo no los presenta como resueltos. El build
mantiene la guarda contra texto de demo: solo exceptúa un diagnóstico literal
de PDF.js dentro de su chunk propio. Cinco casos verifican que los demás TODO,
textos de demo y rutas de desarrollo se siguen rechazando.

## Evidencia y límites materiales

[Capturas anteriores y nuevas](evidencia/README.md). Los PDFs comerciales de
referencia tienen 12 páginas Editorial y 10 Compacto; el pack de taller, 19.
La inspección incluye las páginas finales para comprobar que aceptación y resumen
comercial permanecen juntos. Las referencias no cambian los documentos emitidos.

- La IA puede preparar presentación mediante campos autorizados. No edita código
  arbitrario de la aplicación ni permisos; no existe una transacción única que
  aplique diseño, precio y PDF de una vez. Primero se aplica el diseño revisado.
- La lectura integral por bloques está construida, pero faltan OCR por regiones,
  citas con bbox y un corpus de catálogos de fabricante evaluado de extremo a
  extremo. No se promete convertir cualquier PDF en autoridad de fabricación.
- Texturas ilustrativas; faltan activos aprobados de fabricantes. El renderer
  proporcional del PDF sigue separado del renderer interactivo del frontend.
- Materiales se enlazan al módulo/paño cuando el BOM aporta identidad; no se
  inventa una barra física individual a partir de SKU u orden de fila.
- Producción aún no tiene miniaturas y agrupación completa por obra. Clientes,
  cobranza y analítica heredan base/navegación, pero conservan su composición
  anterior. Esos ámbitos no se registran como un rediseño completo.
- No se hizo una aceptación profesional independiente ni una validación exhaustiva
  de todos los dispositivos. Datos DEMO, sandbox y pruebas automáticas no acreditan
  certificación industrial ni funcionamiento de servicios externos productivos.

Los [prompts](08-prompts.md) conservan la estructura original para contexto y
continuidad. No se vuelven a ejecutar paquetes ya construidos ni se convierten
sus objetivos futuros en hechos de implementación.
