# Plan de ejecución, calidad y cierre

## Forma de trabajar

Este paquete no autoriza implementación durante la investigación actual. Cuando el dueño entregue el prompt de inicio a Claude, el trabajo puede avanzar por las etapas siguientes con continuidad, sin pedir aprobación de cada decisión rutinaria. Emitir, enviar, publicar contenido externo o comprometer acciones de negocio conserva su clic humano.

La construcción prioriza recorridos y calidad. **Registrar defectos incidentales y agrupar bug fixing, pruebas automatizadas y verificación funcional en la etapa final.** La revisión de composición mientras se diseña no es una campaña de depuración. Si un bloqueo impide continuar una etapa, registrar la dependencia y resolver solo lo mínimo imprescindible o avanzar en trabajo independiente. No aprovechar una excepción para convertir todo el proyecto en pruebas continuas.

Mantener las invariantes durante la implementación. Las pruebas requeridas por cambios de fórmulas, RLS, pagos o contratos se preparan/ejecutan en el cierre antes de entregar; no se omiten ni se debilitan. Un diseño bonito no autoriza romper precisión o aislamiento.

## Etapas y prompts

| Etapa | Trabajo completo | Dependencias y resultado | Prompt |
|---|---|---|---|
| 01 | Consolidar dirección y sistema visual | Actualizar constitución con intención reciente, componentes, jerarquía y estados; preservar logo | [01](prompts/01-direccion-y-base.md) |
| 02 | Navegación, proyectos y primera cotización | Base 01; shell, listas, clientes en contexto, herencia y borrador | [02](prompts/02-recorrido-y-proyectos.md) |
| 03 | Editor, dibujos, perfiles y materiales visuales | Objetos de 02; edición directa, acabado normal, texturas y uniones | [03](prompts/03-editor-y-materiales-visuales.md) |
| 04 | IA contextual y ejecución | Servicios existentes y recorrido 02–03; capacidades tipadas, jobs, contexto, reversión y límites | [04](prompts/04-ia-trabajador.md) |
| 05 | Importación PDF de catálogos | IA/servicios base; pipeline por páginas, relaciones, revisión y fusión | [05](prompts/05-catalogos.md) |
| 06 | Documentos y editor | Dibujo/IA; ocho diseños, numeración, firma opcional y edición real | [06](prompts/06-documentos.md) |
| 07 | Precio, material y corte | Modelo y documentos; precio contextual, material enlazado y botón de corte | [07](prompts/07-precio-materiales-corte.md) |
| 08 | Taller y resto del producto | Continuidad 07; compras, stock, estaciones, CNC, portal, terreno y ajustes | [08](prompts/08-operacion-y-resto.md) |
| 09 | Integración y pase editorial | Recorridos completos y herramientas IA conectadas a catálogos/documentos/corte; retirar UI sustituida | [09](prompts/09-integracion-y-calidad.md) |
| 10 | Corrección y verificación final | Lista de incidencias, capacidades completas, gates y muestras reales | [10](prompts/10-cierre-y-pruebas.md) |

Cada etapa termina con objetos y superficies concretas, no con otra lista de ideas. La etapa 04 puede preparar las herramientas de nuevos dominios como contratos, pero no debe anunciar como operativas herramientas que solo se conectarán en 05–09. Ningún stub cuenta como entrega.

En 08 incluir también presentación de acceso/MFA, recuperación y portada, conservando su lógica y límites de seguridad. No crear nuevos planes comerciales. Los contratos del documento 13 sirven para comprobar cobertura de estas superficies menos frecuentes.

## Secuencia práctica dentro de cada etapa

Leer únicamente evidencia/specs pertinentes → comprobar puntos de integración → decidir composición y comportamiento → implementar la capacidad completa → revisar el resultado visual/editorial → registrar lo pendiente → continuar. Guardar un estado breve de trabajo con hechos, archivos, decisiones y dependencias para sobrevivir a cambios de contexto.

No releer todo el PRD o todos los planes históricos en cada etapa. No rehacer el motor, autenticación o API generada por preferencia estética. Cambios API parten del backend y regeneran OpenAPI/orval. No editar archivos generados a mano.

No crear un sistema de features escondidas para conservar todas las versiones viejas. Si se sustituye una superficie, retirar el camino anterior cuando el nuevo conserve sus capacidades, rutas y permisos. Una bandera transitoria puede ayudar a migrar, pero necesita salida concreta.

## Dependencias externas que no deben detener todo

- PDF exactos de fabricantes: construir pipeline y corpus sintético claro; no declarar importación Proline/Aluminios 2000 probada hasta recibirlos.
- Navegador: avanzar en fuente/composición, pero no firmar aceptación visual sin una inspección real posterior.
- Editor de PDF externo: completar documentos propios; preparar una decisión de SDK concreta y registrar licencia/integración pendiente si corresponde.
- Máquina CNC: completar intercambio neutro y contrato de adaptador; no afirmar homologación física sin acceso.
- «Sistemas Z»: mantener como investigación pendiente de identidad, no inventar comparación.

