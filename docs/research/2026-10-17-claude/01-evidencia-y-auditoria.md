# Evidencia y auditoría del producto restaurado

## Cómo leer este diagnóstico

**C** = código comprobado en `6f78e3299d93816991fb7c2fe2a2044458fc5e7a`; **H** = captura/PDF anterior revisado; **D** = declaración del dueño; **P** = propuesta de diseño. Una captura anterior no demuestra el comportamiento actual de una API. Un texto en el código no acredita que todo el recorrido funcione en vivo.

La auditoría visual nueva quedó limitada por la conexión del navegador. Se intentó el acceso admitido por la herramienta después de la activación del dueño; no se consiguió una sesión. No se cambió el stack ni se utilizaron accesos alternativos para eludir esa configuración.

## Mapa de evidencia local

| ID | Fuente | Alcance y cautela |
|---|---|---|
| C01 | `frontend/src/app/navigation.ts:12–65` | La navegación declara que refleja capacidades de lectura de las API; agrupa ventas, ingeniería, operación, asistente y analítica |
| C02 | `frontend/src/styles/tokens.css`; `styles/base.css:36–45`; `ui/Controls.css:74–77` | Densidad compacta y foco implementado. No corresponde afirmar que «no hay foco» |
| C03 | `features/projects/FinishSelector.tsx:93–194` | Interior/exterior en el flujo normal, precio diferencial y procedencia |
| C04 | `features/canvas/finishMaterials3d.ts:11–51` | Carga de texturas, sRGB, repetición y materiales físicos existentes |
| C05 | `features/canvas/Product3DScene.ts:422–474` | Extrusión de sección declarada; encuentro de extremos rectos; caja aproximada si falta sección |
| C06 | `features/canvas/SectionPreviewSvg.tsx:45–88` | Polígono declarado o rectángulo aproximado explícito |
| C07 | `features/projects/ProjectPages.tsx:70–82`; `ProjectQuotationPanel.tsx` | Metadatos del proyecto y gran concentración de decisiones comerciales/técnicas |
| C08 | `features/pricing/ProjectPrices.tsx:1132–1185,1544`; `PricingPage.tsx:289–329` | Superficie global de solicitudes/aprobaciones; lenguaje de autoridades e historial |
| C09 | `backend/documents/quotation.py:273,278,387–391` | Folio técnico, huella en pie, aceptación/firma incondicional y QR condicionado a URL |
| C10 | `backend/documents/preferences.py:16–24`; `features/projects/DocumentSettings.tsx:335–347` | Preferencias existentes; caducidad de vista privada expuesta; sin familias de plantilla en esos defaults |
| C11 | `backend/projects/company_views.py:158–164,268–277`; `supabase/migrations/20270124000001_company_administration.sql:162–166` | Numeración de consulta existente: P, OC, RT, REC. No acredita edición de numeración comercial de cotizaciones |
| C12 | `features/catalogs/CatalogImportsPanel.tsx`; `backend/ingest/catalog_service.py:29,238–305` | Importación estructurada/IA, revisión y publicación; límite de archivo de 15 MB |
| C13 | `backend/ingest/catalog_ai.py:53–65,75–84` | Comprobación literal de valores de alta confianza; límite de texto con división manual solicitada |
| C14 | `backend/ai_gateway/multimodal.py:9–42`; `providers.py:381–402` | Soporte real de PDF/imagen; máximo 20 páginas y 100.000 caracteres en ese helper; página con texto omite imagen |
| C15 | `backend/ai_gateway/prompts/agent-v2.md:43`; `agent.py:59–60,173–174,293–363` | Propuestas, simulación y enlaces de preparación; varios flujos no pueden ejecutar mutaciones directamente |
| C16 | `features/assistant/AssistantWorkspacePage.tsx:53–81`; `Orb.tsx:5–39,79–120` | Selección de flujo/superficie; mascota con estados vinculados a trabajos |
| C17 | `features/production/ProductionPage.tsx:1243,1285,1687,1846,2050–2068` | Packs de corte/producción y optimización existentes, dentro de producción |
| C18 | `backend/production/cnc.py:901–907,943–965` | Revisión requerida; salida `NEUTRAL_INTERCHANGE` del postprocesador neutro |
| C19 | `features/onboarding/CompanySetup.tsx:19–85`; `OnboardingPage.tsx:234–437` | Preparación por pasos; serie, cliente, obra y primera posición |
| C20 | `features/purchasing/PurchaseNeeds.tsx:154–175`; `InventoryPage.tsx`; `field/FieldPage.tsx`; `portal/PortalQuotePage.tsx` | Capacidades y vocabulario comprobados, sin nueva ejecución completa |
| C21 | `features/commands/registry.ts:15–65`; `canvas/ProductFrontSvg.tsx:39–46` | Registro contextual de comandos y dibujo reutilizado: bases útiles que conviene extender |
| C22 | `frontend/src/ui/Signature.tsx:5–47`; `app/railIcons.tsx:2–39` | Cargador de cota y familia actual de iconos |
| C23 | `frontend/src/auth/LoginPage.tsx`; `auth/MfaPage.tsx`; `app/RouteErrorBoundary.tsx`; `features/landing/LandingPage.tsx`; `features/notifications/MailPanels.tsx` | Acceso por enlace, MFA, recuperación de ruta, portada y estados de correo; inspección de fuente, sin nueva ejecución |
| C24 | `backend/ai_gateway/agent.py:110–139` | Límites de objetivo/respuesta, pasos/consultas/rondas y lotes de hasta 15 posiciones en esas rutas; no equivale a un límite universal del producto |

