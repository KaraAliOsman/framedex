# P16 · catálogo técnico y procedencia

Verificación local del 10-10-2026, rama `codex/P16-catalogo-tecnico`, sobre
integración `0ca7ec11`. El catálogo muestra la autoridad de la serie, las fuentes
de cada registro y los requisitos que afectan fabricación. Una revisión humana
se distingue de una verificación documental; DEMO nunca cambia de naturaleza.

## Autoridad y alcance

`catalog_authority_gate` comparte revisión, fabricación y proceso entre catálogo
y emisión. El catálogo declara cobertura de la serie; cada posición emitida
declara los SKU consumidos. Las pruebas de paridad comparan el mismo conjunto de
artículos en DEMO_60 y en una copia incompleta. Una posición no depende de artículos
que no usa. La liberación lee la decisión y el proceso sellados; las modificaciones
posteriores del catálogo no reescriben revisiones emitidas.

La escalera conserva el contrato previo `WHITE_FIXED_CATALOG`: la capacidad de
cotizar no acredita todos los requisitos de fabricación, estaciones ni CNC.
Comprar, inspeccionar y las políticas declaradas siguen siendo requisitos
adicionales. Se mantienen los goldens y los contratos históricos de P14.

Una sección nueva exige contorno válido, profundidad exacta según orientación y
origen local coherente. Una sección histórica sigue siendo legible, pero la
ausencia de interpretación explícita impide verificarla. Una sección ausente
aparece como Sin dato. La miniatura ajusta la vista al contenedor y declara que
no tiene una escala física 1:1.

## Recorridos y evidencia

El PDF sintético de tres páginas pasó por MiMo real, revisión y corrección de
colores y sección desde el original. La regla de corte se desmarcó. El diff se
comprobó antes del clic de publicación. La ficha mostró REVIEWED y sección válida;
el enlace al campo Sección trasladó el foco al destino. Deshacer conservó las
seis etapas de la auditoría y los candidatos revisados.

- [Recorrido PDF y auditoría](captures/catalogo-tecnico/recorrido-importacion.json).
- [Matriz sistema/ficha](captures/catalogo-tecnico/recorrido-matriz.json):
  1440×900, 1280×800 y 1024×768, claro/oscuro, siete pestañas, sin desbordes ni
  errores de JavaScript.
- [Cinco estados](captures/catalogo-tecnico/estados.json): vacío, carga, error y
  recuperación, costos sin permiso y bloqueo con destino; original HTTP 403 para
  estimador. Vacío/carga/error se provocan en el transporte de prueba, sin alterar
  la autoridad real persistida.
- [Recorrido final](captures/catalogo-tecnico/recorrido-final.json): costos DEMO
  del dueño, foco de las tres políticas ausentes y acción de revisión en ficha.
- [Capturas generales](captures/catalogo-tecnico/despues/report.json): ocho
  combinaciones de ancho/tema, incluidos 390 px, sin hallazgos finales.
- [Antes](captures/catalogo-tecnico/antes-sistema-1440-claro.png) y
  [después](captures/catalogo-tecnico/despues-sistema-1440-light.png).
- [Corrección de sección](captures/catalogo-tecnico/importacion-correccion-seccion-1440-light.png),
  [diff](captures/catalogo-tecnico/importacion-diff-1440-light.png) y
  [ficha](captures/catalogo-tecnico/importacion-ficha-fuente-1440-light.png).

Los archivos de prueba y sus datos son sintéticos, sin certificación. La ruta
multimodal reutiliza el transporte de IA3: los valores de una imagen sin literal
comprobable permanecen LOW/UNKNOWN y requieren contraste humano. Nunca adquieren
autoridad por la confianza declarada por el proveedor.
La [foto rasterizada](captures/catalogo-tecnico/recorrido-foto.json) produce un
candidato con MiMo real, desmarcado y sin publicar. El
[PDF original](captures/catalogo-tecnico/fixture-fuente.pdf) queda como evidencia
sintética reproducible; no contiene datos comerciales reales.

## Pase editorial: dos rondas

Primera ronda: se quitó el mapa redundante; se reemplazaron las cajas de sección
inferidas por geometría declarada o Sin dato; se separaron DEMO, declaración,
revisión humana y evidencia documental vigente. Se mantuvieron los siete grupos
técnicos y sus acciones reales.

