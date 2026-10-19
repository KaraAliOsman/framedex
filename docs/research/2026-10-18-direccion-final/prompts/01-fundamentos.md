# 01 — Fundamentos de producto y diseño

Desarrolla la base compartida del encargo de [dirección final](../direccion-final.md). Sigue el [prompt maestro](../prompt-maestro.md). Esta etapa es implementación, sin campaña de pruebas ni aprobación intermedia.

## Construir

1. Inspecciona rama, HEAD y diff; registra lo preexistente. No reemplaces el árbol de trabajo de Claude. Usa las rutas de la wiki para localizar implementaciones y dependencias, sin cargar todos los PRD.
2. Reconcilia `docs/PRODUCT.md` y `docs/design/CONSTITUCION.md` con las decisiones del dueño: base manual completa; Mesa + Estudio; IA opcional en popup; no IA central por defecto; catálogo real y DEMO separado. La Constitución §5.4/§5.11 y la regla de demo inicial requieren revisión explícita. Revisa también cualquier regla de preview universal que contradiga Omitir todo para cambios reversibles autorizados. Conserva validaciones, accesibilidad, número único, inmutabilidad y clic humano externo.
3. Usa [producto y dos vistas](../01-producto-y-dos-vistas.md), [diseño y operación](../02-diseno-y-referencias.md) y [copiloto/planes](../03-copiloto-y-planes.md) como contratos coordinados. Incorpora [créditos/límites](../04-planes-creditos-y-limites.md), [referencias profesionales](../05-referencias-profesionales.md) y [personaje Grok Bot](../06-grok-bot-personaje-y-movimiento.md). No agregues una nueva decisión de layout que vuelva a encerrar la IA en el editor. Reconcilia también la figura de placa facial y el tope de animaciones: las transiciones breves de controles no limitan los ciclos expresivos del personaje. Todos los planes IA usan MiMo hasta cambio expreso del dueño, sin fallback automático; las diferencias principales son de consumo.
4. Refina los tokens y primitivas existentes: superficies con función, tinta/contraste, bordes, estados de foco/error/selección, acción primaria/secundaria/destructiva, densidad por tarea y formatos exactos. Conserva identidad útil y renderer técnico. Los mocks previos no fijan píxeles aprobados. El contrato visual tiene criterios concretos para decidir; no hagas un tema paralelo.
5. Define en el código compartido los límites entre preferencia de vista, entidad/selección, borrador y revisión; estado de apertura del popup; hilo activo y destino de job. Reutiliza controllers/hooks y almacenamiento existentes; no crees otro almacén global con copias de todo el proyecto.
6. Deja jerarquía global coherente: navegación habitual por rol, nombre de obra, búsqueda, avisos, usuario/empresa. Para planes sin IA el shell conserva su utilidad y no muestra controles que parezcan acciones disponibles pero fallen por falta de modelo. No rehagas cobros aquí.
7. Actualiza el registro de implementación con mapa de archivos y decisiones concretas. Si un camino antiguo se sustituye, conserva su enlace con redirección o compatibilidad y retira la implementación duplicada cuando el reemplazo exista.

## Resultado que debe existir al continuar

El resto de etapas puede consumir primitivas, navegación y contratos coherentes. Producto/Constitución ya no ordenan acoplar IA al inspector. No hay una biblioteca visual nueva sin consumidores reales: integra los fundamentos en shell y componentes que efectivamente usarán 02–06.

Continúa directamente con 02. Las pruebas formales y la revisión de accesibilidad/anchos se ejecutan en 07; corrige bloqueos de compilación cuando surjan.