Los prefijos `features/`, `styles/` y `ui/` en esta tabla pertenecen a `frontend/src/`. Las líneas son orientativas del ref auditado; usar también los nombres de símbolo al continuar en otro ref.

**Capturas históricas seleccionadas:** `docs/redesign/captures/aceptacion-final/ux/` contiene precios comerciales, proyecto, asistente, emisión, catálogo y `stack-limpio/03-editor.png`; la revisión del importador está en `catalogo/pdf/01-fuente-revision.png`. Consultar el [mapa de capturas](../../redesign/captures/README.md) para procedencia.

**Muestras de una auditoría anterior:** `.run/ux-audit-2026-10-17/` contiene D01–D14 y renderizados de PDF. La auditoría anterior no fijó el SHA servido: sirven para estudiar fricción y composición, no para certificar el build actual. No se copian al repositorio las capturas de YouTube con contenido lateral ajeno al estudio.

## Diagnóstico transversal

La arquitectura tiene capacidad técnica y controles valiosos. La interfaz los expone como una sucesión de requisitos, autoridades, revisiones y paneles. El usuario necesita descubrir la estructura interna antes de realizar un trabajo sencillo. La IA reproduce parte de esa estructura al diagnosticar qué falta y enviar a otra superficie.

La solución requiere tres cambios conjuntos: **recorridos de trabajo**, **presentación visual** y **capacidad de ejecución**. Si solo cambia la apariencia, seguirán las mismas decisiones innecesarias. Si solo se agregan herramientas de IA, el usuario seguirá sin entender qué cambió ni qué resultado está aprobando.

## Antes / Después / Por qué

«Después» describe el diseño propuesto, no una modificación aplicada. Prioridad A = recorrido principal; B = profundidad profesional; C = especialización o pulido posterior dentro del cierre.