Segunda ronda: se acotó la lista lateral y se eliminó la navegación duplicada en
la ficha de serie; los enlaces enfocan el artículo/campo o la autoridad de proceso
correspondiente; se corrigieron contraste oscuro y errores silenciosos de fuentes
y centros. Se eliminó el salto genérico que competía con el destino del bloqueo.
La carga usa la cota compartida y los errores ofrecen recuperación.
La cobertura de costos conserva DEMO y los hechos de sección son accesibles.
Colocación, manillas y refuerzo tienen destinos propios con revisión y fuente;
una política ausente ya no enlaza a una autoridad de proceso distinta.

| R | Estado | Evidencia |
|---|---|---|
| R1 | PASA | Medidas y contorno exactos en Mono; lexemas editables conservan precisión. |
| R2 | PASA | Tokens de radios; sección sobre hoja. |
| R3 | PASA | Reglas finas y divulgación de fuentes. |
| R4 | PASA | Naranja reservado a marca y revisión humana. |
| R5 | PASA | Teal funcional, ambos temas. |
| R6 | PASA | Roles, origen, orientación y etapas en español. |
| R7 | PASA | Ficha agrupada; series con scroll local acotado. |
| R8 | PASA | Cinco estados recorridos y recuperados. |
| R9 | PASA | Sección real sobre hoja; contexto sobre mesa. |
| R10 | PASA | Selección por borde y tinte. |
| R11 | PASA | Contorno y gramática heredados del dibujo real. |
| R12 | PASA | Foco de teclado y destino de enlace comprobados. |
| R13 | PASA | Tokens de movimiento, sin animación añadida. |
| R14 | PASA | Comparar y publicar como pasos sucesivos. |
| R15 | PASA | Fuentes junto a cada campo; ausencias UNKNOWN/Sin dato. |
| R16 | PASA | Guardas sin degradados, blur ni color de IA. |
| R17 | PASA | Matriz de tamaños y temas sin recortes de página. |
| R18 | PASA | Navegación/mapa duplicados eliminados; acciones y reintentos reales. |
| R19 | PASA | DemoBadge y sección F10 conservados. |
| R20 | PASA | PDF → fuente → corrección → diff → publicación → historial → deshacer. |

## Validación

Pruebas focalizadas: 237 unitarias de los contratos afectados, 43 integraciones
de regresión, siete integraciones nuevas, 20 pruebas frontend y 14 pruebas nuevas
de procedencia/geometría. La prueba pgTAP P16 pasa sus 16 aserciones, incluida
autocertificación y evidencia/auditoría inmutable.

Los cuatro gates locales pasan: 881 pruebas del motor (+2 xfail), 1.476 del backend y 967 del frontend, goldens byte a byte y build.
El gate de base de datos termina con `[PASS] database gate`: 1315 aserciones pgTAP, 493 integraciones, 19 E2E y diez verificaciones de upgrade PG16. El stack aislado termina detenido y el fixture persistente se conserva.
CI se registra cuando terminen los cuatro checks del PR.
El pgTAP aislado en una base limpia necesitó acceso de prueba a `extensions`
para el rol técnico. El permiso está dentro de la transacción que termina en
ROLLBACK; no cambia permisos de producción ni relaja aserciones.
La corrida siguiente pasó 1.315 pgTAP, 493 integraciones y 18 E2E. El recorrido
de serie esperaba la navegación previa; ahora abre la lista desde la ficha antes
de editar y conserva las aserciones de reapertura, relaciones y decimales.
La repetición final acredita ese recorrido actualizado.

La corrida previa pasó los 19 E2E y detectó que el contrato mínimo de autenticación del gate PG16 no contenía `raw_user_meta_data`. Se amplió esa tabla de compatibilidad con el campo real de Supabase; las migraciones de dominio y las aserciones permanecen intactas.

## Decisiones y límites

No se agrega un valor de fabricación por defecto. El costo permanece privado del
dueño; el original puede contener costos y solo lo abren revisores autorizados.
Cada valor técnico presente necesita evidencia vigente para la proyección VERIFIED.
Una corrección humana conserva su original y no se atribuye al fabricante.

No se certifica un fabricante, una norma ni una máquina con el fixture. Los datos
globales siguen bajo autoridad de plataforma; un tenant no puede revisarlos ni
publicar evidencia sobre datos de otra organización. Railway, Flow, SII y correo
conservan los adaptadores y estados existentes; este encargo no activa servicios.
