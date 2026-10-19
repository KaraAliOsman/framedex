# Asistente: dos modos, tres niveles de autonomía

> **Contrato actualizado:** la corrección del dueño exige popup global opcional y plan base manual sin IA. Consultar el [contrato vigente de copiloto y planes](../2026-10-18-direccion-final/03-copiloto-y-planes.md). Chat/Trabajo y las autonomías se conservan; la composición acoplada/elección pendiente siguiente es histórica.

Intención explícita del dueño, 18-10-2026: Chat y Trabajo, acceso desde cualquier pantalla, espacio propio e historial. Última aclaración: “omitir todo”, ejecutar sin detenerse y contar al final lo realizado. **Los nombres y la composición visual siguientes son propuesta pendiente de elección.**

## Interacción que debe sentir el usuario

El asistente se abre donde está trabajando, mantiene la conversación al navegar y puede visitar otra parte del producto para completar el encargo. Su área propia conserva conversaciones, archivos, encargos y resultados. El usuario puede usar todas las funciones manualmente.

| Modo | Resultado esperado |
|---|---|
| **Chat** | Consultar, explicar, comparar y analizar archivos. No modifica objetos por conversar. Puede convertir el acuerdo en un encargo de Trabajo. |
| **Trabajo** | Llevar un objetivo hasta un resultado verificable mediante operaciones del dominio, con el nivel de autonomía elegido. |

| Autonomía en Trabajo | Comportamiento concreto |
|---|---|
| **Solo proponer** | Prepara alternativas y cambios revisables; no los aplica. Agrupa el resultado en un artefacto útil. |
| **Con aprobación** | Investiga y prepara en segundo plano. Pide aprobación de un cambio concreto o lote coherente antes de aplicarlo; evita confirmar cada consulta o paso interno. |
| **Omitir todo** | Ejecuta de principio a fin las operaciones reversibles autorizadas, resuelve fallos recuperables y presenta un recibo al final. No pide confirmar cada paso, ni elige preguntas en lugar de trabajar. |

“Omitir todo” omite aprobaciones intermedias de esos cambios; el motor sigue validando. Según los invariantes de DEKOPEN, emisión, envío, pagos, compra/compromiso externo y acciones equivalentes conservan un clic humano explícito. El agente llega hasta el resultado listo para ese clic y señala que está pendiente. No trata una aprobación anterior como autorización ilimitada.

## Menos preguntas sin inventar

Orden de resolución: datos de la pantalla/selección → obra → cliente → preferencias de empresa → catálogo aprobado → pregunta imprescindible. Si una elección reversible tiene un valor habitual ya autorizado, usarlo y dejar el supuesto en el recibo. No volver a pedir vidrio o acabado guardados sin un conflicto.

Si faltan ancho y alto no se inventan. Preparar lo que sí sea independiente y pedir **un bloque de datos faltantes** con alcance concreto. Diferenciar “no puedo terminar por esta medida” de “terminé”. Los ajustes estéticos o reversibles no deben bloquear un encargo en Omitir todo. Una incompatibilidad física no se cura cambiando de serie sin permiso o inventando una receta.

Ejemplo de cierre correcto: “Preparé la obra y el cliente. Faltan ancho y alto de V1–V3 para crear las ventanas y calcular. El encargo está esperando esos datos.” Con medidas conocidas y valores habituales, debe crear las ventanas, validarlas y calcular, sin volver a preguntar preferencias ya elegidas.

## Persistencia y estructura de información

- **Conversación**: identidad estable dentro de organización y dueño; título, mensajes, adjuntos y archivos producidos. No pertenece exclusivamente a una URL.
- **Encargo**: objetivo concreto dentro de conversación; alcance, autonomía autorizada, pasos, punto de reanudación y condiciones de finalización.
- **Contexto**: pantalla, selección y referencias de trabajo; puede cambiar sin reemplazar la conversación. Destino fijado visible cuando hay varios proyectos.
- **Operación**: cambio tipado con entrada, versión previa, validación del motor, aplicación y recuperación.
- **Artefacto/recibo**: objeto o archivo comprobable y vínculos; no una tarjeta que solo repite una promesa.

Estos son conceptos del contrato, no una orden de crear cinco tablas nuevas si el repositorio ya los resuelve. Revisar y reutilizar jobs/operaciones/transcripciones existentes. Definir migración de continuidad sin perder historial anterior y sin ampliar lecturas entre tenants.

## Ciclo del encargo

Estados comprensibles: Preparando → Trabajando → Esperando datos / Esperando aprobación → Terminado / Parcial / Falló / Cancelado. El estado del proveedor o del worker es independiente. `response_complete` no implica `goal_complete`.

Antes de Terminado, comprobar las postcondiciones según objetivo: cliente vinculado, cantidad de posiciones, configuraciones válidas, cálculo vigente, documento borrador generado o importación revisada. Si el resultado requiere un clic humano externo, usar “Preparado para emitir/enviar” en lugar de “Enviado”.

Reintentar por paso con idempotencia. Ante un fallo recuperable, preservar los pasos confirmados y continuar; ante un conflicto de versión, mostrar diferencia y no pisar cambios manuales posteriores. Cancelar detiene pasos futuros; no asegura que lo ya confirmado haya desaparecido.

## Recibo final

Un párrafo claro con cuatro datos cuando correspondan: qué terminó, dónde está, supuestos usados y qué queda pendiente. Debajo, acceso a resultado, cambios y recuperación. Detalles de herramientas/consultas se pueden expandir; no ocupan la conversación por defecto. No mostrar números escritos por el modelo como cálculos oficiales.

La interfaz debe permitir minimizar, detener, abrir a pantalla completa, volver al objeto e iniciar otra conversación sin perder la actual. El historial es visible desde el panel; búsqueda, renombrado y archivo deben tener alcance y recuperación claros. No hace falta una mascota grande para indicar actividad.

## Pruebas que deciden si está logrado

1. Pedir cliente y tres ventanas conocidas desde Catálogos; termina en una obra con cliente vinculado, tres posiciones válidas y cálculo solicitado. La tarea puede navegar y el hilo no cambia.
2. Cerrar panel, recargar, abrir desde otra ruta y recuperar conversación/archivos/resultados; otro usuario/tenant no los recibe.
3. Ejecutar el mismo encargo en los tres niveles: propuesta sin aplicación; lote revisable con aprobación; aplicación reversible sin interrupciones en Omitir todo.
4. Faltan dimensiones: una pregunta agrupada, trabajo independiente preparado y estado Esperando datos. Nunca Terminado con 0/3 ventanas.
5. Se agota una consulta o falla el proveedor: reanudación sin duplicar cliente/ventana y sin asegurar que el objetivo se cumplió.
6. Operación manual posterior: deshacer de IA preserva ese cambio o explica un conflicto verificable.
7. Emisión/envío: deja resultado listo y obtiene clic humano; cambiar autonomía no amplía rol o permisos.

Modelo preferido actual: **MiMo 2.6 Pro**. Verificar disponibilidad, nombre de API, herramientas y límites en la integración real antes de afirmar soporte. El modelo no sustituye al motor; el protocolo del producto debe seguir siendo reemplazable.