| Área y prioridad | Antes: evidencia | Después: intervención propuesta | Por qué y señal de calidad |
|---|---|---|---|
| Navegación · A | C01: destinos separados por dominios técnicos | Cuatro áreas habituales y accesos según rol; precios dentro del proyecto | El usuario encuentra su trabajo sin elegir un módulo del backend |
| Inicio · A | H D13: lista repetida de OT y bloqueos | Reanudar trabajos, nueva cotización y pocas decisiones agrupadas | El inicio orienta a actuar; no funciona como consola de incidencias |
| Nombre del trabajo · A | C07/H: código P domina varios lugares | Nombre de obra/cliente primero; código en detalle | Se reconoce una obra sin memorizar identificadores |
| Nueva cotización · A | C19: varios pasos previos al primer dibujo | Lienzo y tipologías desde el inicio; cliente al momento necesario | La persona obtiene una primera ventana antes de completar administración |
| Datos de cliente · A | C19: cliente dentro de una secuencia obligatoria | Buscar/crear en contexto, con mínimo requerido por etapa | No repetir identidad, contacto y dirección en varias pantallas |
| Proyecto · A | H: fases, pestañas y filtros desplazan ventanas | Colección de ventanas como contenido principal; progreso resumido | El trabajo actual ocupa la primera vista |
| Duplicación · A | C21 aporta comandos compartidos | Duplicar ventana o aplicar vidrio/acabado a una selección con resultado visible | Las obras repetitivas no se reconstruyen pieza por pieza |
| Inspector · A | C07/H: decisiones técnicas y derivadas mezcladas | Solo propiedades del objeto seleccionado; especialidades en detalle | El inspector explica qué se está editando |
| Acciones · A | H/D: botones y enlaces poco distinguibles | Primario sólido, secundario delineado, enlace para navegar | Una persona puede anticipar el efecto antes de pulsar |
| Tipografía · A | C02: cuerpo 13, etiquetas 11, datos densos | Lectura habitual más cómoda; densidad elegida por tarea | La precisión no obliga a leer todo como una tabla técnica |
| Tema · A | D: ambos temas rechazados | Una dirección clara definitiva propuesta; sin selector visible de tema | El esfuerzo se concentra en una composición coherente |
| Iconos · A | C22: metáforas propias poco familiares en ciertas áreas | Familia genérica consistente; símbolos del oficio donde añaden información | Reconocimiento más rápido; texto en acciones importantes |
| Selección del lienzo · A | H editor: fuerte contorno turquesa y cotas reiteradas | Selección localizada, cotas relevantes y manijas claras | La selección no tapa el producto |
| Acabados · A | C03: interior y exterior permanentes | Un selector «Acabado» con muestra grande; bicolor avanzado | Resuelve el caso habitual con una decisión |
| Texturas · A | C04: soporte existe; D: no se perciben bien | Mapas preparados, orientación y escala por miembro; misma muestra en PDF | Nogal y blanco se distinguen por material, no solo por texto |
| Uniones · A | C05: extremos rectos, sin inglete visual resuelto ahí | Encuentros según tipo de unión documentado y detalle de presentación | No dibujar todas las esquinas como el mismo marco genérico |
| Perfiles · A | C06/H: muchos rectángulos de reserva | Ilustración reconocible de familia y foto opcional, separadas de sección exacta | Se puede distinguir marco, hoja y junquillo sin inventar geometría |
| 3D · B | C04–C05: base real reutilizable | Vista de inspección/material, cámara estable y fondos sobrios | El 3D ayuda a elegir y explicar, sin sustituir cálculo |
| Materiales · A | H D07: modal estrecho dominado por SKU | Vista amplia vinculada al dibujo, agrupada por perfiles/vidrios/herrajes | Saber qué corresponde a cada ventana sin cruzar listas a mano |
| Precio · A | C08: «solicitudes y decisiones», autoridades | Precio en proyecto; detalle de costo/margen al solicitarlo | Cotizar no requiere entrar al proceso de aprobación |
| Falta de costo · A | C08: mensaje general sobre autoridades | Material identificado, motivo y acción concreta para el rol | La corrección ocurre donde se ve el problema |
| Trazas · B | H: huellas/procedencia/«Sin dato» muy frecuentes | Resumen de faltantes relevantes y traza a un clic | Se mantiene confianza sin una pared de advertencias |
| Cotizaciones emitidas · A | C20: lista de revisiones vigentes por proyecto | Vista guardada comprensible, con borrador/enviada/aceptada y cliente | El nombre corresponde al contenido que espera el usuario |
| Emisión · A | H: checklist y formulario, PDF aún vacío | Documento real desde temprano; resumen compacto de faltantes | La persona revisa lo que va a entregar |
| PDF comercial · A | H pdf-casa: portada larga y tono técnico | Tres composiciones editoriales con dibujo, alcance y total claros | El cliente reconoce una propuesta profesional |
| Firma · A | C09: bloque incondicional | Botón/política «Solicitar aceptación»; bloque según configuración | Una oferta preliminar no parece contrato definitivo |
| Folio · A | C09/C11: folio COT-P-… y consulta técnica | N.º 1 por empresa, prefijo/inicio editables y revisión separada | Numeración humana sin perder identidad técnica |
| Plantillas · A | C10: papel/acento y condiciones | Familias con composición, campos y estilo editables | Cambiar color no equivale a tener diseños diferentes |
| Edición final · A | C09–C10: renderizador, no editor completo acreditado | Original estructurado editable en borrador y revisión tras emisión | Se evita salir a otras aplicaciones para cambiar contenido |
| Configuración PDF · B | C10: vigencia técnica de preview expuesta | Vigencia comercial visible; caducidad técnica gestionada por el sistema | Distinguir «vale 15 días» de «el enlace privado vence» |
| IA de entrada · A | C16/H: flujo/superficie, robot grande, inspector vacío | Compositor contextual con pocas acciones útiles; resultado junto al archivo | No pedir al usuario que organice el trabajo del agente |
| IA ejecutora · A | C15: varias preparaciones son navegación | Herramientas de borrador y edición reales, compartidas con la UI | «Hecho» significa que el objeto existe y se puede abrir |
| IA y contexto · A | C15–C16: selectores/presets de diagnóstico | Contexto del proyecto, selección y documento activo, visible y modificable | No volver a explicar dónde debe trabajar |
| IA y obras grandes · B | C24: lotes y rondas acotados | Dividir internamente el trabajo, reanudar y revisar el conjunto | No obligar a repetir la petición por cada lote ni ampliar límites a ciegas |
| Confirmaciones IA · A | C15: humana en la aplicación del cambio | Permiso para borradores reversibles; revisión agrupada para compromisos | La automatización ahorra trabajo sin borrar la decisión humana |
| Mascota IA · A | C16/C22: esfera/orbita y figura actual | Figura circular 2D original, viva por eventos reales | Personalidad sobria; menos ruido y mejor reconocimiento |
| Carga · B | C22: cota que recorre avance indeterminado | Estado local estable y progreso real cuando exista | La animación no simula un porcentaje de trabajo |
| Importar catálogo · A | C12/H: plantilla manual y revisión tabular extensa | Un PDF como entrada principal, progreso y excepciones | La estructura interna no se convierte en formulario obligatorio |
| Catálogo largo · A | C13–C14: límites y división manual | Partición interna, reanudación y resumen de cobertura | El usuario no necesita editar el PDF para que el sistema lo entienda |
| Página mixta · A | C14: si hay texto no se adjunta imagen | Texto y región visual cuando tabla/dibujo lo requieren | Un pie de página con texto no debe ocultar un plano escaneado |
| Fusión de catálogos · B | C12–C14 no prueban el recorrido completo pedido | Añadir PDF a la línea, comparar conflictos y publicar versión | Ampliar no significa duplicar o pisar datos |
| Corte · A | C17/H: se descubre dentro de producción | «Orden de corte» desde proyecto, ventana y materiales | El nombre de la acción coincide con el resultado buscado |
| Optimización · B | C17: parámetros y agrupaciones | Preferencias habituales heredadas; ajustes de taller expandibles | No preguntar lo mismo para cada orden |
| Compra · B | C20/H D11: varios números muy separados por material | Tabla por proveedor, falta real, cantidad propuesta e importe | Leer y revisar lotes sin recorrer bloques largos |
| Inventario · B | C20/H D12: códigos y métricas compactas | Nombre/acabado/longitud y disponibilidad; historial en detalle | No reducir stock a un código ni confundir reserva con disponible |
| Taller · B | H D10: tarjetas minúsculas con códigos de OT | Obra, dibujo, cantidad, estación y siguiente acción | La información responde a «qué hago ahora» |
| Operario · B | C20: estación especializada existente | Pieza actual, dibujo/orientación y controles de uso físico | No trasladar el escritorio completo a una tablet |
| CNC · B | C18: intercambio neutro comprobado | Etiquetado honesto, adaptador por máquina y homologación | No confundir exportar un archivo con integración probada |
| Terreno · B | C20/H D14: vacío y filtros | Agenda personal, obra, lista de carga y sincronización explícita | Se mantiene útil en móvil y al perder conexión |
| Portal · B | C20: decisión, documentos y pagos en superficie amplia | Presentación clara; firma/pago solo cuando el negocio los habilite | El cliente revisa primero qué compra |
| Analítica · C | Código existente; sin inspección visual nueva | Priorizar preguntas de negocio y contexto; entrar desde resumen | No convertir el inicio en un mural de indicadores |
| Notificaciones · B | H D13: gran contador de fixture | Agrupar por obra y decisión; separar aviso de tarea ejecutable | El tamaño del fixture no debe definir la experiencia de alertas |
| Configuración · B | C19/C10: múltiples detalles tempranos | Preferencias de empresa por tarea y especialidades a demanda | Configurar una vez debe reducir futuras preguntas |
| Acceso/recuperación · B | C23: enlace de acceso, MFA y recovery existentes | Misma claridad visual y destino recuperado; estados de enlace enviado/caducado comprensibles | Mejorar presentación sin debilitar controles de acceso |
| Portada pública · C | C23: presentación del producto y asistente | Mostrar trabajos/resultados reales y una acción principal | No prometer capacidades no entregadas ni abrir trabajo nuevo de planes |
| Correo · B | C23: preview, confirmación y entrega incierta | Destinatario/documento/estado juntos; confirmar envío concreto | No tratar falta de respuesta como permiso para duplicar un correo |

