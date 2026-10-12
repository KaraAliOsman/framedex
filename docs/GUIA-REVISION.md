# Revisión de DEKOPEN v1

Esta revisión usa datos **DEMO** y pagos simulados. No autoriza fabricar ni acredita
dinero, certificación térmica o documentos tributarios reales. Los cálculos y
decisiones pasan por el mismo producto que usará su empresa.

## Abra el producto

1. Abra Docker Desktop y espere a que indique que está funcionando.
2. En la carpeta de este repositorio, abra PowerShell y ejecute:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
   ```

3. Espere «Revisión lista». El primer inicio construye el producto, aplica las
   migraciones y prepara las cuentas, catálogo y obras; puede tardar varios minutos.
4. Abra <http://127.0.0.1:5179>. El correo de esta revisión está en
   <http://127.0.0.1:25364>. Ambos son locales.
5. En Acceso escriba un correo de la tabla y pulse **Enviar enlace de acceso**.
   Abra el último mensaje para ese destinatario en el correo local y pulse su
   enlace una vez. Para cambiar de persona, cierre sesión y solicite otro enlace.

| Persona | Correo de revisión | Qué comprobar |
|---|---|---|
| Dueño | demo-owner@fixture.dekopen.local | Precios, permisos, aprobaciones, cobranza y ajustes |
| Estimador | demo-estimator@fixture.dekopen.local | Crear, dibujar, cotizar, emitir y revisar cambios |
| Jefe de taller | demo-manager@fixture.dekopen.local | Compras, recepción, producción, calidad y despacho |
| Operario | demo-operator@fixture.dekopen.local | Su estación y la pieza escaneada |
| Instalador | demo-installer@fixture.dekopen.local | Visitas asignadas, foto, firma e incidencia |
| Cliente final | Enlace de una cotización emitida | Revisar opciones, pedir cambios, aprobar y pagar en prueba |

El dueño debe configurar y comprobar el segundo factor cuando el producto lo
solicite. Escanee el QR con su aplicación de autenticación, escriba el código y
conserve el factor mientras revisa; el acceso a funciones sensibles sigue protegido.

La revisión conserva su base al cerrarse y al volver a abrirse. Usa recursos
propios `framedex-review`; no necesita reiniciar ni borrar otra base local.
Para detenerla sin perder avances:

```powershell
python scripts/review_stack.py stop
```

Requisitos del primer inicio: Git, Node, Python, Docker Desktop y Supabase CLI
2.116.0. El script usa la `.venv` si existe. Las credenciales locales se leen de
`.env` en memoria; no las copie a comandos, capturas ni archivos compartidos.

## Primera vuelta de 30 minutos

La vivienda tiene doce posiciones, un bow de tres módulos y un conjunto de dos.
La torre tiene cien posiciones. Los demás proyectos son puntos de partida para
ensayar anticipo, fabricación, despacho, instalación y rechazo: sus nombres no
acreditan que esas acciones ya ocurrieron.

| Minutos | Persona y recorrido | Qué debería ver |
|---|---|---|
| 0–4 | Estimador: Hoy → Proyectos → vivienda → primera posición | Dibujo real, vista interior, medidas con unidades, vidrio, color y qué falta |
| 4–8 | Editor: cambie una cota; proponga un cambio con el asistente; revise, aplique y deshaga | Diferencia visible antes del clic, resultado calculado y recuperación del diseño |
| 8–12 | Obra → Precios → cambie el margen → revise y aplique | Venta y utilidad con fuente; si sale de la banda, solicitud y decisión del dueño |
| 12–17 | Cotización → Preparar emisión → complete condiciones → revisar PDF → confirmar emisión | Checklist accionable, PDF real y revisión sellada; el bow sin autoridad muestra Solo cotización |
| 17–21 | Abra el enlace del cliente en otra ventana, a 390 px | Dibujos, condiciones y opción elegida; solicite cambios o apruebe con identidad y consentimiento |
| 21–25 | Cobranza de una obra aprobada → Crear enlace de prueba → retorno | Marca simulada, un movimiento, recibo y saldo; repetir la verificación no duplica el pago |
| 25–30 | Dueño: Ajustes → Integraciones; cambie tema y vuelva a la obra | Estado y pasos de cada conexión; preferencias guardadas y emisiones anteriores intactas |

## Recorridos completos

Dedique hasta 30 minutos a cada fila. Empiece desde una obra de ensayo nueva para
las acciones que cambien un acuerdo; las revisiones emitidas se conservan.
La columna final describe la señal de aceptación, no una tarea automática.

| # | Recorrido | Señal que debe comprobar |
|---|---|---|
| 1 | Cuenta de estimador → configuración inicial → cliente → obra → primera posición → precio → emisión | Se pide solo lo necesario; datos guardados, cálculo y PDF revisado antes de emitir |
| 2 | Vivienda de doce posiciones → precio fuera de banda → dueño decide → revisión A → cliente pide cambio → cambio global → revisión B → aprobación → anticipo de prueba | Delta del motor, decisión humana y elección/cobro ligados a la revisión |
| 3 | Abra A y B y use Comparar revisiones | A mantiene su dibujo, precio, condiciones y PDF originales |
| 4 | Jefe: Comprar lo que falta → revisar orden → recepción parcial con daño → cancelar saldo → recomprar → Inventario | Solo lo útil aumenta stock; daño, saldo y retazos tienen origen y dirección física |
| 5 | Revisión aprobada y apta → liberar → tablero → estación → calidad falla → reposición → calidad pasa → embalaje → despacho | Una pieza por pantalla; supervisor decide calidad, etiquetas y reposición trazables |
| 6 | Producción → Mecanizado → misma pieza, máquina compatible e incompatible | Revisión del intercambio, advertencias concretas o bloqueo; una operación sin autoridad permanece visible y sin emitir |
| 7 | Editor → asistente → propuesta → preview → aplicar → deshacer → auditoría; cancelar y reintentar otra petición | MiMo real, operaciones tipadas y ninguna aplicación sin clic |
| 8 | Cambie entre los cinco roles y las dos empresas | Solo datos y acciones permitidos; copiar una dirección ajena no abre su registro |
| 9 | Calendario de una obra aprobada → pago manual → enlace por saldo → pago de prueba | Saldo del motor llega a cero y el recibo no se duplica al volver al retorno |
| 10 | Catálogo → importar PDF o planilla con IA → revisar → publicar; pruebe la plantilla manual | Fuente literal, diff y revisión humana; readiness coincide con el gate, DEMO sigue declarado |
| 11 | Compare fijo, abatible, oscilobatiente, corredera, bow y acoplado; después las tipologías avanzadas compatibles | Aperturas, vidrio, dos caras, extras y fabricación conservan cortes/BOM/precio en dibujo, PDF, portal, OT y 3D |
| 12 | Revise el informe de IA enlazado en la aceptación | Proveedor real, tasa E/J acreditada, cero números inventados y cero acciones consecuentes automáticas |
| 13 | Instalador: medición → rectificación revisada → fabricación → visita → foto/firma → incidencia → postventa | Evidencia por unidad, sincronización con acceso vigente y actas inmutables |
| 14 | Dueño: obra cerrada → Analítica → margen → causa → F6 → movimiento | Cotizado y real con período, cobertura y fuente; falta de evidencia dice Sin dato |

Para una primera emisión complete RUT válido, correo del cliente y dirección de
obra; el checklist lleva al campo que falta. Declare vigencia, pago, plazo, instalación, exclusiones,
garantía y ubicación. Confirme las sugerencias de fabricación que corresponden.
No convierta un aviso de autoridad faltante en aprobación: complete su fuente o
use **Solo cotización**. La vista previa muestra si una revisión permite producir.

## Decisiones que puede cambiar

En Ajustes se guardan identidad de empresa, moneda/FX declarado, IVA y banda de
margen, vigencia de cotización y revisión privada del PDF, anticipo y calendario,
papel/documentos, numeración, estaciones, garantía, aviso/correo, preferencias
de analítica e IA. El detalle y sus límites están en
[valores por defecto](decisions/valores-por-defecto.md).
Un cambio configura nuevas operaciones; no reescribe una emisión anterior.

## Conecte después de aceptar

El proveedor de IA local ya está configurado. Revise en Ajustes › Inteligencia
artificial la conexión antes de usarla. Complete [ACTIVACION](operations/ACTIVACION.md) para
hosting, Supabase productivo, Flow de su empresa, certificado/CAF/transporte SII,
correo del dominio y webhooks. Añada catálogo, precios, tarifas, datos térmicos y
calibración industrial con fuentes reales. La marca DEMO desaparece solo al
reemplazar la autoridad sintética mediante revisión y publicación.

El [informe de aceptación](redesign/acceptance-2026-10-12.md) conserva las pruebas,
capturas, mediciones y límites que acompañan el PR de revisión.
