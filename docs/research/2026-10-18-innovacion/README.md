# DEKOPEN — revisión desde dirección de innovación

18-10-2026 · investigación y recomendaciones, sin cambios en el producto.

Mi recomendación es construir una ventaja alrededor de **cotizar con certeza y conservar esa certeza hasta la entrega**. El cliente del SaaS necesita responder: qué está vendiendo, si puede hacerlo, cuánto gana, qué falta y qué consecuencias tiene cambiarlo. El asistente puede acelerar ese trabajo; la ventaja debe existir también al trabajar manualmente.

Se revisaron veinte fuentes primarias adicionales de quince organizaciones: dieciocho páginas accesibles y dos documentos de Odoo mediante extractos indexados, con timeout al intentar abrirlos. Se reutiliza la investigación sectorial previa. No se operaron licencias privadas ni se midió rendimiento competitivo. La inspección del repositorio fue estática sobre `claude/v1-implementacion`, HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a` **más cambios locales extensos**, que se preservaron. Ninguna recomendación acredita funcionamiento actual ni demanda comercial validada.

Actualización posterior del dueño: las ideas recibieron una valoración favorable y se añadió explícitamente **entrada por documentos, imágenes y demás archivos compatibles**. Se incorporó a los contratos/prompts de Claude. La [nota de ampliación](06-archivos-y-mejoras-con-sentido.md) analiza tres mejoras conectadas —fuentes de obra, contradicciones localizadas y señalar correcciones— con cinco páginas oficiales adicionales. Estas extensiones no convierten toda la cartera anterior en requisitos automáticos del lanzamiento.

## La decisión gerencial

DEKOPEN ya tiene una base técnica extensa. Añadir más entradas al menú antes de unir bien sus recorridos podría aumentar su complejidad. El problema descrito por el dueño —funciones mezcladas, aperturas que fallan, controles ambiguos y asistente que añade trabajo— requiere primero una experiencia confiable.

Propondría organizar la innovación en tres resultados:

| Resultado | Lo que compra el taller | Diferencia que debemos demostrar |
|---|---|---|
| Cotizar con certeza | Preparar una propuesta que entiende y puede defender. | Datos trazables, configuración válida, alcance explícito y revisión de pendientes antes de emitir. |
| Proteger el margen | Saber qué cambios o decisiones le cuestan dinero. | Impacto de cambios, costos completos, alternativas comparables y contraste con el costo real. |
| Coordinar la obra | Hacer llegar a cada persona la versión y el siguiente paso correctos. | Medición, compra, producción, instalación y postventa vinculadas a los mismos objetos. |

Es una propuesta de posicionamiento. No demuestra exclusividad frente a Logikal, Klaes, FeneVision o PrefSuite, cuyas capacidades industriales ya son amplias.

## Seis oportunidades prioritarias

| Orden recomendado | Mejora | Ejemplo de comportamiento | Naturaleza |
|---|---|---|---|
| 1 | Revisión antes de cotizar y fabricar | «Falta confirmar el vano de V3; el precio de V5 no está vigente. Abrir lo que bloquea esta etapa». | Integrar validaciones que ya existen; base manual. |
| 2 | Catálogo que avisa qué cambia | Una actualización de proveedor identifica borradores afectados y permite recalcularlos; lo emitido conserva su versión. | Extender autoridad/versionado existente; gran dependencia de datos. |
| 3 | Alternativas que ayudan a vender | Comparar la misma obra con dos soluciones válidas, explicando diferencias verificadas de configuración, precio y prestaciones. | Refinar alternativas ya existentes; base manual. |
| 4 | Impacto completo de un cambio | Antes de cambiar vidrio o medida, ver precio/BOM, compras o producción afectada y aprobaciones que deben renovarse. | Unir diff, revisiones y compromisos existentes. |
| 5 | Primera cotización con datos del taller | Importar una planilla con vista previa, resolver duplicados y usar una serie revisada y valores propios. | Mejorar adopción, sin depender de IA. |
| 6 | Margen explicado por causa | Comparar lo cotizado con consumos y costos reales revisados, localizar diferencias y proponer una política futura. | Refinar analítica existente; datos incompletos siguen incompletos. |

Los seis se desarrollan en [la recomendación detallada](04-recomendacion.md). Este orden es un juicio de producto, no una medición de retorno ni una estimación de esfuerzo del equipo. No se añaden automáticamente al compromiso de lanzamiento: primero separar lo ya exigido, lo que solo necesita integración y la ampliación opcional.

## Qué investigué y qué queda por validar

- [Fuentes y lecciones](01-fuentes.md): veinte fuentes, hecho observado, aplicación propuesta y límites.
- [Base actual contrastada](02-base-actual.md): capacidades encontradas en código y mejora incremental; evita proponer módulos duplicados.
- [Cartera de oportunidades](03-oportunidades.md): veinticuatro mejoras evaluadas y seis apuestas más abiertas.
- [Seis prioridades](04-recomendacion.md): recorrido, datos, restricciones y condición observable de éxito.
- [Experimentos, planes y secuencia](05-validacion-y-negocio.md): cómo elegir con evidencia, medir valor, proteger el lanzamiento y cobrar por valor adicional real.
- [Archivos y tres mejoras con sentido](06-archivos-y-mejoras-con-sentido.md): requisito de adjuntos integrado en el encargo, base técnica comprobada y refinamientos recomendados.

## Qué conservaría y qué cambiaría

Conservaría Mesa + Estudio, la base manual completa, el popup global opcional, MiMo común y los niveles de autonomía. La IA debe trabajar sobre las mismas operaciones y fuentes que el usuario. El personaje y el pulido visual tienen valor en claridad y personalidad; no sustituyen una cotización correcta o la continuidad del trabajo.

Cambiaría la manera de presentar capacidades. En vez de «tienes corte, QR, IA y analítica», mostraría recorridos concretos: «revisa lo que impide emitir», «entiende el impacto del cambio», «prepara la compra correcta» o «encuentra la causa de la pérdida». La pantalla se organiza alrededor de esa tarea y del objeto actual.

Evitaría por ahora un marketplace abierto, predicciones sin datos, colaboración CAD simultánea general y una nueva aplicación móvil nativa. Son apuestas estudiables; no son condiciones para demostrar el valor inicial. La integración final de Railway, Supabase y pagos mantiene el alcance aclarado en el [encargo vigente](../2026-10-18-direccion-final/prompt-maestro.md).

La cartera original no cambia por sí sola el encargo de desarrollo. La adición explícita de adjuntos sí está integrada en sus contratos, prompts y aceptación; las otras extensiones conservan su condición de recomendaciones.
