# Método y rúbrica de evaluación

Consulta: 18-10-2026. Selección por relevancia industrial, amplitud documental, configuración de ventanas y utilidad para un taller chileno. No es un ranking universal de los mejores ni una evaluación de compra de licencias.

## Selección y deduplicación

Quince familias: Klaes, PrefSuite, RA Workshop, Logikal, SchüCal, Cyncly V6 Advantage, A+W Cantor, FeneVision, Matrix, Windowmaker, WindowCC/WindoorCraft, 3E LOOK, NuveraPRO, Winart y WinMaker 10. Moxisys es una ficha adicional de distribución de WindoorCraft. WinMaker de Lepton es distinto de Windowmaker. FeneVision pertenece al ecosistema FeneTech/Cyncly; no se confunde con Logikal/Forterro.

Las suites grandes enseñan continuidad industrial; las regionales enseñan incorporación de proveedor, lenguaje y cotización local. Ni una licencia masiva ni una interfaz antigua hacen automáticamente adecuada una función para DEKOPEN.

## Jerarquía de evidencia

| Código | Qué acredita | Qué no acredita |
|---|---|---|
| RUN | Acción ejecutada con entrada, estado y salida comprobables. En este trabajo se usa para DEKOPEN. | Cobertura de todas las configuraciones o rendimiento industrial. |
| VIS | Píxeles de una captura, PDF o fotograma inspeccionados; se identifica su antigüedad. | Operación real, backend, exactitud, accesibilidad o permiso. |
| DOC | Procedimiento o capacidad descrita en manual, notas o página oficial. | Que se haya probado ni que esté en todas las ediciones. |
| COM | Afirmación comercial. Los subinformes la conservan bajo DOC indicando tipo de fuente. | Una medición independiente o garantía de resultado. |
| NV | No verificable con lo reunido. | Ausencia de la función. |
| PROP | Propuesta o inferencia para DEKOPEN. | Implementación actual o decisión aceptada. |

En los subinformes PVC y operación, `OBS` significa captura inspeccionada. La matriz común lo convierte en `VIS`. El informe de ingeniería reservó OBS para ejecución y no contiene ninguna. No se mezclan estas dos definiciones para inflar la evidencia.

Cada casilla conserva hallazgo, alcance, fuente, límite e implicación. Las fichas incluyen flujos reconstruidos a partir de documentos, no sesiones completas ejecutadas. Vídeos localizados, GIF parcialmente inspeccionado y tutorial observado por fotogramas se etiquetan por separado.

## Rúbrica común y prueba de aceptación

Los pesos siguientes son una **propuesta para evaluar la próxima DEKOPEN**. Suman 100. No se aplican retrospectivamente a competidores privados con pruebas faltantes.

| Eje | Peso | Qué examinar | Evidencia mínima para evaluar DEKOPEN |
|---|---:|---|---|
| 1. Entrada | 4 | Primer trabajo, valores habituales y preparación de datos. | Cuenta limpia → empresa → serie publicada → primera ventana, sin conocer nombres internos. |
| 2. Catálogos | 12 | Fabricante/serie, versiones, fuentes, imágenes y aptitud por uso. | Proline contiene sus series; búsqueda por artículo vuelve a su serie; fuente/página identificables. |
| 3. Editor/aperturas | 12 | Selección, mano, cara, campos, acoples y corrección. | Cambiar cada apertura declarada compatible, guardar, recargar, deshacer; rechazar una incompatible con causa. |
| 4. 2D/3D | 5 | Misma configuración, materiales, cara y movimiento. | Coinciden hoja, manilla, sentido y medidas entre vistas y documento. |
| 5. Componentes | 8 | Perfiles, refuerzos, vidrio, herrajes, acabados y BOM. | Cada pieza tiene identidad, cantidad del motor, unidad, posición y evidencia de compatibilidad. |
| 6. Precio | 7 | Costos privados, moneda, descuento, margen y revisión. | Cambio de costo produce revisión trazable; rol sin costo no lo recibe por UI, API o PDF. |
| 7. Cotización/PDF | 7 | Documento reconocible, editable visualmente e inmutable al emitir. | Edición de texto/orden/imagen no altera cifras; segunda revisión conserva la primera. |
| 8. Corte/retazos | 5 | Cobertura de piezas, barras, sobrantes y fallos. | Reconciliar piezas requeridas, ubicadas y no ubicadas; reservar sobrante físico una sola vez. |
| 9. Compras/stock | 5 | Necesidad, orden, recepción parcial y disponibilidad. | Pedir, recibir parcialmente y completar sin duplicar stock ni ocultar faltantes. |
| 10. Taller/CNC | 6 | Estación, unidad, revisión, requisito y máquina concreta. | Puesto ve trabajo correcto; plan obsoleto bloquea con solución; salida CNC solo con adapter homologado. |
| 11. QR/terreno | 3 | Objeto, acceso, medición e incidencia. | Etiqueta identifica una pieza/unidad; lectura móvil autorizada y sin fuga entre empresas. |
| 12. IA | 8 | Resultado ejecutado, preguntas necesarias y recuperación. | Encargo compuesto terminado con postcondiciones del servidor, usando MiMo real y operaciones tipadas. |
| 13. Historial | 4 | Conversación, trabajo, revisión y deshacer. | Cambiar ruta, recargar y volver conserva contenido, archivos, resultados y ámbito correcto. |
| 14. Roles | 4 | Lectura/acción por persona y empresa. | Matriz de roles, pruebas negativas y RLS; la IA no amplía capacidades del usuario. |
| 15. Claridad | 4 | Prioridad, selección, control, causa y significado del color. | Revisión en tareas con dueño: encontrar acción principal y objeto seleccionado sin explicación. |
| 16. Teclado/móvil | 2 | Foco, atajos y tarea específica por tamaño. | Escritorio 1440/1280/1024; teléfono 390/360; foco visible y lectura útil al reducir ancho. |
| 17. Integración | 2 | Contrato, formato, fuente y recuperación. | Importar con diagnóstico; repetir no duplica; exportar conserva unidades y revisión. |
| 18. Madurez | 2 | Soporte, límites, incidentes y operación comercial. | Estado de capacidades honesto, guía de operación, restauración y observabilidad verificadas. |

Escala futura por tarea: 0 = no completa; 1 = completa con intervención técnica; 2 = completa con fricción relevante; 3 = completa con autonomía y claridad; 4 = completa, recuperable y verificada también en error. **No evaluado se marca NE y no se convierte en cero.** Una nota solo es comparable si acompaña cobertura y condiciones equivalentes. Exactitud numérica, tenancy e inmutabilidad son puertas de aceptación: no se compensan con un promedio visual alto.

## Límites y próximos accesos útiles

No hubo cuentas privadas, compra, contacto comercial, activación de licencias ni máquinas de competidores. Logikal Demo Tour deriva a un formulario; PrefSuite devolvió challenge en la captura de la página, por lo que se usó una imagen oficial accesible y se conservó el límite. REA no recuperó algoritmos industriales privados.

Para un benchmark de rendimiento comparable faltan sesiones autorizadas con el mismo caso, catálogo, hardware y operador; para compras faltan ofertas comerciales equivalentes. Eso no impide extraer patrones de producto, pero impide inventar notas de velocidad, precisión o facilidad para cada competidor.