## Criterios de calidad de v1

| Dimensión | Resultado exigido | Evidencia final |
|---|---|---|
| Comprensión | Acciones principales reconocibles y vocabulario del oficio | Recorrido sin explicación previa y observaciones |
| Rapidez | Ventana estándar y cotización con preferencias; corte localizable | Tiempos medidos con condiciones declaradas |
| Aprendizaje | Persona nueva consigue tareas principales en unos 15 min | Sesión observada; ayuda requerida registrada |
| Visual | Coherencia entre shell, editor, PDF, IA y taller | Capturas reales comparables y muestras documentales |
| Dibujo | Apertura, vista, textura y encuentros comprensibles | Casos técnicos/comerciales del documento 05 |
| Documento | Ocho diseños útiles, edición manual/IA y firma opcional | PDF exportados y fuentes/versiones conservadas |
| IA | Realiza cambios y produce archivos/objetos válidos | Tareas con proveedor real y recibos; no solo texto |
| Catálogo | Un PDF, extracción reanudable, relaciones y excepciones | Corpus y referencia por campo/página |
| Operación | Material/corte/compra/taller continúan el mismo trabajo | Obra completa con cambios e invalidaciones |
| Confianza | Motor, Decimal, RLS, historia e idempotencia conservados | Gates pertinentes y revisión de contratos |

Los objetivos de tiempo no deben aprobarse con un video editado o una fixture que ya realizó los pasos. Medir tiempo activo y espera por separado. Si no se consiguen, explicar la causa y simplificar antes de afirmar cumplimiento.

## Escenarios completos de cierre

1. Negocio preparado: ventana estándar manual → cliente → PDF → material → corte.
2. Obra de varias ventanas: duplicación, cambios en lote, ambiente y precio.
3. IA prepara la obra con preferencias; el dueño cambia solo una ventana y revisa resultado.
4. Comparación de alternativas sin alterar el original; elección y nueva propuesta.
5. PDF: plantilla, edición local, firma desactivada, activación explícita y revisión emitida inmutable.
6. Catálogo digital/escaneado/mixto/largo, excepción y reanudación.
7. Segundo catálogo: ampliación y conflicto de edición; proyecto anterior conserva versión.
8. Material/corte con stock, retazos, longitudes comerciales y falta real de autoridad.
9. Compra por proveedor, recepción, taller, etiqueta y trazabilidad de pieza.
10. CNC neutro claramente identificado; programa obsoleto y máquina sin preparación.
11. Portal en móvil y agenda de instalador; sincronización y permisos.
12. Interrupción, cancelar/reanudar, doble clic, versión antigua y solicitud fuera del rol.

Ningún escenario de envío real, cobro, publicación o máquina se ejecuta sin la autorización humana específica que corresponda. Las pruebas de estas consecuencias usan entornos y datos de revisión.

## Campaña de bugs y pruebas al final

Primero consolidar incidencias por impacto: integridad/seguridad y pérdida de datos; trabajo bloqueado; resultado incorrecto; interacción; presentación. Reproducir y arreglar con casos relevantes. No crear pruebas que solo dupliquen la implementación ni snapshots cosméticos sin valor.

Después ejecutar checks pertinentes del repositorio: lint, typecheck, suites de motor/backend/frontend y build por el alcance transversal; database gate si hay esquema/RLS; mutation drill/goldens si cambian fórmulas. Regenerar goldens únicamente con el procedimiento permitido y revisar su diferencia. No tocar `engine/tests/golden_analytics.json` ajeno para conseguir verde.

Completar revisión de navegador sobre stack propio o del dueño sin resetear sus datos. Seguir la skill local de revisión, usar roles correctos y no interpretar una denegación como bug. Los PDF requieren inspección de páginas renderizadas, no solo que el archivo exista. La IA necesita proveedor real cuando se afirme su capacidad efectiva; un mock solo verifica el contrato simulado.

Una suite verde no reemplaza la revisión de diseño. Volver al recorrido completo y valorar legibilidad, motivación, claridad de controles y calidad comercial después de las correcciones que cambien composición.

## Qué significa terminado

No quedan capacidades principales sustituidas por placeholders ni enlaces que solo explican cómo hacerlo manualmente. Las limitaciones externas se nombran con precisión y no se presentan como terminadas. Se entregan capturas/PDF/recibos seleccionados, resumen de validación real y registro de alcance.

La entrega de implementación puede quedar en una PR revisable, con descripción centrada en el problema y comportamiento final. No fusionar o desplegar por interpretar «hazlo bien» como autorización de publicación. El dueño recibe un resultado concreto para juzgar; no una promesa de perfección.
