# DEKOPEN — Constitución de experiencia v1

**Vigente desde 17-10-2026.** La dirección más reciente del dueño sustituye las
restricciones visuales anteriores. La aceptación histórica no acredita esta v1.
[Investigación y alcance](../ux/2026-10-17/README.md).

## 1. Resultado antes que interfaz

Un profesional debe reconocer sus ventanas, empezar sin configurar la empresa y
obtener una propuesta excelente sin transcribir lo que el sistema ya conoce.
La IA es la capacidad central: hace el trabajo completo solicitado, presenta una
muestra útil y deja corregir/deshacer. La interfaz manual debe ser igual de clara.

El dibujo y el trabajo del usuario mandan sobre la organización del backend.
Cada pantalla tiene una acción principal. Los detalles aparecen cuando ayudan a
una decisión. Quitar ruido no significa quitar capacidades profesionales.

## 2. Una dirección visual

Un único tema claro: mesa luminosa, papel blanco, tinta azul profunda y azul de
acción. Acentos cálidos discretos acompañan el trabajo del usuario. Esta segunda
dirección sustituye el verde anterior, rechazado por el dueño el 17-10-2026;
[criterio y encargos](../ux/2026-10-17/11-reconstruccion.md). El taller cambia
densidad y contraste, no cambia de tema.
Materiales y acabados físicos tienen sus colores propios, independientes del cromo.

IBM Plex Sans para leer; IBM Plex Mono para medidas, códigos y columnas numéricas.
Cuerpo 15/23 px en oficina, 16/24 en taller; títulos 28/34 y 18/24. Etiquetas en
frase normal, sin gritar con mayúsculas. Información técnica secundaria ≥12 px.
Controles habituales 40 px; táctiles ≥44 px. Radios 8 px en controles y 16 px en
paneles/diálogos. Geometría, dibujos y papel conservan esquinas reales.

Los roles en `frontend/src/styles/tokens.css` son la fuente ejecutable del sistema.
Espaciado base 4 px con ajustes ópticos deliberados. Sombra solo para separar capas.
No añadir adornos, tarjetas anidadas, métricas vacías o color por módulo.

Movimiento breve y con propósito: respuesta al tocar, continuidad al abrir, progreso
real al trabajar. Nunca bloquear una acción repetida con una animación. Respetar
movimiento reducido, foco visible, teclado y AA. Diseñar a 1440×900, comprobar
1280×800, 1024×768 y recorridos móviles a 390×844 en el cierre.

## 3. Anatomía del trabajo

- Navegación por relevancia al rol: Hoy, Obras, Asistente y trabajo operativo.
  Herramientas menos frecuentes en Más herramientas y búsqueda global.
- Obra: nombre/estado y ventanas primero; datos comerciales, actividad y técnica a
  demanda. Se puede empezar sin cliente. Antes de emitir, completar lo necesario.
- Biblioteca: elegir visualmente, heredar serie/vidrio/acabado de la obra, conservar
  decisiones compatibles. Medidas y cantidad claras, sin preguntas repetidas.
- Editor: lienzo protagonista, cotas editables, aperturas visibles, selección ligera,
  propiedades habituales primero. Perfiles, refuerzos y trazas bajo detalle técnico.
- IA: una sola entrada contextual. Preguntar o encargar se resuelve con la misma
  conversación. Resultado y muestra primero; consultas/trazas técnicas plegadas.
- Catálogo: arrastrar PDF, preparar automáticamente, revisar dudas sobre su fuente,
  activar capacidades por alcance. No prometer autoridad industrial sin evidencia.
- Documentos: presentación comercial legible y dibujos grandes; taller por tarea y
  pieza, con etiquetas y leyendas que no se superponen. Visor integrado.
- Hoy y producción: agrupar por causa/obra/lote; mostrar la siguiente acción útil.
  Compras/stock explican variante, unidad y faltante sin contratos internos.

## 4. IA capaz, límites comprensibles

El usuario puede delegar una tarea completa, con elecciones reversibles basadas en
el contexto y defaults visibles. Para un cambio simple basta aplicar y Deshacer;
para un lote o nueva presentación, mostrar muestra, alcance y resultado antes del
clic. No solicitar permiso otra vez para decisiones ya delegadas.

La IA puede preparar diseños, obras, textos, preferencias de presentación de la
página/portal y PDF mediante operaciones tipadas, autorizadas y versionadas.
Nunca ejecutar código arbitrario ni modificar permisos mediante una instrucción.
El dueño conserva proveedor, presupuesto, roles y control de capacidades. Ninguna
configuración visible en el navegador sustituye la autorización del servidor.

Enviar a terceros, comprar/pagar, emitir y liberar producción requieren una acción
humana explícita. Lo emitido es inmutable: se crea revisión. La IA no fabrica
precios, cálculos, secciones ni autoridad técnica; usa motor y catálogo aprobado.
Siempre distinguir preparado, aplicado, emitido y enviado.

## 5. Lenguaje y verdad

Español claro y profesional. Hablar de ventanas, hojas, marcos, termopanel, obras,
corte y montaje. Mantener códigos físicos y trazabilidad sin convertirlos en una
clase de backend. Una ayuda breve solo cuando resuelve una duda real.

Un estado vacío explica cómo empezar. Error: qué falló y acción para recuperarse.
Sin permiso: quién puede resolverlo. Un dato ausente no se sustituye por cero; su
causa aparece en el momento que afecta a la tarea, sin repetir avisos por pantalla.

Motor como única autoridad de números. Decimal en mm y dinero, RLS/org, revisiones
inmutables e idempotencia se conservan. Números alineados y tabulares: mm con espacio
fino, CLP con punto de miles; unidades explícitas y fuente a demanda.

## 6. Calidad e integración

Trabajar por recorridos completos, sin paneles de demostración ni acciones vacías.
Aplicar criterio de `apple-design` y `emil-design-eng` a interacción y detalle,
sin copiar otra marca. Revisiones de diseño en tabla Antes/Después/Por qué.

Inspección visual durante la construcción para decidir el diseño. Campaña formal
de pruebas, regresión y corrección general **al final**, según instrucción del
dueño. No debilitar CI, cálculos probados o protecciones para aprobar el cierre.
Registrar implementación real y pendientes; no declarar definitiva una entrega
parcial. Los objetivos se evalúan con tareas completas, no solo capturas bonitas.
