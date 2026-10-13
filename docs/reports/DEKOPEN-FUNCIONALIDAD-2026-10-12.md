---
type: synthesis
status: active
updated: 2026-10-12
volatility: high
verified_ref: 0a9f057ba5338bc6be39181b9ca001915b2f2a59
verification: inspección estática de código y contratos; evidencia funcional histórica de P20
---

# DEKOPEN v1 · Reporte integral de funcionalidad

**Fecha:** 12 de octubre de 2026, America/Santiago. **Repositorio:** [KaraAliOsman/framedex](https://github.com/KaraAliOsman/framedex). **Fuente examinada:** `0a9f057ba5338bc6be39181b9ca001915b2f2a59`, rama `codex/limpieza-repositorio`. El código de producto de esa revisión coincide con la integración v1 de `main`, `2db4e13171884b93a989e68508a55f5590f9b34d`, integrada mediante [PR #157](https://github.com/KaraAliOsman/framedex/pull/157). Los cambios posteriores examinados son de limpieza e instrucciones/documentación.

Este informe describe capacidades, permisos, entradas, resultados, dependencias y límites. Para elaborarlo no se ejecutaron pruebas funcionales, llamadas a IA, pagos, emisiones ni recorridos de navegador. No se reiniciaron servicios ni se modificaron las sesiones del dueño. Las cifras de aceptación se atribuyen a las corridas históricas identificadas; la lectura de código confirma estructura e implementación, sin demostrar disponibilidad actual de un servicio externo o comportamiento de una sesión abierta.

**Cómo leerlo:** primero el panorama y las matrices; después el módulo que interesa; al final los inventarios completos de operaciones, API, motor y declaraciones de datos. Los nombres técnicos de los anexos sirven para localizar implementación. El producto presenta etiquetas humanas y restricciones por rol.


<!-- REPORT_TOC_START -->
**Índice de lectura**

- [1. Alcance y significado de la evidencia](#capitulo-01)
- [2. Qué es DEKOPEN y qué conecta](#capitulo-02)
- [3. Panorama funcional por módulo](#capitulo-03)
- [4. Roles y límites de cada persona](#capitulo-04)
- [5. Navegación y superficies visibles](#capitulo-05)
- [6. Acceso, organización y seguridad](#capitulo-06)
- [7. Empresa, configuración y alta inicial](#capitulo-07)
- [8. Clientes y dossier comercial](#capitulo-08)
- [9. Proyectos, posiciones y revisión](#capitulo-09)
- [10. Modelo paramétrico y verdad numérica](#capitulo-10)
- [11. Editor, comandos e historial](#capitulo-11)
- [12. Geometría, contornos y conjuntos](#capitulo-12)
- [13. Catálogo técnico, importación y publicación](#capitulo-13)
- [14. Aperturas y composiciones físicas](#capitulo-14)
- [15. Vidrio, paneles y pedido al proveedor](#capitulo-15)
- [16. Herrajes, clases, manillas y mecanizados declarados](#capitulo-16)
- [17. Color, acabado y caras](#capitulo-17)
- [18. Accesorios, servicios y plantillas](#capitulo-18)
- [19. Vano, medición y fabricación](#capitulo-19)
- [20. Dibujo técnico 2D, DIN, planta y cotas](#capitulo-20)
- [21. Representación física 3D](#capitulo-21)
- [22. Inspector y condición de fabricación](#capitulo-22)
- [23. Térmica, informes y alcance OGUC](#capitulo-23)
- [24. Precio, costos, listas, monedas y aprobaciones](#capitulo-24)
- [25. Cotización guiada y emisión](#capitulo-25)
- [26. DOC-01, alternativas y otros artefactos](#capitulo-26)
- [27. Portal público y acuerdo del cliente](#capitulo-27)
- [28. Cobranza, pagos y recibos](#capitulo-28)
- [29. Factura, boleta, nota de crédito y SII](#capitulo-29)
- [30. Liberación y órdenes de trabajo](#capitulo-30)
- [31. Tablero de planta, estaciones y operario](#capitulo-31)
- [32. Optimización de barras y láminas](#capitulo-32)
- [33. Papel de corte, etiquetas, CSV y DXF](#capitulo-33)
- [34. Mecanizado y CNC](#capitulo-34)
- [35. Compras y proveedores](#capitulo-35)
- [36. Inventario, movimientos y retazos](#capitulo-36)
- [37. Embalaje, despacho, entrega e instalación](#capitulo-37)
- [38. Terreno, trabajo sin red y postventa](#capitulo-38)
- [39. Analítica, costos reales y explicación de desvíos](#capitulo-39)
- [40. Inteligencia artificial: capacidades y autoridad](#capitulo-40)
- [41. Transporte de IA, presupuesto y trazabilidad](#capitulo-41)
- [42. Asistente contextual, Orb y trabajos](#capitulo-42)
- [43. Hoy, campana, búsqueda y seguimiento](#capitulo-43)
- [44. Worker, jobs durables y automatizaciones internas](#capitulo-44)
- [45. Correo, identidad del remitente y recuperación](#capitulo-45)
- [46. Billetera, planes y comercio de la plataforma](#capitulo-46)
- [47. Presentación, accesibilidad y uso por dispositivo](#capitulo-47)
- [48. Arquitectura técnica y contrato API](#capitulo-48)
- [49. Persistencia, inmutabilidad y concurrencia](#capitulo-49)
- [50. Operación local, entornos y recuperación](#capitulo-50)
- [51. Matriz completa de activación externa](#capitulo-51)
- [52. Aceptación histórica y alcance de las verificaciones](#capitulo-52)
- [53. Límites concretos y consecuencias para el uso](#capitulo-53)
- [54. Recorridos para la revisión manual del dueño](#capitulo-54)
- [55. Lectura de estados, números y códigos](#capitulo-55)
- [56. Fuentes y método de trazabilidad](#capitulo-56)
- [57. Glosario funcional](#capitulo-57)
- [Anexo A. Las 55 operaciones compartidas](#anexo-a)
- [Anexo B. Contrato completo de las 334 operaciones HTTP](#anexo-b)
- [Anexo C. Los 55 módulos del motor](#anexo-c)
- [Anexo D. Enums del modelo físico](#anexo-d)
- [Anexo E. Rutas literales del frontend](#anexo-e)
- [Anexo F. Las 149 declaraciones de tablas encontradas](#anexo-f)
- [Anexo G. Cuerpos de solicitud y campos declarados](#anexo-g)
<!-- REPORT_TOC_END -->

<a id="capitulo-01"></a>

## 1. Alcance y significado de la evidencia

| Etiqueta | Qué acredita | Qué no acredita |
|---|---|---|
| Código / contrato actual | Funciones, rutas, estructuras, validaciones y condiciones presentes en el ref examinado | Que el stack abierto en el navegador use esas imágenes o que una conexión externa responda ahora |
| Aceptación histórica | Un recorrido o matriz documentados sobre sus propios refs, cuentas y datos | Una prueba nueva, cobertura universal o certificación de una fábrica |
| Sandbox / DEMO | Recorrido reproducible con transporte o datos de ensayo declarados | Dinero real, fichas de fabricante, impuestos válidos o fabricación industrial |
| Activación externa | Una interfaz construida que necesita dominio, credenciales, fuentes o revisión del responsable | Que esa activación ya se haya hecho |
| Límite explícito | Función ausente o condición sin autoridad suficiente, identificada por código/documentación | Un valor cero, aprobación implícita o permiso para sustituir datos por estimaciones |

La autoridad depende del dato: cálculo y números del motor y catálogo revisado; esquema de migraciones/RLS; intención del dueño de sus decisiones vigentes; estado funcional de su ref y evidencia. Las páginas de wiki orientan y preservan decisiones. Las observaciones de fases anteriores no se presentan automáticamente como defectos actuales.

Fuentes generales: [invariantes](../ENGINEERING.md), [producto](../PRODUCT.md), [estado vigente](../wiki/state/current-reality.md), [aceptación P20](../redesign/acceptance-2026-10-12.md), [activación](../operations/ACTIVACION.md).

<a id="capitulo-02"></a>

## 2. Qué es DEKOPEN y qué conecta

DEKOPEN combina ingeniería paramétrica, cotización y operación de empresas de ventanas y puertas de PVC/aluminio. Su objeto central es el producto configurado dentro de una posición de una obra. Ese diseño alimenta geometría, materiales, precio, revisión comercial, acuerdo, compras, producción y trazabilidad.

```text
Empresa y permisos → Cliente → Obra/proyecto → Posiciones y diseño
  → Motor + catálogo + inspector → Medidas de fabricación + BOM
  → Precio revisado/aplicado → PDF revisado → Emisión inmutable
  → Cliente elige/aprueba → Cobranza / acuerdo elegido
  → Evidencia de fabricación confirmada → Liberación → OT por posición
  → Compras / recepción / stock → Reserva y optimización
  → Estaciones / corte / calidad / reposición → Embalaje y despacho
  → Terreno / instalación / incidencias / garantía
  → Cierre de costos reales → Analítica y explicación de desvíos
```

Cada transición conserva su autoridad. Diseñar no equivale a fabricar; emitir no libera automáticamente al taller; aprobar no confirma un pago; reservar no consume material; planificar una visita no acredita entrega. La IA propone y prepara acciones sobre ese mismo flujo, con cálculo determinista y decisiones humanas donde corresponden.

### 2.1 Tamaño del contrato examinado

| Elemento | Cantidad / alcance | Método de inventario |
|---|---|---|
| Operaciones HTTP documentadas | 334 | Métodos HTTP de `backend/openapi.yaml` |
| Rutas distintas en ese contrato | 265 | Claves `paths` de OpenAPI |
| Operaciones compartidas de diseño/proyecto | 55 | Registro literal y expansión de preparación en `design_operations.py` |
| Máximo de operaciones de un lote | 50 | `MAX_OPERATIONS`; no es el tamaño del registro |
| Módulos Python del motor puro | 55 | Archivos versionados de `engine/src/dekopen_engine/` |
| Migraciones SQL versionadas | 183 | Archivos de `supabase/migrations/` |
| Archivos SQL de pruebas de DB | 97 | Inventario de `supabase/tests/`; no se ejecutaron para este reporte |
| Roles de organización | 5 | OWNER, ESTIMATOR, WORKSHOP_MANAGER, OPERATOR, INSTALLER |
| Declaraciones de tablas en migraciones | 149 nombres distintos | Historial de `CREATE TABLE`; no es introspección de una DB viva |
| Encargos del programa v1 | 39 mergeados, ninguno bloqueado | Registro de [ESTADO](../cola/ESTADO.md) |

La cantidad de operaciones API mide superficie técnica; no se interpreta como 334 pantallas o como 334 recorridos acreditados.

### 2.2 Arquitectura funcional

| Capa | Responsabilidad | Consecuencia visible |
|---|---|---|
| Motor Python puro | Geometría, materiales, masa, precios, corte, proyecciones comerciales/térmicas/analíticas | Los números tienen una entrada y autoridad reproducibles |
| Django por dominio | Permisos, transacciones, endpoints, persistencia, jobs e integraciones | Un clic guarda o emite bajo reglas de concurrencia y tenant |
| Supabase/Postgres | Auth, schema, RLS, identidades, historial inmutable y almacenamiento | La organización limita los datos aun fuera de la navegación de la UI |
| React/TypeScript/Vite | Lienzo, formularios, navegación, diffs, talleres y portal | Interacciones sobre el mismo modelo y API tipados |
| Worker de jobs | PDFs, correo, IA y derivaciones de eventos | Operaciones largas muestran progreso y resultado recuperables |
| Adaptadores | MiMo, Flow, SMTP/Mailpit, SII e intercambio CNC | Integración separada de la autoridad técnica y comercial |

<a id="capitulo-03"></a>

## 3. Panorama funcional por módulo

| Área | Capacidad implementada | Condición principal |
|---|---|---|
| Acceso | Magic Link, selección de empresa, MFA e invitaciones | Auth válido, membresía activa y segundo factor cuando se exige |
| Empresa | Identidad legal, marca, moneda y preferencias por tarea | Los cambios no reescriben emisiones anteriores |
| Clientes | Personas/empresas, contactos, direcciones, dossier y fusión revisada | Identidad canónica y aislamiento de organización |
| Proyectos | Obra, posiciones, lotes, revisión y centro de trabajo | Precio aplicado o revisión cerrada limita la edición |
| Editor | Cotas, divisiones, biblioteca, propiedades, operaciones y undo/redo | Geometría válida y evaluación vigente; escritura según tamaño/rol |
| Catálogo | Series por familia, perfiles, reglas, procedencia, importación y publicación | Datos técnicos revisados; DEMO conserva su condición sintética |
| Dominio físico | Vidrio, aperturas, herrajes, caras, extras y montaje | Compatibilidad y fuente completa de cada autoridad |
| Dibujo | Elevación DIN, planta y cotas comunes | Vista/movimiento declarados; históricos inferidos identificados |
| 3D | Poses físicas, hojas, cámaras, bicolor, exportación y despiece | Geometría/receta disponible; aproximaciones explícitas |
| Térmica | Uw, informes, alcance OGUC y alternativas revisadas | Uf/Ug/Ψg y espécimen con fuentes válidas |
| Precios | Proyección, aplicado, cascada, delta, reglas y aprobación | Costos/listas/FX vigentes y permisos de compra |
| Cotización | Checklist, PDF privado revisado, sello y recibo | PDF/huellas/condiciones vigentes y confirmación |
| Portal | Alternativas, decisión, documentos y pago | Capacidad vigente y solución sellada |
| Cobranza | Hitos, pagos manuales, Flow, saldos y recibos | Evidencia de movimientos; prueba y real diferenciados |
| Documentos fiscales | Internos, simulación y adaptador real 33/61 | Certificación/CAF/certificado/transporte; 39 real no soportado |
| Producción | Liberación, OT, estaciones, calidad, remake y despacho | Acuerdo/evidencia sellada, ruta, material y permisos |
| Corte | Barras, nesting de láminas, papel, CSV/DXF y etiquetas | Stock y parámetros físicos declarados |
| CNC | Configuración y comparación/emisión de intercambio neutro | Montaje, herramienta, profundidad, sujeción y origen completos |
| Compras | Necesidades, proveedor, OC, envío, recepción parcial y cancelación | Demanda sellada y clic humano de compra/envío |
| Inventario | Movimientos, reserva, formatos y retazos físicos | Identidad, medida, acabado y origen compatibles |
| Terreno | Visitas, evidencia, medición, firma, incidencias y garantía | Asignación viva y contexto sellado; replay validado en servidor |
| Analítica | Venta, margen, planta y terreno con causas/F6/CSV | Cobertura real; ausencia de dato no se convierte en cero |
| IA/asistente | Herramientas, propuestas, contexto, presencia y auditoría | Proveedor/capacidad, presupuesto, fuentes y confirmación de mutación |
| Jobs/correo | Progreso, reintento privado, outbox y recuperación humana | Worker y estado de intento; SMTP aceptado no significa leído |
| Plataforma | Billetera, ofertas, suscripciones/cambios/reconciliación | Oferta y términos provisionados; separación de cobros de la fábrica |

<a id="capitulo-04"></a>

## 4. Roles y límites de cada persona

### 4.1 Perfiles

**Dueño — OWNER.** Administra empresa, acceso, políticas, integraciones y autoridad comercial. Consulta costos y analítica, decide aprobaciones y puede operar los flujos comerciales/técnicos habilitados. Tiene MFA obligatorio. El rol no crea datos de fabricante ni evita bloqueos de fabricación.

**Estimador — ESTIMATOR.** Diseña posiciones, prepara obras y cotizaciones, consulta venta y solicita aprobaciones. Consulta catálogo y ciertas lecturas operativas. La proyección de precios elimina costos privados: una respuesta comercial no debe filtrar costo, margen privado, SKU de compra o autoridades de proveedor anidadas.

**Jefe de taller — WORKSHOP_MANAGER.** Revisa autoridad técnica, compras, inventario, liberación y planta, calidad, despacho y costos/analítica autorizados. El acceso a una confirmación de medición no le concede edición comercial general de proyectos.

**Operario — OPERATOR.** Entra por defecto a Producción, trabaja desde un puesto persistido, escanea piezas y registra acciones autorizadas de estación. Puede consultar inventario; esa consulta no concede recepción, compra, movimiento de retazos ni acceso a información comercial.

**Instalador — INSTALLER.** Consulta su agenda/asignaciones y registra evidencia de terreno autorizada. Las lecturas de producción tienen su alcance; no administra compras ni costos, no diagnostica ni cierra los casos que corresponden a oficina y no obtiene permiso general de taller.

**Cliente final.** No es un sexto rol de empresa. Accede a una propuesta por capacidad opaca ligada a revisión/acuerdo, con permisos públicos limitados. No recibe costos, fuentes privadas, RLS de miembro ni acceso general a proyectos.

### 4.2 Matriz de orientación

| Capacidad | Dueño | Estimador | Jefe | Operario | Instalador | Cliente |
|---|---|---|---|---|---|---|
| Hoy | Sí | Sí | Sí | Sí | Sí | No |
| Clientes/obras | Comercial | Comercial | Lecturas autorizadas | No comercial | Contexto asignado | Solo oferta |
| Diseño/operaciones de proyecto | Sí | Sí | Consulta/acciones puntuales | No | Medición asignada | No |
| Precios/venta | Sí | Venta autorizada | Lecturas autorizadas | No | No | Oferta sellada |
| Costos/autoridad de compra | Sí | Ocultos | Sí según dominio | Ocultos | Ocultos | Ocultos |
| Publicar catálogo | Sí | Consulta | Sí | No | No | No |
| Aprobar política comercial | Sí | Solicita | Según acción específica | No | No | Decide oferta |
| Comprar/recibir/mover retazos | Sí | Lectura limitada | Sí | Consulta stock | No | No |
| Liberar/reponer producción | Sí | Consulta | Sí | No liberación | No liberación | No |
| Acciones de estación | Sí | No generales | Sí | Puesto autorizado | No taller general | No |
| Terreno | Oficina | Oficina permitida | Oficina | No agenda general | Asignaciones propias | Evidencia pública limitada |
| Analítica de costos | Sí | No | Sí | No | No | No |
| IA/asistente | Sí | Sí | Sí | Sin workspace general | Sin workspace general | No asistente privado |
| Integraciones/usuarios | Administración | Lectura/preferencias permitidas | Lectura permitida | Cuenta | Cuenta | No |

La matriz resume la intención funcional. Los permisos exactos se deciden por endpoint, acción, estado del documento, asignación y RLS. Ver una entrada de navegación no autoriza una escritura. Fuente: [navegación](../../frontend/src/app/navigation.ts), `backend/authentication/`, scopes de cada dominio y políticas en `supabase/migrations/`.

<a id="capitulo-05"></a>

## 5. Navegación y superficies visibles

La aplicación agrupa Inicio, Ventas, Ingeniería, Operación, Asistente, Analítica y Ajustes. La navegación se filtra por rol. El operario abre su estación por defecto; los demás roles abren Hoy, salvo retorno a una ruta válida guardada durante el acceso.

| Ruta principal | Superficie / función |
|---|---|
| `/` | Inicio público o redirección según sesión/rol |
| `/login`, `/auth/callback`, `/auth/mfa` | Acceso y segundo factor |
| `/select-organization`, `/invitation` | Contexto de empresa y aceptación de invitación |
| `/dashboard` | Hoy: compromisos, bloqueos y decisiones |
| `/clients`, `/clients/:id` | Directorio y dossier de cliente |
| `/projects`, `/projects/:id` | Obras y centro de trabajo |
| `/projects/:id/positions/new`, `.../:posId/edit` | Crear/editar posición |
| `/projects/:id/pricing`, `/pricing/commercial` | Precio de obra y administración comercial |
| `/quotes` | Índice de cotizaciones |
| `/catalogs/systems`, `/catalogs/sheet-formats` | Catálogo técnico y declaraciones de lámina |
| `/purchasing`, `/inventory` | Compra e inventario separados |
| `/production`, `/dispatch`, `/field` | Taller, despacho y terreno |
| `/assistant`, `/jobs` | Asistente de trabajo y cola de tareas |
| `/analytics` | Lecturas para decisiones |
| `/settings/general`, `/settings/billing`, `/settings/wallet` | Configuración, facturación de plataforma y créditos |
| `/cotizacion/:token` | Propuesta pública del fabricante |
| `/pago/simulado/:linkId`, `/pago/retorno` | Pago de prueba y recuperación/retorno |
| `/about` | Identidad e información de la aplicación |

Hay rutas de desarrollo para benchmark, UI, marca, correos y diseño de referencia. Están condicionadas a desarrollo y no son capacidades productivas entregadas al cliente. El anexo de rutas conserva el inventario literal.

Ctrl+K busca entidades por dirección humana y ejecuta comandos permitidos. La paleta, drawer y ayuda gestionan foco; el cambio de empresa/objeto invalida consultas y comandos capturados. Las rutas desconocidas y errores de carga tienen recuperación explícita.

<a id="capitulo-06"></a>

## 6. Acceso, organización y seguridad

### 6.1 Acceso de usuario

1. El usuario solicita un enlace en Acceso.
2. Supabase Auth entrega el mensaje; en REVIEW se recibe en Mailpit.
3. El enlace de un uso lleva a resolver sesión/membresías y el retorno esperado.
4. Si falta organización se ofrece selección; si falta MFA se deriva al alta/desafío.
5. Una membresía activa y el nivel de aseguramiento adecuado habilitan el contexto.

El dueño siempre requiere `aal2`; una política puede exigirlo a otros miembros. Hay acceso mínimo para configurar MFA sin conceder las funciones protegidas. Una invitación cifra su capacidad, vence en siete días y exige correo verificado y aceptación explícita. Crear un usuario Auth no concede membresía.

### 6.2 Aislamiento y secretos

Los datos de organización llevan `org_id` y RLS. Los scopes del backend preservan claims de usuario y organización al cambiar de rol técnico de DB; workers y llamadas anidadas restauran ese contexto. El catálogo global visible no vuelve públicos clientes, costos, órdenes ni documentos.

Las claves de IA, SMTP, Flow/SII y servicio se usan en servidor/worker; la interfaz muestra estado/capacidad y causas permitidas. Este reporte no incluye valores de `.env`, tokens de sesión, enlaces vivos de cliente, códigos MFA ni credenciales. Un QR de pieza identifica; la sesión y RLS siguen siendo necesarias.

### 6.3 Acceso documental y concurrencia

Storage privado entrega acceso firmado por artefacto/revisión y contexto autorizado. Los tokens públicos se verifican por vigencia, revocación, hash y revisión. Los recibos de operaciones, firmas de preview y claves de reintento evitan que una respuesta tardía aplique sobre otro objeto. Una edición posterior puede invalidar undo o una confirmación anterior.

Fuentes: `backend/authentication/{types,tenancy,rls,jwt_verifier}.py`, [empresa/clientes](../wiki/product/company-customers.md), [documento](../wiki/product/quotation-document.md).

<a id="capitulo-07"></a>

## 7. Empresa, configuración y alta inicial

La empresa conserva identidad legal separada de identidad visual: razón social, RUT, giro, dirección, contacto, logo, color y moneda. La marca se sella con la revisión. Cambiar logo, papel, acento o pie afecta preparaciones/emisiones nuevas; no modifica PDFs históricos.

Las preferencias se organizan por tarea: cuenta/acceso; empresa/marca; condiciones comerciales; documentos; producción/estaciones; vano/montaje; extras/servicios; integraciones; IA/presupuesto; analítica. Los roles ven los controles que les corresponden. La numeración muestra secuencias reales como referencia sin reservar una identidad.

El alta inicial guía Empresa → Comercial → Documentos → serie → cliente → obra → posición. El borrador se guarda por organización; una respuesta de otra organización se descarta. La selección de sistema usa series visibles/evaluables. No se muestra un precio inventado para una miniatura. Una respuesta perdida solo adopta una coincidencia reciente, única y con los campos enviados.

El PDF vivo de preferencias se construye con una revisión real y el renderer DOC-01 común. Conserva precio/moneda sellados; si falta obra/revisión, explica la causa y destino. La preferencia de moneda no convierte precios existentes ni tarifas laborales: una conversión necesita una observación de cambio declarada.

<a id="capitulo-08"></a>

## 8. Clientes y dossier comercial

### 8.1 Ficha y directorio

Se distinguen persona, empresa y tipo histórico desconocido. Se valida RUT nuevo por módulo 11 y se comprueban duplicados canónicos dentro de la organización. Hay contactos con rol, direcciones de obra y notas con autor/fecha. Dirección de facturación y dirección de entrega son diferentes.

El directorio filtra, cuenta y pagina en SQL; contactos/direcciones se leen por lote de la página. El dossier reúne obras, revisiones, acuerdos elegidos, cobros/documentos y saldos por moneda. Una obra sin importe acreditado conserva Sin dato y no aporta cero al total.

### 8.2 Dirección y fusión

Elegir una dirección maestra copia su texto al proyecto y valida pertenencia a cliente/tenant. Editar el texto de entrega desvincula la referencia maestra, evitando que otro cambio la sobrescriba. Seleccionar una dirección nuevamente vuelve a copiarla. Las revisiones emitidas mantienen su información.

La fusión compara dos fichas, exige motivo, confirmación y revisiones vigentes. RUT diferentes y no vacíos impiden fusionar. Locks serializan cambios de contactos/direcciones con la fusión. El origen queda como alias histórico y las copias conservan procedencia; no se reescriben cotizaciones ni documentos antiguos.

Fuente: [empresa/clientes](../wiki/product/company-customers.md), `backend/projects/{clients,client_history,company}.py`.

<a id="capitulo-09"></a>

## 9. Proyectos, posiciones y revisión

El centro de trabajo identifica cliente, dirección, revisión, vigencia y precio aplicado. Sus siete pestañas conectan posiciones, cotización, precio, cobranza, producción, documentos y actividad. La próxima acción depende de fase, permisos, enlace y calendario; un anticipo parcial no completa por sí solo un hito.

Las posiciones muestran elevación interior real, cantidad, acabado, vidrio y fuente comercial. Lista/grilla, filtros y selección se conservan. Piso, recinto y eje son metadatos opcionales; el producto no los inventa. La fila usa precio aplicado de la revisión, separado del indicativo del editor.

| Acción | Resultado | Restricción importante |
|---|---|---|
| Agregar receta de biblioteca | Nuevo diseño evaluado por el motor | Serie/apertura/glass/finish compatibles |
| Duplicar una posición | Copia de configuración con nueva identidad | No copia el levantamiento físico del vano ni precio aplicado |
| Eliminar/reordenar | Cambia el borrador/lote | El orden visual no renumera la dirección física |
| Cambiar metadatos | Actualiza ubicación/cantidad/campos permitidos | BOM/mediciones se preservan cuando el cambio es solo metadata |
| Cambiar en lote | Preview de destinos, diff y aplicación atómica | Firma de concurrencia, idempotencia y acceso a cada posición |
| Clonar proyecto / crear sucesora | Borrador independiente de una historia conservada | Una revisión sellada no se edita en sitio |
| Importar documento/plano | Candidatos y confirmación humana | El documento no es autoridad para números derivados |

Las cien posiciones de la referencia de escala se virtualizan, conservando teclado/foco. La caché de lote se limita a su operación/transacción; resultados idénticos pueden reutilizarse sin quitar reservas de autoridad por destino. Producción se filtra por proyecto en servidor antes del límite. Los borradores de pestañas se invalidan al cambiar de obra/identidad.

Una revisión cerrada o un precio aplicado bloquean escrituras también en Postgres. Retirar/revisar precio y crear sucesora son acciones explícitas. La solución elegida por el cliente gobierna lo que se cobra y fabrica.

Fuente: [centro de trabajo](../wiki/product/project-workspace.md), `backend/projects/`, `frontend/src/features/projects/`.

<a id="capitulo-10"></a>

## 10. Modelo paramétrico y verdad numérica

El ProductModel compone ensamblajes de módulos, perfiles, rellenos y uniones. Cada objeto mantiene identidad para selección, historial, comparación, operaciones de IA y piezas. Bow/bay, puerta con lateral, sobreluz y esquina son recetas del mismo modelo.

Las dimensiones y el dinero usan Decimal. Los transportes nuevos conservan strings decimales; la tolerancia de cálculo es `0,00 mm`. Un renderer puede convertir coordenadas para proyectar píxeles, pero esa proyección no modifica cortes, precio ni snapshot.

| Entrada de autoridad | Resultado del motor | Falta de autoridad |
|---|---|---|
| Medidas, árbol, perfiles/reglas | Geometría, descuentos, cortes y BOM | Error o fabricación incompleta con causa |
| Vidrio/panel y densidades | Área, espesor y masa | Peso/capacidad no certificables |
| Apertura/herrajes/fuentes | Hojas, manillas, movimiento, componentes | Apertura o mecanizado bloqueados |
| Color/compra/costo/FX | Variante física y proyección comercial | Precio Sin dato o cálculo rechazado |
| Stock/sierra/formato | Plan de corte/nesting y retazos | Piezas sin colocar/bloqueo explícito |
| Informes térmicos | Uw y comprobación de alcance | Sin dato o sin afirmación de cumplimiento |

El catálogo histórico y las doce variantes legadas de apertura conservan su camino de cálculo/snapshots. Las autoridades adicionales se incorporan sin reinterpretar precios y documentos emitidos. Los goldens congelan comportamiento de fabricación; el informe los inventaría sin ejecutarlos ni regenerarlos.

<a id="capitulo-11"></a>

## 11. Editor, comandos e historial

### 11.1 Trabajo directo

La franja compacta, biblioteca por familias, lienzo con cotas y propiedades por selección permiten editar el producto desde su dibujo. Se pueden crear divisiones verticales/horizontales, mover/eliminar divisores, igualar paños, cambiar medidas, apertura, vidrio, manilla, acabado y extras; conjuntos agregan módulos, ángulos y uniones.

Los comandos usan el registro compartido. Una simulación devuelve modelo/evaluación/diff antes de commit. Si una operación se rechaza, el campo vuelve al valor aceptado. El historial registra una transacción de edición y habilita deshacer/rehacer con identidades estables.

### 11.2 Estado pendiente y respuestas tardías

Durante debounce puede conservarse el dibujo anterior para mantener continuidad. Eso no autoriza Guardar ni presentar el precio viejo como vigente. Las respuestas de otro diseño o cantidad se descartan. Cambiar de selección, abrir otra obra o navegar con cambios pendientes conserva los guards aplicables.

La venta indicativa se calcula con `ops=[]`, cantidad entera y la misma autoridad comercial. No persiste producto ni precio; el motor multiplica y redondea según contrato. Emisión necesita precio aplicado, no ese indicativo.

### 11.3 Tamaño de pantalla y recuperación

Desde 1280 px el inspector se acopla; a 1024 px se abre como drawer. Debajo se conserva lectura, cotas, precio y navegación, con la restricción de escritura y atajo de guardar del editor. El portal, taller y terreno tienen otras tareas móviles; ese límite no se generaliza a toda la app.

Pan/zoom se acotan al dibujo físico y Ajustar considera margen de cotas. Menú, popover, biblioteca y pie evitan capas simultáneas. Ante una lectura fallida hay causa y Reintentar sobre la misma posición/tenant, sin escritura. La región de diseño tiene nombre accesible; nombres largos y tamaños móviles conservan el dibujo según la aceptación documentada.

Fuentes: [editor](../wiki/product/editor-canvas.md), `frontend/src/features/projects/ProjectPositionEditor.tsx`, `engine/src/dekopen_engine/design_operations.py`.

<a id="capitulo-12"></a>

## 12. Geometría, contornos y conjuntos

El modelo representa módulos rectangulares, contornos y composiciones con uniones explícitas. Las divisiones generan montantes/travesaños dentro del marco; un agregado de módulos genera un conjunto, conservando estructura e identidad de cada unidad.

El dominio distingue geometría válida de fabricación completa. Un arco puede necesitar curvado sin regla, un contorno puede tener apertura no soportada y un vidrio sin marco puede carecer de soporte/herraje. Esas ausencias no se resuelven dibujando una pieza ficticia.

Los contornos conservan vértices, arcos y medidas físicas. Las cadenas de cotas incluyen extremos/cardinales reales; la altura total de un arco no se sustituye por su arranque nominal. Acoplar un contorno o crear splits/aperturas donde el contrato no los admite devuelve una causa específica.

Las conexiones incluyen INLINE, STACKED, TEE y CORNER en el modelo. La presencia del enum no habilita cualquier combinación: conectividad, lados, ciclos, auto-intersección, altura/ancho, artículo y autoridad de unión se validan. El motor deriva cuerda, desarrollo, proyección, altura y ubicación de módulos.

`CouplerRule` declara límites de deflexión y aporte desarrollado con fuente. El aporte no se infiere de un SKU, cara de perfil ni inglete. En STACKED incrementa altura; en frentes se sitúa sobre la bisectriz. Sin regla, se conserva el contrato histórico y no aparece una nueva medida inventada.

La planta y elevación comparten selección, arrastre, simulación, commit y undo. Los módulos apilados se eligen mediante rótulo/fila aun con huella coincidente. El precio de cada módulo se calcula en el motor; el residual Acoples y ajustes cierra exactamente el conjunto y no es reparto proporcional de fabricación.

Fuentes: [conjuntos](../wiki/product/coupled-assemblies.md), `engine/src/dekopen_engine/{product,contour,assembly_measures,geometry}.py`.

### 12.1 Vidrio sin marco

`FramelessSpec` representa el vidrio como producto, con soportes reales por borde —canal continuo o pinzas— y fittings contados: patch fitting, pinza, bisagra, cerradura, conector, sello o soporte. Los canales generan cortes de perfil reales y los fittings cantidades; no se inventan FRAME/SASH para acomodarlo al modelo anterior.

La evaluación actual exige un único paño con vidrio y rechaza contorno no soportado. Una apertura móvil o panel recibe su causa `frameless_opening_unsupported`/`frameless_panel_unsupported`; un enum de fitting bisagra no acredita por sí solo una puerta móvil fabricable. Sin retención declarada no se considera producción completa. SKU de soporte desconocido conserva la advertencia correspondiente.

La medida del vidrio procede del módulo directamente, sin descuento ficticio de marco. La traza industrial conserva paño y canales con identidad, lado/origen y cantidad. Esta capacidad está en el modelo/motor y en `set_frameless`; no se atribuye una matriz de aceptación física adicional que no esté documentada.

<a id="capitulo-13"></a>

## 13. Catálogo técnico, importación y publicación

### 13.1 Estructura y readiness

El catálogo declara material, familia, perfiles/artículos, aperturas, límites, reglas de corte/refuerzo, vidrio, herrajes, colores, extras, sección y fabricación. Una serie practicable no se vuelve corredera por dibujar un rectángulo parecido. Editor y motor usan capacidades de la misma familia.

Cada regla conserva fuente. Descuentos, pérdidas por extremo, refuerzo por largo/acabado y tornillos del BOM son datos de la autoridad, calculados por el motor. La sección revisada exige origen/orientación y profundidad exacta.

`catalog_authority_gate` comunica revisión, fabricación y proceso. Catálogo verifica cobertura; emisión verifica los artículos usados. Cotizable no implica centros, CNC o producción completos. DEMO sigue siendo DEMO tras una revisión humana; REVIEWED tampoco equivale a certificación. VERIFIED exige evidencia acorde con los valores presentes y revisión válida.

### 13.2 Caminos de entrada

| Entrada | Tratamiento | Resultado |
|---|---|---|
| Plantilla CSV/XLSX | Tipos/lexemas decimales, hojas y errores de fila/columna | Candidatos revisables; fórmulas no son autoridad |
| PDF con texto | Extracción literal y referencias | Valores sustentados o desconocidos |
| PDF escaneado/mixto o imagen | Páginas acotadas para visión, evidencia y revisión | Lectura candidata; no certificación automática |
| Texto/correo pegado | Extracción y campos tipados | Misma revisión/diff/publicación |
| Edición estructurada | Campos de autoridad y procedencia | Nueva revisión de datos según uso/locks |

La plantilla documentada tiene diez hojas, incluida Reglas de vidrio. El código/schema publicado gobierna campos actuales. Correcciones humanas conservan original y literal; no se atribuyen al fabricante. Un valor sin evidencia o confianza insuficiente queda UNKNOWN.

### 13.3 Ciclo de control

Importar → extraer → revisar candidatos/corregir/excluir → simular diff → confirmar publicación → exportar/trazar → deshacer si es admisible. El token de revisión liga preview al catálogo vigente; locks/transacción impiden aplicar una versión obsoleta o una parte del archivo.

Dueño/jefe de taller publican. El estimador consulta. Originales comerciales y ciertas fuentes se restringen; una auditoría de IA no debe revelar costos a otros roles. Los eventos y valores de evidencia son inmutables. Deshacer exige que la autoridad no haya sido usada/modificada; retirar preserva identidad e historia.

Las series DEMO sucesivas son aditivas. No certifican un fabricante y no sustituyen fuentes de fabricación. La aceptación con PDF/foto sintéticos acredita el flujo de lectura/revisión/publicación, no validez industrial de la ficha.

Fuentes: [autoridad de catálogo](../wiki/product/catalog-authority.md), `backend/catalogs/`, `backend/ingest/`, `engine/src/dekopen_engine/catalog_authority.py`.

<a id="capitulo-14"></a>

## 14. Aperturas y composiciones físicas

La apertura nueva declara movimiento, bisagras, dirección, papel activo/pasivo y fijo en hoja. El uso ventana/puerta y la composición de hojas/carriles son contratos independientes. Se conservan los doce nombres históricos y sus snapshots; una orientación legada desconocida no adquiere autoridad nueva por conversión.

| Grupo | Configuración disponible bajo catálogo | Condición física |
|---|---|---|
| Fijo | Paño fijo o fijo en hoja según composición | No recibe automáticamente herrajes de movimiento |
| Practicable | Bisagra/cierre y apertura interior/exterior declarados | Símbolo/manilla coherentes con la vista |
| Basculante/oscilobatiente | TILT y TILT_TURN con familia/kit | Recorrido y rangos autorizados |
| Proyectante/abatimiento | TOP_HUNG/BOTTOM_HUNG según receta | Dirección hacia observador o hacia afuera explícita |
| Francesa/doble puerta | Activa y pasiva, bisagras opuestas, inversor/falleba | La pasiva no toma una manilla activa ni se sustituye por montante central |
| Puerta con lateral | Puerta y paño lateral con estructura propia | Conserva montante y comprobaciones estructurales |
| Corredera | Paneles X/O, carriles y viaje LEFT/RIGHT | Cada hoja móvil y su carril deben ser compatibles |
| Elevable HST | Elevación y traslación por receta | No infiere variantes G/K ausentes |
| Paralela PSK | Basculación/separación paralela y viaje | Kit y ejes de la misma autoridad |
| Plegable | Cadena de hojas, paquete y hoja de paso | Longitudes rígidas y cierre de paso independiente |
| Pivote vertical/horizontal | Eje, plano, manilla y límites | La pose proviene de receta evaluada |
| Guillotina | Viaje por hoja/carril y muelle/contrapeso | No se inventa contrapeso ni recorrido |

Las siete series DEMO v8 documentadas añaden catorce recetas avanzadas; son fixtures de dominio, no catorce certificaciones de fabricante. La biblioteca informa qué serie admite una receta y qué falta cuando no existe. En el motor las recetas avanzadas usan contexto Decimal local de 80 dígitos y preservan el camino aritmético legado.

La API rechaza herraje de otro sistema/tenant, desactivado, ausente o incompatible. Una puerta conserva su uso para reglas de seguridad de vidrio aun sin alias histórico. Cambiar una apertura exige recalcular geometría, peso, compatibilidad, BOM y precio; un dibujo por sí solo no habilita producción.

Fuentes: [aperturas](../wiki/product/physical-openings.md), [avanzadas](../wiki/product/advanced-openings.md), `engine/src/dekopen_engine/{openings,advanced_openings,models}.py`.

<a id="capitulo-15"></a>

## 15. Vidrio, paneles y pedido al proveedor

### 15.1 Receta estructurada

La composición ordena de exterior a interior láminas, interláminas y cámaras. Conserva tipo, espesor, color, cara de capa, código de proveedor, gas, separador, sellante y procesos. La notación comercial se parsea/formatea sin perder estructura expresable. La densidad de PVB necesita dato/fuente; no se deduce del nombre.

El modo básico elige un producto compatible. El avanzado muestra sección a escala, procedencia y procesos. La posición guarda receta completa e identidad de autoridad inmutable; backend compara ambas contra el mapping visible. Cambiar solo nombre, fuente, propiedad o receta no permite falsificar un SKU.

### 15.2 Cálculo y seguridad

El motor calcula espesor total/neto, masa, área/corte, mínimo facturable y recargos. Ug, g, transmisión y clase exigen fuente del proveedor. Un espesor desconocido impide una sección a escala; una masa desconocida impide certificar capacidad de herraje. El junquillo depende del espesor total, y la carga considera la hoja completa.

Las reglas de seguridad de la organización pueden advertir o bloquear; una regla obligatoria bloquea si falta la clase compatible. El aviso cita la fuente y ofrece opción compatible cuando existe. El catálogo DEMO no declara una norma oficial. Guardar/preciar aplica reglas también a transportes legados, evitando omitir la receta para eludir un requisito actual.

El ensayo final acepta vidrio float, termopanel float, Low-E, termopanel laminado de seguridad y un suplemento templado. El laminado monolítico de 6,38 mm de esa muestra se rechaza por junquillo ausente; no es una afirmación de que todo laminado sea incompatible.

### 15.3 Pedido y panel

El pedido de vidrio por OT/lote consume piezas e identidades selladas. PDF, CSV y etiquetas conservan medida/cantidad; templado se solicita exacto y contorno necesita plano sellado. Si el cálculo entrega fracciones, se conserva precisión y se solicita aceptación del proveedor; presentar enteros no autoriza cambiar el corte.

El panel tiene geometría, masa y artículo propios; no usa densidad de vidrio por analogía. Los SKU, espesor y compra necesitan autoridad compatible. Un vidrio sin marco tiene contrato de soporte y fittings: la representación visual no sustituye su definición de fabricación.

Fuentes: [vidrio](../wiki/product/glass-composition.md), `glass_composition.py`, `glass_orders.py`, `panel.py`, `product.py`, `backend/catalogs/glass_views.py`.

<a id="capitulo-16"></a>

## 16. Herrajes, clases, manillas y mecanizados declarados

La selección pertenece a sistema/familia/movimiento. Rangos de ancho/alto, masa, relación de hoja, compás, prioridad, componentes, opciones y manillas tienen fuente. Se calcula masa exacta, incluida expansión del herraje; un empate de autoridad no se resuelve por orden de lectura.

Las reglas de cantidad/largo son tipadas y finitas. Componentes por umbral, transmisión cortable y masa por metro producen BOM/costo. Una sustitución reemplaza el componente base sin sumar dos veces. Las combinaciones duplicadas se rechazan; una pasiva conserva su herraje/falleba y no hereda la manilla activa.

La altura de manilla declara referencia local. FLOOR requiere antepecho observado. El motor obtiene coordenadas, cierre y rango; no usa un texto libre como geometría. Cambiar/deshacer altura o clase actualiza la evaluación y necesita autoridad de cada hoja afectada.

El inspector/F6 explica medida, masa, rango, componente y fuente. Una reparación puede proponer otra clase o una división físicamente válida, con preview/diff antes del clic. El neto indicado de herrajes se identifica como componente; no equivale al precio completo de posición.

La emisión sella la expansión exacta. Picking agrupa SKU, largo y fuente por OT/revisión; compra/reserva componentes sin agregar de nuevo el kit completo. Una pieza cortable conserva su variante de largo.

Mecanizar requiere anfitrión inequívoco, coordenadas dentro de pieza, cara, herramienta, profundidad, fuente y cobertura de cantidad. Una declaración incompleta se muestra como declarada no emitida y puede bloquear completar Mecanizado. El nombre del componente no aporta una coordenada CNC.

Fuente: [clases de herrajes](../wiki/product/hardware-classes.md), `hardware_classes.py`, `hardware_machining.py`, `hardware_proposals.py`.

<a id="capitulo-17"></a>

## 17. Color, acabado y caras

La combinación identifica interior, exterior y base de material. La carta declara proceso, código de fabricante, RGB lineal exacto, fuente, aproximación y carácter sintético. PVC distingue masa/foliado/coextrusión; aluminio admite lacado, anodizado y efecto madera según autoridad.

El diseño guarda identidad de combinación; el BOM sella carta y caras. La regla puede afectar holgura de vidrio, límites de posición/hoja, refuerzo y colores de manilla. El recargo se expresa por metro de perfil, porcentaje de costo o importe por posición, con moneda y autoridad comercial.

El delta de venta usa el motor y la configuración de cálculo; no presupone que subir costo siempre cambie venta en matriz/lista. Moneda/costo/regla ausentes producen una causa y Sin dato. El acabado comercial de una ventana no permite sustituir el stock físico por una barra de otra combinación. Acero/refuerzo conserva su identidad independiente.

El editor permite caras diferentes o iguales y undo. Guardar espera el cálculo nuevo. CSS convierte lineal a sRGB; THREE usa valores lineales y materiales por normales. PDF/portal/3D consumen la carta sellada, con vista declarada. Una textura ausente se presenta como aproximación plana, sin ruido aleatorio inventado.

Fuentes: [acabados](../wiki/product/color-finishes.md), `finish_models.py`, `finishes.py`.

<a id="capitulo-18"></a>

## 18. Accesorios, servicios y plantillas

Los extras cubren perfiles/accesorios como vierteaguas, ensanches, tapajuntas y mosquiteros bajo catálogo, junto con selecciones compatibles por ventana/hoja/lado. El motor deriva largos, vuelos y cantidades; las piezas físicas añaden BOM/corte/refuerzo/tornillos cuando la autoridad lo exige.

Los servicios comerciales pueden declararse por área, perímetro, cantidad o zona: instalación, sellado, retiro, andamio y flete. Deben tener tarifa, unidad, moneda y fuente. Las plantillas se aplican a posiciones nuevas; seleccionar o sugerir un extra admite aceptación/descarte/undo.

| Regla de coherencia | Comportamiento |
|---|---|
| Manilla especial | Sustituye la base, sin doble costo |
| Instalación explícita | Suprime el cargo histórico equivalente; duplicidades se rechazan |
| Palillaje/cruces | Usan receta de vidrio, sin segundo BOM ni largo inventado |
| Extra de un módulo | No se habilita por una hoja compatible de otro módulo |
| Importe agrupado/sublíneas | Base + sublíneas cierra al neto aplicado con ajustes explícitos |
| Costo de extra y su BOM | Se cobra una vez, aunque el material también se fabrique/compra |

El dueño con MFA configura servicios/política con revisión e historial. El estimador recibe definiciones/venta, sin costos privados en respuestas anidadas. Emisión conserva selecciones/cantidades/política. Clonar/sucesora no reescribe lo emitido.

Fuente: [extras y servicios](../wiki/product/accessories-services.md), `extra_models.py`, `extras.py`, `backend/projects/extras.py`.

<a id="capitulo-19"></a>

## 19. Vano, medición y fabricación

### 19.1 Entrada y derivación

La regla de montaje pertenece a organización y serie, con revisión inmutable, tipo, fuente, condición DEMO, tolerancia y holgura/premarco/ensanche/traslape por lado. El muro es obligatorio y comienza sin material supuesto.

Se toma una o tres medidas positivas por eje. El motor conserva mínimo y dispersión a centésimas. Fabricación deriva del mínimo más traslapes menos holguras, marco/ensanche según autoridad. Una fijación manual necesita motivo; desviación, descuadre y desplome se comparan con tolerancia declarada.

Si la regla exige ensanche, necesita el accesorio físico compatible en esos lados. Cambiar regla retira exigencias anteriores y conserva extras independientes; los destinos contradictorios requieren corrección. Una propuesta pendiente se invalida cuando cambia diseño/regla.

### 19.2 Confirmación e historial

Cada generación liga regla, entradas y resultado al diseño guardado mediante SHA. La evidencia es append-only. Confirmar exige generación actual, cobertura de todos los marcos y reconocimiento de avisos. Dueño/estimador/jefe tienen la acción específica; el instalador usa su flujo asignado de terreno.

Las emisiones nuevas sellan que la medición es requerida; backend/SQL impiden liberar OT con confirmación pendiente o ajena al diseño. Los históricos sin esa marca conservan su contrato. La cotización/portal distinguen vano y fabricación; el taller usa fabricación y el portal omite motivos/actor privados.

Rectificar una revisión cotizada/aprobada simula el precio completo y muestra delta de venta. Aplicar un token vigente abre sucesora y exige nueva confirmación. Lo anterior conserva PDF/precio. Una obra ya fabricada se corrige mediante el flujo de responsable/terreno, sin reescribir lo liberado.

Fuente: [vano y fabricación](../wiki/product/opening-measurements.md), `mounting.py`, `backend/projects/mounting.py`.

<a id="capitulo-20"></a>

## 20. Dibujo técnico 2D, DIN, planta y cotas

Motor, React y PDF comparten gramática de aperturas. La vista interior/exterior espeja una vez y contrarrefleja textos. Triángulo/continuidad/discontinuidad, flecha y manilla comunican bisagra, giro y sentido; una puerta no se dibuja como una planta dentro de la elevación.

Las correderas declaran viaje por hoja y carril. Un transporte histórico sin viaje se rotula inferido y conserva BOM/bytes; no se presenta como nueva autoridad del fabricante. La planta necesita layout real; no dibuja una franja de carriles inventada.

Las cotas provienen de cadenas físicas del motor: total, ejes de montantes/travesaños, módulos, extremos de contorno y arco. Se reservan niveles para cotas pequeñas/unidades apiladas. Las secciones muestran vértices/ejes declarados; una profundidad no definida no aparece como medida exacta.

Agrupar posiciones para documento/portal considera geometría sellada, evitando unir hojas de autoridades diferentes. La proyección pública permite los hechos visibles y elimina fuentes/costos privados.

Fuente: [dibujos](../wiki/product/opening-drawings.md), `symbols.py`, `drawing.py`, `frontend/src/features/canvas/`.

<a id="capitulo-21"></a>

## 21. Representación física 3D

El editor consume hechos evaluados; el portal consume hechos sellados. Visor, PNG y miniaturas comparten cámara, materiales, entorno y transformaciones rígidas. Las opciones visuales no escriben dimensiones ni retroalimentan el motor.

Cada hoja puede operarse individualmente. Plegable mantiene longitud rígida y paquete; la hoja de paso actúa independientemente al cerrar. HST eleva y PSK separa antes de desplazar. Guillotina y pivotes usan recorrido/plano/eje de su receta. El despiece separa capas cerradas con guías, sin recalcular fabricación.

La cámara no gira sola. Hay controles de teclado, interior/exterior, detalle de manilla, exportación y recuperación tras pérdida de contexto. Reduced motion limita la animación. Sin WebGL se conserva alternativa técnica. La primera carga fría de WebGL tiene una limitación de rendimiento documentada separada de la interacción caliente.

Las correderas simples conservan decodificador visual/layout histórico donde el motor no devuelve hojas físicas nuevas. Una hoja física sin evaluación queda Sin dato. Herrajes/secciones esquemáticos, textura plana y geometría histórica aproximada se identifican. El muro opcional no certifica montaje. DOC-01 usa SVG técnico; el 3D no reescribe ese PDF.

Fuente: [3D físico](../wiki/product/physical-3d.md), `frontend/src/features/canvas/{Product3DScene,poses3d}.ts` y renderers relacionados.

<a id="capitulo-22"></a>

## 22. Inspector y condición de fabricación

El inspector aplica verificaciones tipadas a hechos exactos y observaciones declaradas: medidas/capacidad, estructura, refuerzo, drenajes, cierres, montaje, vidrio y datos de taller según configuración. Una alerta indica objeto, causa, consecuencia y corrección admisible.

Se distinguen fallo real, dato faltante, fabricación incompleta, advertencia y no aplicable. El gate concreto decide si bloquea diseño, emisión documental, liberación o completar una estación. No todos los faltantes bloquean lo mismo; una cotización comercial puede conservar Solo cotización, mientras un fallo crítico puede impedir emitir.

Las sugerencias de reparación se simulan por el motor y necesitan diff/clic. Un diagnóstico no convierte un BOM inválido en válido. Las condiciones manuales —altura, drenajes, cierres, momento de inercia, montaje— no se completan con una frase de IA. El costo/beneficio visible de una reparación conserva permisos y autoridad comercial.

La emisión conserva inspector, políticas y antecedentes de taller. La liberación consulta lo sellado y su proceso autorizado; no reemplaza esa autoridad por catálogo mutable. Las reglas obligatorias de vidrio, la medición vigente y un mecanizado no emitible tienen bloqueos propios.

Fuentes: `inspection_models.py`, `inspector.py`, `backend/engine_api/`, [invariantes](../ENGINEERING.md).

<a id="capitulo-23"></a>

## 23. Térmica, informes y alcance OGUC

El motor obtiene áreas visibles de marco/vidrio y longitud de borde. La estructura de Uw combina áreas por sus transmitancias y borde por Ψg, divididos por área total, con Decimal. Uf, Ug, Ψg, g y clases son datos de informes revisados, no inferencias de color, nombre de perfil o espesor.

Los informes conservan norma, laboratorio, documento, página, vigencia, medidas/apertura y combinación. PERFORMANCE liga espécimen exacto, incluido vidrio/herraje; no extiende un ensayo por un rango supuesto. Sin autoridad completa, contradicción o datos DEMO no se afirma cumplimiento.

El proyecto declara zona oficial, uso y ventanas/muros por orientación; no deriva zona de comuna. La comprobación tiene alcance explícito y considera el mayor Uw del grupo según regla. F6 explica cálculo/fuentes. La alternativa más barata se limita al catálogo evaluable con precio; usa diff/aplicar/undo común.

El anexo térmico opcional se sella al emitir. Revocar un informe afecta cálculos nuevos, conservando fuentes/PDF históricos. El soporte normativo transcrito en `docs/engineering/thermal/` no certifica el producto ni el edificio.

Límites: no FEM, Up para opacos, método para paños solapados ni extensión de ensayos por rango. No acredita condensación, ventilación, cálculo completo de envolvente ni sustitución del responsable profesional/plan de descontaminación.

Fuente: [térmica](../wiki/product/thermal-authority.md), `thermal.py`, `thermal_rules.py`, `backend/projects/thermal.py`.

<a id="capitulo-24"></a>

## 24. Precio, costos, listas, monedas y aprobaciones

### 24.1 Lectura y escenarios

El workspace compara precio aplicado con proyección sin guardar. La cascada y delta son del motor. Dueño/jefe conservan lectura de compra según dominio; el estimador recibe venta por allowlist, también en trazas y lotes. El precio indicativo no sustituye aplicado.

Las autoridades comprenden listas de costo por SKU/unidad, listas/matrices comerciales, vigencia, configuración, modo de precio, segmento, margen, descuento, servicios, impuesto y FX. Una lista sin moneda o un SKU sin cobertura tiene causa y Sin dato/error; no se asume costo cero.

| Momento | Qué representa | Qué persiste |
|---|---|---|
| Indicativo de editor | Venta de la entrada actual | Nada aplicado |
| Preview comercial | Escenario/cascada/delta revisables | Propuesta/operación según lifecycle |
| Solicitud de aprobación | Condiciones fuera de política | Solicitud auditada, sin aprobación automática |
| Aplicación | Precio aprobado y vinculado al estado | Resultado/autoridades comerciales congeladas |
| Retiro/cambio | Liberación explícita de precio o nuevo escenario | Historia anterior conservada |
| Emisión | Venta de la revisión aprobada | Snapshot documental sin repricing futuro |

### 24.2 Cálculo exacto y explicación del delta

Costo consumido de barra conserva precisión alta; composición/cascada usa contexto suficiente para no repartir residuales de cálculo. La multiplicación por cantidad precede a la cuantización requerida; unitario, neto por línea e IVA por proyecto respetan su contrato. Ajustes de representación se explican, sin otro cargo oculto.

Repricing atribuye el delta en orden canónico: cantidad → medidas → vidrio → herrajes → diseño → lista de costos → FX → lista comercial → margen → descuento → segmento → servicios → impuesto. Cada paso usa autoridades congeladas, sin consultar catálogo vivo. Si un intermedio no es físicamente válido o faltan antecedentes, se explica Sin dato en lugar de fabricar una atribución. La suma de causas válidas cierra el delta.

### 24.3 Políticas y monedas

La política documentada parte de banda 25/35/60 % y límite de descuento 10 %, configurables por dueño; no se fuerza esa política a toda organización histórica. Salir de la banda requiere solicitud y decisión. Aplicar relee política bajo bloqueo para evitar carreras. Aprobar/rechazar registra comentario/actor y llega a Hoy/campana del solicitante; marcar leído es otra acción.

CLP y USD mantienen quantum/presentación propios. La preferencia de empresa propone moneda nueva, sin reinterpretar aplicado. USD→CLP usa observación declarada y buffer contractual de importación cuando corresponde. Costo local CLP cotizado en USD se divide por CLP/USD observado, sin reserva adicional. No existe FX implícito para completar datos faltantes.

Las optimizaciones de lectura agrupan stock/membresías/autoridades dentro de una propuesta y transacción repetible. La siguiente propuesta vuelve a consultar fuentes; no se recortan listas para acelerar y no cambia RLS.

Fuente: [workspace de precios](../wiki/product/price-workspace.md), `commercial.py`, `price_workspace.py`, `backend/pricing/`.

<a id="capitulo-25"></a>

## 25. Cotización guiada y emisión

### 25.1 Preparación

La pestaña Cotización conduce por cliente/obra, antecedentes, condiciones y PDF real. El checklist enfoca campo faltante y abre el bloque correspondiente. El backend valida RUT, correo, dirección, fecha/vigencia y condiciones; hitos monetarios proceden del motor.

La preparación fija fecha, preferencias, precio y autoridad. Su PDF privado tiene una huella y QR aún sin acceso al cliente. La revisión del humano liga destinatario, hash del archivo y snapshot. Un cambio de obra/condiciones invalida esa preparación y exige otro PDF.

### 25.2 Confirmación y recibo

Emitir recompone la autoridad, compara huellas y bytes y sella exactamente el PDF revisado. La transacción activa la capacidad DOCUMENT, conserva artefacto y crea outbox. Un recibo inmutable por preview permite recuperar respuesta perdida; dos clics concurrentes convergen al mismo sello/recibo. Un rollback limpia solo uploads del intento propio.

La UI usa la llamada canónica de emisión. Las rutas históricas de freeze permanecen para sus consumidores, sin crear caminos visuales duplicados para emitir/compartir. Emitir comercialmente no libera automáticamente OT incompleta.

### 25.3 Vigencia y acceso

La vigencia inicial documentada es 15 días corridos y la revisión privada del PDF 30 minutos, configurables en rangos 1–365 días y 5–60 minutos. Los históricos no reciben retroactivamente una fecha ausente. El acceso efectivo consulta historial append-only de vigencia/revocación.

Regenerar acceso revoca el anterior y crea SHARE para la misma revisión con recibo cifrado/idempotente. No cambia el QR DOCUMENT del PDF histórico: ese QR presenta su revocación real. Lecturas públicas verifican de nuevo estado y usan políticas de no-cache.

Fuente: [emisión guiada](../wiki/product/guided-quotation.md), `backend/documents/{issuance,quotation}.py`.

<a id="capitulo-26"></a>

## 26. DOC-01, alternativas y otros artefactos

DOC-01 es propuesta comercial del fabricante: emisor, cliente, obra, soluciones, elevaciones/cotas, acabado/vidrio, cantidades/precios, condiciones, hitos y aceptación. Usa fuentes autoalojadas y composición adaptada a cantidad; folio, revisión, página y huella quedan en pie.

Preferencias de papel, acento, textos y marca se sellan. Cambiar Ajustes no rehace un artefacto. El renderer proyecta precio sellado sin repricing. Descuento y ajustes por cantidad/redondeo tienen autoridad; Ug o una condición numérica ausentes no se completan con texto histórico.

Puede incluir hasta tres revisiones anteriores completas del mismo proyecto/tenant como alternativas. No se anidan alternativas recursivas ni se suman sus totales al vigente. El QR pertenece a revisión/slot PDF; compartir no reemplaza ese QR. Revocación bloquea acceso y conserva los bytes.

Otros artefactos de dominio incluyen taller/producción, corte, vidrio, compra, recibo, factura/NC internas y actas de terreno. Los documentos industriales consumen autoridad de manufactura; el PDF comercial no se ofrece como lista completa de compra privada. Jobs y acceso firmado producen/abren el archivo correcto de la revisión.

Fuente: [documento comercial](../wiki/product/quotation-document.md), `backend/documents/`, [formatos de corte](../production/FORMATOS-CORTE.md).

<a id="capitulo-27"></a>

## 27. Portal público y acuerdo del cliente

El portal adopta identidad del fabricante y se abre por capacidad ligada a oferta/revisión. Expone la solución sellada, dibujos, medidas, caras, condiciones, documentos y opciones; no consulta catálogo mutable para reinterpretar lo ofrecido ni presenta costos/SKU de compra privados.

El cliente puede revisar alternativas, pedir cambios o decidir con identidad y consentimiento/evidencia. La decisión conserva oferta, solución elegida, hashes y datos personales inmutables; la lectura pública no entrega toda esa evidencia privada. Su calificación jurídica no se infiere de una prueba de software.

La elección se resuelve contra tenant, proyecto, revisión y bloques realmente ofrecidos. La manufactura utiliza la versión íntegra elegida, no el resumen comercial. Proyecto, Hoy, calendario/cobros, factura, compras y liberación siguen esa elección. Una sucesora parte de esa solución y necesita precio/mediciones propios.

| Estado de propuesta | Consecuencia |
|---|---|
| Vigente y pendiente | Lectura/decisión según contrato |
| Elegida/aprobada | Acuerdo sellado; pago solo si habilitado y con saldo |
| Cambios solicitados | Seguimiento en Hoy/campana y nueva revisión humana |
| Vencida/revocada/reemplazada | Bloqueo explícito de acceso/acciones aplicables |
| Histórica con permiso de sucesora | Puede orientar a vigente si ese permiso quedó sellado |

La sucesora pública está desactivada por defecto. Cambiar preferencia hoy no amplía una capacidad histórica. Si existen cobros, factura, compras o producción de otra solución, se exige conciliación antes de cambiar el acuerdo.

El bruto comercial reparte impuesto sellado entre posiciones/servicios/cargos con Decimal. No asume otra tasa ni cambia deuda anterior. Un pago público exige aprobación, vigencia, saldo, moneda y proveedor; el retorno consulta estado del proveedor y no acredita dinero por navegar.

Fuente: [propuesta/acuerdo](../wiki/product/customer-proposals.md), `backend/portal/{proposal_service,payments}.py`, `backend/documents/agreements.py`.

<a id="capitulo-28"></a>

## 28. Cobranza, pagos y recibos

La vista de cobranza por proyecto muestra acuerdo elegido, hitos, cobrado, saldo, exceso y vencimiento. Fecha declarada prevalece; aprobar usa decisión de esa revisión y entregar exige evidencia de unidades. Agenda de visita no crea deuda vencida. Anulados se excluyen del saldo y simulados conservan marca.

Un pago manual guarda fecha local, actor, monto/moneda/evidencia y recibo RC inmutable. F6 vincula número al acuerdo y movimientos. Una anulación conserva historia; una corrección no altera silenciosamente lo emitido.

### 28.1 Flow de la fábrica

Las credenciales se guardan por organización en Conectar Flow. Son distintas de `FLOW_*` de billetera de plataforma. Crear enlace fija revisión, monto, ambiente y contexto; backend verifica token con Flow, monto/pedido/vínculo y usa locks/idempotencia. Callback temprano, replay y recuperación convergen en un movimiento/recibo.

Verificar consulta proveedor; no crea otro cobro. Un pago real en exceso se registra y queda para conciliación, aun si otro movimiento redujo saldo. Flow cobra CLP; otras monedas no se convierten por una tasa supuesta.

### 28.2 Prueba y recordatorio

El simulador no contacta Flow. Capacidad opaca y caducidad limitan monto/estado; una revisión sustituida bloquea confirmar. Movimiento, saldo y RC dicen simulación y no acreditan transferencia.

El dueño puede preparar recordatorio con MiMo. El modelo escribe plantilla con marcadores; montos/fechas vienen del motor. Revisión/clic/confirmación preceden al outbox, y el saldo se comprueba otra vez antes de SMTP. Un mensaje obsoleto o saldo simulado no se transforma en cobranza real.

Fuente: [cobranza](../wiki/product/collections.md), `collections.py`, `backend/projects/{payments,payment_links}.py`.

<a id="capitulo-29"></a>

## 29. Factura, boleta, nota de crédito y SII

Los documentos internos sellan detalle humano y totales del motor. El ajuste de cantidad/unitario explica el total, sin segundo cargo. Hay control de documento por revisión y replay idéntico. Una NC mantiene el original y distingue abono parcial/anulación total.

| Documento/camino | Alcance | Activación |
|---|---|---|
| Factura/boleta/NC internas | Documento interno con leyenda no tributaria | Datos comerciales completos |
| Simulador 33/39/61 | Folio SIM y resultado aceptado/reparos/rechazado separado | No consume CAF, no TED/XML fiscal ni envío SII |
| DTE real 33/61 | Adaptador existente de factura/NC | Certificado/CAF válidos, contribuyente certificado, transporte oficial |
| Boleta tributaria 39 real | No soportada por timbrador existente | Requiere proveedor autorizado que implemente el contrato |

SII real necesita declaración del dueño, certificado vigente y URLs/token del transporte autorizado. Envío/consulta conservan XML/PDF/estado; una respuesta incierta requiere revisión antes de reenviar. Tener un botón o simulación no certifica emisión fiscal productiva.

Fuente: [activación SII](../operations/ACTIVACION.md), `backend/projects/{sii,sii_envio}.py`, [cobranza](../wiki/product/collections.md).

<a id="capitulo-30"></a>

## 30. Liberación y órdenes de trabajo

### 30.1 Preparación industrial

La preparación de producción resuelve la revisión comercial aplicable y la solución íntegra que eligió el cliente. Revisa mediciones de fabricación, bloqueadores, suministro y ruta. La geometría comercial visible no basta para liberar: las dimensiones, reglas, componentes y evidencias necesarias deben estar confirmados en la autoridad que se sella.

Una revisión puede estar emitida y seguir pendiente de fabricación. La confirmación técnica tampoco sustituye el acuerdo comercial elegido. El centro de trabajo conduce al responsable al dato o decisión pendiente, en vez de crear una OT con números completados por defecto.

### 30.2 Qué se crea al liberar

La liberación crea **una OT por posición**. Una revisión de doce posiciones produce doce OT, con la cantidad de unidades de cada posición. La cantidad no obliga a duplicar doce veces una ventana idéntica en el editor. Cada orden conserva revisión, posición, diseño evaluado, materiales, componentes, plan, identidad de piezas y ruta aplicable.

| Elemento conservado | Para qué sirve |
|---|---|
| Proyecto, revisión y posición | Saber qué solución se está fabricando y para qué obra |
| Modelo y evaluación sellados | Reproducir dimensiones, componentes y decisiones técnicas |
| BOM y autoridad de suministro | Comprar, reservar y cortar el material compatible |
| Ruta por serie y centros de trabajo | Determinar el siguiente paso real de esa orden |
| Cantidad/unidades e identidades de piezas | Trazar calidad, bultos, entrega y reposición |
| Actor, fecha, huellas y referencias | Auditar la liberación sin reinterpretarla con el catálogo de hoy |

Una corrección se expresa en revisión, remake o transición autorizada; no modifica la revisión emitida para que parezca que siempre tuvo la medida nueva. Cancelar conserva la orden y su historia. Revisión de material, liberación y cancelación tienen endpoints y permisos propios.

### 30.3 Consulta y documentación

El responsable puede abrir listado/detalle, trazas de OT, revisión y pieza; consultar plan, materiales y pasos; preparar pack de producción; obtener etiquetas y documentación de corte, vidrio y herrajes. El resultado documental se vincula al snapshot de la OT. Una descarga no acredita fabricación ni movimiento de stock.

Fuente: `backend/production/urls.py`, `backend/production/`, [estaciones](../wiki/product/production-stations.md), [guía de revisión](../GUIA-REVISION.md).

<a id="capitulo-31"></a>

## 31. Tablero de planta, estaciones y operario

### 31.1 Tablero y detalle de OT

El tablero ubica la OT en su primer paso abierto. Las columnas provienen de la ruta real; no se presentan estaciones ajenas a esa ruta como avance obligatorio. El jefe ve obra/cliente, unidades, compromiso y causas de bloqueo. El detalle reúne stepper y pestañas operativas; la lista de piezas reutiliza una tabla virtualizada para órdenes grandes.

La misma dirección física identifica la pieza en pantalla, plan, papel y QR. Medidas, función, corte y mecanizado proceden del plan sellado. La UI puede filtrar y mostrar una selección sin cambiar los índices históricos ni el fingerprint del conjunto completo.

### 31.2 Puesto del operario

El operario elige un puesto que se persiste por usuario y organización. La cola sirve solo la estación válida y pasos que puede trabajar. Cambiar de puesto no amplía el rol. Los endpoints comerciales y las proyecciones de dirección/cliente tienen gates propios; la capacidad de leer una OT no concede acceso a costos.

El QR localiza la pieza, su medida y el siguiente paso. **No cambia automáticamente el puesto ni autoriza otra empresa.** La cámara se ofrece según la capacidad real del navegador. Un lector USB o entrada de código permiten el mismo recorrido cuando no hay cámara.

### 31.3 Transiciones y bloqueos

| Acción | Resultado y control |
|---|---|
| Consultar cola | Orden y pasos del puesto/contexto autorizado |
| Iniciar/completar paso | Transición validada contra estado, ruta y dependencias |
| Registrar evidencia o medición | Hecho ligado a OT/pieza/actor; conserva procedencia |
| Bloquear | Exige motivo explícito y lo hace visible al jefe y en Hoy |
| Actualizar estación | Relee detalle, incluso si otra sesión resolvió el bloqueo |
| Completar Corte | Aplica los efectos de material/retazos autorizados e idempotentes |
| Intentar un paso de otra empresa o sin rol | Denegación; el QR no evita la comprobación |

Los pasos generales de taller admiten OWNER, WORKSHOP_MANAGER y OPERATOR. INSTALLER tiene otro alcance para entrega/instalación; no se le concede firma de soldadura, acristalado o QC de taller por poder abrir un trabajo de terreno.

### 31.4 Calidad y reposición

Una medición fallida se registra; bloquear requiere la decisión explícita del operario. El jefe revisa pieza y evidencia, decide rechazo/reposición y confirma el remake. El rechazo puede mantener QC bloqueado sin impedir seleccionar la pieza responsable.

El remake es transaccional e idempotente: la misma clave devuelve la misma OT de reposición. Conserva pieza y conjunto de origen, su motivo y trazabilidad. No reemplaza todo el BOM por una sola pieza ni altera la revisión comercial anterior. Un PASS posterior debe corresponder al trabajo/evidencia correctos; no se transforma un FAIL histórico en un hecho distinto.

Fuente: `backend/production/{views,stations,quality,pieces}.py`, [producción por estación](../wiki/product/production-stations.md).

<a id="capitulo-32"></a>

## 32. Optimización de barras y láminas

### 32.1 Barras

La optimización consume cortes del motor, longitudes disponibles, acabados y suministro compatibles, parámetros de sierra/despunte y retazos elegibles. La identidad física, función y ángulos limitan qué piezas pueden agruparse. Una barra blanca o de otro suministro no cubre por nombre parecido una pieza bicolor.

El algoritmo de barras es **Best Fit Decreasing determinista**, con aritmética exacta. Orden y desempates deben reproducir el plan; no se afirma que encuentre el óptimo global de cualquier problema industrial. El resultado explica barras, secuencia de cortes, pérdidas y material recuperable. Comparar/reoptimizar es una decisión explícita sobre disponibilidad y parámetros actuales.

### 32.2 Láminas

El nesting de `nesting.py` usa guillotina 2D y formatos/parámetros declarados. Los formatos conservan proveedor, sustrato, dimensiones y fuente. Declarar un formato agrega una variante; **no da de alta existencia física**. Falta de formato lleva a su declaración en Catálogo, sin adoptar un tamaño de lámina silencioso.

La orientación, rotación permitida, separaciones y orden dependen de la autoridad de cada material/plan. No se presenta este nesting como CAM de contorno arbitrario ni como postprocesador de una cortadora específica. Vidrio templado se solicita a medida exacta; el permiso de un algoritmo de paneles no autoriza cortar vidrio ya templado.

### 32.3 Plan previsto frente a hecho real

| Concepto | Cuándo existe | Qué acredita |
|---|---|---|
| Necesidad sellada | OT liberada | Material que requiere esa fabricación |
| Plan de corte | Optimización confirmada | Distribución prevista de piezas sobre material |
| Reserva | Acción transaccional de material | Disponibilidad apartada, sin consumo real implícito |
| Medición real del corte | Registro respaldado de planta | Entrada, piezas, pérdida y retazo realmente obtenidos |
| Retazo recuperable previsto | Plan con identidad RT reservada | Destino/identidad anticipados, todavía sin stock útil |
| Retazo físico | Finalización válida de Corte | Material con identidad, dimensiones y rack |

La medición real debe balancear entrada = piezas + pérdida + retazo recuperable y cubrir las barras aplicables. No copia automáticamente el plan como medición de la fábrica.

Fuente: `engine/src/dekopen_engine/{cutting,nesting}.py`, `backend/production/`, [corte y etiquetas](../wiki/product/cut-documents.md).

<a id="capitulo-33"></a>

## 33. Papel de corte, etiquetas, CSV y DXF

### 33.1 Secuencia y precisión compartidas

Los artefactos usan una secuencia física común: barra/orden de corte y, para láminas, Y/X. La agrupación manual conserva autoridad, color, función, largo y ángulos; ordena por primera aparición y mantiene la dirección de cada pieza. El operador no necesita renombrarla al pasar del papel al QR.

El pack de corte apaisado presenta tres barras por página y cierre Decimal, más secciones de padres/refuerzos/junquillos y vidrios. Las etiquetas admiten Carta, A4 o rollo 100 × 50 mm; cada página de rollo es una etiqueta. La próxima estación procede de la ruta y rama material de la pieza. Todas las hojas llevan huella del plan correspondiente.

### 33.2 Identidad RT y efectos de imprimir

Optimizar reserva identidades UUID5/códigos RT derivados del plan. Imprimir solo lee: no asigna códigos nuevos, no inserta stock y no mueve material. Al completar Corte se insertan las identidades previstas con su rack; un replay evita duplicarlas.

Un plan histórico sin esa dirección RT prevista necesita reoptimización explícita antes de Corte. Imprimirlo no reescribe historia. Racks y formatos son declaraciones reales; un histórico sin fuente sigue diciendo Sin dato.

### 33.3 Intercambio genérico

CSV y DXF son exportaciones genéricas documentadas. DXF AC1021 usa UTF-8 y conserva precisión de origen. Los campos/capas y geometrías se deben interpretar según [FORMATOS-CORTE](../production/FORMATOS-CORTE.md). Descargar el archivo no establece compatibilidad con una máquina particular.

El documento comercial resume la venta. El pack industrial y BOM son las autoridades para corte/picking: no se exige encontrar todos los SKU de compra privados en DOC-01 ni se deducen de una elevación comercial.

Fuente: `backend/production/{cut_manifest,cut_documents,cut_labels}.py`, [corte y papel](../wiki/product/cut-documents.md), [formatos](../production/FORMATOS-CORTE.md).

<a id="capitulo-34"></a>

## 34. Mecanizado y CNC

### 34.1 Alcance implementado

DEKOPEN reúne operaciones de mecanizado procedentes de la autoridad de catálogo, las liga a la pieza y al montaje de planta y genera un **intercambio neutro** revisable. Hay workspace de máquinas/herramientas, readiness, comparación/preview, programas, confirmación, archivos y manifiesto. No se afirma un postprocesador propietario ni envío directo a una CNC.

| Autoridad necesaria | Datos que deben estar declarados |
|---|---|
| Pieza y operación | Ámbito anfitrión, cantidad/cobertura, lado/cara y patrón |
| Perfil/montaje | Sección sellada, orientación de carga y origen inicial |
| Máquina | Ejes, controlador, carreras, capacidades y márgenes |
| Herramienta | Tipo/código, diámetro, largo útil, profundidad máxima y operaciones admitidas |
| Sujeción | Mordazas y zonas revisadas para el montaje |
| Coordenadas | X/Y/Z y profundidad con la fuente correspondiente |

### 34.2 Coordenadas y límites físicos

X se expresa desde el extremo inicial de la pieza, incluso para una operación en cara final. Un plano de extremo no equivale a una trayectoria de fresa. Y/Z no se deducen del vano ni de una vista bonita del perfil. Una coordenada, herramienta, profundidad, mordaza o sección desconocidas bloquean lo que depende de ellas.

La readiness distingue lo emitible, avisos y bloqueos, con causa. Un herraje puede conservar su mecanizado **declarado no emitido**: no se completa con una operación aproximada para permitir cerrar la estación.

### 34.3 Preparar y confirmar

El preview fija fingerprint de plan y autoridad. La confirmación bloquea y comprueba vigencia; un replay devuelve los mismos bytes. Revisar montaje o plan puede requerir un programa nuevo, conservando el anterior. Una OT cancelada no genera un programa nuevo.

El manifiesto permite revisar pieza/origen/operaciones frente al manual y un ensayo de planta. Conectar máquina requiere postprocesador declarado por su fabricante y validación física específica. Los datos DEMO de máquina/herramienta no acreditan calibración, colisión segura o producción industrial.

Fuente: `backend/production/`, [autoridad CNC](../wiki/product/cnc-authority.md), [activación de mecanizado](../operations/ACTIVACION.md).

<a id="capitulo-35"></a>

## 35. Compras y proveedores

### 35.1 Necesidades y asignación

Compras parte de necesidades selladas de las OT. Calcula faltantes con existencias, reservas y tránsito, manteniendo esos estados separados. Cantidad, compatibilidad y neto pertenecen al motor/autoridad comercial; una lista DEMO o una referencia visual no acredita precio real de compra.

El proveedor tiene RUT, contacto/correo, materiales y elegibilidad con fuente. Cambiar su ficha no reinterpreta una OC histórica. La asignación se revisa antes de crear la orden: material, código comercial, unidad, cantidad y precio deben coincidir con la necesidad autorizada.

Los lectores de Compras son OWNER, WORKSHOP_MANAGER y ESTIMATOR; la escritura corresponde a OWNER y WORKSHOP_MANAGER. El alcance de lectura no evita los recortes de información confidencial de cada proyección.

### 35.2 Orden de compra y envío

La OC conserva líneas, proveedor, cantidades, condiciones/autoridad y sus documentos. Prepararla no prueba aceptación del proveedor ni tránsito real. El envío tiene revisión de destinatario/PDF y clic humano; utiliza la outbox cifrada. Una OC cancelada no se envía.

| Acción | Cambio funcional | Evidencia preservada |
|---|---|---|
| Preparar necesidades | Calcula faltantes por OT y material | Fuente sellada y estado de abastecimiento |
| Asignar proveedor/precio | Propone compra compatible | Identidad comercial y fuente |
| Crear OC | Sella el encargo de compra | Líneas, autoridad, actor y documento |
| Enviar | Despacha intención revisada por correo | Contenido, destinatario, SHA e intentos |
| Recibir parcialmente | Incorpora solo unidades útiles | Guía, fecha, lote, rack, actor y daño |
| Cancelar saldo | Libera únicamente lo no recibido | Recepciones y orden anterior intactas |
| Recomprar | Crea demanda/orden correctas para el faltante | Procedencia y separación de compra anterior |

### 35.3 Recepción, daño y excedente

La recepción registra guía, fecha, lote, rack y actor. Lo dañado no ingresa como material útil. Una recepción parcial mantiene el faltante; el exceso exige confirmación y tratamiento explícitos. La reserva/compra/recepción no se confunden con consumo de fabricación.

Cancelar libera el saldo no recibido, conservando material y evidencia ya recibidos. Una cantidad fuera de la capacidad sellada exige revisar planificación o emitir una revisión adicional; no se modifica una OC para borrar el hecho anterior.

Fuente: `backend/purchasing/`, `frontend/src/features/purchasing/`, [compras e inventario](../wiki/product/purchasing-inventory.md), [activación P15](../operations/ACTIVACION.md).

<a id="capitulo-36"></a>

## 36. Inventario, movimientos y retazos

### 36.1 Libro de material

El inventario distingue suministro, variante física, acabado, unidad y ubicación. Los movimientos conservan procedencia, cantidad, referencia y actor. Existencia, reserva, tránsito, consumo, devolución, pérdida y recuperación son hechos diferentes.

OWNER, ESTIMATOR, WORKSHOP_MANAGER y OPERATOR tienen lecturas autorizadas. OWNER y WORKSHOP_MANAGER escriben. El operario que consulta stock no recibe permiso para recepcionar compras ni mover/desechar retazos por ese acceso.

### 36.2 Reserva y disponibilidad

Una reserva vincula material compatible a demanda de OT y se valida transaccionalmente. Reservar no acredita consumo. Reoptimizar con retazos vuelve a comprobar la disponibilidad y estado actuales; la misma pieza física no queda disponible simultáneamente para dos órdenes por una pantalla desactualizada.

La identidad comercial usada por el ledger está protegida. Un formato físicamente incompatible necesita otro código; igual área no basta para sustituir un formato por otro. El orden de variantes mantiene dimensiones y autoridad como desempate determinista.

### 36.3 Retazos físicos

RT identifica una pieza física con suministro, medida, acabado, origen, estado y rack. El retazo manual debe corresponder a una autoridad real: no admite identidades o medidas arbitrarias para cubrir una orden. Mover, reservar y desechar son acciones auditables diferentes.

El rack inicial y días de alerta se configuran en Producción. La etiqueta/QR permite localizar y consultar su origen. El código reservado en el plan coincide con el creado al completar Corte. Imprimir de nuevo conserva el código y no vuelve a incorporar material.

Una fuente o medida ausentes conservan Sin dato y bloquean lo que necesita esa autoridad. La contabilidad de costos trata consumo y crédito recuperable explícitamente; un retazo no se valora dos veces por aparecer en salida y luego en otra OT.

Fuente: `backend/inventory/`, `backend/inventory/sheet_formats.py`, [compras/inventario](../wiki/product/purchasing-inventory.md), [analítica](../wiki/product/decision-analytics.md).

<a id="capitulo-37"></a>

## 37. Embalaje, despacho, entrega e instalación

### 37.1 Preparar salida

El embalaje vincula unidades/piezas a bultos identificables. El despacho conserva esa composición, obra, revisión y destino. Hay etiquetas, guía/nota de despacho, cancelación documental y caminos de documento DTE sujetos a su propia activación fiscal.

El responsable planifica fecha, franja y equipo, registra QR de bultos y confirma salida. Agenda y salida son hechos separados. Una guía emitida tampoco demuestra que el cliente recibió cada unidad.

### 37.2 Entrega e instalación

La recepción puede ser parcial por unidades. La confirmación conserva evidencia y actor; las acciones/recibos idempotentes recuperan una respuesta perdida. La instalación registra su hecho y documentos específicos, sin convertir una visita de servicio en instalación original.

Las asignaciones controlan qué ve y puede confirmar el instalador. El acceso firmado a un archivo no es una asignación de trabajo. Las lecturas de cliente/dirección y las transiciones se proyectan según la persona y el contexto autorizado.

| Hecho | Efecto posible en otros módulos |
|---|---|
| Visita programada | Agenda del instalador y seguimiento del jefe |
| Salida confirmada | Trazabilidad logística y estado de despacho |
| Unidad recibida con firma | Evidencia de entrega, hitos que dependan de ella y garantía según condición sellada |
| Instalación firmada | Evidencia por unidad y comienzo de garantía cuando esa es la regla |
| Acta de servicio | Seguimiento de postventa; no inventa entrega/instalación anterior |
| Incidencia | Diagnóstico, reposición, compra adicional o servicio bajo decisión humana |

Fuente: `backend/production/urls.py`, `backend/production/field_views.py`, [terreno](../wiki/product/field-work.md).

<a id="capitulo-38"></a>

## 38. Terreno, trabajo sin red y postventa

### 38.1 Agenda y evidencia

La superficie de terreno reúne visitas asignadas, unidades, contexto sellado, mediciones, fotos, firma, actas e incidencias. VIS, INC y ACT son códigos humanos por organización. El instalador opera solo sus asignaciones; oficina/jefe revisan y diagnostican bajo su propio rol.

Las fotos y firmas se relacionan con el hecho que documentan. El acta sellada conserva contenido y recibo; una corrección añade una revisión/evidencia nueva en lugar de editar lo ya firmado. Las URLs de activos son privadas y autorizadas.

### 38.2 Cola local y sincronización

El teléfono usa cola local ligada a actor y organización. Debe abrir la agenda con red antes de llevar esa información a un lugar sin señal. Fotos/firmas pendientes permanecen hasta sincronizar. Logout o cambio de contexto limpian la cola privada correspondiente.

El service worker conserva recursos públicos de aplicación/código/fuentes. No cachea API, Auth, Storage ni documentos privados. Esa separación permite cargar la superficie; no permite consultar cualquier proyecto sin red ni demuestra que las acciones pendientes ya llegaron al servidor.

Al reconectar, el servidor revalida membresía, asignación y MFA según política. Una revocación impide el replay autorizado; no borra físicamente una copia que permanece en un teléfono desconectado. Reintentar tras respuesta perdida conserva un único recibo/resultado por clave.

### 38.3 Medición y rectificación

Una medición de terreno se compara con la autoridad comercial/fabricación. El diff explica dimensiones y delta de precio del motor, y puede crear un borrador correctivo con procedencia. La revisión aprobada y su fabricación no cambian por recibir una foto o nuevo valor.

La revisión sucesora necesita sus propias confirmaciones y precio. El hecho que originó el cambio permanece trazable, incluyendo quién midió y la evidencia firmada.

### 38.4 Garantía e incidencias

La garantía conserva días e inicio declarados antes de emitir. El primer hecho firmado pertinente por unidad fija el inicio cuando corresponde a entrega/instalación. Texto libre de condiciones no se interpreta como fecha de garantía.

El jefe registra diagnóstico y decide remake, compra adicional o servicio; el cierre exige evidencia. La incidencia conserva unidad, revisión y acción responsable. El seguimiento analítico usa esas fechas/hechos, sin calcular una garantía retroactiva a partir de la preferencia actual.

Fuente: `backend/production/field_views.py`, `frontend/src/features/field/`, [terreno y postventa](../wiki/product/field-work.md), [activación P23](../operations/ACTIVACION.md).

<a id="capitulo-39"></a>

## 39. Analítica, costos reales y explicación de desvíos

### 39.1 Cuatro preguntas operativas

Analítica organiza ventas, margen, planta y terreno para decidir sobre obras y procesos. OWNER y WORKSHOP_MANAGER acceden a costos. No se asigna ese rol a quien solo necesita cortar/instalar para que vea un gráfico.

| Pregunta | Cohorte/autoridad | Lectura útil |
|---|---|---|
| ¿Qué se vende y qué se aprueba? | Emisión y revisiones/acuerdos | Volumen, venta y estado comercial con detalle |
| ¿Qué margen se consigue realmente? | Venta elegida y cierre de costos respaldado | Cotizado frente a real y causas del desvío |
| ¿Dónde se atasca la planta? | Creación de OT, ruta, pasos y hechos | Avance/bloqueos y evidencia de corte/producción |
| ¿Qué pasa en terreno/postventa? | Agenda de instalación y registro de incidencia | Visitas, cumplimiento y casos con contexto |

Las cohortes usan emisión, creación de OT, agenda de instalación o registro de incidencia según la pregunta. Los estados son los vigentes al consultar; no se promete reconstrucción histórica de cada estado por seleccionar un período. La consulta usa zona horaria de la empresa.

### 39.2 Qué cuenta como costo real

El costo real combina consumo, pérdida adicional, devolución y retazos consumidos con tarifas de su unidad; horas efectivas por tarifa de personas; otros costos y crédito recuperable. Una pérdida ya incluida en consumo no se suma otra vez. Un descuento incluido en venta neta tampoco vuelve a descontarse en el puente.

Cada tarifa conserva moneda, unidad y fuente: factura, parte de trabajo o medición. Cero solo es dato si tiene respaldo. Reserva no es consumo; tiempo previsto no es hora efectiva; el plan de corte no es pérdida medida.

La entrada real de barra debe cerrar exactamente entre piezas, pérdida —incluida sierra/despuntes— y retazo recuperable, con cobertura completa. No se aplica un porcentaje inventado para compensar una medición incompleta.

### 39.3 Cierre y revisiones

Preview reúne cobertura, pendientes y costo. Confirmar conserva un cierre inmutable; registrar revisión de costos añade evidencia. Una corrección o un movimiento posterior puede invalidar que ese cierre sea el más actual, sin alterar los bytes ni la lectura histórica que guardó.

El puente del desvío separa causas hasta sus movimientos/fuentes. F6 permite abrir «¿De dónde sale?»; CSV conserva el contexto y la moneda. Sin dato permanece distinto de cero. No se suman CLP y USD ni se aplica un FX ausente para completar un gráfico.

Fuente: `engine/src/dekopen_engine/analytics.py`, `backend/analytics/`, `frontend/src/features/analytics/`, [analítica para decidir](../wiki/product/decision-analytics.md).

<a id="capitulo-40"></a>

## 40. Inteligencia artificial: capacidades y autoridad

### 40.1 Qué puede hacer

La IA interpreta una petición, consulta referencias autorizadas, usa herramientas del motor y entrega respuesta o propuesta estructurada. Puede ayudar a diseñar, cambiar varias posiciones, explicar precio/bloqueadores, encontrar opciones de catálogo y preparar caminos de emisión, producción, compra o pago. La mutación usa las mismas operaciones que la UI; no existe un segundo motor numérico del modelo.

| Capacidad configurada | Uso | Autoridad que debe conservar |
|---|---|---|
| `design` | Asistencia de diseño y operaciones paramétricas | Modelo, geometría, catálogo y evaluación del motor |
| `agent` | Objetivos con varias consultas/herramientas y propuesta | Referencias observadas, límites de ejecución y confirmación |
| `context` | Preguntas sobre contexto de una superficie | Permisos y lectura vigente del usuario/organización |
| `catalog` | Lectura/ingesta asistida de fuentes técnicas | Documento/fuente y revisión humana antes de publicar |

El dueño con MFA configura proveedor/modelo por capacidad. La elección guardada prevalece sobre la sugerencia del entorno. La credencial solo existe en servidor/worker. MiMo real no se sustituye por un mock porque DEBUG esté activo; una ruta de prueba requiere su habilitación y selección explícitas.

### 40.2 Herramientas y referencias

El conjunto documentado incluye `calculate_position`, `validate_position`, `price_position`, `price_project`, `explain_price_delta`, `list_catalog_options`, `get_blockers`, `simulate_ops` y `preview_project_operations`. Calculan/consultan autoridad real y devuelven referencias. El agente no puede adivinar un identificador y usarlo como prueba de pertenencia.

Las respuestas comerciales eliminan costos privados. Si la venta no se puede resolver, conservan `net: null`, causa y acción siguiente. Un cero histórico de borrador no acredita un precio aplicado. Precio antes/después y Δ se cuantizan a la moneda para que cierren con la lectura visible; en lotes se conserva unitario exacto antes de multiplicar por cantidad.

### 40.3 De petición a propuesta

1. La superficie construye contexto del actor, empresa y entidades autorizadas.
2. El agente identifica la intención y consulta herramientas permitidas.
3. La propuesta expresa operaciones tipadas o una aclaración con opciones reales.
4. Simular calcula modelo, evaluación, diff y precio indicativo sin escribir.
5. Preview del proyecto fija el estado/firma de las posiciones afectadas.
6. El humano revisa y aplica con clave de idempotencia.
7. El recibo permite consultar aplicado/deshecho sin repetir escritura.
8. Deshacer restaura autoridad original si ninguna edición posterior lo volvió obsoleto.

El preview no es una modificación aplicada. Emisión, liberación, compra y enlace de pago preparan su ruta; la acción consecuente exige el clic humano en la superficie correspondiente.

### 40.4 Grounding numérico y aclaración

El verificador acepta medidas explícitas pedidas por el usuario y cifras respaldadas por contexto/herramientas del turno. Un incremento declara el delta y el motor deriva el resultado. No se autorizan números inventados porque la explicación suene plausible.

`clarify {question, options[]}` presenta alternativas del catálogo; los chips continúan el mismo trabajo. Si falta una altura de antepecho no se ofrecen alturas sin fuente. Si el SKU ya satisface la intención, se puede explicar ese resultado sin producir una edición artificial.

### 40.5 Registro compartido

El registro actual contiene **55 operaciones: 38 de diseño, 2 de posición, 11 de proyecto y 4 de preparación**. El máximo por lote es 50. El anexo A enumera cada nombre, parámetros y precondición del contrato. El registro expuesto por API, el motor y la UI comparten ese vocabulario; las guardas adicionales de permiso/estado pertenecen al backend y a cada manejador.

Fuente: `engine/src/dekopen_engine/design_operations.py`, `backend/ai_gateway/`, [operaciones](../ai/OPERACIONES.md), [asistente](../wiki/product/assistant-work.md).

<a id="capitulo-41"></a>

## 41. Transporte de IA, presupuesto y trazabilidad

### 41.1 Conexión y contenido

MiMo admite herramientas y visión en el adaptador. El transporte de catálogo extrae texto y renderiza páginas escaneadas para visión. Un PDF directo rechazado por el proveedor no se presenta como leído: se usa texto/páginas según el contrato. Lectura correcta de una ficha no certifica sus medidas ni autoriza publicarla.

Los errores de proveedor, timeout y respuestas incompatibles tienen estados/causas. Hay hasta dos reintentos transitorios bajo la misma clave/plazo; no se promete que el proveedor responda siempre. La configuración actual de pasos/consultas/rondas se valida al iniciar y registra consumo/latencia por trabajo.

| Límite de agente documentado | Valor inicial | Máximo configurable |
|---|---|---|
| Pasos | 20 | 50 |
| Consultas | 6 | 12 |
| Rondas | 6 | 12 |
| Plazo total | 180 s | 600 s |

Son límites de configuración, no mediciones de rapidez ni garantía de resolver cualquier pedido dentro de ese tiempo. Se controlan con `AI_AGENT_MAX_STEPS`, `AI_AGENT_MAX_QUERIES`, `AI_AGENT_MAX_ROUNDS` y `AI_AGENT_TOTAL_TIMEOUT_S`.

### 41.2 Créditos y costo de proveedor

La IA considera derechos del plan, billetera y presupuesto mensual en créditos. Las reservas concurrentes evitan que dos trabajos consuman el mismo saldo disponible. El débito se liga a auditoría y es inmutable/idempotente; un retry no debe cobrar otra vez la misma operación.

El período de presupuesto del flujo documentado usa America/Santiago. Tokens, créditos y dinero son unidades distintas. Los tokens requieren medición completa; el costo requiere tarifas declaradas de entrada/salida en USD por millón, selladas para esa llamada. Si falta medición o tarifa, se muestra **Sin dato**. No se incorpora un precio público supuesto del proveedor ni se modifica el costo de llamadas anteriores al declarar otra tarifa.

### 41.3 Auditoría disponible

Los trabajos conservan capacidad, proveedor/modelo, estado, fases, consultas/herramientas, operaciones, referencias y latencia. «¿De dónde sale?» abre esa procedencia. Un resultado final con texto respaldado no implica que se ejecutó el artefacto que pidió el usuario; el outcome de negocio se analiza aparte.

### 41.4 Resultado histórico P20 de proveedor real

La corrida **P20, ref `484182126c4f7ba32ba41f3e77b1a1ba31faf04c`**, contiene 26 solicitudes de dueño, 49 intercambios y 89 eventos.

| Grupo | PASA / casos | Lectura |
|---|---|---|
| Editor | 12/13 | Un caso falló por HTTP 524 |
| Proyecto | 6/8 | Una afirmación estructurada ausente y un fallo de proveedor |
| Planta | 1/3 | Dos pedidos no produjeron el artefacto de corte/compra requerido |
| General | 2/2 | Ambos casos cumplieron su oráculo |
| Total | **21/26** | Cinco fallos conservados, no ocultados |
| Editor + proyecto | **18/21; 85,71 %** | Subconjunto usado en la aceptación, no tasa universal de IA |

| Caso que no pasó | Causa registrada |
|---|---|
| E04 | HTTP 524 |
| J04 | Claim estructurado requerido ausente |
| J08 | Fallo del proveedor |
| F02 | Artefacto de corte requerido ausente |
| F03 | Artefacto de compra requerido ausente |

La auditoría de 24 respuestas finales registró **cero cifras finales sin respaldo y cero acciones consecuentes automáticas**. Dos rondas rechazadas y dos errores sin respuesta final permanecen en la evidencia. La medición anterior de IA3 —22/26— es otra corrida y no sustituye este resultado final.

Estas cifras acreditan esa muestra y su ref. No son una consulta nueva de este informe ni demuestran disponibilidad de MiMo en la sesión abierta del dueño.

Fuente: [proveedor IA](../wiki/product/ai-provider.md), [baseline de resultados](../wiki/quality/ai-outcome-baseline.md), [aceptación final](../redesign/acceptance-2026-10-12.md).

<a id="capitulo-42"></a>

## 42. Asistente contextual, Orb y trabajos

### 42.1 Presencia por contexto

El asistente conserva conversación/trabajo por actor, organización y contexto estable de superficie. Orb recupera el último trabajo pertinente; no decide que desapareció por quedar fuera de las últimas treinta filas del listado. Cambiar de proyecto o tenant cambia la presencia autorizada.

El dock de escritorio tiene ancho de 400 px. Muestra fases, respuestas, referencias, diffs y artefactos reales. Una preview usa el renderer y la evaluación disponibles; no dibuja una ventana distinta solo para acompañar el texto del modelo.

### 42.2 Decisiones y recuperación

La UI separa propuesta, aplicado y deshecho. Recargar vuelve a consultar el recibo; no repite aplicar por ausencia de estado local. Una edición posterior bloquea undo obsoleto con causa. Continuar una aclaración reutiliza su trabajo/referencias.

Cancelar puede solicitar interrupción incluso desde RUNNING, según la fase. No se declara cancelada una mutación consecuente ya confirmada por la sola desaparición del dock. Reintentar conversación usa su ruta privada y revalida contexto; el retry genérico del worker rechaza esa variante.

### 42.3 Lista de trabajos

Trabajos permite consultar estado/fases/resultados, filtrar capacidad y abrir evidencia. El acceso es privado al usuario/tenant/contexto que corresponde. Un job fallido muestra causa y recuperación disponible; no se convierte en éxito porque quedó un mensaje parcial del proveedor.

Fuente: `backend/ai_gateway/jobs.py`, `backend/jobs/`, `frontend/src/features/{assistant,jobs}/`, [asistente y trabajos](../wiki/product/assistant-work.md).

<a id="capitulo-43"></a>

## 43. Hoy, campana, búsqueda y seguimiento

Hoy reúne tareas según su consecuencia: aprobación requerida, cotización/acuerdo, material, bloqueo de planta, visita o decisión pendiente. La persona entra por su función y llega al objeto que necesita resolver. Un badge o tarea no reemplaza la comprobación actual del objeto al abrirlo.

La campana conserva avisos y estado de lectura. Aprobar/rechazar una solicitud de margen devuelve decisión/comentario al solicitante; marcar leído es una acción distinta. La ruta contextual lleva a proyecto/posición/OT/visita según el aviso.

La búsqueda encuentra entidades con códigos/nombres humanos y contexto autorizado. No es un buscador global de todas las organizaciones. El código legible no es una contraseña y la referencia buscada debe pasar los mismos permisos del endpoint de detalle.

Las automatizaciones pueden actualizar preparaciones/avisos a partir de hechos reales, pero no se publicitan como compra, correo o pago ejecutados sin intervención. Un motivo de bloqueo visible permite al jefe decidir el siguiente paso.

Fuente: `backend/search/`, `backend/projects/`, `backend/notifications/`, `frontend/src/app/navigation.ts`, [Hoy y flujo](../wiki/product/today-workflow.md), [direcciones humanas](../wiki/product/human-addresses.md).

<a id="capitulo-44"></a>

## 44. Worker, jobs durables y automatizaciones internas

### 44.1 Qué delega la aplicación

El worker procesa jobs registrados y validados: generación de artefactos, entrega de correo y derivaciones internas, además del flujo privado de IA que corresponde. Cada tipo declara roles, payload y manejador. Las autorizaciones de payload pueden restringir un tipo más allá de su lista general de roles.

El job conserva organización, creador, intento y máximo, lease y estado. El worker reclama trabajo y mantiene heartbeat. Un error permanente de permiso, contrato o estado se marca FAILED sin gastar reintentos que no pueden arreglarlo. La vista de progreso comunica fases y resultado; no demuestra una conexión externa por sí sola.

### 44.2 Eventos y preparaciones

`automations.emit` conserva deduplicación/referencias y se usa dentro de transacción/savepoint. Es best effort para que un fallo al encolar no deshaga un freeze, pago o paso ya válido. Los manejadores releen el estado actual; una tarea desactualizada no conserva autoridad solo porque nació de un evento válido.

Los handlers incluyen previsión/preparación de producción, tarea de compra, tarea de catálogo, actualización comercial y avance de paso. Estos efectos orientan/derivan el flujo autorizado. No equivalen a enviar una OC a terceros, cobrar o emitir un documento fiscal sin el clic/contrato correspondiente.

### 44.3 Operación y fallos

API funcionando y worker detenido son estados diferentes: puede haber páginas disponibles y trabajos pendientes. La recuperación exige causa, contexto e idempotencia; reiniciar no autoriza repetir cualquier efecto externo. Roles de backend y claims de job se resuelven desde autoridad persistida, no desde un `org_id` arbitrario que envíe el navegador.

Fuente: `backend/jobs/{registry,worker,handlers}.py`, `backend/automations/{service,handlers}.py`, `backend/jobs/management/commands/runjobs.py`.

<a id="capitulo-45"></a>

## 45. Correo, identidad del remitente y recuperación

### 45.1 Dos transportes

Los mensajes comerciales/notificaciones salen del worker Django. Magic Link y verificación de acceso salen de Supabase Auth. Localmente usan Mailpit; el dominio propio exige configurar ambos transportes. Ver una cotización en Mailpit no demuestra entrega al correo real del cliente.

La identidad del fabricante —nombre, logo, color, emisor y pies— se conserva según documento/intención. Un color sin contraste AA cae al valor definido con aviso. Cambiar la marca actual no rehace una revisión antigua ni su correo sellado.

### 45.2 Preparación y envío humano

La outbox cifra contenido sensible y capacidades, conserva destinatario y SHA del PDF revisado. Cotización, comprobante, invitación, OC y avisos usan su contrato de preparación y elegibilidad. El dueño revisa el PDF/preview real y confirma enviar donde se exige.

Antes de SMTP se comprueba estado: cotización reemplazada/vencida, pago anulado u OC cancelada no se envían como vigentes. Una respuesta perdida conserva la misma intención e identificador; recargar no debe crear otro correo silencioso.

### 45.3 Estados de entrega

| Estado/condición | Significado | Recuperación |
|---|---|---|
| Preparado/en cola | Intención guardada, aún sin acreditar contacto SMTP | Worker procesa con su lease |
| DISPATCHING | Intento guardado antes de contactar SMTP | Evita que otro worker lo envíe simultáneamente |
| FAILED antes de contacto | Fallo confirmado sin entrega SMTP | Resolver causa y retry autorizado |
| UNCERTAIN | Respuesta perdida/interrupción con entrega incierta | Humano revisa proveedor/destinatario antes de reenviar |
| SENT | Servidor SMTP aceptó el mensaje | No acredita lectura ni entrega final |
| Enlace vencido/revocado | La capacidad histórica ya no permite ese acceso | Preparar/revisar otro correo con enlace nuevo; conservar anterior |

«Comprobé que no llegó; reenviar» registra otro intento del mismo envío con contenido/destinatario/identificador conservados. No hay retry automático de una entrega dudosa. SMTP no garantiza exactamente una entrega, y el sistema hace visible esa incertidumbre.

### 45.4 Seguridad de activación

SMTP externo exige TLS, dominio/remitente y SPF/DKIM/DMARC. `MAIL_ENCRYPTION_KEY` debe ser estable e igual en backend/worker: protege outbox y capacidades. Cambiarla sin conservar la anterior puede volver ilegibles pendientes. Los enlaces/capacidades no se publican en jobs, logs ni este informe.

Fuente: `backend/notifications/`, [marca/remitente](../wiki/product/brand-identity.md), [activación de correo](../operations/ACTIVACION.md).

<a id="capitulo-46"></a>

## 46. Billetera, planes y comercio de la plataforma

### 46.1 Separación comercial

La billetera y suscripción pagan derechos/créditos de DEKOPEN. Los cobros del proyecto pagan a la fábrica por la obra. Ambos usan estructuras e integraciones separadas: las variables `FLOW_*` de plataforma no activan el Flow guardado por una organización para sus clientes.

El catálogo de planes incluye STARTER, PRO, BUSINESS y BUSINESS_2X, con reglas de TRIAL y derechos de IA. No se fijan aquí precios/cuotas comerciales a partir del nombre; la oferta provisionada y la política vigente son la autoridad. El plan manual conserva las funciones manuales cuando no hay derecho/saldo IA.

### 46.2 Saldo y derechos

La billetera mantiene ledger inmutable, lotes de créditos, expiración y movimientos. Un débito exige auditoría, derecho y saldo; la misma auditoría/clave no debita dos veces. Consumo de lotes y balance se serializan por organización. Una inconsistencia muestra causa en vez de inventar saldo.

La conciliación incorpora grants debidos, expiración y ciclo de plan. No depende de acertar un cron en un segundo exacto para que un derecho vencido siga protegido. El listado visible de movimientos/pagos puede estar acotado; eso no borra el ledger ni limita las comprobaciones de autoridad a esa pantalla.

### 46.3 Ofertas, checkout y suscripciones

El dueño selecciona una oferta aprobada/provisionada. El navegador no elige monto, tipo de cambio, moneda o identidad de suscripción arbitrarios. Un pack fija créditos/comercial y prepara el pago. La suscripción nativa liga cliente, plan de proveedor, ambiente, importe CLP, período y política.

Si debe registrar medio de pago, el retorno se verifica con proveedor. Preparar/dispatch/recover conserva intenciones e idempotencia. Listas parciales de suscripciones no prueban ausencia: la reconciliación exige paginación completa acotada e identidad comercial compatible.

### 46.4 Cambios y administración

Hay preview/confirmación/abandono de cambio, sincronización, reconciliación y caminos de refund/registro con intención persistida. Los comandos administrativos provisionan oferta, reconcilian y preparan/despachan devolución bajo el contrato. No se presentan como libre edición de términos comerciales desde un endpoint público.

La activación productiva de Flow, dominio y políticas es independiente del simulador y del saldo del fixture. Este informe no acredita una suscripción pagada real ni una devolución externa nueva.

Fuente: `backend/billing/{wallet,commerce,offers,changes,native_subscriptions,lifecycle,settlement}.py`, `engine/src/dekopen_engine/billing.py`, [activación Flow](../operations/ACTIVACION.md).

<a id="capitulo-47"></a>

## 47. Presentación, accesibilidad y uso por dispositivo

### 47.1 Identidad y lectura técnica

La constitución vigente regula producto: tipografía, espaciado, contraste, jerarquía, firmas físicas, significado de estado y trazabilidad. La interfaz usa números del motor y códigos humanos, con unidades/moneda. «Sin dato» es un estado informativo; no es cero ni un permiso para terminar fabricación.

Las superficies dan una acción real para su tarea: editar, revisar, aplicar, emitir, recibir, bloquear o confirmar. La explicación F6 conserva fuente/causa. La marca de la fábrica acompaña sus documentos/portal; la aplicación conserva su identidad de producto donde corresponde.

### 47.2 Escritorio, tablet y móvil

El editor adapta densidad y controles por tamaño, con límites de edición/lectura descritos en su sección. Taller y terreno favorecen objetivos táctiles y tarea concreta. Portal, acceso e inicio tienen sus recorridos móviles. Los PDF conservan papel propio, independiente del tema claro/oscuro del navegador.

La evidencia editorial histórica cubre claro/oscuro a 1440×900, 1280×800 y 1024×768; 390×844 en inicio, portal y workshop. Esa matriz no demuestra soporte perfecto de todos los dispositivos, WebGL o cámara de Brave. No se ejecutó una revisión nueva del navegador para redactar este informe.

### 47.3 Vacíos, errores y recuperación

Las lecturas distinguen carga, vacío, error y dato faltante. El editor puede reintentar lectura sobre el mismo ID/tenant. Nombres largos y tablas grandes usan sus componentes adaptados/virtualizados. Confirmaciones y recibos evitan atribuir a una animación o toast el éxito de una operación persistida.

Los controles de teclado, títulos/etiquetas accesibles, contraste y estados son parte del pase editorial R1–R20. La aceptación histórica documenta correcciones específicas; no se presenta una cifra agregada como garantía universal de accesibilidad.

### 47.4 Página pública y desarrollo

Existen entrada pública, marca, acceso y portal, además de superficies DEV de componentes. DEV no es una función comercial ni una vía para sortear permisos. Las rutas literales se inventarían en el anexo E con su fuente y contexto; el build productivo excluye rutas DEV según su guardado/configuración.

Fuente: [constitución](../design/CONSTITUCION.md), [design system](../wiki/product/design-system.md), `frontend/src/App.tsx`, [aceptación editorial](../redesign/acceptance-2026-10-12.md).

<a id="capitulo-48"></a>

## 48. Arquitectura técnica y contrato API

### 48.1 Motor puro

`engine/src/dekopen_engine/` tiene 55 módulos Python versionados en el ref examinado. No realiza I/O, HTTP ni acceso Django/DB. Recibe entradas estructuradas y autoridad de catálogo; devuelve geometría, issues, materiales, precios y proyecciones. Usa Decimal para milímetros y dinero; la precisión de una representación visual no sustituye la dimensión de fabricación.

El catálogo está fuera de las fórmulas como autoridad versionada. Las fórmulas tienen golden cases; regenerar esos casos no es una forma de aprobar una regresión. El anexo C ofrece módulo, propósito declarado y símbolos públicos para localizar cada capacidad sin abrir todo el repositorio.

### 48.2 Backend por dominio

Django constituye el borde HTTP y orquesta permisos/transacciones. Los dominios funcionales incluyen autenticación, proyectos, catálogo/ingesta, precios, documentos/portal, producción, compras, inventario, terreno, analítica, IA/jobs, correo y billing de plataforma. Números persistidos y documentos proceden de autoridad calculada/sellada, no de fórmulas paralelas en cada vista.

Las rutas se montan en `backend/config/urls.py`. `/health/live/` y `/health/ready/` pertenecen a operación; `/api/schema/` expone el contrato. Su existencia no acredita que hosting, correo, proveedor o todas las bases respondan en este momento.

### 48.3 OpenAPI y cliente

`backend/openapi.yaml` documenta 334 operaciones sobre 265 paths y 899 componentes de schema. Estos componentes incluyen request/response, enums, variantes y serializers parciales; no son 899 funciones de producto. Orval genera el cliente de `frontend/src/api/generated/`.

El anexo B enumera **todas las operaciones de ese contrato**, con método, ruta, `operationId`, parámetros, request, resultado y seguridad declarada. Una fila no acredita una prueba realizada. Los permisos concretos se comprueban en vistas/servicios/RLS; la presencia de Bearer en OpenAPI no describe por sí sola todos los roles admitidos.

### 48.4 Frontend

React 18, TypeScript y Vite organizan superficies en `frontend/src/features/`. La aplicación privada y el portal público tienen entradas/contextos distintos. Lazy loading evita cargar todo el editor en acceso público. Componentes, hooks, renderer y traducciones hacen visible la autoridad calculada; los serializers/generated types limitan divergencias de contrato.

El inventario de rutas del anexo E comprende literales de `App.tsx` y `PublicProposalApp.tsx`. Incluye redirecciones, alias, comodines y DEV: no se cuenta como número de pantallas independientes. Los controles de role/ReadyGuard y autorización backend siguen vigentes al entrar por URL.

Fuente: `AGENTS.md`, `backend/config/urls.py`, `frontend/src/{App,PrivateApplication}.tsx`, [invariantes](../ENGINEERING.md).

<a id="capitulo-49"></a>

## 49. Persistencia, inmutabilidad y concurrencia

### 49.1 Esquema y aislamiento

La fuente de esquema es `supabase/migrations/`: 183 archivos versionados. El inventario estático encuentra 149 nombres distintos en declaraciones CREATE TABLE. Algunas migraciones transforman estructuras anteriores; esta cifra no es una consulta de tablas/filas de una DB viva.

El anexo F localiza cada declaración y su migración. Las tablas de tenant conservan organización y RLS. Tablas compartidas/de infraestructura tienen contratos propios; no se interpreta la lista como si todas debieran admitir el mismo acceso o la misma política.

### 49.2 Qué permanece sellado

| Autoridad | Por qué se conserva |
|---|---|
| Revisión emitida y precio aplicado/sellado | Cambiar tarifa o catálogo mañana no altera una venta anterior |
| PDF/XML/artefacto y hash | Permite recuperar exactamente el archivo revisado/emitido |
| Decisión/acuerdo del cliente | Vincula solución, evidencia y deuda aplicables |
| Pago/recibo e intento externo | Evita duplicación y conserva corrección/anulación |
| OC/recepción y ledger de stock | No desaparece material recibido al cancelar saldo |
| Plan de corte/programa CNC | Reoptimización crea otra autoridad identificable |
| Medición, acta y firma | Rectificación añade hechos; no reescribe una firma anterior |
| Cierre de costos y auditoría IA | Nuevas fuentes/correcciones no cambian el histórico |

Los snapshots contienen la autoridad necesaria para reproducir el hecho. El catálogo actual se usa en propuestas nuevas, sin reinterpretar automáticamente un histórico.

### 49.3 Idempotencia y respuestas perdidas

Claves de operación, recibos, locks y fingerprints vinculan intención con estado. Dos clics o un replay del mismo callback convergen al efecto autorizado. Una clave reusada con contenido incompatible debe dar conflicto; no significa «aceptar cualquier pedido».

La idempotencia local no garantiza exactamente una entrega SMTP ni una respuesta de proveedor. El sistema separa intención persistida, dispatch, verificación/recovery e incertidumbre. Cuando no existe prueba de ausencia, se conserva UNCERTAIN y decisión humana.

### 49.4 Seguridad documental

Storage privado y capacidades/URLs firmadas separan acceso del conocimiento de un ID. Una capacidad pública tiene revisión, permiso, vigencia y revocación; no concede inventario ni precio de compra. Una URL firmada de un acta no convierte a su poseedor en instalador asignado.

No hay credenciales, JWT, capacidades de portal ni enlaces privados en este informe. Los nombres de variables del capítulo de activación identifican configuración; sus valores quedan fuera del documento y de git.

Fuente: `supabase/migrations/`, `backend/authentication/`, `backend/{documents,portal,notifications,billing}/`, [invariantes](../ENGINEERING.md).

<a id="capitulo-50"></a>

## 50. Operación local, entornos y recuperación

### 50.1 Stack de revisión

El runbook local utiliza `scripts/start_local.ps1` y `scripts/review_stack.py` para recursos propios de REVIEW, con Supabase/Postgres, API Django, worker y frontend construidos. El fixture aporta roles y datos de aceptación declarados. Iniciar REVIEW puede reconstruir contenedores y aplicar el fixture: no es un paso inocuo para un informe documental.

| Servicio del perfil REVIEW documentado | Dirección/puerto local | Alcance |
|---|---|---|
| Web de producto | `http://127.0.0.1:5179` | UI del build de revisión |
| API | `http://127.0.0.1:8004` | Django y contratos del stack |
| Supabase | `http://127.0.0.1:25361` | Auth/REST del proyecto local |
| Postgres | Puerto 25362 | DB local con schema/RLS |
| Mailpit | `http://127.0.0.1:25364` | Bandeja sandbox de acceso/producto |

Son valores del perfil documentado, **no un sondeo de disponibilidad realizado por este informe**. En esta tarea no se arrancaron/reiniciaron procesos, no se aplicaron fixtures y no se alteraron Brave ni sesiones.

### 50.2 Desarrollo y productivo

Vite/Django en desarrollo y REVIEW construido son modos diferentes. Los cambios de fuente no se recargan automáticamente dentro de imágenes ya construidas. Django sin `DATABASE_URL` puede usar sqlite; eso no acredita el comportamiento de Supabase/Postgres/RLS.

Hosting productivo requiere servicios/API/worker, migraciones vigentes, secretos por ambiente, dominio HTTPS, proxy/CORS, Storage y observación de jobs/proveedor. No se trata de publicar solo el frontend para que pagos/correo/IA funcionen.

### 50.3 Mantenimiento para agentes

`AGENTS.md` y el índice de wiki conducen por tarea/dominio. Generados, payloads de goldens, cola terminada e historia no entran por defecto en búsquedas generales. Conservan acceso por ruta explícita. Este reporte es un **snapshot bajo demanda**, excluido de descubrimiento amplio, para que futuros agentes no lo carguen como instrucción o sustituto del código actual.

El informe describe el ref de portada. Una modificación posterior debe verificarse en código/contrato y, si interesa conservar el nuevo mapa, generar/actualizar otro snapshot con su fecha/ref. No se elimina una fuente de fabricación o un golden porque resulte extensa.

Fuente: [workspace](../operations/WORKSPACE.md), [guía](../GUIA-REVISION.md), [skill local](../../.agents/skills/testing-framedex/SKILL.md), `scripts/{start_local.ps1,review_stack.py,dev_fixture.py}`.

<a id="capitulo-51"></a>

## 51. Matriz completa de activación externa

La siguiente matriz resume [ACTIVACION](../operations/ACTIVACION.md). Las instrucciones de conexión describen trabajo que hace el responsable; **no se ejecutó para preparar este reporte**. DEMO/sandbox sigue identificado hasta contar con autoridad real.

| Conexión/autoridad | Qué debe aportar o declarar el responsable | Superficie/configuración | Qué se habilita y límite |
|---|---|---|---|
| Railway/hosting | Proyecto, servicios frontend/API/worker, ambientes, migraciones y dominios | `railway*.toml`, configuración Django/Vite | Disponibilidad externa; en programa local figura no conectado |
| Supabase/DB/Storage productivos | Proyecto, schema/RLS, Auth, buckets privados, respaldo y acceso por ambiente | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Tenancy, login y artefactos privados; fixture no es data productiva |
| Dominio/proxy | Orígenes HTTPS públicos y `/api` accesible | `CORS_ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, `DEKOPEN_PUBLIC_APP_URL` | Acceso/QR nuevos; no reescribe PDFs históricos |
| Secrets de aplicación | Clave Django, despliegue por ambiente y cifrado estable | `SECRET_KEY`, `RAILWAY_GIT_COMMIT_SHA`, `MAIL_ENCRYPTION_KEY` | Estado/cifrado; no copiar valores a frontend/git |
| Flow de plataforma | Comercio, llaves, sandbox aprobado y callbacks | `FLOW_API_URL`, `FLOW_API_KEY`, `FLOW_SECRET_KEY`, `FLOW_MERCHANT_TIMEZONE` | Packs/suscripción/billetera; distinto del Flow de fábrica |
| Flow de fábrica | Comercio por organización, llaves/endpoints y vigencia | Ajustes › Integraciones › Conectar Flow; `org_payment_integrations` | Enlaces CLP de obra/portal; no habilitado por llaves de plataforma |
| Retorno/callback de pago | Backend/frontend públicos y URLs autorizadas | `BILLING_CALLBACK_ORIGIN`, `BILLING_FRONTEND_ORIGIN` | Verificación/recovery de pago, nunca acreditar por navegación |
| SII real 33/61 | PFX/contraseña, CAF autorizado, contribuyente certificado y ambiente | Configurar emisión SII; `SII_WS_ENVIO_URL`, `SII_WS_STATUS_URL`, `SII_WS_TOKEN` | Factura/NC real; interno/simulador no es DTE |
| Boleta SII 39 real | Proveedor autorizado que implemente el contrato faltante | Adaptador por integrar | No soportada por timbrador actual |
| Correo comercial | Dominio/remitente, SPF/DKIM/DMARC y SMTP TLS | `MAIL_PROVIDER`, `MAIL_FROM_ADDRESS`, `MAIL_SMTP_HOST`, `MAIL_SMTP_PORT`, `MAIL_SMTP_USER`, `MAIL_SMTP_PASSWORD`, `MAIL_SMTP_STARTTLS`, `MAIL_SMTP_SSL` | Envío externo desde worker; SENT solo aceptación SMTP |
| Correo de acceso | SMTP/remitente en Supabase, Site URL y callback | Supabase Auth; `supabase/templates/magic-link.html` | Magic Link/verificación real; separado de correo comercial |
| Mailpit local | Host/puerto de sandbox del proyecto propio | `MAIL_SANDBOX_HOST`, `MAIL_SANDBOX_PORT` | Bandeja local; no envío al destinatario externo |
| Webhooks | Endpoint HTTPS, firma/verificación de proveedor, retries y observación | Variables específicas; nombres `WEBHOOK_SIGNING_SECRET_*` del índice | Idempotencia y auditoría de replay; no una conexión universal automática |
| MiMo | Key/base/modelo en backend/worker y selección por capacidad | `AI_GATEWAY_MIMO_API_KEY`, `AI_GATEWAY_MIMO_BASE_URL`, `AI_GATEWAY_MIMO_MODEL`, `AI_GATEWAY_ROUTE_PROVIDER` | IA real; conexión local documentada, sin consulta nueva en este reporte |
| IA productiva/ensayo | Mock desactivado en producción, modelo/ruta y límites | `AI_GATEWAY_MOCK_ENABLED=0`; Ajustes › Inteligencia artificial | Selección explícita de transporte; DEBUG no cambia proveedor |
| Tarifa/presupuesto IA | Input/output USD por millón y créditos mensuales reales | Ajustes › Inteligencia artificial | Costo monetario/alerta; sin tarifas conserva Sin dato |
| Catálogo técnico | Fuentes de fabricante por serie/versión, reglas, límites y revisión | Catálogo › Importar/ficha; plantilla `catalogo-v1.xlsx` | Autoridad fabricable; DEMO confirmado sigue sintético |
| Seguridad de vidrio | Norma permitida, reglas/página, clases/umbrales y decisión mandatory | Hoja Reglas de vidrio o Ajustes › Producción | Validación de selección; ejemplos no equivalen a norma oficial |
| Recetas de vidrio/panel | Composición, Ug/g/TL, SKU, densidades/PVB, límites y fuentes | Compositor/hoja Vidrios | Masa, térmica y pedido con autoridad; no completar ausencia por cero |
| Procesos de vidrio | Tarifa/unidad de templado, pulido, perforación/palillaje y mínimo | Catálogo/listas comerciales | Facturación y compra exactas; acuerdo proveedor para precisión/contornos |
| Aperturas/encuentros | Movimiento, dirección, bisagras, uso, rol, inversor/deducciones | Ficha/hoja Sistemas y kits | Francesa/doble/avanzadas reales; no sustituir autoridad por dibujo |
| Herrajes/manillas | Clases, rangos/masa, componentes/umbral, código/unidad/costo y fuentes | Hoja Herrajes, `class_authority`, artículos | Picking/opciones/altura con autoridad; RC requiere evidencia |
| Mecanizados de catálogo | Cara, anfitrión, coordenadas, profundidad/herramienta y cobertura | Catálogo y nueva revisión | Operaciones emitibles; incompleto sigue declarado no emitido |
| Acabados/suministro | Carta, proceso/caras, combinaciones, SKU/color/reglas y recargos | Colores y SKU por color | Bicolor/stock/precio compatible; muestra física confirma apariencia |
| Accesorios y servicios | Regla física, artículos/cortes/masa, tarifa/unidad/moneda y fuente | `extra_authority`; Ajustes › Comercial › Extras y servicios | BOM y venta/sublíneas; FX explícito para otra moneda |
| Montaje y medición | Ficha de montaje, holguras/deducciones y medición confirmada | Vano/Fabricación y catálogo | Dimensión fabricable; medir no reescribe acuerdo |
| Proveedores y listas | Elegibilidad, RUT/contacto, materiales, tarifa autorizada | Compras/catálogo/precios | OC a precio real; ausencia muestra Sin dato |
| Stock/formatos/racks | Material físico, formatos con fuente, racks y días de alerta | Inventario; Ajustes › Producción | Reservas/retazos trazables; declarar formato no genera stock |
| Máquina CNC | Manual, ejes/carrera/controlador, sujeción, montaje, herramientas | Producción › OT › Mecanizado | Intercambio neutro validado; postprocesador/calibración externos |
| Empresa/documentos | Razón social/RUT, marca, giro/contacto, vigencia/condiciones/hitos/papel | Ajustes › Empresa/Comercial/Documentos | Nuevas emisiones coherentes; históricos intactos |
| Usuarios/MFA | Correos verificados, invitaciones/roles y política de autenticador | Usuarios/Cuenta | Acceso real por persona; dueño mantiene MFA obligatorio |
| Terreno | HTTPS, cuentas/asignaciones, teléfonos protegidos y Storage privado | Despacho/Terreno, `/field-worker.js` | Cola/foto/firma privadas; revocar no borra teléfono desconectado |
| Garantía | Días/inicio reales antes de emitir | Comercial | Garantía por hecho firmado de unidad, no texto interpretado |
| Térmica/OGUC | Uf/Ug/Ψg e informes de espécimen, aire, zona/plano y revisión profesional | Catálogo › Térmica; Proyecto › Térmica | Evaluación de ventanas/anexo; no certificación completa del edificio |
| Costos reales | Movimientos, tarifas por unidad/moneda, horas/pérdida/crédito y fuente | Analítica › Margen/cierre | Puente real/cotizado; no tomar plan o costo DEMO como contabilidad |

Los nombres genéricos `SII_ENV`, `SII_CERTIFICATE_PASSWORD` y `SII_PROVIDER_*` del índice son reservados por proveedor; no reemplazan el contrato existente `SII_WS_*` y la carga de PFX/CAF. La tabla de webhooks también es un índice de activación: cada proveedor verifica su protocolo propio.

<a id="capitulo-52"></a>

## 52. Aceptación histórica y alcance de las verificaciones

### 52.1 Integración v1

Los 39 encargos de [ESTADO](../cola/ESTADO.md) figuran mergeados. P20 cerró por PR #156; el programa se integró a `main` por [PR #157](https://github.com/KaraAliOsman/framedex/pull/157), squash `2db4e13171884b93a989e68508a55f5590f9b34d`, con los cuatro checks en verde. La fuente de este informe conserva el mismo código de producto, con limpieza/documentación posteriores.

| Recorrido histórico | Resultado registrado | Condición/observación principal |
|---|---|---|
| Cuenta nueva → onboarding → proyecto → precio → emisión | PASA | Invitación/correo verificado, precio aplicado y PDF revisado |
| Doce posiciones/bow/acoplado → margen → A/B → aprobación → anticipo | PASA con observaciones | Dueño decide margen; pago manual y Flow simulado |
| Nueva revisión y comparación A↔B | PASA | Doce posiciones; bytes/hashes de PDFs conservados |
| Compra → recepción parcial/daño → cancelación → recompra → stock/RT | PASA con observaciones | Solo útil a stock; fuente/materiales DEMO identificados |
| Liberar → operario → QC FAIL/remake/PASS → despacho | PASA con observaciones | Unidades/pieza/reposición; autoridad física DEMO |
| CNC compatible/incompatible y brechas | PASA con observaciones | 34 piezas, diez brechas; intercambio revisado, sin máquina real |
| IA editor: propuesta → aplicar → undo → auditoría/cancelación | PASA | MiMo real y decisión humana; cancelación desde RUNNING |
| Cinco roles/dos empresas/IDs adivinados | PASA | MFA/tenant y proyecciones sin datos de empresa ajena |
| Hitos → pago manual → enlace → saldo cero | PASA con observaciones | Recibos únicos; Flow simulado/SII interno |
| Ingesta IA PDF/XLSX y plantilla manual | PASA con observaciones | Fuente y diff/revisión; catálogo sintético |
| Tipologías/vidrio/caras/extras/vano/OT/PDF/3D | PASA con observaciones | Paridades del motor y rechazos reales por incompatibilidad |
| Suite de 26 peticiones IA | PASA con observaciones | 21/26; cinco fallos conservados |
| Medición/rectificación → firma → incidencia/postventa | PASA con observaciones | Evidencia congelada y diagnóstico humano; fotos/firmas DEMO |
| Analítica real/cotizado/cierre/desvío | PASA con observaciones | F6 y revisiones aditivas; tarifas del oráculo DEMO |

### 52.2 Matrices de dominio y UX

La matriz de dominio principal contiene 35 tipologías × cuatro recetas = 140 posiciones. El suplemento añade 35 templados monolíticos: **175 positivos**. Las 35 variantes de laminado monolítico 6,38 mm se rechazan por junquillo ausente (`bead_incompatible`); no se inventó un perfil para aprobarlas.

Se registraron 175 paridades de OT/PDF y 350 vistas editor/3D en ambos temas. La QA manual documentada revisó las 350 vistas 3D y 175 elevaciones claras; la elevación oscura conserva captura/paridad y la revisión global, sin atribuirle esa misma inspección manual individual. Los PDFs de dominio tenían 80 y 22 páginas, renderizadas/revisadas según el recibo histórico.

El baseline UX documenta 912 vistas históricas. No se suma ese número a las 350 vistas de dominio como si fueran muestras independientes de la misma prueba. Cada matriz mantiene su alcance/ref. El pase editorial R1–R20 compara por persona y superficie; no todos los componentes existen en todas las pantallas.

### 52.3 Rendimiento medido en P20

| Operación | Muestras | p50 | p95 | Alcance de la muestra |
|---|---|---|---|---|
| Abrir posición | 12 | 306,83 ms | 720,20 ms | Sesión preparada hasta resultado visible y dos cuadros |
| Recalcular precio | 12 | 916,48 ms | 971,85 ms | Incluye debounce 180 ms y cascada real del motor |
| Abrir OT de obra de cien posiciones | 12 | 693,48 ms | 799,21 ms | Una de sus cien OT, no una OT artificial de cien posiciones |
| Portal móvil 4G, contexto frío | 12 | 2.949,26 ms | 2.972,86 ms | 390×844; 150 ms; 1,6 Mbps bajada/750 kbps subida |

Percentiles de rango más cercano, ceil(n×p): con doce muestras, p95 corresponde a la mayor observación. El portal pasó de p50/p95 8.871,22/9.373,35 ms a 2.949,26/2.972,86 ms en ese protocolo. La lectura de propuesta documentó 947→131 consultas SQL preservando RLS/autoridad.

Son mediciones históricas, no benchmarks ejecutados para este informe ni promesas de infraestructura productiva. La primera descarga/render WebGL del editor/3D se mantiene separada de interacción con sesión preparada.

### 52.4 Refs que no deben mezclarse

| Evidencia | Ref/registro |
|---|---|
| IA real P20 | `484182126c4f7ba32ba41f3e77b1a1ba31faf04c` |
| Baseline UX | `4efd739e` según aceptación |
| Presentación corregida | `b8450659` / PR #154 |
| Optimización portal | `cc0003ab` según aceptación |
| Interacción/recapturas de Ajustes | `b8e62295`, incluido en PR #155 |
| CI correctivo #154 | `d4dea5827d9509adb288c94eb8e01ddd05948f13`, corrida `38295986860` |
| CI correctivo #155 | `e5fef9b504158d064f180c4b5af558459bdbd895` |
| CI cierre P20 #156 | `c8ac0612aa1ff10008ab666c9527eccc67a9bc4c` |

Los refs cortos de la fuente se conservan como tales; no se inventa su expansión. El SHA de portada identifica inspección documental/código, sin apropiarse de las corridas anteriores.

Fuente: [aceptación del 12-10-2026](../redesign/acceptance-2026-10-12.md), [rendimiento](../redesign/P20-RENDIMIENTO.md), [guía probada históricamente](../GUIA-REVISION.md).

<a id="capitulo-53"></a>

## 53. Límites concretos y consecuencias para el uso

| Límite | Consecuencia práctica | Cómo resolver lo que depende de él |
|---|---|---|
| DEMO/synthetic | El recorrido puede funcionar sin acreditar fabricación ni prestaciones reales | Catálogo/fichas/precios/montaje revisados del proveedor |
| Compra con precio Sin dato — A6 | La cantidad es conocida; el unitario real no está autorizado | Cargar lista comercial válida y su fuente |
| Boleta SII 39 real — F25 | No emitirla tributariamente con timbrador actual | Integrar proveedor autorizado con contrato 39 |
| Entrega fiscal productiva — F26 | Interno/sandbox no acredita aceptación fiscal | CAF, certificado, transporte y certificación del contribuyente |
| Primera carga fría editor/3D — P2-1 | Descarga/WebGL inicial puede tardar más que abrir una posición preparada | Medir/optimizar en entorno objetivo; no reutilizar p95 caliente como frío |
| IA P20 cinco casos fallidos | No todas las peticiones producen el resultado/artefacto solicitado | Revisar caso y contrato; continuar desde UI/herramientas con autoridad |
| SMTP entrega incierta | Reintento ciego puede duplicar correo | Verificar ausencia y confirmar recovery humano |
| CNC intercambio neutro | Un archivo descargado no está listo para cualquier controlador | Postprocesador/manual/calibración y ensayo físico específicos |
| Térmica con fuente/espécimen incompletos | No existe una prestación certificada universal de la serie | Informe exacto revisado y responsable de obra |
| Vidrio sin junquillo compatible | La selección se rechaza; no se fabrica el ejemplo negativo | Autoridad real compatible o elección distinta |
| Datos offline en dispositivo revocado | El servidor bloquea replay; copia sin red puede permanecer local | Logout, gestión física del teléfono y política de acceso |
| Moneda/tarifa/tiempo ausentes | No hay costo/margen real completo | Registrar fuente/unidad/moneda/FX cuando proceda |
| QR/capacidad emitida | Destino y permisos pertenecen al histórico | Nueva emisión/enlace por camino autorizado; no editar PDF previo |
| Stack construido distinto de fuente editada | Navegador puede usar imágenes anteriores | Rebuild autorizado por runbook cuando se quiera actualizar producto |
| Cobertura histórica finita | Los 14 recorridos no cubren toda entrada/dispositivo/concurrencia posible | Revisión del dueño sobre sus datos y flujos concretos |

El registro histórico contiene 343 hallazgos clasificados —331 resueltos, ocho descartados y cuatro vigentes en el cierre—, pero P20 no reprodujo individualmente todas las auditorías antiguas. Se preserva ese contexto sin presentar cada riesgo histórico como defecto actual.

Fuente: [aceptación/límites](../redesign/acceptance-2026-10-12.md), [riesgos](../wiki/quality/known-risks.md), [activación](../operations/ACTIVACION.md).

<a id="capitulo-54"></a>

## 54. Recorridos para la revisión manual del dueño

Estos son guiones de uso derivados de las funciones descritas. No son pruebas ejecutadas durante este trabajo. Use datos de aceptación separados de la operación real cuando una acción emita, libere, envíe o registre un pago.

### 54.1 Acceso y personas

| Persona | Inicio de recorrido | Qué revisar |
|---|---|---|
| Dueño | Acceso con MFA → empresa → Hoy → Ajustes | Identidad, políticas, integraciones y decisiones bajo su cuenta |
| Estimador | Hoy → clientes → proyecto → editor/precio/cotización | Opciones válidas, pendientes, precio sin costos privados y solicitud de aprobación |
| Jefe | Hoy → preparación → Producción/Compras/Analítica | Bloqueadores, autoridad de fabricación, abastecimiento, calidad y costos |
| Operario | Producción → seleccionar puesto → cola → escanear | Solo trabajo del puesto; pieza/siguiente paso; motivo al bloquear |
| Instalador | Terreno → visita asignada → unidades/foto/firma | Solo asignaciones; estado pendiente/sincronizado; acta y recibo |
| Cliente final | Capacidad de propuesta vigente → revisar/decidir | Oferta/alternativa, identidad/consentimiento y saldo de solución elegida |

Sesión de cada rol significa cuenta/persona auténticas. Cambiar una etiqueta visual no demuestra cambio de permiso. Este informe no inició/cerró ni alteró sesiones de Brave.

### 54.2 Obra y diseño

1. Abra un cliente con dirección de facturación y obra diferenciadas; cree proyecto y posición con cantidad.
2. Elija serie/familia y tipología compatibles; cambie ancho/alto y una división.
3. Revise cotas y selección en elevación/planta; consulte estado del motor y cause un límite conocido sin guardarlo como válido.
4. Configure apertura, vidrio/panel, herraje/manilla, caras y extras disponibles con fuente.
5. Revise vista 3D, interior/exterior y pose según capacidad; no confunda representación con certificación.
6. Abra F6/inspector, atienda faltantes y revise medidas de vano/fabricación.
7. Guarde y reabra. Compare modelo/medidas/opciones; deshaga un cambio admisible.

Para conjuntos, compruebe identidad/orden de módulos, uniones/ángulos, módulos apilados y medida total. Una unión visible sin autoridad no debe habilitar fabricación. Un cambio por lote debe enseñar posiciones afectadas y diff antes de aplicarse.

### 54.3 Precio, cotización y cliente

1. Abra Precio y compruebe unidad, cantidad, moneda, cascada, fuentes y Sin dato.
2. Proponga un cambio, compare Δ, solicite aprobación si sale de política y aplique con la persona autorizada.
3. Complete antecedentes/condiciones y prepare PDF; ábralo antes de confirmar emisión.
4. Compruebe revisión/hash/documento y compare otra revisión sin alterar bytes anteriores.
5. Revise propuesta/alternativas como cliente, pida cambio o elija/apruebe la solución.
6. En Cobranza compruebe hitos y saldo de esa solución; use un movimiento marcado de ensayo o sandbox cuando corresponda.
7. Si se usa Flow, revise rechazo/retorno/verificación/recibo según el runbook de conexión. Abrir la página de retorno debe consultar estado, no inventar pago.

La comparación debe conservar el total vigente separado de alternativas. No busque costos privados en el portal ni SKU de compra completos en DOC-01.

### 54.4 Planta, abastecimiento y material

1. Complete fabricación y confirme preparación; libere con la revisión/acuerdo pertinentes.
2. Compruebe una OT por posición y cantidad/unidades de la posición.
3. Abra necesidades y diferencie stock/reserva/tránsito/OC; cree compra revisada si falta material.
4. Reciba parcialmente con guía/lote/rack, registre daño separado y verifique material útil.
5. Optimice con parámetros reales y revise barras/láminas/pérdida/RT; imprimir debe conservar identidad sin crear stock.
6. Desde el puesto del operario escanee pieza, avance un paso autorizado y registre motivo al bloquear.
7. Revise QC/remake con jefe; compruebe origen y que un replay no crea otra reposición.
8. Complete Corte y siga el RT al rack/inventario; prepare embalaje y despacho.

CNC necesita su recorrido propio de montaje/herramienta/preview/confirmación/manifiesto. Un intercambio compatible en software todavía requiere validación física con máquina/postprocesador reales.

### 54.5 Terreno y cierre

1. Asigne fecha/franja/equipo y abra agenda del instalador con red.
2. Registre unidad/medición/foto/firma y observe pendiente frente a sincronizado.
3. Compruebe recepción parcial y garantía según el hecho firmado, sin atribuirlo a una visita programada.
4. Registre incidencia; el jefe diagnostica y decide reposición/compra/servicio.
5. Para una rectificación revise diff/borrador y preserve revisión aprobada.
6. En Analítica valore consumos/tarifas/horas/pérdida con fuente, revise cobertura y confirme cierre.
7. Abra F6 hasta el movimiento y compare CSV/moneda. Una corrección añade revisión, sin editar el cierre anterior.

### 54.6 IA y mensajes

Solicite una modificación con medidas y referencias claras. Observe herramientas/diff, revise precio y confirme aplicar; consulte recibo y undo admisible. Un pedido de emisión/compra debe llevar a su revisión/clic. Revise trabajo fallido/cancelación/reintento con su causa, sin asumir que un texto final creó el artefacto pedido.

Para correo, revise destinatario/PDF y el estado de outbox. «Aceptado por el servidor» no acredita lectura. En incertidumbre, la recuperación necesita comprobación humana; la bandeja sandbox no envía al destinatario externo.

Fuente: [GUIA-REVISION](../GUIA-REVISION.md), [ACTIVACION](../operations/ACTIVACION.md) y capítulos funcionales de este informe.

<a id="capitulo-55"></a>

## 55. Lectura de estados, números y códigos

### 55.1 Estados que no son intercambiables

| Expresión | Significado operacional |
|---|---|
| Geometría válida | La forma cumple el contrato geométrico evaluado |
| Fabricación incompleta | Faltan autoridades/datos; una geometría válida no basta |
| Cotizable | Existe autoridad comercial suficiente para el camino permitido |
| Precio indicativo | Cálculo sin aplicar/persistir venta definitiva |
| Precio aplicado | Proyección comercial confirmada y protegida por estado |
| Preparado | Intención/preview disponible; su acción final puede seguir pendiente |
| Emitido | Revisión/artefacto sellados con recibo |
| Compartido/vigente | Capacidad autorizada actualmente para su alcance |
| Aprobado/elegido | Decisión del cliente sobre solución concreta |
| Pagado | Movimiento verificado/manual con evidencia; simulación conserva marca |
| Liberado | Creación de fabricación/OT bajo autoridad confirmada |
| Reservado | Material apartado; todavía no consumo |
| Recibido útil | Material físico aceptado, separado de daño/excedente |
| Corte planificado | Distribución prevista de material, sin medición real implícita |
| Paso completado | Hecho de planta validado; efectos según paso/ruta |
| Entregado/instalado | Hecho por unidad y evidencia correspondiente |
| Cierre de costo | Lectura real sellada con cobertura; puede tener revisión posterior |
| Sin dato | Ausencia conocida que debe resolverse o conservarse explícita |

### 55.2 Presentación exacta

| Magnitud | Presentación humana del contrato | Exportación técnica |
|---|---|---|
| mm | Entero o fracción original con coma y agrupación fina | Decimal de origen, punto, sin miles |
| m / m² | Dos decimales | Unidad/campo según formato |
| kg | Un decimal | Precisión definida por schema/autoridad |
| Unidades | Entero | Entero |
| % | Un decimal y espacio antes de % | Valor numérico según campo |
| CLP | Sin decimales, agrupación con puntos | Importe de moneda según contrato |
| USD | Dos decimales, coma decimal | Importe de moneda según contrato |
| Ángulo | Entero o fracción declarada | Precisión de origen |
| Fecha | dd-mm-yyyy; America/Santiago donde aplica | ISO/campo del contrato correspondiente |

El formateo de lectura no modifica valor calculado ni bytes sellados. CSV/DXF conservan sus convenciones de máquina. Los ejemplos de formato de ingeniería son ejemplos de presentación, no valores de un proyecto del dueño.

### 55.3 Direcciones humanas

Proyectos conservan secuencia global `P-000123`. OC, RT y REC usan códigos por organización. Piezas físicas usan direcciones como `P01-U02-M03` y refuerzo `-R`; el escáner acepta el separador histórico cuando corresponde. Los números confirmados no se reutilizan al eliminar/cancelar una entidad.

Los códigos son direcciones, no permisos. Un QR une OT, código e identidad estable; trace comprueba todos. El escaneo de pieza sin OT limita candidatos de taller a cien; un candidato adicional exige el QR con OT antes de leer snapshots, sin presentar historia parcial como completa. Plan invalidado/ausente bloquea etiquetas físicas de corte; etiquetas históricas de manifest pueden conservar su lectura con causa explícita.

Fuente: [ENGINEERING](../ENGINEERING.md), [direcciones humanas](../wiki/product/human-addresses.md).

<a id="capitulo-56"></a>

## 56. Fuentes y método de trazabilidad

### 56.1 Fuentes actuales utilizadas

| Fuente | Uso en este informe |
|---|---|
| `AGENTS.md`, `docs/ENGINEERING.md`, `docs/PRODUCT.md` | Mapa, invariantes y dirección del producto |
| `docs/design/CONSTITUCION.md` | Reglas de superficie/producto |
| `docs/wiki/index.md` y páginas de dominio citadas | Síntesis por capacidad y decisiones; contrastadas con fuente actual |
| `frontend/src/App.tsx`, `PrivateApplication.tsx`, `navigation.ts`, `PublicProposalApp.tsx` | Superficies/rutas, entrada y persona |
| `backend/config/urls.py`, urls/views/services por dominio | Rutas, permisos, estados y efectos |
| `backend/openapi.yaml` | Inventario 334 operaciones, 265 paths y schemas |
| `engine/src/dekopen_engine/` | Registro de operaciones, tipos y cálculos puros |
| `supabase/migrations/` | Declaraciones de datos y evolución de autoridad/RLS |
| `docs/operations/ACTIVACION.md`, `docs/GUIA-REVISION.md` | Conexiones y modo de uso del dueño |
| `docs/redesign/acceptance-2026-10-12.md` y refs citados | Aceptación histórica y límites medidos |
| `docs/cola/ESTADO.md` | Registro de los 39 encargos e integración |

El inventario técnico se obtuvo de YAML, AST de Python y literales de rutas/declaraciones SQL, sin importar Django ni ejecutar el motor. Los anexos son índices de estructura, no resultados de pruebas. La validación de este entregable comprueba formato, conteos, enlaces y ausencia de material privado; no realiza operaciones del producto.

### 56.2 Criterio de lectura futura

Un hecho de este snapshot se debe contrastar con su ref si cambió el código. Un resultado de aceptación se contrasta con el ref de aquella corrida. Una intención del dueño conserva su categoría; no se transforma en prestación física o certificación. Una fuente de fabricante se revisa y se liga a la regla/espécimen aplicables.

La versión HTML es una proyección navegable de este mismo Markdown, con índice, buscador y vista de impresión. No incorpora datos vivos, llamadas de red, telemetría ni autenticación. Los enlaces de fuente del inventario apuntan al SHA examinado para permitir revisión estable.

<a id="capitulo-57"></a>

## 57. Glosario funcional

| Término | Significado en DEKOPEN |
|---|---|
| Tenant / organización | Empresa que delimita datos, permisos y autoridad privada |
| ProductModel | Modelo compuesto de ensamblaje/módulos/uniones y diseño |
| Posición | Solución vendida de la obra, con diseño y cantidad |
| Módulo | Unidad geométrica de un conjunto; no necesariamente otra posición |
| Paño / BAY | Región de relleno/apertura del árbol paramétrico |
| Montante / travesaño | División vertical/horizontal dentro del marco |
| Acople / coupler | Unión con regla y artículo entre módulos |
| Vano | Hueco medido de obra usado por una regla de montaje |
| Fabricación | Dimensión/definición técnica derivada y confirmada para producir |
| BOM | Lista calculada de materiales/componentes con autoridad e identidad |
| SKU | Artículo/código técnico o comercial; su unidad y variante importan |
| Supply / suministro | Identidad de material comprable/stock compatible |
| Readiness | Estado/causas de autoridad necesaria para un proceso |
| Snapshot | Datos/autoridades conservados para reproducir un hecho |
| Fingerprint / hash | Huella que liga contenido/plan/estado con su recibo |
| Idempotencia | Repetir una intención compatible conserva su efecto/recibo |
| Revisión | Versión de la solución/comercial; lo emitido permanece inmutable |
| DOC-01 | Propuesta comercial sellada, con revisión y acceso del cliente |
| Capacidad pública | Permiso opaco limitado por revisión, alcance y vigencia |
| Acuerdo | Decisión/evidencia que liga al cliente con la solución elegida |
| OT | Orden de trabajo por posición liberada |
| QC | Control de calidad y decisión/evidencia de planta |
| Remake / RM | Reposición con procedencia y decisión autorizadas |
| OC / REC | Orden de compra / recepción con dirección humana |
| RT | Retazo físico recuperable, identificado y localizado |
| Ledger | Historial de movimientos de material, créditos o dinero según dominio |
| Nesting | Distribución de piezas sobre láminas bajo reglas declaradas |
| CNC neutro | Intercambio de operaciones; no programa propietario listo para toda máquina |
| VIS / ACT / INC | Visita / acta / incidencia por organización |
| Uw / Uf / Ug / Ψg | Transmitancia de ventana/marco/vidrio y borde, con autoridad térmica |
| FX | Tipo de cambio observado y declarado para conversión explícita |
| F6 | Firma de explicación de origen/cálculo/causa de un dato |
| Orb | Presencia del trabajo del asistente ligada al contexto |
| Job | Trabajo durable con estado/progreso/intentos/resultados |
| Outbox | Intención de correo sellada/cifrada antes de su entrega |
| UNCERTAIN | Intento externo sin resultado concluyente; exige revisión de recovery |
| DEMO / synthetic | Fuente/fixture de ensayo que no certifica datos productivos |
| RLS | Políticas de Postgres que limitan acceso a filas por autoridad |
| MFA | Segundo factor requerido por rol/política |
| SII / CAF / DTE | Autoridad tributaria / folios autorizados / documento tributario electrónico |

Los símbolos técnicos de los anexos sirven para buscar código; la interfaz de usuario debe mantener el lenguaje humano del contrato.

<!-- GENERATED_APPENDICES_START -->

<a id="anexo-a"></a>

## Anexo A. Las 55 operaciones compartidas

Inventario del registro del ref examinado. Una precondición publicada no enumera todas las guardas de backend, RLS, estado y manejador. Los campos «requeridos» y «campos de payload» reproducen sus listas declaradas; algunos targets tienen su propio contrato. Máximo 50 operaciones por lote. Preparar no ejecuta la acción consecuente.


### A.1 Diseño: 38 operaciones

| Operación / fuente | Descripción declarada | Requeridos | Campos de payload | Precondición publicada |
|---|---|---|---|---|
| [split_bay](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L94) | Divide un paño dentro del mismo marco; V crea montante y H travesaño. | `bay`, `axis`, `from` | `axis`, `offset_mm`, `from` | Diseño editable y serie visible; validación del motor. |
| [move_divider](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L97) | Mueve el eje de un montante o travesaño. | `divider`, `offset_mm` | `offset_mm`, `from` | Diseño editable y serie visible; validación del motor. |
| [remove_divider](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L100) | Retira una división conservando el paño indicado; rechaza estructura anidada. | `divider` | `keep_bay` | Diseño editable y serie visible; validación del motor. |
| [set_bay_size](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L102) | Ajusta un paño moviendo su división inmediata; requiere eje compatible. | `bay`, `axis`, `size_mm` | `axis`, `size_mm` | Diseño editable y serie visible; validación del motor. |
| [equalize_bays](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L105) | Reparte el marco en paños con ejes iguales; count cambia la cantidad en un solo marco. | `module`, `axis` | `module`, `axis`, `count` | Diseño editable y serie visible; validación del motor. |
| [set_opening](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L108) | Cambia la apertura de un paño o todos los paños del módulo según el catálogo. | `module`, `opening` | `opening`, `opening_use`, `hinged_layout`, `opening_recipe_code`, `sliding_layout` | Diseño editable y serie visible; validación del motor. |
| [flip_handing](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L114) | Invierte bisagras y cierre conservando movimiento y dirección. | `bay` | — | Diseño editable y serie visible; validación del motor. |
| [set_handle_height](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L115) | Declara la altura local de manilla; FLOOR exige antepecho explícito. | `bay`, `height_mm`, `reference` | `height_mm`, `reference`, `sill_height_mm`, `all_handles` | Diseño editable y serie visible; validación del motor. |
| [set_sliding_layout](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L119) | Define corredera: X móvil, O fijo; cada móvil declara carril. | `bay`, `panels`, `tracks` | `panels`, `tracks`, `panel_tracks`, `panel_travel`, `travel_mm` | Diseño editable y serie visible; validación del motor. |
| [set_travel](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L124) | Prepara el recorrido declarado de corredera; exige soporte explícito del modelo. | `bay`, `travel_mm` | `travel_mm` | La serie y el contrato de corredera declaran recorrido editable; en caso contrario devuelve un bloqueo. |
| [set_glass](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L127) | Asigna SKU real o composición que coincida exactamente con una receta del catálogo. | `module` | `sku`, `composition` | Diseño editable y serie visible; validación del motor. |
| [set_glass_thickness](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L129) | Elige un espesor declarado por la serie. | `module`, `mm` | `module`, `mm` | Diseño editable y serie visible; validación del motor. |
| [set_panel](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L131) | Asigna o retira un panel disponible. | `module`, `sku` | `sku` | Diseño editable y serie visible; validación del motor. |
| [set_module_width](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L137) | Fija el ancho nominal de un módulo. | `module`, `width_mm` | `module`, `width_mm` | Diseño editable y serie visible; validación del motor. |
| [resize](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L139) | Suma un incremento a las dimensiones actuales; el motor calcula el nuevo valor exacto. | `module` | `module`, `delta_width_mm`, `delta_height_mm` | Diseño editable y serie visible; validación del motor. |
| [set_total_width](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L142) | Reparte proporcionalmente el ancho total entre módulos. | `width_mm` | `width_mm` | Diseño editable y serie visible; validación del motor. |
| [set_height](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L143) | Fija el alto nominal de los módulos. | `height_mm` | `height_mm` | Diseño editable y serie visible; validación del motor. |
| [equalize_widths](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L144) | Iguala anchos nominales conservando exactamente el total. | — | — | Diseño editable y serie visible; validación del motor. |
| [equalize_angles](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L145) | Iguala ángulos según la primera unión declarada. | — | — | Diseño editable y serie visible; validación del motor. |
| [set_coupling_angle](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L146) | Fija el ángulo de una unión existente. | `coupling`, `angle_deg` | `coupling`, `angle_deg` | Diseño editable y serie visible; validación del motor. |
| [set_coupling_kind](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L147) | Cambia el tipo de unión compatible con sus bordes. | `coupling`, `kind` | `coupling`, `kind` | Diseño editable y serie visible; validación del motor. |
| [set_module_count](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L148) | Cambia la cantidad de marcos independientes acoplados; no equivale a dividir paños. | `count` | `count` | Diseño editable y serie visible; validación del motor. |
| [add_unit](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L149) | Agrega un marco unido en un extremo libre. | `side` | `side` | Diseño editable y serie visible; validación del motor. |
| [remove_unit](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L150) | Quita un marco; conserva las conexiones restantes compatibles. | `module` | `module` | Diseño editable y serie visible; validación del motor. |
| [duplicate_module](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L151) | Duplica un marco sobre un borde libre. | `module` | `module` | Diseño editable y serie visible; validación del motor. |
| [add_stacked_unit](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L152) | Agrega un fijo superior conectado al borde libre del marco. | `module` | `module` | Diseño editable y serie visible; validación del motor. |
| [insert_module](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L153) | Inserta un marco dentro de una unión recta existente. | `coupling` | `coupling` | Diseño editable y serie visible; validación del motor. |
| [remove_coupling](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L154) | Desconecta una unión conservando sus marcos. | `coupling` | `coupling` | Diseño editable y serie visible; validación del motor. |
| [set_bay_spec](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L155) | Declara herraje, tratamiento y clasificación de un paño; el motor comprueba la autoridad. | `module`, `bay`, `patch` | `patch` | Diseño editable y serie visible; validación del motor. |
| [clear_glass_thickness](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L157) | Retira el espesor declarado y deja su ausencia explícita. | `module` | `module` | Diseño editable y serie visible; validación del motor. |
| [set_module_tree](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L159) | Aplica una especificación declarada o copiada conservando la identidad del marco; el motor la valida completa. | `module`, `tree` | `module`, `tree` | Diseño editable y serie visible; validación del motor. |
| [set_extras](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L161) | Declara accesorios y medidas del vano sobre el marco; las cantidades salen del motor. | `module`, `extras` | `module`, `extras`, `context` | Diseño editable y serie visible; validación del motor. |
| [set_frameless](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L164) | Declara soportes y herrajes del paño sin marco; la evaluación comprueba su catálogo. | `module`, `spec` | `module`, `spec` | Diseño editable y serie visible; validación del motor. |
| [set_contour_vertex](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L166) | Fija un vértice del contorno; END mide la distancia desde el extremo del marco. | `module`, `index`, `x_mm`, `y_mm` | `module`, `index`, `x_mm`, `y_mm`, `from` | Diseño editable y serie visible; validación del motor. |
| [set_contour_bulge](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L169) | Declara la flecha de un arco del contorno. | `module`, `index`, `rise_mm` | `module`, `index`, `rise_mm` | Diseño editable y serie visible; validación del motor. |
| [resize_seam](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L172) | Desplaza la unión entre dos marcos; conserva exactamente su ancho total. | `left`, `right`, `delta_mm` | `left`, `right`, `delta_mm` | Diseño editable y serie visible; validación del motor. |
| [swap_modules](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L174) | Intercambia dos marcos en la disposición existente. | `module`, `other` | `module`, `other` | Diseño editable y serie visible; validación del motor. |
| [set_coupler_sku](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L176) | Declara el acople real de una unión, o retira su selección. | `coupling`, `sku` | `coupling`, `sku` | Diseño editable y serie visible; validación del motor. |

### A.2 Posición: 2 operaciones

| Operación / fuente | Descripción declarada | Requeridos | Campos de payload | Precondición publicada |
|---|---|---|---|---|
| [set_finish](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L133) | Selecciona caras interior/exterior de la carta de acabados real. | `interior`, `exterior` | `interior`, `exterior` | Diseño editable y serie visible; validación del motor. |
| [set_system](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L135) | Cambia la serie y vuelve a validar todas sus compatibilidades. | `system_id` | `system_id` | Diseño editable y serie visible; validación del motor. |

### A.3 Proyecto: 11 operaciones

| Operación / fuente | Descripción declarada | Requeridos | Campos de payload | Precondición publicada |
|---|---|---|---|---|
| [set_location](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L178) | Cambia la ubicación de una posición. | `position_id`, `location` | `position_id`, `location` | Diseño editable y serie visible; validación del motor. |
| [set_quantity](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L179) | Cambia la cantidad exacta de una posición. | `position_id`, `quantity` | `position_id`, `quantity` | Diseño editable y serie visible; validación del motor. |
| [add_position](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L180) | Crea una posición desde una plantilla real o apertura catalogada y dimensiones explícitas. | `system_id`, `template`, `dims`, `location`, `glass_sku`, `color` | `system_id`, `template`, `dims`, `location`, `quantity`, `glass_sku`, `color` | Diseño editable y serie visible; validación del motor. |
| [duplicate_position](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L183) | Crea copias exactas de una posición; count es el número de copias nuevas. | `position_id`, `count`, `location` | `position_id`, `count`, `location` | Diseño editable y serie visible; validación del motor. |
| [remove_position](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L184) | Quita una posición de la revisión editable. | `position_id` | `position_id` | Diseño editable y serie visible; validación del motor. |
| [duplicate_positions](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L185) | Duplica exactamente un lote de posiciones; conserva su ubicación y agrupación. | `position_ids` | `position_ids` | Diseño editable y serie visible; validación del motor. |
| [add_design_position](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L188) | Agrega la receta completa de la biblioteca después de validarla con el catálogo y el motor. | `system_id`, `product`, `glass_sku`, `color`, `location`, `quantity` | `system_id`, `product`, `glass_sku`, `color`, `location`, `quantity` | Diseño editable y serie visible; validación del motor. |
| [remove_positions](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L192) | Quita un lote de la revisión editable con vista previa y deshacer. | `position_ids` | `position_ids` | Diseño editable y serie visible; validación del motor. |
| [set_positions](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L195) | Declara cantidad, ubicación o piso/recinto/eje para posiciones seleccionadas. | `position_ids` | `position_ids`, `quantity`, `location`, `placement` | Diseño editable y serie visible; validación del motor. |
| [reorder_positions](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L201) | Reordena la lista completa sin cambiar el número ni la identidad física de una posición. | `position_ids` | `position_ids` | Diseño editable y serie visible; validación del motor. |
| [apply_to_positions](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L204) | Propone un cambio sobre posiciones filtradas por ubicación, tipología o ids. | `filter`, `ops` | `filter`, `ops` | Diseño editable y serie visible; validación del motor. |

### A.4 Preparación: 4 operaciones

| Operación / fuente | Descripción declarada | Requeridos | Campos de payload | Precondición publicada |
|---|---|---|---|---|
| [prepare_emit](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L205) | Prepara emisión de cotización. | `project_id` | `project_id` | Solo prepara la ruta; exige clic humano independiente. |
| [prepare_release](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L205) | Prepara liberación de producción. | `project_id` | `project_id` | Solo prepara la ruta; exige clic humano independiente. |
| [prepare_purchase](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L205) | Prepara compra de faltantes. | `project_id` | `project_id` | Solo prepara la ruta; exige clic humano independiente. |
| [prepare_payment_link](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py#L205) | Prepara enlace de pago. | `project_id` | `project_id` | Solo prepara la ruta; exige clic humano independiente. |

<a id="anexo-b"></a>

## Anexo B. Contrato completo de las 334 operaciones HTTP

Inventario de OpenAPI: 265 paths y 334 pares método/ruta. Se agrupa por la primera etiqueta del contrato para no duplicar operaciones; las doce etiquetadas también CNC pertenecen al grupo Producción. Hay health/schema fuera de este inventario de paths de negocio.

«Entrada» nombra schema y obligatoriedad del body. Parámetros incluyen lugar/tipo y asterisco si son required. Las respuestas muestran schemas de éxito y todos los códigos declarados; un código listado no demuestra que se haya ejercitado. Seguridad reproduce la declaración de operación: ausencia de Bearer no evita comprobar capacidad, firma, contexto o permisos en la vista. Las descripciones son extractos acotados del contrato; el enlace de método/ruta abre su fuente completa.


| Etiqueta principal | Operaciones |
|---|---|
| `auth` | 3 |
| `projects` | 98 |
| `catalogs` | 46 |
| `engine` | 6 |
| `pricing` | 13 |
| `documents` | 11 |
| `v1` | 20 |
| `production` | 58 |
| `inventory` | 15 |
| `purchasing` | 14 |
| `field` | 5 |
| `analytics` | 10 |
| `ai` | 17 |
| `jobs` | 4 |
| `billing` | 13 |
| `search` | 1 |

### B.1 Autenticación — 3

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [POST `/api/v1/auth/invitation/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2043) | `invitation_inspect` | `InvitationTokenRequest`<br>Body obligatorio | — | `200` → `InvitationInspect`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/auth/invitation/accept/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2111) | `invitation_accept` | `InvitationTokenRequest`<br>Body obligatorio | — | `200` → `InvitationAccepted`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/auth/me/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2179) | `auth_me` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `AuthMeResponse`<br>Códigos: `200`, `400`, `401`, `403`, `409` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.2 Proyectos, clientes, empresa y revisiones — 98

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/catalogs/systems/{system_id}/thermal/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6260) | `catalog_thermal_reports` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` * · path · `string (uuid)` | `200` → `ThermalCatalogResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/systems/{system_id}/thermal/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6329) | `catalog_thermal_declare` | `ThermalAuthorityRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` * · path · `string (uuid)` | `201` → `object`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/systems/{system_id}/thermal/{report_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6406) | `catalog_thermal_review` | `ThermalReviewRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`report_id` * · path · `string (uuid)`<br>`system_id` * · path · `string (uuid)` | `200` → `object`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/clients/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6495) | `clients_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `ClientListResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/clients/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6558) | `clients_create` | `ClientWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `ClientResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/clients/directory/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7135) | `client_directory` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`include_merged` · query · `boolean`<br>`limit` · query · `integer`<br>`offset` · query · `integer`<br>`q` · query · `string`<br>`with_active_projects` · query · `boolean`<br>`with_balance` · query · `boolean` | `200` → `ClientDirectory`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/clients/{client_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6771) | `clients_deactivate` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `204` → Sin body declarado<br>Códigos: `204`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/clients/{client_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6628) | `clients_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `200` → `ClientResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/clients/{client_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6697) | `clients_update` | `PatchedClientUpdateRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `200` → `ClientResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/clients/{client_id}/dossier/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6837) | `client_dossier` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `200` → `ClientDossierResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/clients/{client_id}/merge-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6983) | `client_merge_preview` | `ClientMergePreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `200` → `ClientMergePreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/clients/{client_id}/merge/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6907) | `client_merge` | `ClientMergeRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `200` → `ClientResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/clients/{client_id}/notes/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7059) | `client_note_add` | `ClientNoteWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`client_id` * · path · `string (uuid)` | `201` → `ClientNote`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/branding/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9984) | `organization_branding_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `OrgBranding`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/branding/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10047) | `organization_branding_save` | `OrgBrandingWriteRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)` | `200` → `OrgBranding`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/organization/branding/logo/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10252) | `organization_branding_logo_delete` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `OrgBranding`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/branding/logo/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10116) | `organization_branding_logo_read` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/branding/logo/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10180) | `organization_branding_logo_upload` | `object`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)` | `200` → `OrgBranding`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/collections/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10316) | `collection_integrations` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CollectionIntegration`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/collections/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10379) | `collection_settings_save` | `CollectionSettingsRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `CollectionIntegration`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/company/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10449) | `company_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `Company`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/company/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10512) | `company_save` | `CompanyWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `Company`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/organization/document-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10582) | `company_document_preview` | `CompanyPreviewRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/extras/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10659) | `organizationExtraPolicy` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `PolicyResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/extras/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10722) | `organizationExtraPolicySave` | `PolicyWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `PolicyResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/organization/invitations/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10798) | `company_invite` | `InvitationWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `CompanyUsers`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/organization/invitations/{identity}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10874) | `company_invitation_revoke` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`identity` * · path · `string (uuid)` | `200` → `CompanyUsers`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/mounting/{system_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11008) | `mountingRules` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` * · path · `string (uuid)` | `200` → `Rules`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/mounting/{system_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11077) | `mountingRuleSave` | `RuleWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` * · path · `string (uuid)` | `200` → `Rules`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/numbering/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11153) | `company_numbering` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `NumberingList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/users/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11217) | `company_users` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CompanyUsers`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/organization/users/{identity}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11281) | `company_user_update` | `CompanyUserWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`identity` * · path · `string (uuid)` | `200` → `CompanyUsers`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/positions/{position_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11856) | `positions_destroy` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`expected_updated_at` * · query · `string (date-time)`<br>`position_id` * · path · `string (uuid)` | `204` → Sin body declarado<br>Códigos: `204`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/positions/{position_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11712) | `positions_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)` | `200` → `PositionResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/positions/{position_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11781) | `positions_update` | `PositionUpdateRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)` | `200` → `PositionResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/positions/{position_id}/design-alternatives/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11928) | `positions_design_alternatives` | `DesignAlternativesRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)` | `200` → `DesignAlternativesResponse`<br>Códigos: `200`, `502`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/positions/{position_id}/design-assist/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12010) | `positions_design_assist` | `DesignAssistRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)` | `200` → `DesignAssistResponse`<br>Códigos: `200`, `502`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/positions/{position_id}/measurements/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12092) | `measurementConfirm` | `MeasurementConfirmRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)` | `200` → `MeasurementResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/positions/{position_id}/measurements/rectify/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12174) | `measurementRectify` | `RectificationRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)` | `200` → `RectificationResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17874) | `projects_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `ProjectListResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17937) | `projects_create` | `ProjectWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `ProjectResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/design-options/{system_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21963) | `project_design_options` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` * · path · `string (uuid)` | `200` → `DesignOptions`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/extras-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22033) | `positionExtrasPreview` | `ExtrasPreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `ExtrasPreviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/flow/confirm/{link_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22185) | `project_payment_flow_confirm` | `FlowConfirmationRequest`<br>Body obligatorio | `link_id` * · path · `string (uuid)` | `200` → `FlowAcknowledgement`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Flow urlConfirmation webhook — public, verified server-side. |
| [GET `/api/v1/projects/flow/simulated/{link_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22255) | `flow_simulation_status` | Sin body declarado | `link_id` * · path · `string (uuid)`<br>`token` * · query · `string` | `200` → `FlowSimulation`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Sin esquema declarado en la operación; revisar vista | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/flow/simulated/{link_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22320) | `flow_simulation_confirm` | `FlowSimulationRequestRequest`<br>Body obligatorio | `link_id` * · path · `string (uuid)` | `200` → `FlowSimulation`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Sin esquema declarado en la operación; revisar vista | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/hardware-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22387) | `hardware_preview` | `HardwarePreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `HardwarePreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/mounting-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22463) | `mountingPreview` | `MountingPreviewRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `MountingPreviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/operations/registry/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22533) | `design_operations_registry` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `OperationsRegistry`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/operations/simulate/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22597) | `design_operations_simulate` | `SimulateOpsRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `Simulation`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/payment-integration/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22667) | `project_payment_integration_status` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `PaymentIntegrationStatus`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/projects/payment-integration/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22730) | `project_payment_integration_save` | `PaymentIntegrationRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `PaymentIntegrationStatus`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18007) | `projects_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/projects/{project_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18076) | `projects_update` | `PatchedProjectUpdateRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/clone/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18227) | `projects_clone` | `CloneProjectRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `ProjectResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/collection-reminder/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18303) | `collection_reminder_prepare` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `CollectionReminder`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/collection-reminder/send/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18373) | `collection_reminder_send` | `CollectionReminderSendRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `202` → `MailRecord`<br>Códigos: `202`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/credit-notes/{credit_note_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18449) | `project_credit_note_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`credit_note_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectCreditNoteAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/credit-notes/{credit_note_id}/dte-envio/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18525) | `project_credit_note_dte_envio_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`credit_note_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `SiiEnvioAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/credit-notes/{credit_note_id}/dte-envio/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18600) | `project_credit_note_dte_envio_send` | `SiiEnvioSendRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`credit_note_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `SiiEnvio`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/fiscal-simulations/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18681) | `fiscal_simulations` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `FiscalSimulations`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/fiscal-simulations/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18750) | `fiscal_simulate` | `FiscalSimulationRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `FiscalSimulation`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/imports/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18826) | `project_imports_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ImportListResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/imports/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18895) | `project_imports_create` | `ImportUploadRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ImportCreateResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/imports/{import_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18971) | `project_import_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ImportDetailResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/imports/{import_id}/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19047) | `project_import_confirm` | `ImportConfirmRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ImportConfirmResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/invoices/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19135) | `project_invoice_emit` | `InternalDocumentRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `ProjectInvoice`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/invoices/{invoice_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19210) | `project_invoice_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectInvoiceAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/invoices/{invoice_id}/credit-note-dte/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19367) | `project_credit_note_dte_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectDteAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/invoices/{invoice_id}/credit-note-dte/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19442) | `project_credit_note_dte_emit` | `ProjectCreditNoteEmitRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `ProjectDte`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/invoices/{invoice_id}/credit-note/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19286) | `project_credit_note_emit` | `ProjectCreditNoteEmitRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `ProjectCreditNote`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/invoices/{invoice_id}/dte-envio/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19674) | `project_invoice_dte_envio_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `SiiEnvioAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/invoices/{invoice_id}/dte-envio/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19749) | `project_invoice_dte_envio_send` | `SiiEnvioSendRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `SiiEnvio`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/invoices/{invoice_id}/dte/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19523) | `project_invoice_dte_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectDteAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/invoices/{invoice_id}/dte/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19598) | `project_invoice_dte_emit` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`invoice_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `ProjectDte`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/operations/apply/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19906) | `project_operations_apply` | `ProjectOpsApplyRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectOpsResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/operations/preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19982) | `project_operations_preview` | `ProjectOpsPreviewRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectOpsPreviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/operations/state/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20058) | `project_operations_state` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`operation_key` * · query · `string`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectOpsState`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/operations/{operation_id}/undo/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L19830) | `project_operations_undo` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`operation_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectOpsResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/payment-links/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20135) | `project_payment_links_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `PaymentLinksResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/payment-links/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20204) | `project_payment_link_create` | `PaymentLinkCreateRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `PaymentLinkResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/payment-links/{link_id}/recover/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20280) | `project_payment_link_recover` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`link_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `PaymentLinkResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/payments/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20356) | `project_payments_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `PaymentsSummary`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/payments/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20425) | `project_payments_record` | `PaymentRecordRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `PaymentRecordResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/payments/{payment_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20501) | `project_payment_void` | `PaymentVoidRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`payment_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `PaymentsSummary`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/payments/{payment_id}/receipt/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20745) | `project_payment_receipt` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`payment_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `PaymentReceiptAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/positions/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20821) | `positions_create` | `PositionWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `PositionResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/reset-pricing/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21427) | `projects_reset_pricing` | `ResetPricingRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/services/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21509) | `projectExtraServices` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ServicesResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/projects/{project_id}/services/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21578) | `projectExtraServicesSave` | `ServicesWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ServicesResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/successor/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21660) | `projects_start_successor` | `SuccessorRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ProjectResponse`<br>`201` → `ProjectResponse`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/thermal/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21742) | `project_thermal_report` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ThermalReport`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/projects/{project_id}/thermal/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21811) | `project_thermal_save` | `ThermalWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ThermalReport`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/thermal/{position_id}/alternatives/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21887) | `thermal_compliant_alternative` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`position_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ThermalAlternative`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/sii/cafs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23917) | `sii_cafs_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `SiiCafList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/sii/cafs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23980) | `sii_caf_register` | `SiiCafUploadRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `SiiCaf`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/sii/certificate/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L24050) | `sii_certificate_status` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `SiiCertificateStatus`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/sii/certificate/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L24113) | `sii_certificate_upload` | `SiiCertificateUploadRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `SiiCertificate`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.3 Catálogo e ingesta — 46

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/catalog-imports/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3126) | `catalog_imports_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CatalogImportListResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalog-imports/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3189) | `catalog_imports_create` | `ImportUploadRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `CatalogImportCreateResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalog-imports/schema/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3872) | `catalog_template_schema` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CatalogTemplateSchema`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalog-imports/template/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3936) | `catalog_template_download` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`format` · query · `string`<br>`sheet` · query · `string` | `200` → `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalog-imports/{import_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3259) | `catalog_import_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `CatalogImportDetailResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalog-imports/{import_id}/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3329) | `catalog_import_confirm` | `CatalogImportConfirmRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `CatalogImportConfirmResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalog-imports/{import_id}/export/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3411) | `catalog_import_export` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)`<br>`sheet` · query · `string` | `200` → `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalog-imports/{import_id}/publish/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3497) | `catalog_import_publish` | `CatalogPublishRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `CatalogImportConfirmResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalog-imports/{import_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3573) | `catalog_import_review` | `CatalogReviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `CatalogReviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalog-imports/{import_id}/source/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3649) | `catalog_import_source` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalog-imports/{import_id}/timeline/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3720) | `catalog_import_timeline` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `CatalogImportTimeline`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalog-imports/{import_id}/undo/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3790) | `catalog_import_undo` | `CatalogUndoRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`import_id` * · path · `string (uuid)` | `200` → `CatalogImportDetailResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/articles/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4023) | `catalog_article_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` · query · `string (uuid)` | `200` → `ArticleList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/articles/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4085) | `catalog_article_create` | `ArticleWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `ArticleResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/catalogs/articles/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4286) | `catalog_article_delete` | Sin body declarado | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `204` → Sin body declarado<br>Códigos: `204`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/articles/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4149) | `catalog_article_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `ArticleResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/catalogs/articles/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4212) | `catalog_article_update` | `PatchedArticleWriteRequest`<br>Body opcional | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `ArticleResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/articles/{row_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4352) | `catalog_article_review` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `ArticleResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Mark the row technically reviewed; LEGACY_UNVERIFIED provenance becomes MANUAL. |
| [GET `/api/v1/catalogs/evidence/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4418) | `catalog_evidence_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` * · query · `string (uuid)` | `200` → `EvidenceList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | GET evidence/?system_id= — the source trail behind a system's parameters. POST — a member declares evidence (declared PENDING; the review stamp is a separate server-set transition). |
| [POST `/api/v1/catalogs/evidence/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4486) | `catalog_evidence_declare` | `EvidenceInputRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `EvidenceRow`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | GET evidence/?system_id= — the source trail behind a system's parameters. POST — a member declares evidence (declared PENDING; the review stamp is a separate server-set transition). |
| [POST `/api/v1/catalogs/evidence/{row_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4554) | `catalog_evidence_review` | `EvidenceReviewInputRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `EvidenceRow`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | POST evidence/{id}/review/ — stamp a review verdict. The reviewer identity and timestamp come from the request, never from the client. |
| [POST `/api/v1/catalogs/glass/preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4627) | `catalog_glass_preview` | `GlassPreviewInputRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `GlassPreviewOutput`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/glass/rules/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4691) | `catalog_glass_rules` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `GlassRulesOutput`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/catalogs/glass/rules/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4748) | `catalog_glass_rules_replace` | `GlassRulesRequest`<br>Body obligatorio | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)` | `200` → `GlassRulesOutput`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/glass/variants/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4818) | `catalog_glass_variant_publish` | `GlassVariantRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `GlassVariantOutput`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/glazing/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4882) | `catalog_bead_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` · query · `string (uuid)` | `200` → `BeadList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/glazing/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L4944) | `catalog_bead_create` | `BeadWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `BeadResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/catalogs/glazing/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5145) | `catalog_bead_delete` | Sin body declarado | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `204` → Sin body declarado<br>Códigos: `204`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/glazing/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5008) | `catalog_bead_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `BeadResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/catalogs/glazing/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5071) | `catalog_bead_update` | `PatchedBeadWriteRequest`<br>Body opcional | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `BeadResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/glazing/{row_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5211) | `catalog_bead_review` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `BeadResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Mark the row technically reviewed; LEGACY_UNVERIFIED provenance becomes MANUAL. |
| [GET `/api/v1/catalogs/hardware-kits/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5277) | `catalog_kit_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`system_id` · query · `string (uuid)` | `200` → `KitList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/hardware-kits/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5339) | `catalog_kit_create` | `KitWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `KitResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/catalogs/hardware-kits/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5540) | `catalog_kit_delete` | Sin body declarado | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `204` → Sin body declarado<br>Códigos: `204`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/hardware-kits/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5403) | `catalog_kit_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `KitResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/catalogs/hardware-kits/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5466) | `catalog_kit_update` | `PatchedKitWriteRequest`<br>Body opcional | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `KitResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/hardware-kits/{row_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5606) | `catalog_kit_review` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `KitResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Mark the row technically reviewed; LEGACY_UNVERIFIED provenance becomes MANUAL. |
| [GET `/api/v1/catalogs/process-profiles/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5672) | `catalog_process_profile_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `ProcessProfileOptionList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | GET process-profiles/ — the declared process authorities an org may bind a system to (global library plus org-owned rows). |
| [POST `/api/v1/catalogs/section-imports/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5733) | `catalog_section_import_create` | `object`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)` | `200` → `SectionImportResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | POST section-imports/ — upload a DXF/SVG drawing, get back the stored document path + detected outline candidates for human review. |
| [GET `/api/v1/catalogs/systems/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5803) | `catalog_system_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `SystemList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/systems/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5860) | `catalog_system_create` | `SystemWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `SystemResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [DELETE `/api/v1/catalogs/systems/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6061) | `catalog_system_delete` | Sin body declarado | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `204` → Sin body declarado<br>Códigos: `204`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/catalogs/systems/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5924) | `catalog_system_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `SystemResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/catalogs/systems/{row_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L5987) | `catalog_system_update` | `PatchedSystemWriteRequest`<br>Body opcional | `If-Match` * · header · `string`<br>`X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `SystemResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/catalogs/systems/{row_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6127) | `catalog_system_review` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `SystemResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | Mark the row technically reviewed; LEGACY_UNVERIFIED provenance becomes MANUAL. |
| [GET `/api/v1/catalogs/systems/{row_id}/workspace/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L6193) | `catalog_system_workspace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`row_id` * · path · `string (uuid)` | `200` → `SystemWorkspace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `503` | `SupabaseBearer` | GET systems/&lt;id&gt;/workspace/ — the §06 aggregate read: identity + readiness + every entity bound to the system in one fetch. |

### B.4 Evaluación del motor — 6

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [POST `/api/v1/engine/assembly/calculate/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8170) | `engine_assembly_calculate` | `EngineAssemblyCalculateRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `EngineAssemblyCalculateResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `422` | `SupabaseBearer` | Evaluate a compositional product (modules + couplings). Same auth/RLS flow as EngineCalculateView; all mathematics stay in /engine. The response separates geometry validity from manufacturing completeness and carries plan-view geometry for the editor. |
| [POST `/api/v1/engine/calculate/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8240) | `engine_calculate` | `EngineCalculateRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `EngineCalculateResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/engine/inspect/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8310) | `engine_inspect` | `EngineInspectRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `EngineInspectResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/engine/layout/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8386) | `engine_layout` | `EngineCalculateRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `EngineLayoutResponse`<br>Códigos: `200` | `SupabaseBearer` | Expose traversal dimensions without adding a second geometry implementation. |
| [POST `/api/v1/engine/optimize-cut/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8421) | `engine_optimize_cut` | `EngineOptimizeRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `EngineOptimizeResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/engine/systems/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8497) | `engine_systems` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `EngineSystemsResponse`<br>Códigos: `200`, `400`, `401`, `403`, `409` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.5 Precios — 13

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [POST `/api/v1/pricing/acknowledge/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12250) | `pricing_acknowledge` | `AcknowledgeRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AdminResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/pricing/admin/{resource}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12320) | `pricing_admin_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`resource` * · path · `string` | `200` → `AdminResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/admin/{resource}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12388) | `pricing_admin_write` | `AdminWriteRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`resource` * · path · `string` | `200` → `AdminResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/design-batch-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12463) | `pricing_design_batch_preview` | `DesignBatchPreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `DesignBatchPreviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/drafts/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12533) | `pricing_create_draft` | `DraftProjectRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `DraftResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/import/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12603) | `pricing_import_xlsx` | `ImportRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AdminResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/pricing/operations/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12673) | `pricing_operations` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `PriceResponse[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/pricing/operations/{operation_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12739) | `pricing_operation` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`operation_id` * · path · `string (uuid)` | `200` → `PriceResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/operations/{operation_id}/apply/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12809) | `pricing_apply` | `ApplyRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`operation_id` * · path · `string (uuid)` | `200` → `PriceResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/operations/{operation_id}/withdraw/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12885) | `pricing_withdraw` | `WithdrawRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`operation_id` * · path · `string (uuid)` | `200` → `PriceResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/pricing/options/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L12961) | `pricing_options` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `PricingOptions`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13025) | `pricing_preview` | `PriceRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `PriceResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/pricing/workspace/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13095) | `pricing_workspace` | `PriceRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `WorkspaceResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.6 Documentos — 11

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [POST `/api/v1/documents/artifacts/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7298) | `documentary_generate_artifact` | `ArtifactRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `ArtifactResponse`<br>`201` → `ArtifactResponse`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/documents/artifacts/{artifact_id}/access/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7380) | `documentary_artifact_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`artifact_id` * · path · `string (uuid)` | `200` → `SignedAccessResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/documents/projects/{project_id}/artifacts/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7450) | `documentary_list_artifacts` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ArtifactListResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/documents/projects/{project_id}/freeze/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7520) | `documentary_freeze_revision_a` | `FreezeRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `FreezeResponse`<br>`201` → `FreezeResponse`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/documents/projects/{project_id}/inputs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7608) | `documentary_prepare_inputs` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `DocumentaryPreparationResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/documents/projects/{project_id}/inputs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7677) | `documentary_save_inputs` | `DocumentaryInputsRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `DocumentaryInputsResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/documents/projects/{project_id}/issue/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7759) | `quotation_issue` | `QuotationIssueRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `QuotationIssue`<br>`201` → `QuotationIssue`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/documents/projects/{project_id}/quotation-customer/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7847) | `quotation_save_customer` | `PatchedQuotationCustomerRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `QuotationCustomer`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/documents/projects/{project_id}/quotation-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7928) | `quotation_prepare_preview` | `QuotationPreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `201` → `QuotationPreview`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/documents/projects/{project_id}/quotation-previews/{preview_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8010) | `quotation_preview_access` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`preview_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `QuotationPreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/documents/projects/{project_id}/versions/compare/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8086) | `documents_compare_versions` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`base` * · query · `string`<br>`head` * · query · `string`<br>`project_id` * · path · `string (uuid)` | `200` → `RevisionCompareResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.7 Correo, portal y otras rutas compartidas — 20

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/dev/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L7232) | `mail_examples` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `MailExample[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9831) | `mail_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` · query · `string (uuid)` | `200` → `MailRecord[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/mail/{mail_id}/recover/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9902) | `mail_recover` | `MailRecoveryRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`mail_id` * · path · `string (uuid)` | `200` → `MailRecord`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/organization/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L10944) | `mail_integration_status` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `MailIntegration`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/portal/payments/{context_id}/return/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11363) | `portal_payment_return` | Sin body declarado | `access` * · query · `string`<br>`context_id` * · path · `string (uuid)`<br>`redirect` · query · `boolean` | `200` → `PortalPayReturn`<br>`302` → Sin body declarado<br>Códigos: `200`, `302`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/portal/payments/{context_id}/return/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11436) | `portal_payment_provider_return` | Sin body declarado | `access` * · query · `string`<br>`context_id` * · path · `string (uuid)` | `302` → Sin body declarado<br>Códigos: `302`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/portal/quotes/{token}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11500) | `portal_quote_retrieve` | Sin body declarado | `token` * · path · `string` | `200` → `PortalQuote`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Public quote summary behind a share token. |
| [POST `/api/v1/portal/quotes/{token}/decide/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11563) | `portal_quote_decide` | `DecideRequestRequest`<br>Body obligatorio | `token` * · path · `string` | `200` → `PortalQuote`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Customer approves or declines the shared quote. |
| [POST `/api/v1/portal/quotes/{token}/pay/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L11638) | `portal_quote_pay` | `PortalPayRequestRequest`<br>Body obligatorio | `token` * · path · `string` | `200` → `PortalPayResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/finish-preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22109) | `projectFinishPreview` | `FinishPreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `FinishPreviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/approve/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L18151) | `project_quote_approve_internal` | `InternalApprovalRequest`<br>Body opcional | `project_id` * · path · `string (uuid)` | `200` → `InternalApprovalResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Staff records that the customer approved the quote off-channel — same audit trail and project transition as a portal decision. |
| [GET `/api/v1/projects/{project_id}/payments/{payment_id}/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20582) | `payment_mail_preview` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`payment_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `MailPreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/payments/{payment_id}/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20657) | `payment_mail_send` | `MailSendRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`payment_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `MailRecord`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/projects/{project_id}/quote-link/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20897) | `project_quote_links_list` | Sin body declarado | `project_id` * · path · `string (uuid)` | `200` → `ApprovalRecord[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Every approval link minted for the project, newest first. |
| [POST `/api/v1/projects/{project_id}/quote-link/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L20962) | `project_quote_link_create` | Sin body declarado | `project_id` * · path · `string (uuid)` | `200` → `ShareQuoteResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Mint a customer-approval link for the latest sealed version. |
| [PUT `/api/v1/projects/{project_id}/quote-links/{approval_id}/deadline/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21026) | `project_quote_link_deadline` | `LinkDeadlineRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`approval_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ApprovalRecord[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/quote-links/{approval_id}/regenerate/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21116) | `project_quote_link_regenerate` | `LinkRegenerateRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`approval_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ShareQuoteResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/quote-links/{approval_id}/revoke/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21204) | `project_quote_link_revoke` | Sin body declarado | `approval_id` * · path · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `ApprovalRecord[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Revoke a PENDING customer-approval link — the token dies immediately. |
| [GET `/api/v1/projects/{project_id}/quote-mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21276) | `quote_mail_preview` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `MailPreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/projects/{project_id}/quote-mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L21345) | `quote_mail_send` | `MailSendRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` * · path · `string (uuid)` | `200` → `MailRecord`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.8 Producción y CNC — 58

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/production/cnc/machines/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13165) | `production_cnc_machines` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CncMachineList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/cnc/machines/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13229) | `production_cnc_machine_create` | `CncMachineRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `CncMachine`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/production/cnc/machines/{machine_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13306) | `production_cnc_machine_update` | `PatchedCncMachinePatchRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`machine_id` * · path · `string (uuid)` | `200` → `CncMachine`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/cnc/programs/{program_id}/file/{filename}`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13388) | `production_cnc_program_file` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`filename` * · path · `string`<br>`program_id` * · path · `string (uuid)` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/cnc/tools/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13467) | `production_cnc_tools` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CncToolList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/cnc/tools/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13531) | `production_cnc_tool_create` | `CncToolRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `CncTool`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PATCH `/api/v1/production/cnc/tools/{tool_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13608) | `production_cnc_tool_update` | `PatchedCncToolPatchRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`tool_id` * · path · `string (uuid)` | `200` → `CncTool`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/cnc/workspace/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13690) | `production_cnc_workspace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `CncWorkspace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/glass-orders/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14129) | `production_glass_order` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`export_format` · query · `string`<br>`orders` * · query · `string` | `200` → `GlassOrder`, `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/operator-station/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14216) | `production_operator_station` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `OperatorStation`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/production/operator-station/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14279) | `production_operator_station_select` | `OperatorStationRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `OperatorStation`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14355) | `production_orders` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`project_id` · query · `string (uuid)` | `200` → `ProductionOrderList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14424) | `production_order_detail` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ProductionOrderDetail`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/cancel/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14494) | `production_order_cancel` | `WorkOrderCancelRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ProductionOrderDetail`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/cnc-export/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14576) | `production_order_cnc_export` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `CncExport`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/cnc-export/{filename}`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14646) | `production_order_cnc_file` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`filename` * · path · `string`<br>`order_id` * · path · `string (uuid)` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/cnc/preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14721) | `production_order_cnc_preview` | `CncPreviewRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `CncPreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/cnc/programs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14804) | `production_order_cnc_programs` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `CncProgramList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/cnc/programs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14874) | `production_order_cnc_program_generate` | `CncGenerateRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `CncProgram`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/cnc/readiness/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14957) | `production_order_cnc_readiness` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `CncReadiness`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/cut-pack/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15028) | `production_order_cut_pack` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`grouped` · query · `boolean`<br>`order_id` * · path · `string (uuid)` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/delivery/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15102) | `production_order_delivery` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DeliveryResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/production/orders/{order_id}/delivery/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15171) | `production_order_delivery_schedule` | `DeliveryScheduleRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DeliveryResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/delivery/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15253) | `production_order_delivery_confirm` | `DeliveryConfirmRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DeliveryConfirmResponse`<br>`201` → `DeliveryConfirmResponse`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/delivery/confirmation/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15341) | `production_order_delivery_confirmation` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`delivery` · query · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DeliveryConfirmationAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/delivery/transition/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15417) | `production_order_delivery_transition` | `DeliveryTransitionRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DeliveryResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/dispatch-note-dte/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15657) | `production_order_dispatch_note_dte` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DispatchNoteDteAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/dispatch-note-dte/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15726) | `production_order_dispatch_note_dte_emit` | `DispatchNoteDteEmitRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `DispatchNoteDte`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/dispatch-note-envio/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15807) | `production_order_dispatch_note_dte_envio` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `SiiEnvioAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/dispatch-note-envio/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15876) | `production_order_dispatch_note_dte_envio_send` | `SiiEnvioSendRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `SiiEnvio`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/dispatch-note-void/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15957) | `production_order_dispatch_note_void` | `DispatchNoteVoidRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ProductionOrderDetail`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/dispatch-note/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15580) | `production_order_dispatch_note` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`note` · query · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `DispatchNoteAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/dispatch/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L15499) | `production_order_dispatch` | `DispatchRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ProductionOrderDetail`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/dxf-export/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16039) | `production_order_dxf_export` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `DxfExport`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/dxf-export/{filename}`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16109) | `production_order_dxf_file` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`filename` * · path · `string`<br>`order_id` * · path · `string (uuid)` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/install/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16184) | `production_order_install` | `InstallationRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ProductionOrderDetail`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/labels/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16265) | `production_order_labels` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `PackingLabels`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/material-recheck/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16335) | `production_order_material_recheck` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `MaterialRecheck`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/operations-export/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16405) | `production_order_ops_export` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `OpsExport`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/operations-export/{filename}`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16475) | `production_order_ops_file` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`filename` * · path · `string`<br>`order_id` * · path · `string (uuid)` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/optimize/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16550) | `production_order_optimize` | `WorkOrderOptimizeRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `WorkOrderOptimize`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/optimize/compare/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16631) | `production_order_optimize_compare` | `WorkOrderOptimizeCompareRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `WorkOrderOptimizeCompare`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/packing/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16712) | `production_order_packing` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `PackingManifest`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/piece-labels/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16782) | `production_order_piece_labels` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`grouped` · query · `boolean`<br>`order_id` * · path · `string (uuid)`<br>`paper` · query · `string` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/production-pack/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16864) | `production_order_pack` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `string`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/qc-remake/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L16934) | `production_qc_remake` | `QcRemakeRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `ProductionOrderDetail`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/orders/{order_id}/remake/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17016) | `production_order_remake` | `RemakeRequestRequest`<br>Body opcional | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `ProductionOrderDetail`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/orders/{order_id}/trace/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17097) | `production_order_trace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ProductionOrderTrace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/pieces/{piece_id}/trace/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17167) | `production_piece_trace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`piece_id` * · path · `string` | `200` → `ProductionPieceTrace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/prep/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17236) | `production_prep` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `ProductionPrep`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/station-queue/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17300) | `production_station_queue` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `ProductionStationQueue`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Cross-order floor view: open steps grouped by station — what each bench/cell has queued, which one is next, which are blocked. |
| [POST `/api/v1/production/steps/{step_id}/transition/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17367) | `production_step_transition` | `StepTransitionRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`step_id` * · path · `string (uuid)` | `200` → `StepTransition`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/versions/{version_id}/hardware-picking/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17449) | `production_version_hardware_picking` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`version_id` * · path · `string (uuid)` | `200` → `VersionHardwarePicking`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/versions/{version_id}/release/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17519) | `production_release` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`version_id` * · path · `string (uuid)` | `200` → `ProductionRelease`<br>`201` → `ProductionRelease`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/versions/{version_id}/trace/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17595) | `production_version_trace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`version_id` * · path · `string (uuid)` | `200` → `ProductionVersionTrace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/work-centers/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17665) | `production_work_centers` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `WorkCenterList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/work-centers/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17728) | `production_work_centers_create` | `WorkCenterRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `WorkCenter`<br>`201` → `WorkCenter`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/work-centers/seed-defaults/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L17810) | `production_work_centers_seed_defaults` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `WorkCenterList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.9 Inventario — 15

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/inventory/bar-authorities/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8543) | `inventory_bar_authorities` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `BarAuthorityList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/inventory/movements/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8607) | `inventory_movements` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`item_id` · query · `string (uuid)`<br>`limit` · query · `integer` | `200` → `InventoryMovements`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/movements/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8682) | `inventory_movements_record` | `InventoryMovementRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `InventoryMovement`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/orders/{order_id}/receipts/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8758) | `inventory_order_receive` | `OrderReceiptRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `OrderReceiving`<br>`201` → `OrderReceiving`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/inventory/orders/{order_id}/receiving/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8846) | `inventory_order_receiving` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `OrderReceiving`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/inventory/remnants/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8916) | `inventory_remnants` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`kind` · query · `string`<br>`status` · query · `string` | `200` → `RemnantList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/remnants/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9005) | `inventory_remnant_create` | `RemnantCreateRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `Remnant`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/inventory/remnants/{remnant_id}/label/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9081) | `inventory_remnant_label` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`remnant_id` * · path · `string (uuid)` | `200` → `RemnantLabel`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/remnants/{remnant_id}/move/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9151) | `inventory_remnant_move` | `RemnantMoveRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`remnant_id` * · path · `string (uuid)` | `200` → `Remnant`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/remnants/{remnant_id}/release/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9233) | `inventory_remnant_release` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`remnant_id` * · path · `string (uuid)` | `200` → `Remnant`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/remnants/{remnant_id}/reserve/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9303) | `inventory_remnant_reserve` | `RemnantReserveRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`remnant_id` * · path · `string (uuid)` | `200` → `Remnant`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/remnants/{remnant_id}/scrap/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9385) | `inventory_remnant_scrap` | `RemnantActionRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`remnant_id` * · path · `string (uuid)` | `200` → `Remnant`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/inventory/sheet-formats/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9467) | `inventory_sheet_formats` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `SheetFormatList`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/inventory/sheet-formats/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9530) | `inventory_sheet_format_declare` | `SheetFormatRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `SheetFormatCreated`<br>`201` → `SheetFormatCreated`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/inventory/stock/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9612) | `inventory_stock` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `InventoryStock`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.10 Compras — 14

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/purchasing/needs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22800) | `purchasing_needs` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `PurchaseNeeds`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/needs/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22864) | `purchasing_needs_confirm` | `PurchaseNeedsConfirmRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `PurchaseNeedsResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/purchasing/orders/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L22940) | `purchasing_orders_index` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `OrderIndexResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/orders/{order_id}/cancel/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23004) | `purchasing_cancel_order` | `SendOrderRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `OrderResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/purchasing/orders/{order_id}/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23086) | `purchasing_mail_preview` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `PurchaseMailPreview`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/orders/{order_id}/mail/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23155) | `purchasing_mail_send` | `PurchaseMailRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `PurchaseMailResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/orders/{order_id}/send/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23237) | `purchasing_send_order` | `SendOrderRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `OrderResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/purchasing/requirements/{requirement_id}/allocation/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23319) | `purchasing_allocate_requirement` | `AllocationRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`requirement_id` * · path · `string (uuid)` | `200` → `AllocationResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/purchasing/suppliers/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23401) | `purchasing_suppliers_index` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `SuppliersIndexResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/suppliers/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23464) | `purchasing_upsert_supplier` | `SupplierUpsertRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `Supplier`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/purchasing/versions/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23540) | `purchasing_versions` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `PurchasingState`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/purchasing/versions/{version_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23604) | `purchasing_version_state` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`version_id` * · path · `string (uuid)` | `200` → `PurchasingState`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/versions/{version_id}/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23674) | `purchasing_confirm_order_type` | `ConfirmBatchRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`version_id` * · path · `string (uuid)` | `200` → `OrderResponse[]`<br>`201` → `OrderResponse[]`<br>Códigos: `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/purchasing/versions/{version_id}/eligibilities/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23766) | `purchasing_create_eligibility` | `EligibilityRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`version_id` * · path · `string (uuid)` | `201` → `EligibilityResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.11 Terreno — 5

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/production/field/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13755) | `fieldWorkspace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `FieldWorkspace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/production/field/assets/{asset_id}/access/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13819) | `fieldAssetAccess` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`asset_id` * · path · `string (uuid)` | `200` → `FieldAssetAccess`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/field/schedule/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13889) | `fieldSchedule` | `FieldScheduleRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `201` → `FieldReceipt`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/field/visits/{visit_id}/commands/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L13965) | `fieldCommand` | `FieldCommandRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`visit_id` * · path · `string (uuid)` | `200` → `FieldReceipt`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/production/field/visits/{visit_id}/review/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L14047) | `fieldReview` | `FieldReviewRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`visit_id` * · path · `string (uuid)` | `200` → `FieldReviewResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.12 Analítica — 10

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/analytics/decision/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1264) | `analytics_decision_workspace` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`end` · query · `string (date)`<br>`start` · query · `string (date)` | `200` → `AnalyticsWorkspace`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/analytics/decision/export/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1338) | `analytics_decision_csv` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`end` · query · `string (date)`<br>`start` · query · `string (date)` | `200` → `string (binary)`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/analytics/orders/{order_id}/actual/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1413) | `analytics_actual_report` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ActualReportResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/analytics/orders/{order_id}/actual/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1482) | `analytics_actual_report_save` | `ActualReportRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `201` → `ActualReportResponse`<br>Códigos: `201`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/analytics/orders/{order_id}/actual/preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1564) | `analytics_actual_report_preview` | `ActualReportRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)`<br>`order_id` * · path · `string (uuid)` | `200` → `ActualReportResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/analytics/preferences/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1646) | `analytics_preferences` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `AnalyticsPreference`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/analytics/preferences/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1709) | `analytics_preferences_save` | `AnalyticsPreferenceRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AnalyticsPreference`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/analytics/quotations/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1785) | `analytics_quotations` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`attention` · query · `string`<br>`currency` · query · `string`<br>`limit` · query · `integer`<br>`offset` · query · `integer`<br>`phase` · query · `string`<br>`q` · query · `string` | `200` → `QuotationIndexResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/analytics/summary/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1915) | `analytics_operational_summary` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `OperationalSummary`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/analytics/today/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1979) | `analytics_today` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `TodayResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.13 IA — 17

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [POST `/api/v1/ai/agent/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L8) | `ai_agent` | `AiAgentRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `202` → `AiAgentAccepted`<br>Códigos: `202`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | The agent surface: a goal becomes a bounded observe → plan → propose loop. Queries run server-side inside typed projections; every emitted step is validated before it reaches the client, and nothing consequential executes without the human clicking on the real surface. |
| [GET `/api/v1/ai/ask/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L89) | `ai_ask_thread` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`refs` * · query · `string`<br>`surface` * · query · `string` | `200` → `AiAskTurn[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | The durable ask thread for this context — the dock restores it after reload so a conversation survives instead of resetting. |
| [POST `/api/v1/ai/ask/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L169) | `ai_ask` | `AiAskRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AiAskResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Contextual "Preguntar a DEKOPEN" — the question and surface come from the client; every fact in the context is queried server-side under the caller's RLS. The provider answers inside that projection only. |
| [POST `/api/v1/ai/connection-test/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L249) | `ai_connection_test` | `AiConnectionTestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AiConnectionResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/ai/invoke/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L325) | `ai_invoke` | `AiInvokeRequestRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AiInvokeResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/ai/jobs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L401) | `ai_job_list` | Sin body declarado | `before` · query · `string (date-time)`<br>`before_id` · query · `string (uuid)` | `200` → `AiJob[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | The caller's recent AI jobs — the workspace's left rail. |
| [DELETE `/api/v1/ai/jobs/{job_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L538) | `ai_job_cancel` | Sin body declarado | `job_id` * · path · `string (uuid)` | `200` → `AiJob`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | One job with its full transcript; DELETE cancels a live run. |
| [GET `/api/v1/ai/jobs/{job_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L475) | `ai_job_retrieve` | Sin body declarado | `job_id` * · path · `string (uuid)` | `200` → `AiJobDetail`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | One job with its full transcript; DELETE cancels a live run. |
| [POST `/api/v1/ai/jobs/{job_id}/messages/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L602) | `ai_job_message_create` | `AiJobMessageRequest`<br>Body obligatorio | `job_id` * · path · `string (uuid)` | `202` → `AiAgentAccepted`<br>Códigos: `202`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | §07-B follow-up instructions: appends a user turn and runs the agent again inside the same job — transcript, plan and artifacts keep accumulating; the earlier result is never deleted. |
| [POST `/api/v1/ai/jobs/{job_id}/outcome/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L681) | `ai_job_outcome_create` | `AiJobOutcomeRequest`<br>Body obligatorio | `job_id` * · path · `string (uuid)` | `200` → `AiJobOutcomeResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | §08 measurement — the client reports what the human did with a proposed step. Idempotent: a retried report dedupes on (turn, step, action) and answers 200 with recorded=false instead of double-counting. |
| [POST `/api/v1/ai/jobs/{job_id}/retry/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L761) | `ai_job_retry` | Sin body declarado | `job_id` * · path · `string (uuid)` | `202` → `AiJob`<br>Códigos: `202`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Re-run a retryable failed round. The goal is the FAILED round's own message — the last user turn in the transcript — not the job's original goal, so a retry of a failed follow-up doesn't silently re-execute the first request and emit a duplicate proposal. The payload's replay flag makes the transcript turn read as a re-run, not a new message. |
| [GET `/api/v1/ai/metrics/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L830) | `ai_metrics` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`days` · query · `integer` | `200` → `AiMetrics`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | §08 measurement — org-level AI metrics over the trailing window. |
| [GET `/api/v1/ai/mode/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L899) | `ai_mode_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `AiMode`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/ai/presence/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L963) | `ai_presence_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`refs` · query · `string`<br>`surface` * · query · `string` | `200` → `AiPresence`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Latest work for this caller and this exact stable context, without a page limit. |
| [GET `/api/v1/ai/settings/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1043) | `ai_settings_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `AiSettings`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [PUT `/api/v1/ai/settings/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1106) | `ai_settings_save` | `AiSettingsSaveRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `AiSettings`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/ai/usage/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L1182) | `ai_usage_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`capability` · query · `string`<br>`limit` · query · `integer`<br>`offset` · query · `integer`<br>`state` · query · `string` | `200` → `AiUsageWork[]`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.14 Jobs — 4

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/jobs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9676) | `jobs_list` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`limit` · query · `integer`<br>`offset` · query · `integer`<br>`state` · query · `string`<br>`type` · query · `string` | `200` → `JobRun[]`<br>Códigos: `200` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/jobs/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9735) | `jobs_enqueue` | `JobEnqueueRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `JobRun`<br>`201` → `JobRun`<br>Códigos: `200`, `201` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/jobs/{job_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9775) | `jobs_get` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`job_id` * · path · `string (uuid)` | `200` → `JobRun`<br>Códigos: `200` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/jobs/{job_id}/retry/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L9803) | `jobs_retry` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`job_id` * · path · `string (uuid)` | `200` → `JobRun`<br>Códigos: `200` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.15 Billetera y comercio de plataforma — 13

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/billing/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2225) | `billing_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `Billing`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/change/abandon/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2289) | `billing_change_abandon` | `ConfirmChangeRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `ChangeResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/change/confirm/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2365) | `billing_change_confirm` | `ConfirmChangeRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `ChangeResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/change/preview/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2441) | `billing_change_preview` | `ChangeInputRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `ChangeResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/checkout/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2517) | `billing_checkout` | `CheckoutInputRequest`<br>Body obligatorio | `X-Organization-ID` · header · `string (uuid)` | `200` → `CheckoutResult`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/billing/commerce/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2593) | `commerce_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `Commerce`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/flow/confirm/{order_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2657) | `flow_payment_confirm` | `FlowConfirmationRequest`<br>Body obligatorio | `order_id` * · path · `string (uuid)` | `200` → `FlowAcknowledgement`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/flow/plan/{offer_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2726) | `flow_subscription_confirm` | `FlowConfirmationRequest`<br>Body obligatorio | `offer_id` * · path · `string (uuid)` | `200` → `FlowAcknowledgement`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/flow/refund/{operation_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2795) | `flow_refund_confirm` | `FlowConfirmationRequest`<br>Body obligatorio | `operation_id` * · path · `string (uuid)` | `200` → `FlowAcknowledgement`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/flow/register/{operation_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2864) | `flow_registration_confirm` | `FlowConfirmationRequest`<br>Body obligatorio | `operation_id` * · path · `string (uuid)` | `200` → `FlowAcknowledgement`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/flow/registration-return/{operation_id}/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2933) | `flow_registration_return` | `FlowConfirmationRequest`<br>Body obligatorio | `operation_id` * · path · `string (uuid)` | `303` → Sin body declarado<br>Códigos: `303`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | Alternativa sin esquema | Sin descripción adicional en OpenAPI. |
| [POST `/api/v1/billing/sync/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L2998) | `billing_sync` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `Billing`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |
| [GET `/api/v1/billing/wallet/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L3062) | `wallet_retrieve` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)` | `200` → `Wallet`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

### B.16 Búsqueda — 1

| Método / ruta | operationId | Entrada | Parámetros | Respuestas | Seguridad declarada | Extracto del contrato |
|---|---|---|---|---|---|---|
| [GET `/api/v1/search/`](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/backend/openapi.yaml#L23848) | `global_search` | Sin body declarado | `X-Organization-ID` · header · `string (uuid)`<br>`q` * · query · `string` | `200` → `SearchResponse`<br>Códigos: `200`, `400`, `401`, `403`, `404`, `409`, `422`, `503` | `SupabaseBearer` | Sin descripción adicional en OpenAPI. |

<a id="anexo-c"></a>

## Anexo C. Los 55 módulos del motor

Propósitos sintetizados de su código/docstrings. Los símbolos son funciones y clases declaradas a nivel de módulo; no incluyen cada método, atributo, importación o alias. Se deduplican overloads del mismo nombre. Su presencia no convierte una capacidad interna en un botón ni prueba que el catálogo de una empresa la habilite.


| Módulo / fuente | Propósito | Funciones y clases declaradas |
|---|---|---|
| [__init__.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/__init__.py) | Interfaz del paquete de cálculo puro. | Sin declaración pública top-level en este archivo |
| [advanced_openings.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/advanced_openings.py) | Recetas avanzadas con fuente, límites y proyecciones físicas. | `recipe_geometry_context`, `has_advanced_opening`, `requires_recipe`, `capability_family`, `validate_capability_recipes`, `validate_recipe_bindings`, `resolve_recipe`, `validate_recipe_limits`, `plan_endpoints`, `passage_endpoints` |
| [analytics.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/analytics.py) | Costos reales, balances y puente de margen sobre evidencia inmutable. | `number`, `decimal_text`, `ratio`, `total`, `average`, `remnant_quantity`, `actual_cost`, `margin_bridge`, `driver_sources`, `bar_reading` |
| [assembly_measures.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/assembly_measures.py) | Medidas exactas de conjunto y colocación desarrollada/proyectada. | `AssemblyModuleMeasure`, `AssemblyMeasure`, `developed_layout`, `assembly_measures` |
| [billing.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/billing.py) | Conversión comercial pura de la plataforma y derechos del plan. | `ai_usage_cost_usd`, `platform_charge_clp`, `upgrade_credits`, `product_terms` |
| [bom.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/bom.py) | Composición determinista de la lista de materiales. | `build_engine_result` |
| [catalog_authority.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/catalog_authority.py) | Hechos de revisión de catálogo y preservación histórica. | `section_review_facts`, `process_authority_gate`, `fabrication_authority_gate` |
| [catalog_rules.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/catalog_rules.py) | Compatibilidad por familia y reglas exactas de fabricación. | `CatalogRuleError`, `validate_family`, `sliding_parameters`, `leaf_profile_role`, `rounded_profile_cut`, `validate_profile_authority`, `reinforcement_sku`, `reinforcement_required`, `reinforcement_screws`, `validate_leaf_limits` |
| [cnc_authorization.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/cnc_authorization.py) | Autorización estricta del intercambio CNC nuevo. | `authorize_member_operations`, `section_fingerprint`, `member_preview`, `program_diff` |
| [collections.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/collections.py) | Proyección del acuerdo elegido y libro inmutable de cobros. | `PaymentMilestone`, `CollectionPayment`, `CollectionMilestone`, `CollectionSummary`, `credit_split`, `tax_percent`, `collection_summary` |
| [commercial.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/commercial.py) | Aritmética comercial con autoridades resueltas. | `PricingError`, `PricingMode`, `number`, `fraction`, `quantum`, `quantize_currency`, `convert_cost`, `direct_cost`, `matrix_price`, `typology_price`, `discount_state`, `validate_segment`, `unit_price`, `CommercialLine`, `indicative_line_net`, `assembly_sale_adjustment`, `CommercialResult`, `totals`, `finish_lines`, `_decimal_ratio`, `_currency_amount`, `target_project` |
| [contour.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/contour.py) | Geometría de contorno cerrado para formas no rectangulares. | `_q`, `_pt`, `_sub`, `_length`, `_dist`, `Contour`, `signed_area`, `ensure_ccw`, `_edge`, `arc_params`, `arc_length`, `contour_bounds`, `edge_length`, `_edge_tangent`, `interior_angle`, `validate_contour`, `_seg_intersects`, `edge_points`, `contour_points`, `contour_area`, `_offset_line`, `_line_intersect`, `_circle_line_intersect`, `_circle_circle_intersect`, `offset_contour`, `is_axis_aligned_rect` |
| [customer_accounts.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/customer_accounts.py) | Saldos de cliente separados por moneda/autoridad. | `CustomerAccount`, `customer_accounts` |
| [cutting.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/cutting.py) | Best Fit Decreasing exacto sobre stock y sierra declarados. | `InvalidCutContract`, `MissingStockAuthority`, `AmbiguousStockAuthority`, `MissingCuttingProfile`, `AmbiguousCuttingProfile`, `PieceLongerThanUsableStock`, `CutMaterial`, `CuttingProfile`, `CutPiece`, `StockRule`, `CutPlacement`, `RemnantBar`, `CutBar`, `UnplacedCut`, `CutPlanMetrics`, `PurchaseLine`, `CutOptimizationResult`, `pieces_from_result`, `_piece_order`, `_variants_of`, `_usable`, `_piece_fits`, `_angle_ok`, `_pack_remnant`, `_bfd_fill`, `_DeepBudgetExceeded`, `_enumerate_patterns`, `_deep_bins`, `_metrics_of`, `_cost_key`, `_emit_bars`, `_pack_group`, `optimize_cut` |
| [design_operations.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/design_operations.py) | Registro/ejecución de edición compartida y atómica. | `handled_leaf_keys`, `model_schema`, `optional`, `choice`, `spec`, `OperationError`, `_validate`, `validate_operation`, `fingerprint`, `decimal`, `mm`, `walk`, `as_product`, `_module`, `_target`, `_replace`, `_parent`, `_top`, `_layout`, `_opening`, `editable_legacy_openings`, `_new_id`, `_dimensions`, `_resize_module`, `_apply`, `_flip`, `_materialize`, `_structure`, `apply_operations` |
| [documentary_canonical.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/documentary_canonical.py) | Bytes canónicos e identidades SHA de evidencia documental. | `_datetime_text`, `_documentary_value`, `documentary_canonical_json_v1`, `documentary_sha256_v1`, `bom_hash_v1`, `snapshot_sha256_v1`, `file_sha256` |
| [drawing.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/drawing.py) | Cadenas de cotas técnicas sobre ejes declarados. | `DimensionSegment`, `DimensionChain`, `DrawingBay`, `DrawingHandleDatum`, `DrawingFacts`, `DrawingEnvelope`, `dimension_chains` |
| [extra_models.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/extra_models.py) | Contratos de accesorios/servicios con cantidades y tarifas autorizadas. | `ExtraModel`, `ExtraRate`, `ExtraDefinition`, `ExtraSelection`, `ExtraContext`, `ExtraAuthority`, `ExtraPolicy`, `ExtraFact`, `ExtraLine`, `ExtraSuggestion` |
| [extras.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/extras.py) | Cantidades, sugerencias y sublíneas de extras. | `AccessoryLeaf`, `position_price`, `price_facts`, `compatible`, `selected_definition`, `line`, `position_lines`, `suggestions`, `project_lines`, `PricePartition`, `partition_price`, `service_price`, `target_services`, `glass_bar_lines` |
| [finish_models.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/finish_models.py) | Autoridad de acabados común a catálogo, BOM y representación. | `FinishModel`, `FinishColor`, `FinishSurcharge`, `FinishCombination`, `FinishAuthority`, `ResolvedFinish` |
| [finishes.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/finishes.py) | Bicolor, refuerzo, límites, holgura, suministro y recargos. | `resolve_finish`, `finish_article`, `prepare_finish`, `validate_finish_size`, `finish_result`, `finish_surcharge`, `finish_description`, `finish_selling_delta`, `finish_rgb_css` |
| [geometry.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/geometry.py) | Geometría paramétrica determinista del núcleo. | `SlidingLayoutError`, `_moving_panel`, `resolved_sliding_layout`, `rail_count`, `sliding_travel`, `validate_sliding_layout`, `_Rect`, `_MemberPlacement`, `_GeometryAccumulator`, `_trace_point`, `_validate_leaf_limits`, `_trace_rect`, `_validate_advanced_limits`, `_trace_segment`, `welding_loss_per_end`, `joint_adjustment_per_end`, `_article`, `_normalize_top_node`, `reinforcement_cut_length`, `_append_profile`, `_append_frame`, `resolve_bead_rule`, `_append_glazing_beads`, `SashGeometry`, `_jointed_sash`, `single_rectangular_sash_geometry`, `rebate_depth`, `_end_milling_overlap`, `_pocket_dimension`, `_append_leaf`, `_append_frame_glazed_pane`, `_append_sliding`, `_append_paired_leaves`, `_append_advanced_bay`, `_append_bay`, `_append_door_frame`, `_append_door`, `_append_mullion`, `_walk_node`, `accessory_leaves`, `_append_extras`, `compute_geometry`, `calculate_geometry` |
| [glass.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/glass.py) | Espesor, área y masa de vidrio con Decimal. | `GlassMetadata`, `glass_piece_metadata`, `_parse_pane_thickness`, `derive_net_glass_thickness`, `exact_glass_area_m2`, `exact_glass_weight`, `build_glass_piece`, `migrate_glass_spec` |
| [glass_composition.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/glass_composition.py) | Recetas de vidrio, seguridad, facturación e instrucciones. | `GlassModel`, `GlassPly`, `GlassInterlayer`, `GlassPane`, `GlassChamber`, `GlassComposition`, `SupplierValue`, `SupplierSafety`, `GlassProperties`, `GlassLimits`, `GlassBilling`, `GlassProduct`, `GlassProcessing`, `GlassSafetyRule`, `GlassAssessment`, `_number`, `_pane`, `_chamber`, `parse_glass_notation`, `_format_number`, `format_glass_notation`, `net_glass_thickness`, `total_glass_thickness`, `glass_mass_per_m2`, `assess_glass_safety`, `assess_glass`, `GlassCharge`, `GlassPrice`, `price_glass`, `relative_glass_prices`, `glass_polygon_perimeter_m`, `candidate_leaf_mass`, `glass_section`, `glass_rate_requirements` |
| [glass_orders.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/glass_orders.py) | Pedido desde piezas selladas, sin reintroducir medidas. | `GlassSupplierRow`, `supplier_glass_rows` |
| [hardware.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/hardware.py) | Selección de kit según dimensiones acabadas y masa exacta. | `NoCompatibleHardwareKit`, `AmbiguousHardwareKit`, `normalize_opening_type`, `HardwareCandidateEvaluation`, `evaluate_hardware_candidates`, `resolve_hardware_evaluations`, `resolve_hardware_kit` |
| [hardware_classes.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/hardware_classes.py) | Expansión de componentes/clases, precios y picking sellado. | `parse_hardware_class`, `HardwareExpansion`, `HardwareRuleViolation`, `_component`, `expand_hardware`, `hardware_component_cost`, `hardware_cost`, `hardware_sale_price`, `hardware_total_sale_price`, `hardware_price_delta`, `hardware_picking` |
| [hardware_machining.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/hardware_machining.py) | Proyección neutra de mecanizados y brechas exactas. | `hardware_operations` |
| [hardware_proposals.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/hardware_proposals.py) | Propuestas de división valoradas mediante la misma geometría. | `split_hardware_bay` |
| [inspection_models.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/inspection_models.py) | Configuración, observaciones y contratos del inspector. | `InspectorConfigurationError`, `InspectorRuleId`, `InspectorSeverity`, `RuleEvaluationStatus`, `Fixability`, `InspectionMode`, `InspectorTarget`, `WorkshopAnnotations`, `StructuralInput`, `AddBottomDrainHole`, `DiffPreconditions`, `InspectorDiff`, `InspectorFinding`, `RuleEvaluation`, `InspectorResult`, `ExactRuleConfig`, `R01Config`, `R02Config`, `R03Config`, `R04Config`, `R05Config`, `R06Config`, `R07Config`, `R08Config`, `R09Config`, `R10Config`, `R11Config`, `R12Config`, `R13Config`, `R14Config`, `InspectorConfig`, `InspectorInput` |
| [inspector.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/inspector.py) | Verificación de taller sobre hechos exactos y observaciones explícitas. | `_drain_diff`, `_glass_class`, `inspect`, `apply_inspector_diff` |
| [inventory.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/inventory.py) | Cobertura de stock y totales declarados de compra. | `stock_shortfall`, `purchase_total`, `purchase_glass_areas`, `purchase_source_ledger` |
| [layout.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/layout.py) | Medidas de presentación y offsets del recorrido canónico. | `AxisOffsets`, `NodeLayout`, `node_layout` |
| [manufacturing.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/manufacturing.py) | Proyección industrial desde traza semántica a hechos de taller. | `ManufacturingAuthorityError`, `VerticalReference`, `PlacementOffsetV1`, `ManufacturingPlacementPolicyV1`, `_json_decimal`, `handle_policy_from_json`, `_placement_offset_from_json`, `placement_policy_from_json`, `reinforcement_policy_from_json`, `HandleIntentV1`, `HandleSlotRuleV1`, `HandleRequirementPolicyV1`, `handle_rules_for_leaf`, `ReinforcementCutRuleV1`, `ReinforcementCutPolicyV1`, `PhysicalMemberIdentityV1`, `PhysicalMemberFactV1`, `ReinforcementFactV1`, `LeafAssemblyFactV1`, `InfillLocationFactV1`, `HandleLocationFactV1`, `PhysicalRelationshipV1`, `ManufacturingFactsV1`, `_segment_for_side`, `_offset_rect`, `_offset_segment`, `_one_offset`, `_member_side`, `_vertical_coordinate`, `_matching_reinforcement_rule`, `project_manufacturing_facts_v1` |
| [manufacturing_trace.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/manufacturing_trace.py) | Identidad/traza física emitida durante geometría. | `PlacementDomain`, `MemberSide`, `Axis`, `TracePointV1`, `TraceRectV1`, `TraceSegmentV1`, `SemanticLeafTraceV1`, `SemanticInfillTraceV1`, `SemanticMemberTraceV1`, `GeometryManufacturingTraceV1` |
| [models.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py) | Tipos serializables de geometría, catálogo y evaluación. | `EngineModel`, `MaterialType`, `SystemFamily`, `RailType`, `ProfileRole`, `NodeType`, `BayOpeningType`, `OpeningMovement`, `HingeSide`, `OpeningDirection`, `LeafRole`, `OpeningUse`, `Opening`, `HingedLeaf`, `HingedLayout`, `PairedLeafRule`, `OpeningHandleRule`, `AdvancedPanel`, `AdvancedOpeningRecipe`, `OpeningCapability`, `SlidingPanelKind`, `SlidingTravel`, `SlidingPanel`, `SlidingLayout`, `PlanPoint`, `GlassPiece`, `HardwareQuantityRule`, `HardwareLengthRule`, `HardwareMachiningRule`, `HardwareComponentRule`, `HardwareHandleColor`, `HardwareHandleModel`, `HardwareOption`, `HardwareClassAuthority`, `HardwareSelection`, `HardwareResolution`, `HardwareComponent`, `HardwareItem`, `HardwareKitRule`, `SectionPoint`, `SectionAxis`, `_segments_properly_intersect`, `polygon_self_intersects`, `ProfileSection`, `ProfileCutRule`, `ProfileReinforcementRule`, `CouplerRule`, `EffectiveProfileArticle`, `GlazingBeadRule`, `PanelRule`, `PanelPiece`, `LeafWeight`, `SlidingSystemParameters`, `SystemDimensionalLimit`, `SystemParams`, `ParametricNode`, `ProfileCut`, `FittingPiece`, `ReinforcementPiece`, `OpeningHandleFact`, `LeafOpeningFact`, `OpeningPlanPoint`, `AdvancedLeafFact`, `EngineResult` |
| [mounting.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/mounting.py) | Medición de vano y dimensión de fabricación con holguras sourced. | `MountingModel`, `Allowance`, `MountingRule`, `FabricationOverride`, `OpeningSurvey`, `merge_mounting_extras`, `AxisDerivation`, `MountingResult`, `derive_fabrication`, `validate_mounting_extras`, `resize_contour` |
| [nesting.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/nesting.py) | Guillotina 2D de láminas y formatos declarados. | `PieceLargerThanUsableSheet`, `NestPiece`, `SheetRule`, `NestPlacement`, `SheetRemnant`, `ProducedRemnant`, `SheetLayout`, `SheetPurchase`, `SheetNestingResult`, `_FreeRect`, `_Placed`, `_SheetBin`, `_fits`, `_piece_key`, `_piece_fits`, `_split`, `_prune`, `_choose_split`, `_pack`, `nest_rects` |
| [openings.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/openings.py) | Semántica física de apertura y adaptación histórica. | `OpeningCapabilityError`, `opening_from_legacy`, `legacy_from_opening`, `node_opening`, `node_use`, `fabrication_alias`, `matches_capability`, `resolve_capability`, `normalize_opening_tree`, `geometry_opening_type`, `handle_fact`, `opening_label` |
| [operations.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/operations.py) | Operaciones industriales neutrales de máquina. | `OperationKind`, `CoordinateSystem`, `ToolKind`, `MemberFace`, `ClampZone`, `Tool`, `MachineProfile`, `ManufacturingOperation`, `_num`, `_op_id`, `_face`, `_piece_detail`, `_saw_ops`, `_member_ops`, `operations_from_plan`, `member_meta_map`, `ops_document`, `_group`, `ops_fingerprint`, `PostProcessor`, `NeutralOpsPostProcessor`, `_cell`, `OperationValidation`, `validate_operations`, `member_program`, `program_fingerprint` |
| [panel.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/panel.py) | Geometría y masa de panel con su densidad/autoridad propia. | `exact_panel_weight`, `build_panel_piece` |
| [price_workspace.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/price_workspace.py) | Lecturas comerciales y atribución exacta de deltas. | `percent_points`, `money_trace`, `linear_purchase`, `gross_margin`, `policy`, `comparison`, `cascade`, `unit_price_trace`, `composition`, `undiscounted_lines`, `explain` |
| [pricing.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/pricing.py) | Primitivas de margen bruto. | `_require_nonnegative`, `price_from_cost_and_margin`, `gross_margin_pct` |
| [product.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py) | Modelo compuesto, evaluaciones de conjunto/contorno/sin marco y cambios. | `ProductStatus`, `Severity`, `IssueCode`, `ConnectionKind`, `EdgeSide`, `CouplingDef`, `FramelessSupportKind`, `FramelessFittingKind`, `FramelessSupport`, `FramelessFitting`, `FramelessSpec`, `ProductModule`, `CoupledAssembly`, `ProductModel`, `PlanModule`, `PlanCoupling`, `PlanGeometry`, `ProductIssue`, `SlidingPanelFacts`, `SlidingLayoutFacts`, `ModuleEvaluation`, `ProductEvaluation`, `_q`, `_seg_intersects`, `_polygons_overlap`, `_resolved_pairs`, `_stack_parents`, `_resolve_stack_roots`, `ElevationMember`, `ElevationColumnJoint`, `ElevationStackJoint`, `ElevationLayout`, `elevation_layout`, `elevation_envelope`, `elevation_drawing_envelope`, `_plan_geometry`, `_top_with_module_dims`, `_sliding_facts`, `_prefix_result`, `_single_region_leaf`, `_qa`, `_is_axis_rect`, `_evaluate_contour_module`, `_evaluate_frameless_module`, `contour_module_computation`, `frameless_retention_declared`, `frameless_module_computation`, `evaluate_product`, `_evaluate_product`, `_bay_node`, `make_single_unit`, `make_bow_assembly`, `_replace_module`, `_replace_coupling`, `set_module_count`, `set_module_width`, `set_module_height`, `equalize_module_widths`, `set_coupling_angle`, `equalize_coupling_angles`, `set_coupler_sku`, `_with_opening`, `set_module_opening`, `set_module_tree`, `module_ids`, `coupling_ids`, `nominal_width_mm`, `nominal_height_mm` |
| [purchasing.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/purchasing.py) | Proyección de compra sobre manufactura expandida/sellada. | `PurchaseAuthorityError`, `SupplierOrderType`, `PhysicalSourceKind`, `EdgePolishingV1`, `GlassPolishingAuthorityV1`, `PhysicalStockBindingV1`, `GlassPurchaseMappingV1`, `HardwarePurchaseMappingV1`, `PanelPurchaseAuthorityV1`, `HardwareSelectionV1`, `FittingPurchaseMappingV1`, `FittingSelectionV1`, `fitting_selections_v1`, `AccessoryLineV1`, `AccessoryScheduleV1`, `PositionPurchaseInputV1`, `StockGroupResultV1`, `PurchaseRequirementV1`, `PurchaseRequirementsV1`, `_RequirementDraft`, `_one_mapping`, `_cut_piece`, `_binding_for_piece`, `_stock_group_key`, `_draft_key`, `_merge_drafts`, `project_purchase_requirements_v1` |
| [quotation.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/quotation.py) | Precios sellados e hitos monetarios declarados. | `QuotationLine`, `quotation_line`, `QuotationSummary`, `quotation_summary`, `payment_amounts`, `representative_index`, `GrossQuotationInput`, `GrossQuotationLine`, `GrossQuotation`, `gross_quotation` |
| [snapshot.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/snapshot.py) | Serialización canónica e identidad del cálculo. | `_json_value`, `canonical_json`, `calculation_hash`, `result_payload`, `calculation_response`, `evaluation_payload`, `evaluation_response` |
| [symbols.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/symbols.py) | Primitivas DIN de elevación, independientes de la UI. | `SymbolLine`, `symbol_names`, `opening_symbol_lines` |
| [technical_facts.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/technical_facts.py) | Hechos internos de ejecución geométrica fuera del BOM público. | `InfillTechnicalFacts`, `LeafTechnicalFacts`, `OpeningTechnicalFacts`, `SpanTechnicalFacts`, `GeometryComputation` |
| [thermal.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/thermal.py) | Uw con áreas visibles y comprobaciones OGUC acotadas/revisadas. | `ThermalModel`, `fingerprint`, `ThermalAuthority`, `ThermalPane`, `ThermalGeometry`, `glass_binding`, `thermal_geometry`, `authority_matches`, `calculate_uw`, `thermal_delta`, `ThermalPositionContext`, `ThermalProjectInput`, `assess_project`, `_assess_project` |
| [thermal_rules.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/thermal_rules.py) | Reglas térmicas normativas transcritas y su alcance. | `maximum_percentage`, `orientation_from_azimuth` |
| [trig.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/trig.py) | Trigonometría Decimal para proyección visual. | `_reduce`, `_sin_series`, `_cos_series`, `sin_degrees`, `cos_degrees`, `_atan_series`, `_atan_full`, `atan2_degrees`, `asin_degrees` |
| [warranty.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/warranty.py) | Fechas de garantía desde declaración sellada. | `warranty_deadline` |
| [weight.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/weight.py) | Masa exacta de hoja móvil. | `MissingWeightAuthority`, `MissingFabricationAuthority`, `_accumulate`, `ExactLeafWeight`, `base_leaf_weight`, `with_hardware_weight` |
| [work_queue.py](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/work_queue.py) | Proyecciones puras de la cola diaria, sin repricing ni I/O. | `money_sum`, `outstanding`, `consequence`, `queue_order` |

<a id="anexo-d"></a>

## Anexo D. Enums del modelo físico

Las 21 definiciones siguientes proceden de models.py, cutting.py y product.py. Los valores son vocabulario de transporte/dominio: tener un enum no basta para habilitar una combinación, una estación ni una fabricación. IssueCode recoge ese enum concreto; existen otros errores de servicios y reglas fuera de esta lista.


| Enum / fuente | Valores literales |
|---|---|
| [MaterialType](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L22) | `PVC`, `ALUMINIUM` |
| [SystemFamily](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L27) | `CASEMENT`, `SLIDING`, `LIFT_SLIDE`, `DOOR`, `FACADE_FIXED` |
| [RailType](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L35) | `dual`, `mono` |
| [ProfileRole](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L40) | `FRAME`, `SASH`, `MULLION_V`, `MULLION_H`, `INVERSOR`, `GLAZING_BEAD`, `COUPLER`, `ADDITIONAL`, `THRESHOLD`, `CHANNEL`, `SLIDING_SASH`, `INTERLOCK`, `RAIL`, `DOOR_SASH`, `FRAME_EXTENSION`, `SILL`, `COVER_TRIM`, `PLINTH` |
| [NodeType](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L62) | `ROOT`, `SPLIT_H`, `SPLIT_V`, `BAY` |
| [BayOpeningType](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L69) | `FIXED`, `TURN_LEFT`, `TURN_RIGHT`, `TILT_TURN_LEFT`, `TILT_TURN_RIGHT`, `SLIDING_2L`, `SLIDING_3L`, `SLIDING_4L`, `SLIDING`, `AWNING`, `DOOR_ENTRY`, `DOOR_DOUBLE` |
| [OpeningMovement](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L86) | `FIXED`, `TURN`, `TILT`, `TILT_TURN`, `TOP_HUNG`, `BOTTOM_HUNG`, `SLIDE`, `LIFT_SLIDE`, `PARALLEL_SLIDE`, `FOLD`, `PIVOT_V`, `PIVOT_H`, `VERTICAL_SLIDE` |
| [HingeSide](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L102) | `LEFT`, `RIGHT`, `TOP`, `BOTTOM`, `NONE` |
| [OpeningDirection](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L110) | `INWARD`, `OUTWARD` |
| [LeafRole](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L115) | `ACTIVE`, `PASSIVE`, `SINGLE` |
| [OpeningUse](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L121) | `WINDOW`, `DOOR` |
| [SlidingPanelKind](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L372) | `MOVING`, `FIXED` |
| [SlidingTravel](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/models.py#L377) | `LEFT`, `RIGHT` |
| [CutMaterial](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/cutting.py#L40) | `PVC`, `ALUMINIUM`, `STEEL` |
| [ProductStatus](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L93) | `VALID`, `MANUFACTURING_INCOMPLETE`, `INVALID` |
| [Severity](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L99) | `error`, `warning` |
| [IssueCode](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L104) | `coupler_angle_incompatible`, `system_family_incompatible`, `system_dimensional_limit`, `couplings_count_mismatch`, `assembly_folds_back`, `plan_self_intersection`, `module_geometry_failed`, `coupler_profile_missing`, `coupler_profile_unknown`, `coupler_height_mismatch`, `coupler_reinforcement_nonpositive`, `contour_invalid`, `contour_splits_unsupported`, `contour_opening_unsupported`, `contour_panel_unsupported`, `member_bending_required`, `coupler_width_mismatch`, `coupler_module_unknown`, `coupler_edge_invalid`, `coupler_edge_conflict`, `connection_type_unsupported`, `assembly_disconnected`, `stacked_cycle`, `inline_not_adjacent`, `contour_coupling_unsupported`, `sliding_layout_invalid`, `sliding_tracks_unsupported`, `frameless_splits_unsupported`, `frameless_opening_unsupported`, `frameless_panel_unsupported`, `frameless_contour_unsupported`, `frameless_article_unknown`, `member_exceeds_stock`, `hardware_kit_incompatible`, `hardware_kit_overweight`, `hardware_undecidable` |
| [ConnectionKind](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L143) | `INLINE`, `STACKED`, `TEE`, `CORNER` |
| [EdgeSide](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L152) | `left`, `right`, `top`, `bottom` |
| [FramelessSupportKind](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L180) | `CHANNEL`, `CLAMPS` |
| [FramelessFittingKind](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/engine/src/dekopen_engine/product.py#L187) | `PATCH_FITTING`, `CLAMP`, `HINGE`, `LOCK`, `CONNECTOR`, `SEAL`, `SUPPORT` |

<a id="anexo-e"></a>

## Anexo E. Rutas literales del frontend

43 declaraciones únicas por archivo/ruta, incluidos dos comodines de entradas diferentes. No son 43 pantallas independientes. DEV está condicionado y excluido del producto construido. ReadyGuard, controles internos de página, rol y backend determinan el acceso efectivo; esta clasificación no es una autorización.


| Ruta | Contexto | Destino/capacidad | Fuente |
|---|---|---|---|
| `/settings/billing` | Aplicación privada / rol | Comercio/suscripción de plataforma | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/settings/wallet` | Aplicación privada / rol | Saldo y movimientos de créditos | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/projects/:id` | Aplicación privada / rol | Centro de trabajo del proyecto | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/projects/:id/positions/new` | Aplicación privada / rol | Nueva posición | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/projects/:id/pricing` | Aplicación privada / rol | Precio del proyecto | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/dev/marca` | Solo DEV | Exploración DEV de marca | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/dev/correos` | Solo DEV | Exploración DEV de correos | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/dev/ui` | Solo DEV | Manual DEV de componentes | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/projects/demo/positions/g1/edit` | Solo DEV | Editor DEV de demo | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/benchmark` | Solo DEV | Superficie DEV de medición | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/pricing/commercial` | Aplicación privada / rol | Workspace comercial | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/pricing/cost-lists` | Aplicación privada / rol | Listas/costos autorizados | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/` | Entrada según sesión | Presentación anónima o redirección por sesión/rol | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/analytics` | Aplicación privada / rol | Ventas/margen/planta/terreno | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/about` | Aplicación privada / rol | Acerca del producto, con sesión lista | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/login` | Acceso / contrato de invitación | Acceso | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/auth/callback` | Acceso / contrato de invitación | Retorno de autenticación | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/auth/mfa` | Sesión / resolución de acceso | Alta/verificación del segundo factor bajo SessionGuard | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/select-organization` | Sesión / resolución de acceso | Elegir membresía/empresa bajo SessionGuard | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/dashboard` | Aplicación privada / rol | Hoy / trabajo por consecuencia | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/clients/:id?` | Aplicación privada / rol | Directorio y dossier de cliente | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/jobs` | Aplicación privada / rol | Trabajos/progreso/resultados | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/purchasing` | Aplicación privada / rol | Necesidades y órdenes de compra | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/production` | Aplicación privada / rol | Tablero/estaciones/OT | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/field` | Aplicación privada / rol | Terreno; entrada propia de FieldPage | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/dispatch` | Aplicación privada / rol | Despacho y postventa de oficina | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/projects/:id/positions/:posId/edit` | Aplicación privada / rol | Editor de posición | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/projects` | Aplicación privada / rol | Lista/centro de proyectos | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/catalogs` | Alias / redirección | Redirección a /catalogs/systems | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/catalogs/sheet-formats` | Aplicación privada / rol | Formatos declarados de lámina | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/assistant` | Aplicación privada / rol | Workspace del asistente | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/catalogs/systems` | Aplicación privada / rol | Catálogo técnico/ingesta | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/onboarding` | Aplicación privada / rol | Alta/primer recorrido | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/settings/general` | Aplicación privada / rol | Ajustes de empresa y dominios | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/settings` | Alias / redirección | Redirección a /settings/general | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/invitation` | Acceso / contrato de invitación | Aceptar invitación bajo su contrato de acceso | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/inventory` | Aplicación privada / rol | Inventario/retazos | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/quotes` | Aplicación privada / rol | Cotizaciones | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `*` | Fallback | Recuperación de ruta inexistente | [App.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/App.tsx) |
| `/cotizacion/:token` | Público por capacidad/contexto | Propuesta por capacidad pública | [PublicProposalApp.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/features/portal/PublicProposalApp.tsx) |
| `/pago/simulado/:linkId` | Público por capacidad/contexto | Pago de ensayo por capacidad | [PublicProposalApp.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/features/portal/PublicProposalApp.tsx) |
| `/pago/retorno` | Público por capacidad/contexto | Retorno y verificación de pago | [PublicProposalApp.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/features/portal/PublicProposalApp.tsx) |
| `*` | Fallback | Recuperación de ruta inexistente | [PublicProposalApp.tsx](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/frontend/src/features/portal/PublicProposalApp.tsx) |

<a id="anexo-f"></a>

## Anexo F. Las 149 declaraciones de tablas encontradas

Índice estático de nombres distintos de CREATE TABLE en las migraciones versionadas. La fuente identifica una declaración del historial. No lista columnas, filas, tamaño, tablas actuales de una instancia ni estado efectivo de RLS; ALTER/DROP y migraciones posteriores deben revisarse para comprender el schema actual. Incluye estructuras compartidas/de infraestructura además de tenant. Los timestamps de archivo identifican orden de migración; no son una certificación de fecha de puesta en producción.


| Nombre declarado | Migración fuente |
|---|---|
| `public.ai_ask_turns` | [20261223000000_ai_ask_turns.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261223000000_ai_ask_turns.sql) |
| `public.ai_audit_logs` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.ai_audit_provenance` | [20261004000000_ai_audit_provenance_v2.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261004000000_ai_audit_provenance_v2.sql) |
| `public.ai_capability_routes` | [20270106000000_ai_provider_operations.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270106000000_ai_provider_operations.sql) |
| `public.ai_job_cancel_signals` | [20261214000000_ai_jobs_async.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261214000000_ai_jobs_async.sql) |
| `public.ai_jobs` | [20261202000000_ai_jobs.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261202000000_ai_jobs.sql) |
| `public.ai_provider_usage` | [20270106000000_ai_provider_operations.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270106000000_ai_provider_operations.sql) |
| `public.ai_routes` | [20260930000000_ai_gateway.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260930000000_ai_gateway.sql) |
| `public.ai_settings` | [20270106000000_ai_provider_operations.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270106000000_ai_provider_operations.sql) |
| `public.ai_usage_events` | [20270106000000_ai_provider_operations.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270106000000_ai_provider_operations.sql) |
| `public.analytics_preferences` | [20270128000000_analytics_evidence.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270128000000_analytics_evidence.sql) |
| `public.billing_checkouts` | [20260921000600_shot_11_checkout.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000600_shot_11_checkout.sql) |
| `public.billing_credit_grants` | [20260921000200_shot_11_payment_settlement.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000200_shot_11_payment_settlement.sql) |
| `public.billing_invoice_observations` | [20260921000600_shot_11_checkout.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000600_shot_11_checkout.sql) |
| `public.billing_lifecycle_events` | [20260921000500_shot_11_lifecycle.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000500_shot_11_lifecycle.sql) |
| `public.billing_offers` | [20260921000600_shot_11_checkout.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000600_shot_11_checkout.sql) |
| `public.billing_orders` | [20260921000200_shot_11_payment_settlement.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000200_shot_11_payment_settlement.sql) |
| `public.billing_periods` | [20260921000500_shot_11_lifecycle.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000500_shot_11_lifecycle.sql) |
| `public.catalog_color_skus` | [20261229000300_catalog_review_interchange.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261229000300_catalog_review_interchange.sql) |
| `public.catalog_demo_prices` | [20261229000100_catalog_family_authorities.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261229000100_catalog_family_authorities.sql) |
| `public.catalog_family_migrations` | [20261229000400_catalog_saved_family_upgrade.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261229000400_catalog_saved_family_upgrade.sql) |
| `public.catalog_glass_compositions` | [20261230000000_glass_composition_and_rules.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261230000000_glass_composition_and_rules.sql) |
| `public.catalog_glass_retractions` | [20261229000300_catalog_review_interchange.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261229000300_catalog_review_interchange.sql) |
| `public.catalog_import_events` | [20270121000000_catalog_review_sources.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270121000000_catalog_review_sources.sql) |
| `public.catalog_import_publications` | [20261229000300_catalog_review_interchange.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261229000300_catalog_review_interchange.sql) |
| `public.catalog_imports` | [20261003000000_catalog_imports.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261003000000_catalog_imports.sql) |
| `public.catalog_parameter_evidence` | [20261227000002_catalog_parameter_evidence.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261227000002_catalog_parameter_evidence.sql) |
| `public.catalog_thermal_authorities` | [20270127000000_thermal_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270127000000_thermal_authority.sql) |
| `public.client_addresses` | [20270124000000_client_dossiers.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270124000000_client_dossiers.sql) |
| `public.client_contacts` | [20270124000000_client_dossiers.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270124000000_client_dossiers.sql) |
| `public.client_merges` | [20270124000000_client_dossiers.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270124000000_client_dossiers.sql) |
| `public.client_notes` | [20270124000000_client_dossiers.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270124000000_client_dossiers.sql) |
| `public.clients` | [20261008000000_clients.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261008000000_clients.sql) |
| `public.cnc_authority_events` | [20270120000000_cnc_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270120000000_cnc_authority.sql) |
| `public.cnc_machines` | [20260928000000_cnc.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260928000000_cnc.sql) |
| `public.cnc_programs` | [20260928000000_cnc.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260928000000_cnc.sql) |
| `public.cnc_tools` | [20260928000000_cnc.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260928000000_cnc.sql) |
| `public.collection_preferences` | [20270119000000_collection_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270119000000_collection_authority.sql) |
| `public.collection_reminders` | [20270119000000_collection_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270119000000_collection_authority.sql) |
| `public.cost_list_items` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.cost_lists` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.credit_ledger` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.credit_lot_movements` | [20260921000500_shot_11_lifecycle.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000500_shot_11_lifecycle.sql) |
| `public.credit_lots` | [20260921000100_shot_11_wallet_trial.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000100_shot_11_wallet_trial.sql) |
| `public.customer_approvals` | [20260923220000_customer_approvals.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923220000_customer_approvals.sql) |
| `public.cutting_profiles` | [20260906000000_shot_07_authorities.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260906000000_shot_07_authorities.sql) |
| `public.deliveries` | [20260924000000_deliveries.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260924000000_deliveries.sql) |
| `public.delivery_confirmations` | [20261013000000_delivery_confirmations.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261013000000_delivery_confirmations.sql) |
| `public.dispatch_notes` | [20261010000000_dispatch_notes.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261010000000_dispatch_notes.sql) |
| `public.document_artifacts` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.document_imports` | [20261001000000_document_imports.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261001000000_document_imports.sql) |
| `public.document_portal_links` | [20270109000000_quote_document_v2.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270109000000_quote_document_v2.sql) |
| `public.entity_code_counters` | [20270107000000_human_entity_codes.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270107000000_human_entity_codes.sql) |
| `public.entity_codes` | [20270107000000_human_entity_codes.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270107000000_human_entity_codes.sql) |
| `public.field_assets` | [20270125000000_field_work.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270125000000_field_work.sql) |
| `public.field_events` | [20270125000000_field_work.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270125000000_field_work.sql) |
| `public.field_incidents` | [20270125000000_field_work.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270125000000_field_work.sql) |
| `public.field_purchase_authorizations` | [20270125000000_field_work.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270125000000_field_work.sql) |
| `public.field_receipts` | [20270125000000_field_work.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270125000000_field_work.sql) |
| `public.field_visits` | [20270125000000_field_work.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270125000000_field_work.sql) |
| `public.fitting_purchase_mappings` | [20261104000000_fitting_purchase_mappings.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261104000000_fitting_purchase_mappings.sql) |
| `public.flow_customer_operations` | [20260921000400_shot_11_customer_registration.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000400_shot_11_customer_registration.sql) |
| `public.flow_lifecycle_operations` | [20260921000500_shot_11_lifecycle.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000500_shot_11_lifecycle.sql) |
| `public.flow_subscription_intents` | [20260921000300_shot_11_native_subscription_intent.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260921000300_shot_11_native_subscription_intent.sql) |
| `public.glass_purchase_mappings` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.glass_safety_rule_revisions` | [20261230000000_glass_composition_and_rules.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261230000000_glass_composition_and_rules.sql) |
| `public.glass_safety_rule_sets` | [20261230000000_glass_composition_and_rules.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261230000000_glass_composition_and_rules.sql) |
| `public.glazing_bead_matrix` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.handle_requirement_policies` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.hardware_kits` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.hardware_purchase_mappings` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.infill_articles` | [20260905000000_shot_06_catalog_authorities.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260905000000_shot_06_catalog_authorities.sql) |
| `public.inspector_rule_configs` | [20260906000000_shot_07_authorities.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260906000000_shot_07_authorities.sql) |
| `public.inventory_items` | [20260923130000_inventory.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923130000_inventory.sql) |
| `public.inventory_movements` | [20260923130000_inventory.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923130000_inventory.sql) |
| `public.inventory_remnant_events` | [20270118000000_purchasing_inventory_trace.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270118000000_purchasing_inventory_trace.sql) |
| `public.inventory_remnants` | [20261101000000_inventory_remnants.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261101000000_inventory_remnants.sql) |
| `public.job_runs` | [20260923120000_job_runs.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923120000_job_runs.sql) |
| `public.mail_attempts` | [20270108000000_brand_and_mail.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270108000000_brand_and_mail.sql) |
| `public.mail_outbox` | [20270108000000_brand_and_mail.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270108000000_brand_and_mail.sql) |
| `public.manufacturing_placement_policies` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.manufacturing_process_profiles` | [20261121000000_process_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261121000000_process_authority.sql) |
| `public.mounting_rules` | [20270104000000_opening_mounting.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270104000000_opening_mounting.sql) |
| `public.offcut_inventory` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.order_allocation_batches` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.order_receipt_lines` | [20260923130000_inventory.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923130000_inventory.sql) |
| `public.order_receipts` | [20260923130000_inventory.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923130000_inventory.sql) |
| `public.order_requirement_lines` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.orders` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.org_payment_integrations` | [20260926000000_payment_links.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260926000000_payment_links.sql) |
| `public.organization_admin_events` | [20270124000001_company_administration.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270124000001_company_administration.sql) |
| `public.organization_extra_history` | [20270103000000_accessory_services.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270103000000_accessory_services.sql) |
| `public.organization_extra_settings` | [20270103000000_accessory_services.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270103000000_accessory_services.sql) |
| `public.organization_invitations` | [20270124000001_company_administration.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270124000001_company_administration.sql) |
| `public.panel_purchase_authorities` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.payment_customers` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.payment_events` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.payment_receipts` | [20261009000000_payment_receipts.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261009000000_payment_receipts.sql) |
| `public.payments` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.portal_payment_contexts` | [20270123000000_portal_decisions.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270123000000_portal_decisions.sql) |
| `public.position_documentary_inputs` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.position_measurements` | [20270104000000_opening_mounting.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270104000000_opening_mounting.sql) |
| `public.price_audit_logs` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.pricing_attention_receipts` | [20270110000100_p07_price_workspace.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270110000100_p07_price_workspace.sql) |
| `public.pricing_configurations` | [20260910000000_shot_08_pricing.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260910000000_shot_08_pricing.sql) |
| `public.pricing_fx_snapshots` | [20260910000000_shot_08_pricing.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260910000000_shot_08_pricing.sql) |
| `public.pricing_matrix_cells` | [20260910000000_shot_08_pricing.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260910000000_shot_08_pricing.sql) |
| `public.pricing_operations` | [20260910000000_shot_08_pricing.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260910000000_shot_08_pricing.sql) |
| `public.pricing_rules` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.production_actual_reports` | [20270128000000_analytics_evidence.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270128000000_analytics_evidence.sql) |
| `public.production_operator_stations` | [20270112000000_operator_station.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270112000000_operator_station.sql) |
| `public.production_step_events` | [20260923150000_production.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923150000_production.sql) |
| `public.production_steps` | [20260923150000_production.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923150000_production.sql) |
| `public.profile_articles` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.profile_purchase_mappings` | [20260906000000_shot_07_authorities.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260906000000_shot_07_authorities.sql) |
| `public.profile_systems` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.project_credit_notes` | [20261012000000_project_credit_notes.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261012000000_project_credit_notes.sql) |
| `public.project_documentary_inputs` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.project_dtes` | [20261016000000_sii_dtes.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261016000000_sii_dtes.sql) |
| `public.project_edit_operations` | [20270105000000_project_edit_operations.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270105000000_project_edit_operations.sql) |
| `public.project_extra_services` | [20270103000000_accessory_services.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270103000000_accessory_services.sql) |
| `public.project_fiscal_simulations` | [20270119000000_collection_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270119000000_collection_authority.sql) |
| `public.project_invoices` | [20261011000000_project_invoices.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261011000000_project_invoices.sql) |
| `public.project_payment_links` | [20260926000000_payment_links.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260926000000_payment_links.sql) |
| `public.project_payments` | [20260925000000_project_payments.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260925000000_project_payments.sql) |
| `public.project_positions` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.project_thermal_inputs` | [20270127000000_thermal_authority.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270127000000_thermal_authority.sql) |
| `public.project_versions` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.projects` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.purchase_allocations` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.purchase_need_decisions` | [20270118000000_purchasing_inventory_trace.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270118000000_purchasing_inventory_trace.sql) |
| `public.purchase_projections` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.purchase_requirement_lines` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.quotation_issues` | [20270114000000_guided_quotation.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270114000000_guided_quotation.sql) |
| `public.quotation_previews` | [20270114000000_guided_quotation.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270114000000_guided_quotation.sql) |
| `public.quote_decisions` | [20270123000000_portal_decisions.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270123000000_portal_decisions.sql) |
| `public.quote_link_deadlines` | [20270114000000_guided_quotation.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270114000000_guided_quotation.sql) |
| `public.quote_link_regenerations` | [20270114000000_guided_quotation.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20270114000000_guided_quotation.sql) |
| `public.reinforcement_articles` | [20260906000000_shot_07_authorities.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260906000000_shot_07_authorities.sql) |
| `public.reinforcement_cut_policies` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.sii_cafs` | [20261016000000_sii_dtes.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261016000000_sii_dtes.sql) |
| `public.sii_certificates` | [20261019000000_sii_envios.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261019000000_sii_envios.sql) |
| `public.sii_envios` | [20261019000000_sii_envios.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261019000000_sii_envios.sql) |
| `public.subscriptions` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.supplier_eligibility_versions` | [20260914000000_shot_09_documentary.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260914000000_shot_09_documentary.sql) |
| `public.suppliers` | [20261219140000_supplier_directory.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20261219140000_supplier_directory.sql) |
| `public.tenancy_memberships` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.tenancy_organizations` | [20260901000000_initial_schema.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260901000000_initial_schema.sql) |
| `public.work_centers` | [20260923150000_production.sql](https://github.com/KaraAliOsman/framedex/blob/0a9f057ba5338bc6be39181b9ca001915b2f2a59/supabase/migrations/20260923150000_production.sql) |

<a id="anexo-g"></a>

## Anexo G. Cuerpos de solicitud y campos declarados

144 schemas referenciados directamente por cuerpos de solicitud en las 334 operaciones; 806 propiedades declaradas en esos schemas. Se deduplican los media types que usan el mismo schema. Un mismo campo puede repetirse en variantes completas/parciales. Este anexo no copia ejemplos, defaults ni credenciales; no reemplaza el OpenAPI completo de 899 componentes.

«Obligatorio» reproduce required del schema, separado de la obligatoriedad del body del anexo B. Type/ref, restricciones y descripción son contrato estático. Validaciones de negocio, permiso, catálogo, estado e idempotencia también se aplican aunque no aparezcan como un minimum o enum aquí. Los schemas anidados se resuelven en OpenAPI.


### G.1 `AcknowledgeRequest`

Usado por: `POST /api/v1/pricing/acknowledge/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_ids` | `string (uuid)[]` | Sí | items máx.: `100` | — |

### G.2 `ActualReportRequestRequest`

Usado por: `POST /api/v1/analytics/orders/{order_id}/actual/`; `POST /api/v1/analytics/orders/{order_id}/actual/preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `request_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `expected_revision` | `integer` | Sí | mín.: `0` | — |
| `source_fingerprint` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `currency` | `ActualReportRequestCurrencyEnum` | Sí | Sin restricción simple declarada | — |
| `source` | `string` | Sí | largo mín.: `3`<br>largo máx.: `1000` | — |
| `reason` | `string` | Sí | largo mín.: `3`<br>largo máx.: `1000` | — |
| `materials` | `MaterialActualRequest[]` | Sí | Sin restricción simple declarada | — |
| `labor` | `LaborActualRequest[]` | Sí | Sin restricción simple declarada | — |
| `other_cost` | `string (decimal) / null` | Sí | patrón: `^-?\d{0,24}(?:\.\d{0,8})?$` | — |
| `reusable_credit` | `string (decimal) / null` | Sí | patrón: `^-?\d{0,24}(?:\.\d{0,8})?$` | — |
| `closed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `bars` | `BarActualRequest` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |

### G.3 `AdminWriteRequest`

Usado por: `POST /api/v1/pricing/admin/{resource}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |
| `values` | `object` | Sí | Sin restricción simple declarada | — |

### G.4 `AiAgentRequestRequest`

Usado por: `POST /api/v1/ai/agent/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `surface` | `string` | Sí | largo mín.: `2`<br>largo máx.: `40` | — |
| `refs` | `object` | No | Sin restricción simple declarada | — |
| `goal` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `product` | `object` | No | Sin restricción simple declarada | — |
| `product_sig` | `string` | No | largo máx.: `64` | — |
| `history` | `AiAgentHistoryRequest[]` | No | Sin restricción simple declarada | — |
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |

### G.5 `AiAskRequestRequest`

Usado por: `POST /api/v1/ai/ask/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `surface` | `string` | Sí | largo mín.: `2`<br>largo máx.: `40` | — |
| `refs` | `object` | No | Sin restricción simple declarada | — |
| `question` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |

### G.6 `AiConnectionTestRequest`

Usado por: `POST /api/v1/ai/connection-test/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |

### G.7 `AiInvokeRequestRequest`

Usado por: `POST /api/v1/ai/invoke/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `capability` | `string` | Sí | largo mín.: `2`<br>largo máx.: `100` | — |
| `tool_name` | `string` | No | largo máx.: `100` | — |
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |
| `input_payload` | `object` | Sí | Sin restricción simple declarada | — |

### G.8 `AiJobMessageRequest`

Usado por: `POST /api/v1/ai/jobs/{job_id}/messages/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `message` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `product` | `object` | No | Sin restricción simple declarada | — |
| `refs` | `object` | No | Sin restricción simple declarada | — |
| `product_sig` | `string` | No | largo máx.: `64` | — |

### G.9 `AiJobOutcomeRequest`

Usado por: `POST /api/v1/ai/jobs/{job_id}/outcome/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `turn_index` | `integer` | Sí | mín.: `0`<br>máx.: `1000` | — |
| `step_index` | `integer` | Sí | mín.: `0`<br>máx.: `1000` | — |
| `action` | `AiJobOutcomeActionEnum` | Sí | Sin restricción simple declarada | — |
| `ops` | `string[]` | No | items máx.: `200` | — |

### G.10 `AiSettingsSaveRequest`

Usado por: `PUT /api/v1/ai/settings/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_revision` | `integer` | Sí | mín.: `1` | — |
| `monthly_budget_credits` | `integer / null` | Sí | mín.: `0`<br>máx.: `2147483647` | — |
| `routes` | `AiRouteSettingsRequest[]` | Sí | Sin restricción simple declarada | — |

### G.11 `AllocationRequestRequest`

Usado por: `PUT /api/v1/purchasing/requirements/{requirement_id}/allocation/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `supplier_eligibility_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.12 `AnalyticsPreferenceRequest`

Usado por: `PUT /api/v1/analytics/preferences/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `period_days` | `integer` | Sí | mín.: `1`<br>máx.: `366` | — |

### G.13 `ApplyRequest`

Usado por: `POST /api/v1/pricing/operations/{operation_id}/apply/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |
| `reject` | `boolean` | No | Sin restricción simple declarada | — |

### G.14 `ArticleWriteRequest`

Usado por: `POST /api/v1/catalogs/articles/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `coupling_rule` | `CouplerRuleRequest` | No | Sin restricción simple declarada | — |
| `cut_rule` | `ProfileCutRuleRequest` | No | Sin restricción simple declarada | — |
| `reinforcement_rule` | `ProfileReinforcementRuleRequest` | No | Sin restricción simple declarada | — |
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `sku` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `section` | `ProfileSectionRequest` | No | Sin restricción simple declarada | — |
| `role` | `CatalogProfileRoleEnum` | Sí | Sin restricción simple declarada | — |
| `material` | `MaterialEnum` | Sí | Sin restricción simple declarada | — |
| `face_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `commercial_length_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `welding_loss_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `reinforcement_sku` | `string / null` | No | largo máx.: `100` | — |
| `reinforcement_gap_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `weight_kg_m` | `string (decimal) / null` | No | patrón: `^-?\d{0,4}(?:\.\d{0,4})?$` | — |
| `steel_weight_kg_m` | `string (decimal) / null` | No | patrón: `^-?\d{0,4}(?:\.\d{0,4})?$` | — |

### G.15 `ArtifactRequestRequest`

Usado por: `POST /api/v1/documents/artifacts/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `document_type` | `DocumentTypeEnum` | Sí | Sin restricción simple declarada | — |
| `format` | `FormatEnum` | Sí | Sin restricción simple declarada | — |
| `project_version_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `order_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |

### G.16 `BeadWriteRequest`

Usado por: `POST /api/v1/catalogs/glazing/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `glass_thickness_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `bead_article_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `bead_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `gasket_interior_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `gasket_exterior_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `cut_add_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `is_active` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.17 `CatalogImportConfirmRequest`

Usado por: `POST /api/v1/catalog-imports/{import_id}/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `items` | `CatalogItemRequest[]` | Sí | Sin restricción simple declarada | — |

### G.18 `CatalogPublishRequestRequest`

Usado por: `POST /api/v1/catalog-imports/{import_id}/publish/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `items` | `CatalogReviewItemRequest[]` | Sí | Sin restricción simple declarada | — |
| `review_token` | `string` | Sí | largo mín.: `1`<br>patrón: `^sha256:[0-9a-f]{64}$` | — |
| `reviewed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.19 `CatalogReviewRequestRequest`

Usado por: `POST /api/v1/catalog-imports/{import_id}/review/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `items` | `CatalogReviewItemRequest[]` | Sí | Sin restricción simple declarada | — |

### G.20 `CatalogUndoRequestRequest`

Usado por: `POST /api/v1/catalog-imports/{import_id}/undo/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.21 `ChangeInputRequest`

Usado por: `POST /api/v1/billing/change/preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `offer_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `cancel` | `boolean` | No | Sin restricción simple declarada | — |

### G.22 `CheckoutInputRequest`

Usado por: `POST /api/v1/billing/checkout/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `offer_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.23 `ClientMergePreviewRequestRequest`

Usado por: `POST /api/v1/clients/{client_id}/merge-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `target_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.24 `ClientMergeRequestRequest`

Usado por: `POST /api/v1/clients/{client_id}/merge/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `target_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `expected_source_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |
| `expected_target_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.25 `ClientNoteWriteRequest`

Usado por: `POST /api/v1/clients/{client_id}/notes/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `body` | `string` | Sí | largo mín.: `1`<br>largo máx.: `4000` | — |

### G.26 `ClientWriteRequest`

Usado por: `POST /api/v1/clients/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `rut` | `string` | No | largo máx.: `50` | — |
| `email` | `string (email) / string` | No | Sin restricción simple declarada | — |
| `phone` | `string` | No | largo máx.: `50` | — |
| `address` | `string` | No | Sin restricción simple declarada | — |
| `giro` | `string` | No | largo máx.: `80` | — |
| `comuna` | `string` | No | largo máx.: `20` | — |
| `notes` | `string` | No | largo máx.: `4000` | — |
| `party_kind` | `PartyKindEnum` | No | Sin restricción simple declarada | — |
| `contacts` | `ClientContactWriteRequest[]` | No | Sin restricción simple declarada | — |
| `addresses` | `ClientAddressWriteRequest[]` | No | Sin restricción simple declarada | — |

### G.27 `CloneProjectRequest`

Usado por: `POST /api/v1/projects/{project_id}/clone/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |

### G.28 `CncGenerateRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/cnc/programs/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_preview` | `string` | Sí | largo mín.: `1`<br>largo máx.: `64` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `machine_id` | `string` | Sí | largo mín.: `1` | — |
| `member_id` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |

### G.29 `CncMachineRequestRequest`

Usado por: `POST /api/v1/production/cnc/machines/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `machine_type` | `string` | No | largo máx.: `40` | — |
| `profile_setups` | `object[]` | No | Sin restricción simple declarada | — |
| `axes` | `string[] / null` | No | Sin restricción simple declarada | — |
| `clamps_declared` | `boolean` | No | Sin restricción simple declarada | — |
| `authority_source` | `string` | No | largo máx.: `500` | — |
| `code` | `string` | Sí | largo mín.: `1`<br>largo máx.: `40` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `120` | — |
| `manufacturer` | `string` | No | largo máx.: `120` | — |
| `model` | `string` | No | largo máx.: `120` | — |
| `controller_family` | `string` | No | largo máx.: `80` | — |
| `coordinate_systems` | `string[]` | No | Sin restricción simple declarada | — |
| `supported_kinds` | `string[] / null` | No | Sin restricción simple declarada | — |
| `supported_faces` | `string[] / null` | No | Sin restricción simple declarada | — |
| `max_member_length_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `safe_margin_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `clamp_zones` | `object[]` | No | Sin restricción simple declarada | — |
| `tool_ids` | `string[]` | No | Sin restricción simple declarada | — |
| `postprocessor_id` | `string` | No | largo máx.: `80` | — |
| `postprocessor_version` | `string` | No | largo máx.: `40` | — |
| `units` | `string` | No | largo mín.: `1`<br>largo máx.: `20` | — |
| `encoding` | `string` | No | largo mín.: `1`<br>largo máx.: `40` | — |
| `active` | `boolean` | No | Sin restricción simple declarada | — |

### G.30 `CncPreviewRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/cnc/preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `machine_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `member_id` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |

### G.31 `CncToolRequestRequest`

Usado por: `POST /api/v1/production/cnc/tools/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `authority_source` | `string` | No | largo máx.: `500` | — |
| `code` | `string` | Sí | largo mín.: `1`<br>largo máx.: `40` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `120` | — |
| `kind` | `string` | Sí | largo mín.: `1`<br>largo máx.: `30` | — |
| `diameter_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `working_length_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `max_depth_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `compatible_kinds` | `string[] / null` | No | Sin restricción simple declarada | — |
| `active` | `boolean` | No | Sin restricción simple declarada | — |

### G.32 `CollectionReminderSendRequest`

Usado por: `POST /api/v1/projects/{project_id}/collection-reminder/send/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `reminder_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.33 `CollectionSettingsRequestRequest`

Usado por: `PUT /api/v1/organization/collections/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `simulation_enabled` | `boolean` | Sí | Sin restricción simple declarada | — |
| `payment_link_days` | `integer` | Sí | mín.: `1`<br>máx.: `90` | — |
| `sii_active` | `boolean` | Sí | Sin restricción simple declarada | — |
| `sii_certified` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.34 `CompanyPreviewRequest`

Usado por: `POST /api/v1/organization/document-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `version_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `branding` | `OrgBrandingWriteRequest` | No | Sin restricción simple declarada | — |

### G.35 `CompanyUserWriteRequest`

Usado por: `PUT /api/v1/organization/users/{identity}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `role` | `MembershipRoleEnum` | Sí | Sin restricción simple declarada | — |
| `is_active` | `boolean` | Sí | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |

### G.36 `CompanyWriteRequest`

Usado por: `PUT /api/v1/organization/company/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `tax_id` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `currency` | `CurrencyEnum` | Sí | Sin restricción simple declarada | — |
| `require_mfa` | `boolean` | Sí | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |

### G.37 `ConfirmBatchRequestRequest`

Usado por: `POST /api/v1/purchasing/versions/{version_id}/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `order_type` | `OrderTypeEnum` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.38 `ConfirmChangeRequest`

Usado por: `POST /api/v1/billing/change/abandon/`; `POST /api/v1/billing/change/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.39 `DecideRequestRequest`

Usado por: `POST /api/v1/portal/quotes/{token}/decide/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `decision` | `DecisionEnum` | Sí | Sin restricción simple declarada | — |
| `decided_by` | `string` | No | largo máx.: `255` | — |
| `decided_rut` | `string` | No | largo máx.: `32` | — |
| `note` | `string` | No | largo máx.: `500` | — |
| `selected_revision` | `string` | Sí | largo mín.: `1`<br>patrón: `^REV-[A-Z]+$` | — |
| `expected_offering_sha256` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `expected_selected_sha256` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |
| `consent_text` | `string` | No | largo máx.: `1000` | — |
| `position_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |

### G.40 `DeliveryConfirmRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/delivery/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `receiver_name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `receiver_rut` | `string` | No | largo máx.: `30` | — |
| `signature_png` | `string` | Sí | largo mín.: `1` | — |
| `payment` | `DeliveryPaymentRequestRequest` | No | Sin restricción simple declarada | — |

### G.41 `DeliveryScheduleRequestRequest`

Usado por: `PUT /api/v1/production/orders/{order_id}/delivery/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `scheduled_date` | `string` | Sí | largo mín.: `1`<br>largo máx.: `10` | — |
| `time_window` | `TimeWindowEnum` | No | Sin restricción simple declarada | — |
| `address` | `string` | Sí | largo mín.: `1`<br>largo máx.: `300` | — |
| `contact_name` | `string` | No | largo máx.: `200` | — |
| `contact_phone` | `string` | No | largo máx.: `50` | — |
| `installer_name` | `string` | No | largo máx.: `200` | — |
| `notes` | `string` | No | largo máx.: `500` | — |
| `unit_indexes` | `integer[] / null` | No | Sin restricción simple declarada | — |

### G.42 `DeliveryTransitionRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/delivery/transition/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `status` | `DeliveryTransitionRequestStatusEnum` | Sí | Sin restricción simple declarada | — |

### G.43 `DesignAlternativesRequestRequest`

Usado por: `POST /api/v1/positions/{position_id}/design-alternatives/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `brief` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `count` | `integer` | No | mín.: `1`<br>máx.: `3` | — |
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `operation_key` | `string` | Sí | largo mín.: `1`<br>largo máx.: `120` | — |
| `width_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |

### G.44 `DesignAssistRequestRequest`

Usado por: `POST /api/v1/positions/{position_id}/design-assist/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `prompt` | `string` | Sí | largo mín.: `2`<br>largo máx.: `2000` | — |
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |
| `product` | `object` | Sí | Sin restricción simple declarada | — |
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.45 `DesignBatchPreviewRequestRequest`

Usado por: `POST /api/v1/pricing/design-batch-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `project_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `effective_date` | `string (date)` | Sí | Sin restricción simple declarada | — |
| `items` | `DesignBatchPreviewItemRequest[]` | Sí | Sin restricción simple declarada | — |

### G.46 `DispatchNoteDteEmitRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/dispatch-note-dte/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `ind_traslado` | `IndTrasladoEnum` | No | Sin restricción simple declarada | — |

### G.47 `DispatchNoteVoidRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/dispatch-note-void/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `500` | — |

### G.48 `DispatchRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/dispatch/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `note` | `string` | No | largo máx.: `500` | — |
| `unit_indexes` | `integer[] / null` | No | Sin restricción simple declarada | — |

### G.49 `DocumentaryInputsRequest`

Usado por: `PUT /api/v1/documents/projects/{project_id}/inputs/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `payment_terms` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `quotation_valid_until` | `string (date)` | Sí | Sin restricción simple declarada | — |
| `commercial_terms` | `CommercialTermsRequest` | No | Sin restricción simple declarada | — |
| `alternative_version_ids` | `string (uuid)[]` | No | items máx.: `3` | — |
| `positions` | `PositionDocumentaryInputRequest[]` | Sí | Sin restricción simple declarada | — |

### G.50 `DraftProjectRequest`

Usado por: `POST /api/v1/pricing/drafts/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `code` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `client_name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |
| `positions` | `DraftPositionRequest[]` | Sí | Sin restricción simple declarada | — |

### G.51 `EligibilityRequestRequest`

Usado por: `POST /api/v1/purchasing/versions/{version_id}/eligibilities/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `order_type` | `OrderTypeEnum` | Sí | Sin restricción simple declarada | — |
| `supplier_identity` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `supplier_name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `300` | — |
| `supplier_details` | `SupplierDetailsRequest` | Sí | Sin restricción simple declarada | — |
| `eligible_requirement_keys` | `string[]` | Sí | Sin restricción simple declarada | — |
| `evidence` | `EligibilityEvidenceRequest` | Sí | Sin restricción simple declarada | — |
| `version` | `integer` | Sí | mín.: `1` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.52 `EngineAssemblyCalculateRequest`

Usado por: `POST /api/v1/engine/assembly/calculate/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `nominal_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `nominal_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `product` | `—` | Sí | Sin restricción simple declarada | — |

### G.53 `EngineCalculateRequestRequest`

Usado por: `POST /api/v1/engine/calculate/`; `POST /api/v1/engine/layout/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `nominal_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `nominal_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `parametric_tree` | `—` | Sí | Sin restricción simple declarada | — |

### G.54 `EngineInspectRequestRequest`

Usado por: `POST /api/v1/engine/inspect/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `nominal_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `nominal_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `parametric_tree` | `—` | Sí | Sin restricción simple declarada | — |
| `annotations` | `AnnotationRequest[]` | No | Sin restricción simple declarada | — |
| `structural_inputs` | `StructuralInputRequest[]` | No | Sin restricción simple declarada | — |
| `mode` | `ModeEnum` | No | Sin restricción simple declarada | — |

### G.55 `EngineOptimizeRequestRequest`

Usado por: `POST /api/v1/engine/optimize-cut/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `nominal_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `nominal_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `parametric_tree` | `—` | Sí | Sin restricción simple declarada | — |
| `cutting_profile_code` | `string / null` | No | largo mín.: `1` | — |

### G.56 `EvidenceInputRequest`

Usado por: `POST /api/v1/catalogs/evidence/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `authority_table` | `AuthorityTableEnum` | Sí | Sin restricción simple declarada | — |
| `row_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `field_name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `80` | — |
| `value_text` | `string / null` | No | largo máx.: `10000` | — |
| `unit` | `EvidenceInputUnitEnum / NullEnum` | No | Sin restricción simple declarada | — |
| `scope` | `EvidenceInputScopeEnum` | No | Sin restricción simple declarada | — |
| `applicability` | `string / null` | No | largo máx.: `300` | — |
| `source_document` | `string` | Sí | largo mín.: `1`<br>largo máx.: `300` | — |
| `source_page` | `integer / null` | No | mín.: `1` | — |
| `source_url` | `string (uri) / null` | No | largo mín.: `1` | — |
| `source_ref` | `string / null` | No | largo mín.: `1`<br>largo máx.: `500` | — |
| `source_quote` | `string / null` | No | largo mín.: `1`<br>largo máx.: `10000` | — |

### G.57 `EvidenceReviewInputRequest`

Usado por: `POST /api/v1/catalogs/evidence/{row_id}/review/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `review_state` | `ReviewStateEnum` | Sí | Sin restricción simple declarada | — |

### G.58 `ExtrasPreviewRequestRequest`

Usado por: `POST /api/v1/projects/extras-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `nominal_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `nominal_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `parametric_tree` | `—` | Sí | Sin restricción simple declarada | — |
| `target_module_id` | `string` | No | largo mín.: `1`<br>largo máx.: `150` | — |

### G.59 `FieldCommandRequest`

Usado por: `POST /api/v1/production/field/visits/{visit_id}/commands/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `kind` | `FieldCommandKindEnum` | Sí | Sin restricción simple declarada | — |
| `position_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `unit_index` | `integer` | No | mín.: `1`<br>máx.: `10000` | — |
| `scan` | `string` | No | largo máx.: `3000` | — |
| `note` | `string` | No | largo máx.: `2000` | — |
| `photo_b64` | `string` | No | largo mín.: `1`<br>largo máx.: `2000000` | — |
| `signature_b64` | `string` | No | largo mín.: `1`<br>largo máx.: `270000` | — |
| `checks` | `FieldChecksRequest` | No | Sin restricción simple declarada | — |
| `measurements` | `—[]` | No | items máx.: `20` | — |
| `incident_kind` | `IncidentKindEnum` | No | Sin restricción simple declarada | — |
| `incident_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |
| `receiver_name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `receiver_rut` | `string` | No | largo mín.: `1`<br>largo máx.: `30` | — |
| `resolution_kind` | `ResolutionKindEnum` | No | Sin restricción simple declarada | — |
| `requirement_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `quantity` | `integer` | No | mín.: `1`<br>máx.: `10000` | — |
| `planned_on` | `string (date)` | No | Sin restricción simple declarada | — |
| `assigned_to` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `team` | `string` | No | largo mín.: `1`<br>largo máx.: `120` | — |

### G.60 `FieldReviewRequest`

Usado por: `POST /api/v1/production/field/visits/{visit_id}/review/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `measurement_event_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |
| `proposal_token` | `string` | No | largo mín.: `1`<br>largo máx.: `64` | — |

### G.61 `FieldScheduleRequest`

Usado por: `POST /api/v1/production/field/schedule/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `project_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `project_version_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `kind` | `FieldScheduleKindEnum` | Sí | Sin restricción simple declarada | — |
| `assigned_to` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `planned_on` | `string (date)` | Sí | Sin restricción simple declarada | — |
| `team` | `string` | Sí | largo mín.: `1`<br>largo máx.: `120` | — |
| `vehicle` | `string` | No | largo máx.: `120` | — |
| `address` | `string` | No | largo mín.: `1`<br>largo máx.: `1000` | — |
| `units` | `FieldUnitChoiceRequest[]` | Sí | Sin restricción simple declarada | — |

### G.62 `FinishPreviewRequestRequest`

Usado por: `POST /api/v1/projects/finish-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `nominal_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `nominal_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `parametric_tree` | `—` | Sí | Sin restricción simple declarada | — |
| `baseline_color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |

### G.63 `FiscalSimulationRequestRequest`

Usado por: `POST /api/v1/projects/{project_id}/fiscal-simulations/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `80` | — |
| `invoice_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `credit_note_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `scenario` | `FiscalSimulationStatusEnum` | Sí | Sin restricción simple declarada | — |

### G.64 `FlowConfirmationRequest`

Usado por: `POST /api/v1/projects/flow/confirm/{link_id}/`; `POST /api/v1/billing/flow/confirm/{order_id}/`; `POST /api/v1/billing/flow/plan/{offer_id}/`; `POST /api/v1/billing/flow/refund/{operation_id}/`; `POST /api/v1/billing/flow/register/{operation_id}/`; `POST /api/v1/billing/flow/registration-return/{operation_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `token` | `string` | Sí | largo mín.: `1`<br>largo máx.: `512` | — |

### G.65 `FlowSimulationRequestRequest`

Usado por: `POST /api/v1/projects/flow/simulated/{link_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `token` | `string` | Sí | largo mín.: `20`<br>largo máx.: `100` | — |
| `outcome` | `OutcomeEnum` | Sí | Sin restricción simple declarada | — |

### G.66 `FreezeRequestRequest`

Usado por: `POST /api/v1/documents/projects/{project_id}/freeze/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `pricing_operation_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.67 `GlassPreviewInputRequest`

Usado por: `POST /api/v1/catalogs/glass/preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `product` | `—` | Sí | Sin restricción simple declarada | — |
| `processing` | `—` | No | Sin restricción simple declarada | — |
| `width_mm` | `string (decimal)` | No | Sin restricción simple declarada | — |
| `height_mm` | `string (decimal)` | No | Sin restricción simple declarada | — |
| `opening_type` | `string` | No | largo mín.: `1` | — |
| `opening_use` | `OpeningUseEnum / NullEnum` | No | Sin restricción simple declarada | — |
| `is_sidelight` | `boolean` | No | Sin restricción simple declarada | — |
| `sill_height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `hardware_sku` | `string / null` | No | largo mín.: `1` | — |
| `leaf_weight_kg` | `string (decimal) / null` | No | Sin restricción simple declarada | — |
| `previous_infill_kg` | `string (decimal) / null` | No | Sin restricción simple declarada | — |
| `technical_sku` | `string` | No | largo mín.: `1` | — |

### G.68 `GlassRulesRequest`

Usado por: `PUT /api/v1/catalogs/glass/rules/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `items` | `—[]` | Sí | items máx.: `200` | — |

### G.69 `GlassVariantRequest`

Usado por: `POST /api/v1/catalogs/glass/variants/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `technical_sku` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `purchasing_sku` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `manufacturer_name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `version` | `integer` | Sí | mín.: `1` | — |
| `product` | `—` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.70 `HardwarePreviewRequestRequest`

Usado por: `POST /api/v1/projects/hardware-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `bay_id` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `parametric_tree` | `—` | Sí | Sin restricción simple declarada | — |

### G.71 `ImportConfirmRequest`

Usado por: `POST /api/v1/projects/{project_id}/imports/{import_id}/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `items` | `ConfirmItemRequest[]` | Sí | Sin restricción simple declarada | — |

### G.72 `ImportRequestRequest`

Usado por: `POST /api/v1/pricing/import/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `file` | `string (binary)` | Sí | Sin restricción simple declarada | — |
| `mapping` | `string` | Sí | largo mín.: `1` | JSON object mapping sku, description, unit and unit_cost to column names. |
| `decimal_separator` | `DecimalSeparatorEnum` | No | Sin restricción simple declarada | — |
| `cost_list_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |
| `apply` | `boolean` | No | Sin restricción simple declarada | — |

### G.73 `ImportUploadRequest`

Usado por: `POST /api/v1/projects/{project_id}/imports/`; `POST /api/v1/catalog-imports/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `file` | `string (binary)` | Sí | Sin restricción simple declarada | — |

### G.74 `InstallationRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/install/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `note` | `string` | No | largo máx.: `500` | — |

### G.75 `InternalApprovalRequest`

Usado por: `POST /api/v1/projects/{project_id}/approve/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `note` | `string` | No | largo máx.: `500` | — |

### G.76 `InternalDocumentRequestRequest`

Usado por: `POST /api/v1/projects/{project_id}/invoices/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `document_kind` | `DocumentKindEnum` | No | Sin restricción simple declarada | — |

### G.77 `InventoryMovementRequestRequest`

Usado por: `POST /api/v1/inventory/movements/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `item_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `movement_type` | `InventoryMovementRequestMovementTypeEnum` | Sí | Sin restricción simple declarada | — |
| `quantity` | `string (decimal)` | Sí | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |
| `lot_code` | `string / null` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `rack_location` | `string / null` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `note` | `string` | Sí | largo mín.: `1`<br>largo máx.: `500` | — |

### G.78 `InvitationTokenRequest`

Usado por: `POST /api/v1/auth/invitation/`; `POST /api/v1/auth/invitation/accept/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `token` | `string` | Sí | largo mín.: `1`<br>patrón: `^[A-Za-z0-9_-]{40,100}$`<br>solo escritura: `True` | — |

### G.79 `InvitationWriteRequest`

Usado por: `POST /api/v1/organization/invitations/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `email` | `string (email)` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `role` | `MembershipRoleEnum` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.80 `JobEnqueueRequest`

Usado por: `POST /api/v1/jobs/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `type` | `string` | Sí | largo mín.: `1`<br>largo máx.: `120` | — |
| `payload` | `—` | Sí | Sin restricción simple declarada | — |
| `idempotency_key` | `string / null` | No | largo mín.: `1`<br>largo máx.: `128` | — |
| `max_attempts` | `integer` | No | mín.: `1`<br>máx.: `10` | — |

### G.81 `KitWriteRequest`

Usado por: `POST /api/v1/catalogs/hardware-kits/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid) / null` | Sí | Sin restricción simple declarada | — |
| `sku` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `opening_type` | `KitOpeningTypeEnum` | Sí | Sin restricción simple declarada | — |
| `min_leaf_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `max_leaf_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `min_leaf_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `max_leaf_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `max_leaf_weight_kg` | `string (decimal)` | Sí | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `rail_type` | `RailTypeEnum` | Sí | Sin restricción simple declarada | — |
| `carriages_qty` | `integer` | Sí | mín.: `0`<br>máx.: `2147483647` | — |
| `stay_arms_qty` | `integer` | Sí | mín.: `0`<br>máx.: `2147483647` | — |
| `contents` | `CatalogHardwareComponentRequest[]` | Sí | Sin restricción simple declarada | — |
| `weight_kg` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,2})?$` | — |
| `carriage_capacity_kg` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,2})?$` | — |
| `is_active` | `boolean` | Sí | Sin restricción simple declarada | — |
| `class_authority` | `estructura / null` | No | Sin restricción simple declarada | — |

### G.82 `LinkDeadlineRequest`

Usado por: `PUT /api/v1/projects/{project_id}/quote-links/{approval_id}/deadline/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_expires_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |
| `expires_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.83 `LinkRegenerateRequest`

Usado por: `POST /api/v1/projects/{project_id}/quote-links/{approval_id}/regenerate/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.84 `MailRecoveryRequest`

Usado por: `POST /api/v1/mail/{mail_id}/recover/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_attempt` | `integer` | Sí | mín.: `1` | — |
| `confirmed_remote_absence` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.85 `MailSendRequest`

Usado por: `POST /api/v1/projects/{project_id}/payments/{payment_id}/mail/`; `POST /api/v1/projects/{project_id}/quote-mail/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `expected_source_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `expected_recipient` | `string (email)` | Sí | largo mín.: `1` | — |
| `expected_document_sha256` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.86 `MeasurementConfirmRequest`

Usado por: `POST /api/v1/positions/{position_id}/measurements/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |
| `expected_generation` | `integer` | Sí | mín.: `1` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `acknowledge_warnings` | `boolean` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |

### G.87 `MountingPreviewRequest`

Usado por: `POST /api/v1/projects/mounting-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `design` | `PositionDesignRequest` | Sí | Sin restricción simple declarada | — |
| `measurements` | `—` | Sí | Sin restricción simple declarada | — |

### G.88 `OperatorStationRequestRequest`

Usado por: `PUT /api/v1/production/operator-station/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `station_code` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |

### G.89 `OrderReceiptRequestRequest`

Usado por: `POST /api/v1/inventory/orders/{order_id}/receipts/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `receipt_key` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `note` | `string / null` | No | largo mín.: `1`<br>largo máx.: `500` | — |
| `lines` | `ReceiptLineRequestRequest[]` | Sí | Sin restricción simple declarada | — |
| `supplier_document` | `string / null` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `received_on` | `string (date) / null` | No | Sin restricción simple declarada | — |
| `confirm_over_receipt` | `boolean` | No | Sin restricción simple declarada | — |

### G.90 `OrgBrandingWriteRequest`

Usado por: `PUT /api/v1/organization/branding/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `document_preferences` | `DocumentPreferencesPatchRequest` | No | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | No | Sin restricción simple declarada | — |
| `brand_primary_color` | `string` | No | largo mín.: `1`<br>patrón: `^#[0-9A-Fa-f]{6}$` | — |
| `document_attribution` | `boolean` | No | Sin restricción simple declarada | — |
| `portal_attribution` | `boolean` | No | Sin restricción simple declarada | — |
| `notification_email` | `string (email) / string` | No | Sin restricción simple declarada | — |
| `internal_mail_enabled` | `boolean` | No | Sin restricción simple declarada | — |
| `commercial_name` | `string / null` | No | largo máx.: `255` | — |
| `giro` | `string / null` | No | largo máx.: `255` | — |
| `brand_address` | `string / null` | No | largo máx.: `255` | — |
| `brand_phone` | `string / null` | No | largo máx.: `64` | — |
| `brand_email` | `string / null` | No | largo máx.: `255` | — |

### G.91 `PatchedArticleWriteRequest`

Usado por: `PATCH /api/v1/catalogs/articles/{row_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `coupling_rule` | `CouplerRuleRequest` | No | Sin restricción simple declarada | — |
| `cut_rule` | `ProfileCutRuleRequest` | No | Sin restricción simple declarada | — |
| `reinforcement_rule` | `ProfileReinforcementRuleRequest` | No | Sin restricción simple declarada | — |
| `system_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `sku` | `string` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `section` | `ProfileSectionRequest` | No | Sin restricción simple declarada | — |
| `role` | `CatalogProfileRoleEnum` | No | Sin restricción simple declarada | — |
| `material` | `MaterialEnum` | No | Sin restricción simple declarada | — |
| `face_width_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `commercial_length_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `welding_loss_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `reinforcement_sku` | `string / null` | No | largo máx.: `100` | — |
| `reinforcement_gap_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `weight_kg_m` | `string (decimal) / null` | No | patrón: `^-?\d{0,4}(?:\.\d{0,4})?$` | — |
| `steel_weight_kg_m` | `string (decimal) / null` | No | patrón: `^-?\d{0,4}(?:\.\d{0,4})?$` | — |

### G.92 `PatchedBeadWriteRequest`

Usado por: `PATCH /api/v1/catalogs/glazing/{row_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `glass_thickness_mm` | `string (decimal)` | No | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `bead_article_id` | `string (uuid)` | No | Sin restricción simple declarada | — |
| `bead_width_mm` | `string (decimal)` | No | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `gasket_interior_mm` | `string (decimal)` | No | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `gasket_exterior_mm` | `string (decimal)` | No | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `cut_add_mm` | `string (decimal)` | No | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `is_active` | `boolean` | No | Sin restricción simple declarada | — |

### G.93 `PatchedClientUpdateRequest`

Usado por: `PATCH /api/v1/clients/{client_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `rut` | `string` | No | largo máx.: `50` | — |
| `email` | `string (email) / string` | No | Sin restricción simple declarada | — |
| `phone` | `string` | No | largo máx.: `50` | — |
| `address` | `string` | No | Sin restricción simple declarada | — |
| `giro` | `string` | No | largo máx.: `80` | — |
| `comuna` | `string` | No | largo máx.: `20` | — |
| `notes` | `string` | No | largo máx.: `4000` | — |
| `party_kind` | `PartyKindEnum` | No | Sin restricción simple declarada | — |
| `contacts` | `ClientContactWriteRequest[]` | No | Sin restricción simple declarada | — |
| `addresses` | `ClientAddressWriteRequest[]` | No | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | No | Sin restricción simple declarada | — |

### G.94 `PatchedCncMachinePatchRequest`

Usado por: `PATCH /api/v1/production/cnc/machines/{machine_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_revision` | `string` | No | largo mín.: `64`<br>largo máx.: `64` | — |
| `machine_type` | `string` | No | largo máx.: `40` | — |
| `profile_setups` | `object[]` | No | Sin restricción simple declarada | — |
| `axes` | `string[] / null` | No | Sin restricción simple declarada | — |
| `clamps_declared` | `boolean` | No | Sin restricción simple declarada | — |
| `authority_source` | `string` | No | largo máx.: `500` | — |
| `code` | `string` | No | largo mín.: `1`<br>largo máx.: `40` | — |
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `120` | — |
| `manufacturer` | `string` | No | largo máx.: `120` | — |
| `model` | `string` | No | largo máx.: `120` | — |
| `controller_family` | `string` | No | largo máx.: `80` | — |
| `coordinate_systems` | `string[]` | No | Sin restricción simple declarada | — |
| `supported_kinds` | `string[] / null` | No | Sin restricción simple declarada | — |
| `supported_faces` | `string[] / null` | No | Sin restricción simple declarada | — |
| `max_member_length_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `safe_margin_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `clamp_zones` | `object[]` | No | Sin restricción simple declarada | — |
| `tool_ids` | `string[]` | No | Sin restricción simple declarada | — |
| `postprocessor_id` | `string` | No | largo máx.: `80` | — |
| `postprocessor_version` | `string` | No | largo máx.: `40` | — |
| `units` | `string` | No | largo mín.: `1`<br>largo máx.: `20` | — |
| `encoding` | `string` | No | largo mín.: `1`<br>largo máx.: `40` | — |
| `active` | `boolean` | No | Sin restricción simple declarada | — |

### G.95 `PatchedCncToolPatchRequest`

Usado por: `PATCH /api/v1/production/cnc/tools/{tool_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_revision` | `string` | No | largo mín.: `64`<br>largo máx.: `64` | — |
| `authority_source` | `string` | No | largo máx.: `500` | — |
| `code` | `string` | No | largo mín.: `1`<br>largo máx.: `40` | — |
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `120` | — |
| `kind` | `string` | No | largo mín.: `1`<br>largo máx.: `30` | — |
| `diameter_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `working_length_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `max_depth_mm` | `string / null` | No | Sin restricción simple declarada | — |
| `compatible_kinds` | `string[] / null` | No | Sin restricción simple declarada | — |
| `active` | `boolean` | No | Sin restricción simple declarada | — |

### G.96 `PatchedKitWriteRequest`

Usado por: `PATCH /api/v1/catalogs/hardware-kits/{row_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `sku` | `string` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `opening_type` | `KitOpeningTypeEnum` | No | Sin restricción simple declarada | — |
| `min_leaf_width_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `max_leaf_width_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `min_leaf_height_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `max_leaf_height_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `max_leaf_weight_kg` | `string (decimal)` | No | patrón: `^-?\d{0,4}(?:\.\d{0,2})?$` | — |
| `rail_type` | `RailTypeEnum` | No | Sin restricción simple declarada | — |
| `carriages_qty` | `integer` | No | mín.: `0`<br>máx.: `2147483647` | — |
| `stay_arms_qty` | `integer` | No | mín.: `0`<br>máx.: `2147483647` | — |
| `contents` | `CatalogHardwareComponentRequest[]` | No | Sin restricción simple declarada | — |
| `weight_kg` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,2})?$` | — |
| `carriage_capacity_kg` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,2})?$` | — |
| `is_active` | `boolean` | No | Sin restricción simple declarada | — |
| `class_authority` | `estructura / null` | No | Sin restricción simple declarada | — |

### G.97 `PatchedProjectUpdateRequest`

Usado por: `PATCH /api/v1/projects/{project_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `client_name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `client_rut` | `string` | No | largo máx.: `50` | — |
| `client_email` | `string (email) / string` | No | Sin restricción simple declarada | — |
| `client_phone` | `string` | No | largo máx.: `50` | — |
| `client_giro` | `string` | No | largo máx.: `80` | — |
| `client_comuna` | `string` | No | largo máx.: `20` | — |
| `client_address` | `string` | No | largo máx.: `70` | — |
| `client_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `client_address_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `delivery_address` | `string` | No | Sin restricción simple declarada | — |
| `notes_commercial` | `string` | No | Sin restricción simple declarada | — |
| `notes_internal` | `string` | No | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | No | Sin restricción simple declarada | — |

### G.98 `PatchedQuotationCustomerRequestRequest`

Usado por: `PATCH /api/v1/documents/projects/{project_id}/quotation-customer/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_updated_at` | `string (date-time)` | No | Sin restricción simple declarada | — |
| `client_name` | `string` | No | largo mín.: `1`<br>largo máx.: `255` | — |
| `client_rut` | `string` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `client_email` | `string (email)` | No | largo mín.: `1` | — |
| `delivery_address` | `string` | No | largo mín.: `1`<br>largo máx.: `2000` | — |

### G.99 `PatchedSystemWriteRequest`

Usado por: `PATCH /api/v1/catalogs/systems/{row_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `extra_authority` | `estructura / null` | No | Sin restricción simple declarada | — |
| `system_family` | `SystemFamilyEnum` | No | Sin restricción simple declarada | — |
| `sliding_parameters` | `SlidingSystemParametersRequest` | No | Sin restricción simple declarada | — |
| `dimensional_limits` | `SystemDimensionalLimitRequest[]` | No | Sin restricción simple declarada | — |
| `opening_capabilities` | `estructura / null` | No | Sin restricción simple declarada | — |
| `paired_leaf_rule` | `estructura / null` | No | Sin restricción simple declarada | — |
| `finish_authority` | `estructura / null` | No | Sin restricción simple declarada | — |
| `name` | `string` | No | largo mín.: `1`<br>largo máx.: `150` | — |
| `code` | `string` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `depth_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `material` | `MaterialEnum` | No | Sin restricción simple declarada | — |
| `chamber_count` | `integer` | No | mín.: `1`<br>máx.: `2147483647` | — |
| `sash_overlap_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `glass_clearance_white_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `glass_clearance_foil_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `pulley_height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `central_overlap_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `sliding_lateral_clearance_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `sliding_end_add_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `corner_bracket_loss_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `hook_depth_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `door_threshold_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `door_bottom_clearance_mm` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `rail_type` | `RailTypeEnum / NullEnum` | No | Sin restricción simple declarada | — |
| `sliding_glazing_deduction_width_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `sliding_glazing_deduction_height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `door_leaf_side_clearance_mm` | `string (decimal)` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `rebate_depth_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `end_milling_overlap_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `chamber_clearance_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `version` | `integer` | No | mín.: `1`<br>máx.: `2147483647` | — |
| `is_active` | `boolean` | No | Sin restricción simple declarada | — |
| `manufacturer` | `string / null` | No | largo máx.: `255` | — |
| `family` | `string / null` | No | largo máx.: `150` | — |
| `applications` | `string[]` | No | Sin restricción simple declarada | — |
| `finishes` | `string[]` | No | Sin restricción simple declarada | — |
| `process_profile_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |

### G.100 `PaymentIntegrationRequest`

Usado por: `PUT /api/v1/projects/payment-integration/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `api_url` | `ApiUrlEnum` | Sí | Sin restricción simple declarada | — |
| `api_key` | `string / string` | No | Sin restricción simple declarada | — |
| `secret_key` | `string / string` | No | solo escritura: `True` | — |
| `payer_return_url` | `string` | No | largo máx.: `500` | — |
| `enabled` | `boolean` | No | Sin restricción simple declarada | — |

### G.101 `PaymentLinkCreateRequest`

Usado por: `POST /api/v1/projects/{project_id}/payment-links/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `80` | — |
| `kind` | `PaymentKindEnum` | Sí | Sin restricción simple declarada | — |
| `amount` | `string (decimal)` | Sí | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |
| `payer_email` | `string (email)` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `subject` | `string` | No | largo máx.: `200` | — |
| `simulated` | `boolean` | No | Sin restricción simple declarada | — |
| `expires_at` | `string (date-time)` | No | Sin restricción simple declarada | — |

### G.102 `PaymentRecordRequest`

Usado por: `POST /api/v1/projects/{project_id}/payments/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `80` | — |
| `kind` | `PaymentKindEnum` | Sí | Sin restricción simple declarada | — |
| `amount` | `string (decimal)` | Sí | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |
| `method` | `MethodEnum` | Sí | Sin restricción simple declarada | — |
| `reference` | `string` | No | largo máx.: `200` | — |
| `note` | `string` | No | largo máx.: `2000` | — |
| `recorded_at` | `string (date-time)` | No | Sin restricción simple declarada | — |
| `recorded_on` | `string (date)` | No | Sin restricción simple declarada | — |

### G.103 `PaymentVoidRequest`

Usado por: `POST /api/v1/projects/{project_id}/payments/{payment_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `reason` | `string` | No | largo máx.: `500` | — |

### G.104 `PolicyWriteRequest`

Usado por: `PUT /api/v1/organization/extras/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `policy` | `—` | Sí | Sin restricción simple declarada | — |
| `expected_revision` | `integer` | Sí | mín.: `0` | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |

### G.105 `PortalPayRequestRequest`

Usado por: `POST /api/v1/portal/quotes/{token}/pay/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `amount` | `string (decimal)` | Sí | patrón: `^-?\d{0,14}(?:\.\d{0,0})?$` | — |
| `payer_email` | `string (email)` | Sí | largo mín.: `1`<br>largo máx.: `254` | — |

### G.106 `PositionUpdateRequest`

Usado por: `PUT /api/v1/positions/{position_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `location_tag` | `string` | Sí | largo máx.: `120` | — |
| `quantity` | `integer` | Sí | mín.: `1`<br>máx.: `2147483647` | — |
| `design` | `PositionDesignRequest` | Sí | Sin restricción simple declarada | — |
| `measurements` | `—` | No | Sin restricción simple declarada | — |
| `measurement_reason` | `string` | No | largo mín.: `1`<br>largo máx.: `1000` | — |
| `placement` | `PositionPlacementRequest` | No | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |

### G.107 `PositionWriteRequest`

Usado por: `POST /api/v1/projects/{project_id}/positions/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `location_tag` | `string` | Sí | largo máx.: `120` | — |
| `quantity` | `integer` | Sí | mín.: `1`<br>máx.: `2147483647` | — |
| `design` | `PositionDesignRequest` | Sí | Sin restricción simple declarada | — |
| `measurements` | `—` | No | Sin restricción simple declarada | — |
| `measurement_reason` | `string` | No | largo mín.: `1`<br>largo máx.: `1000` | — |
| `placement` | `PositionPlacementRequest` | No | Sin restricción simple declarada | — |

### G.108 `PriceRequestRequest`

Usado por: `POST /api/v1/pricing/preview/`; `POST /api/v1/pricing/workspace/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `project_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `pricing_mode` | `PricingModeEnum` | Sí | Sin restricción simple declarada | — |
| `context_code` | `string` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `currency` | `CurrencyEnum` | Sí | Sin restricción simple declarada | — |
| `effective_date` | `string (date)` | Sí | Sin restricción simple declarada | — |
| `fx_snapshot_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `discount_pct` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,4})?$` | — |
| `target_margin` | `string (decimal)` | No | patrón: `^-?\d{0,2}(?:\.\d{0,4})?$` | — |
| `segment` | `SegmentEnum` | No | Sin restricción simple declarada | — |
| `extras` | `ExtraChargeRequest[]` | No | items máx.: `10` | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |

### G.109 `ProjectCreditNoteEmitRequest`

Usado por: `POST /api/v1/projects/{project_id}/invoices/{invoice_id}/credit-note-dte/`; `POST /api/v1/projects/{project_id}/invoices/{invoice_id}/credit-note/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `reason` | `string` | No | Sin restricción simple declarada | — |
| `amount` | `string (decimal)` | No | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |

### G.110 `ProjectOpsApplyRequest`

Usado por: `POST /api/v1/projects/{project_id}/operations/apply/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `ops` | `DesignOperationRequest[]` | Sí | Sin restricción simple declarada | — |
| `before_sig` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |

### G.111 `ProjectOpsPreviewRequest`

Usado por: `POST /api/v1/projects/{project_id}/operations/preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `ops` | `DesignOperationRequest[]` | Sí | Sin restricción simple declarada | — |

### G.112 `ProjectWriteRequest`

Usado por: `POST /api/v1/projects/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `client_name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `client_rut` | `string` | No | largo máx.: `50` | — |
| `client_email` | `string (email) / string` | No | Sin restricción simple declarada | — |
| `client_phone` | `string` | No | largo máx.: `50` | — |
| `client_giro` | `string` | No | largo máx.: `80` | — |
| `client_comuna` | `string` | No | largo máx.: `20` | — |
| `client_address` | `string` | No | largo máx.: `70` | — |
| `client_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `client_address_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `delivery_address` | `string` | No | Sin restricción simple declarada | — |
| `notes_commercial` | `string` | No | Sin restricción simple declarada | — |
| `notes_internal` | `string` | No | Sin restricción simple declarada | — |

### G.113 `PurchaseMailRequestRequest`

Usado por: `POST /api/v1/purchasing/orders/{order_id}/mail/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `expected_recipient` | `string (email)` | Sí | largo mín.: `1` | — |

### G.114 `PurchaseNeedsConfirmRequest`

Usado por: `POST /api/v1/purchasing/needs/confirm/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `operation_key` | `string` | Sí | largo mín.: `8`<br>largo máx.: `120` | — |
| `preview_hash` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `lines` | `PurchaseNeedChoiceRequest[]` | Sí | Sin restricción simple declarada | — |

### G.115 `QcRemakeRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/qc-remake/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `operation_key` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `note` | `string` | Sí | largo mín.: `1`<br>largo máx.: `500` | — |
| `item_code` | `string` | No | largo máx.: `50` | — |

### G.116 `QuotationIssueRequestRequest`

Usado por: `POST /api/v1/documents/projects/{project_id}/issue/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `preview_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `expected_snapshot_sha256` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `expected_document_sha256` | `string` | Sí | largo mín.: `1`<br>patrón: `^[0-9a-f]{64}$` | — |
| `expected_recipient` | `string (email)` | Sí | largo mín.: `1` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.117 `QuotationPreviewRequestRequest`

Usado por: `POST /api/v1/documents/projects/{project_id}/quotation-preview/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `pricing_operation_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.118 `RectificationRequest`

Usado por: `POST /api/v1/positions/{position_id}/measurements/rectify/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `design` | `PositionDesignRequest` | Sí | Sin restricción simple declarada | — |
| `measurements` | `—` | Sí | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |
| `expected_current_revision` | `string` | Sí | largo mín.: `1`<br>patrón: `^REV-[A-Z]+$` | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |
| `confirmed` | `boolean` | No | Sin restricción simple declarada | — |
| `proposal_token` | `string` | No | largo mín.: `1`<br>largo máx.: `64` | — |

### G.119 `RemakeRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/remake/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `note` | `string / null` | No | largo mín.: `1`<br>largo máx.: `500` | — |

### G.120 `RemnantActionRequest`

Usado por: `POST /api/v1/inventory/remnants/{remnant_id}/scrap/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `3`<br>largo máx.: `500` | — |

### G.121 `RemnantCreateRequest`

Usado por: `POST /api/v1/inventory/remnants/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `kind` | `StockKindEnum` | Sí | Sin restricción simple declarada | — |
| `stock_authority_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `sheet_workshop_sku` | `string / null` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `physical_stock_identity` | `string / null` | No | largo mín.: `1` | — |
| `material` | `string / null` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `color` | `string / null` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `length_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |
| `width_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |
| `height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,12}(?:\.\d{0,2})?$` | — |
| `rack_location` | `string / null` | No | largo mín.: `1`<br>largo máx.: `100` | — |
| `notes` | `string / null` | No | largo mín.: `1`<br>largo máx.: `500` | — |

### G.122 `RemnantMoveRequest`

Usado por: `POST /api/v1/inventory/remnants/{remnant_id}/move/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `3`<br>largo máx.: `500` | — |
| `rack_location` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |

### G.123 `RemnantReserveRequest`

Usado por: `POST /api/v1/inventory/remnants/{remnant_id}/reserve/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `order_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |

### G.124 `ResetPricingRequest`

Usado por: `POST /api/v1/projects/{project_id}/reset-pricing/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `expected_operation_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.125 `RuleWriteRequest`

Usado por: `PUT /api/v1/organization/mounting/{system_id}/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `rule` | `—` | Sí | Sin restricción simple declarada | — |
| `expected_revision` | `integer` | Sí | mín.: `0` | — |
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |

### G.126 `SendOrderRequestRequest`

Usado por: `POST /api/v1/purchasing/orders/{order_id}/cancel/`; `POST /api/v1/purchasing/orders/{order_id}/send/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `expected_at` | `string (date) / null` | No | Sin restricción simple declarada | — |
| `sent_to` | `string / null` | No | largo máx.: `200` | — |

### G.127 `ServicesWriteRequest`

Usado por: `PUT /api/v1/projects/{project_id}/services/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `selections` | `—[]` | Sí | items máx.: `30` | — |
| `expected_updated_at` | `string (date-time)` | Sí | Sin restricción simple declarada | — |

### G.128 `SheetFormatRequestRequest`

Usado por: `POST /api/v1/inventory/sheet-formats/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `kind` | `SheetFormatRequestKindEnum` | Sí | Sin restricción simple declarada | — |
| `technical_sku` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `sku` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `edge_trim_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `supplier` | `string` | Sí | largo mín.: `1`<br>largo máx.: `255` | — |
| `source` | `string` | Sí | largo mín.: `1`<br>largo máx.: `500` | — |

### G.129 `SiiCafUploadRequest`

Usado por: `POST /api/v1/sii/cafs/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `caf_xml` | `string` | Sí | largo mín.: `1`<br>largo máx.: `131072` | — |
| `giro_emis` | `string` | No | largo máx.: `80` | — |
| `dir_origen` | `string` | No | largo máx.: `70` | — |
| `cmna_origen` | `string` | No | largo máx.: `20` | — |
| `acteco` | `integer / null` | No | mín.: `100000`<br>máx.: `999999` | — |

### G.130 `SiiCertificateUploadRequest`

Usado por: `POST /api/v1/sii/certificate/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `pfx_b64` | `string` | Sí | largo mín.: `1`<br>largo máx.: `90000` | — |
| `password` | `string` | No | largo máx.: `200` | — |
| `nro_resol` | `integer` | Sí | mín.: `0` | — |
| `fch_resol` | `string` | Sí | largo mín.: `1`<br>largo máx.: `10` | — |

### G.131 `SiiEnvioSendRequest`

Usado por: `POST /api/v1/projects/{project_id}/credit-notes/{credit_note_id}/dte-envio/`; `POST /api/v1/projects/{project_id}/invoices/{invoice_id}/dte-envio/`; `POST /api/v1/production/orders/{order_id}/dispatch-note-envio/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `resubmit` | `boolean` | No | Sin restricción simple declarada | — |

### G.132 `SimulateOpsRequest`

Usado por: `POST /api/v1/projects/operations/simulate/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `system_id` | `string (uuid)` | Sí | Sin restricción simple declarada | — |
| `color` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `product` | `—` | Sí | Sin restricción simple declarada | — |
| `ops` | `DesignOperationRequest[]` | Sí | Sin restricción simple declarada | — |
| `quantity` | `integer` | No | mín.: `1`<br>máx.: `2147483647` | — |

### G.133 `StepTransitionRequestRequest`

Usado por: `POST /api/v1/production/steps/{step_id}/transition/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `block_on_fail` | `boolean` | No | Sin restricción simple declarada | — |
| `action` | `StepTransitionRequestActionEnum` | Sí | Sin restricción simple declarada | — |
| `note` | `string / null` | No | largo mín.: `1`<br>largo máx.: `500` | — |
| `qc_result` | `QcResultEnum / NullEnum` | No | Sin restricción simple declarada | — |
| `qc_check` | `QcCheckRequest` | No | Sin restricción simple declarada | — |
| `qc_item` | `string / null` | No | largo máx.: `50` | — |
| `ops_done` | `string[] / null` | No | Sin restricción simple declarada | — |

### G.134 `SuccessorRequestRequest`

Usado por: `POST /api/v1/projects/{project_id}/successor/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `expected_current_revision` | `string` | Sí | largo mín.: `1`<br>patrón: `^REV-[A-Z]+$` | — |

### G.135 `SupplierUpsertRequest`

Usado por: `POST /api/v1/purchasing/suppliers/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `tax_id` | `string` | Sí | largo mín.: `1`<br>largo máx.: `100` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `300` | — |
| `details` | `SupplierDetailsRequest` | No | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.136 `SystemWriteRequest`

Usado por: `POST /api/v1/catalogs/systems/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `extra_authority` | `estructura / null` | No | Sin restricción simple declarada | — |
| `system_family` | `SystemFamilyEnum` | Sí | Sin restricción simple declarada | — |
| `sliding_parameters` | `SlidingSystemParametersRequest` | No | Sin restricción simple declarada | — |
| `dimensional_limits` | `SystemDimensionalLimitRequest[]` | No | Sin restricción simple declarada | — |
| `opening_capabilities` | `estructura / null` | No | Sin restricción simple declarada | — |
| `paired_leaf_rule` | `estructura / null` | No | Sin restricción simple declarada | — |
| `finish_authority` | `estructura / null` | No | Sin restricción simple declarada | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `150` | — |
| `code` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `depth_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `material` | `MaterialEnum` | Sí | Sin restricción simple declarada | — |
| `chamber_count` | `integer` | Sí | mín.: `1`<br>máx.: `2147483647` | — |
| `sash_overlap_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `glass_clearance_white_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `glass_clearance_foil_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `pulley_height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `central_overlap_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `sliding_lateral_clearance_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `sliding_end_add_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `corner_bracket_loss_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `hook_depth_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `door_threshold_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `door_bottom_clearance_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,2}(?:\.\d{0,2})?$` | — |
| `rail_type` | `RailTypeEnum / NullEnum` | No | Sin restricción simple declarada | — |
| `sliding_glazing_deduction_width_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `sliding_glazing_deduction_height_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `door_leaf_side_clearance_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `rebate_depth_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `end_milling_overlap_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `chamber_clearance_mm` | `string (decimal) / null` | No | patrón: `^-?\d{0,8}(?:\.\d{0,2})?$` | — |
| `version` | `integer` | Sí | mín.: `1`<br>máx.: `2147483647` | — |
| `is_active` | `boolean` | Sí | Sin restricción simple declarada | — |
| `manufacturer` | `string / null` | No | largo máx.: `255` | — |
| `family` | `string / null` | No | largo máx.: `150` | — |
| `applications` | `string[]` | No | Sin restricción simple declarada | — |
| `finishes` | `string[]` | No | Sin restricción simple declarada | — |
| `process_profile_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |

### G.137 `ThermalAuthorityRequest`

Usado por: `POST /api/v1/catalogs/systems/{system_id}/thermal/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `kind` | `ThermalAuthorityKindEnum` | Sí | Sin restricción simple declarada | — |
| `profile_skus` | `string[]` | No | Sin restricción simple declarada | — |
| `glass_sku` | `string / null` | No | largo mín.: `1`<br>largo máx.: `200` | — |
| `source_position_id` | `string (uuid) / null` | No | Sin restricción simple declarada | — |
| `spacer_code` | `string / null` | No | largo mín.: `1`<br>largo máx.: `200` | — |
| `uf` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,6})?$` | — |
| `ug` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,6})?$` | — |
| `solar_factor` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,6})?$` | — |
| `psi_g` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,6})?$` | — |
| `air_class` | `integer / null` | No | mín.: `0`<br>máx.: `4` | — |
| `air_pressure_pa` | `string (decimal) / null` | No | patrón: `^-?\d{0,6}(?:\.\d{0,6})?$` | — |
| `water_class` | `string / null` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `wind_class` | `string / null` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `min_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `max_width_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `min_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `max_height_mm` | `string (decimal)` | Sí | patrón: `^-?\d{0,10}(?:\.\d{0,2})?$` | — |
| `opening_types` | `string[]` | Sí | items mín.: `1` | — |
| `source_document` | `string` | Sí | largo mín.: `1`<br>largo máx.: `500` | — |
| `source_url` | `string (uri)` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `source_page` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `laboratory` | `string` | Sí | largo mín.: `1`<br>largo máx.: `300` | — |
| `laboratory_registration` | `string` | No | largo máx.: `1000` | — |
| `report_date` | `string (date)` | Sí | Sin restricción simple declarada | — |
| `valid_until` | `string (date)` | Sí | Sin restricción simple declarada | — |
| `standard` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `applicability` | `string` | Sí | largo mín.: `1`<br>largo máx.: `2000` | — |
| `synthetic` | `boolean` | No | Sin restricción simple declarada | — |

