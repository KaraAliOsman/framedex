# El agente de DEKOPEN · especificación

**Posición:** a octubre de 2026 casi ningún programa del rubro tiene IA real
(ver informe). Extrusia (EE. UU.) responde preguntas; A+W lee pedidos en PDF;
amazive y Window Tracer cotizan desde planos o croquis, sin precisión publicada;
Forterro (Logikal + KLAES) solo anuncia. DEKOPEN gana si su IA **hace el trabajo
completo** —de la solicitud del cliente a la cotización enviada y la orden de
taller— con las cifras del motor y la aprobación humana donde corresponde.

## 1. Principios no negociables

1. **El motor calcula, la IA opera.** La IA solo llama funciones del producto
   (`engine/src/dekopen_engine/design_operations.py`, operaciones del backend).
   Nunca escribe una medida, un precio ni un corte en texto libre.
2. **Cada cifra se puede rastrear.** Toda cantidad propuesta por la IA enlaza al
   origen: el párrafo del correo, la celda del Excel, la hoja y la zona del plano,
   la foto. Patrón Ruh AI: si falta el origen, la línea queda sin precio, no se inventa.
3. **Doble lectura para documentos.** Extracciones de planos y catálogos se hacen
   dos veces con estrategias distintas; solo las diferencias van a revisión humana.
4. **Controles en la aplicación, no en el prompt** (OWASP LLM06). Los permisos,
   el presupuesto de créditos y las acciones que requieren clic humano se
   imponen en el servidor.
5. **Todo se puede deshacer** salvo lo externo: emitir, enviar, pagar, comprar y
   publicar requieren siempre un clic humano (invariante actual del repositorio).

## 2. Las 12 automatizaciones del lanzamiento (ordenadas por valor)

| # | Automatización | Entrada | Salida | Verificación |
|---|---|---|---|---|
| 1 | **Solicitud → cotización borrador** | Texto, WhatsApp pegado, correo, nota de voz | Obra con ventanas configuradas + precio del motor + PDF borrador | Cada ventana enlaza a la frase de origen; supuestos marcados |
| 2 | **Plano o PDF → cuadro de vanos** | PDF de arquitectura, foto de plano | Lista de vanos con medidas y tipología | Doble lectura, discrepancias marcadas, enlace a hoja/zona |
| 3 | **Foto de la obra → ventana** | Foto del vano con referencia de medida | Tipología propuesta + medidas aproximadas («para cotizar, no para fabricar») | Etiqueta «aproximado» hasta medición en terreno |
| 4 | **Manual del fabricante → serie** | PDF de catálogo/lista de precios | Ficha de serie con perfiles, reglas, precios (ver catálogo §5) | Doble extracción + ventana de prueba |
| 5 | **Cambios en lista de precios** | Nueva lista del proveedor | Diferencias por artículo y obras afectadas | El usuario aprueba la nueva vigencia |
| 6 | **Revisión antes de emitir** | Cotización en borrador | Lista de riesgos: hojas fuera de rango, vidrio sin seguridad donde se exige, margen bajo, condiciones faltantes | Reglas del motor; cada aviso enlaza a la ventana |
| 7 | **Cambios por conversación** | «Haz la V3 corredera de 3 hojas y sube todas a 1,20 de alto» | Operaciones del motor aplicadas con deshacer | Vista previa del cambio antes de aplicar (según autonomía) |
| 8 | **Seguimiento comercial** | Cotizaciones enviadas | Borrador de recordatorio por WhatsApp/correo | Envío solo con clic humano |
| 9 | **Aceptación → producción** | Cotización aceptada | OT, hoja de corte optimizada, pedido de compra propuesto | El jefe de taller libera; compras con clic |
| 10 | **Preguntas del negocio** | «¿Cuánto vendí en PVC este mes?», «¿qué obras están atrasadas?» | Respuesta con tabla y enlaces | Consultas sobre datos reales, con la consulta visible |
| 11 | **Medición en terreno asistida** | Medidas dictadas o fotografiadas en obra | Medidas de fabricación con descuentos de montaje | Confirmación del instalador |
| 12 | **Postventa** | Reclamo con foto | Caso con ventana identificada y propuesta de solución | El responsable decide |

Fuera del lanzamiento (fase 2): pronóstico de demanda, planificación de
estaciones, detección de defectos por foto, licitaciones (GAEB/Excel de constructoras).

## 3. Autonomía (se conserva y se simplifica)

| Nivel | Nombre visible | Comportamiento |
|---|---|---|
| 1 | **Proponer** | Muestra el cambio; el usuario aplica |
| 2 | **Hacer y avisar** | Aplica cambios reversibles; muestra un resumen con «Deshacer» |
| 3 | **Hacer todo** | Encadena tareas reversibles sin interrumpir; entrega un recibo final |

En los tres niveles: emitir, enviar, comprar, pagar y publicar esperan clic humano.

## 4. Dónde vive la IA en la interfaz

- **Barra de comandos global (Ctrl K):** buscar, navegar y pedir («nueva cotización
  para Pérez, 4 ventanas PVC»). Reemplaza al popup como punto de entrada principal.
- **Panel lateral del agente:** conversación persistente por obra, con adjuntos,
  progreso de tareas, recibos y deshacer. Se abre desde la barra o el botón
  «Pedir a DEKOPEN».
- **Sugerencias en línea:** en el editor y en la cotización, chips discretos
  («2 ventanas sin vidrio de seguridad en baño — corregir»), nunca modales.
- **Bandeja de revisión:** cola única de lo que la IA preparó y espera aprobación
  (cotizaciones borrador, series importadas, diferencias de precios).

## 5. Contrato técnico (para el trabajador GPT)

- **Herramientas del agente = API del producto.** Cada herramienta mapea a un
  endpoint existente o nuevo del backend con validación del motor. Lista mínima:
  `crear_obra`, `agregar_ventana`, `modificar_ventana(operaciones)`,
  `calcular_precio`, `generar_pdf_borrador`, `buscar_cliente`, `importar_tabla_serie`,
  `comparar_lista_precios`, `revisar_cotizacion`, `crear_ot_desde_cotizacion`,
  `proponer_compra`, `consultar_datos(metrica, filtros)`.
- **Ejecución:** trabajos en `backend/jobs/` con estado, pasos, postcondiciones y
  recibo (existe base en `backend/ai_gateway/` y `backend/jobs/`). Un trabajo solo
  queda «Terminado» si sus postcondiciones se cumplen (p. ej. la obra tiene N
  ventanas con precio), corrigiendo el fallo histórico de «Completado con cero posiciones».
- **Proveedor:** MiMo vía `backend/ai_gateway/` (decisión vigente del dueño), con
  interfaz de proveedor intercambiable. Créditos y presupuesto según
  [suscripción](../../wiki/product/subscription-credits.md).
- **Evaluación continua:** un conjunto de 30 casos reales anonimizados (correos,
  planos, fotos, manuales) con resultado esperado; se mide en CI de evaluación
  (no bloqueante) la tasa de ventanas correctas, supuestos marcados y cero cifras inventadas.

## 6. Métricas de éxito

- Tiempo de solicitud a cotización enviada: **< 5 minutos** con IA (hoy: imposible en serie real).
- ≥ 90 % de vanos de un plano de prueba extraídos correctamente, 100 % de
  discrepancias marcadas.
- 0 cifras en documentos que no provengan del motor (verificado por pruebas).