## Lo que no debe perderse

- Motor determinista y trazabilidad de cifras; aislamiento por organización; revisiones emitidas inmutables.
- Comandos compartidos del editor y reutilización del dibujo entre superficies.
- Distinción entre sección real y representación aproximada.
- Infraestructura existente de materiales, optimización, corte, documentos, portal y trabajos de IA.
- Foco visible, estados accesibles y soporte de movimiento reducido ya presentes: mejorarlos al cambiar componentes, no borrarlos.

## Interpretaciones que esta auditoría descarta

El D08 anterior muestra un rol sin permiso de importar; no demuestra que el importador falle. Los cientos de avisos/OT y nombres repetidos de inventario pertenecen a fixtures; no son mediciones de un negocio real. La importación ya tiene IA multimodal y verificación de citas; no corresponde proponer «agregar OCR desde cero». Las texturas 3D también tienen implementación existente. El problema de estilo es una valoración del dueño apoyada por análisis de composición; no se presenta como una puntuación objetiva de laboratorio.

## Cobertura y lo que queda por observar

Se examinó código y/o evidencia histórica de las superficies principales de venta, diseño, catálogo, IA, documento, materiales y taller. No se certificaron en vivo autenticación, todas las variantes móviles, accesibilidad completa, casos vacíos de cada rol, compras reales, aceptación jurídica, rendimiento ni conexión CNC. El [registro de pendientes](12-incidencias-y-pendientes.md) y la campaña final indican cómo cerrar esas brechas sin fingir que ya están resueltas.