### G.138 `ThermalReviewRequest`

Usado por: `POST /api/v1/catalogs/systems/{system_id}/thermal/{report_id}/review/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `state` | `ThermalReviewStateEnum` | Sí | Sin restricción simple declarada | — |
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |

### G.139 `ThermalWriteRequest`

Usado por: `PUT /api/v1/projects/{project_id}/thermal/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `inputs` | `ThermalInputRequest` | Sí | Sin restricción simple declarada | — |
| `expected_updated_at` | `string (date-time) / null` | Sí | Sin restricción simple declarada | — |

### G.140 `WithdrawRequest`

Usado por: `POST /api/v1/pricing/operations/{operation_id}/withdraw/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `reason` | `string` | Sí | largo mín.: `1`<br>largo máx.: `1000` | — |

### G.141 `WorkCenterRequestRequest`

Usado por: `POST /api/v1/production/work-centers/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `code` | `string` | Sí | largo mín.: `1`<br>largo máx.: `50` | — |
| `name` | `string` | Sí | largo mín.: `1`<br>largo máx.: `200` | — |
| `kind` | `WorkCenterRequestKindEnum` | Sí | Sin restricción simple declarada | — |
| `display_order` | `integer` | No | Sin restricción simple declarada | — |

### G.142 `WorkOrderCancelRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/cancel/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `confirmed` | `boolean` | Sí | Sin restricción simple declarada | — |
| `note` | `string / null` | No | largo máx.: `500` | — |

### G.143 `WorkOrderOptimizeCompareRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/optimize/compare/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `color` | `string` | No | largo máx.: `50` | — |

### G.144 `WorkOrderOptimizeRequestRequest`

Usado por: `POST /api/v1/production/orders/{order_id}/optimize/`.

| Campo | Tipo / ref | Obligatorio | Restricciones declaradas | Descripción |
|---|---|---|---|---|
| `color` | `string` | No | largo máx.: `50` | — |
| `cutting_profile_code` | `string / null` | No | largo mín.: `1`<br>largo máx.: `50` | — |
| `strategy` | `StrategyEnum` | No | Sin restricción simple declarada | — |

<!-- GENERATED_APPENDICES_END -->
