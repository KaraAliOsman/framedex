# Grok Bot: personaje fiel y movimiento conectado al trabajo

18-10-2026 · referencia externa + contrato para Claude. **No es código implementado ni aceptación visual.** La aclaración final del dueño se refiere principalmente al personaje animado de Grok Bot; sus estilos pueden aportar cuando encajan con DEKOPEN. No obliga a reproducir la aplicación de mensajería completa.

## 1. Dirección cerrada

Conservar la simplicidad, silueta, ojos, expresividad y calidad de movimiento del personaje oficial con **alta fidelidad**. El círculo con placa facial, brillo y órbita del Companion actual no satisface esta referencia por conservar dos ojos. El personaje vive en el acceso al copiloto y en su ventana; el cotizador sigue siendo una aplicación manual completa.

El popup mantiene Chat/Trabajo, historial, tres autonomías y los contratos de [copiloto](03-copiloto-y-planes.md). La figura no concede permisos, no interpreta una animación como tarea y no amplía el alcance de Omitir todo. El plan manual no monta personaje, popup ni polling de IA. El proveedor común es MiMo hasta una decisión posterior explícita del dueño.

## 2. Qué se investigó y qué demuestra

Fuentes oficiales consultadas el 18-10-2026:

| Fuente | Evidencia | Uso y límite |
|---|---|---|
| [Demo pública oficial](https://x.ai/bot) | VIS/RUN de la demo en navegador: hero, selección del hilo Chief, apertura de su vista Computer y retorno visual al personaje. DOM visible con SVG animado y estilos. | Demuestra composición y respuestas de la demo; no ejecutamos una tarea real ni usamos una licencia de escritorio. |
| [Introducción oficial](https://x.ai/news/introducing-grok-bot) | DOC: trabajo delegado y persistente. | Referencia de resultado; no acredita precisión de ingeniería ni fiabilidad de DEKOPEN. |
| [Descripción del producto](https://docs.x.ai/grok-bot/overview) | DOC: contexto conservado y trabajo por encargo con acceso a herramientas. | Adoptar continuidad y resultado; no añadir un ordenador cloud a este alcance. |
| [Computer and apps](https://docs.x.ai/grok-bot/computer-and-apps) | DOC: seguimiento del trabajo, salida de la vista sin detenerlo y preferencia por conectores disponibles. | DEKOPEN usa sus API y servicios tipados; no reproduce sesiones/credenciales compartidas entre bots. |
| [Guía 101](https://x.ai/bot/guides/grok-bot-101) | DOC: explica delegación, aprobación y rutinas con imágenes y enlace al walkthrough. | Se leyó la guía; no se declara haber visto el vídeo completo ni probado rutinas. |

El estilo observado muestra una conversación contenida, compositor estable y resultado legible. La apertura de Computer transforma el reparto del espacio **dentro de su propia demo**, con avatares compactos y detalle a la derecha. Esta composición no autoriza encoger el lienzo de DEKOPEN: aquí se aplica solo dentro del popup ampliado cuando sea útil.

### REA y artefactos públicos

Se inventariaron 62 scripts first party realmente declarados por el DOM de la página y se adquirieron sus bytes públicos como datos inertes en la carpeta temporal. REA analizó **solo tres**: 319.612 bytes, tres parses sin fallo; 59 archivos quedaron fuera del análisis y el grafo semántico tiene truncamiento por los límites de 5.000 nodos por archivo y 10.000 totales. No se ejecutó su bootstrap.

| Artefacto público observado | Papel identificado por lectura estática | SHA-256 |
|---|---|---|
| [1yeohavp76p77.js](https://x.ai/_next/static/chunks/1yeohavp76p77.js?dpl=270e6ec7856a61e2e1689c74197e8f37497ebd48) | Tabla de estados/clips y render/movimiento del personaje. | 64e50a12ad53dee5112c7583ea270f6557ad5be7a5720164147b871ed9c31be7 |
| [3t485hyf3nrj0.js](https://x.ai/_next/static/chunks/3t485hyf3nrj0.js?dpl=270e6ec7856a61e2e1689c74197e8f37497ebd48) | Wrapper lazy, alternativa estática, visibilidad y adaptación de estados. | 4246ad9b78d33026b3898650bf74e05c8f5218d2df09e41dc268b7d9cc68a285 |
| [3m_9a1yuonjb6.js](https://x.ai/_next/static/chunks/3m_9a1yuonjb6.js?dpl=270e6ec7856a61e2e1689c74197e8f37497ebd48) | Interfaz de la demo y representación de actividad. | 3284ac203e54e5039b6cf60c08ced24fca27502a59390c5f15579c486a9badf4 |

Identidad REA del análisis completo retenido: `ev_a9f38122e0ff9fb17e373422b2bc577458a28bf67a87d96d7017536b21037ac2`. Vista de resumen: `ev_03fa26b7abbdc247475244598c732cbded89b212fc8f52181c706f49f6faa3ff`.

**Límite de runtime REA:** el lanzamiento temporal de Edge recibió una página WAF de bloqueo, aunque el escenario reportó navegación técnicamente completada. Su evidencia `ev_408784e74795fa4014e068533220f83a07a5270595d27195767b484abc787148` no contiene la interfaz de Grok Bot. No se sorteó el bloqueo. La observación visual procede del navegador accesible ya abierto; REA acredita aquí análisis estático parcial, no ejecución del producto privado.

Recibos, inventario y bytes exploratorios quedan en `.run/revision-profunda/grok-bot/`. La evidencia duradera es esta síntesis, sus identidades y la selección de imágenes; no incorporar todos los bundles ni base64 al repositorio.

## 3. Hallazgos que cambian la construcción

| Observado o recuperado | Decisión para DEKOPEN | Alcance |
|---|---|---|
| Cuerpo plano compacto y dos ojos recortados/de contraste, sin placa de rostro separada. | Reconstruir esa gramática: contorno, espacio negativo y proporción de ojos. Retirar placa, brillo y aro como identidad predeterminada del Companion. | Fidelidad pedida por el dueño. Color se adapta a tokens de la página. |
| SVG cambia geometría de cuerpo y ojos entre fotogramas; no es un emoji quieto con una rotación CSS aplicada a todo. | Movimiento coordinado de volumen/silueta, orientación y ojos; conservar sensación de peso y miradas. | No basta traducir el grupo entero tres píxeles. Tampoco obliga a portar el renderer externo completo. |
| Hero inspeccionado: caja nominal 60 px, SVG de referencia 92 × 92 dentro de una envoltura al 153,333%; el cuerpo ocupa aproximadamente la caja nominal. | Reservar margen para deformación sin recortar; ajustar por tamaño óptico. | Medición de esa instancia de marketing, no tamaño del botón de DEKOPEN ni proporción universal de todo fotograma. |
| El motor público tiene 53 etiquetas de estado y 28 clips nominales. Muchos estados comparten gestos de trabajo. | Implementar un vocabulario pequeño y completo para los estados reales del sistema, con la misma riqueza de gesto. | Conteo estático de ese bundle; no se observaron 53 estados ni se promete copiarlos todos. |
| Clips de reposo nominales de 4–6 s y trabajo de 4–8 s; hay variaciones de trabajo y respuesta de éxito. | Evitar repetición mecánica de un loop idéntico. Alternar variantes discretas con semilla estable y transiciones continuas. | Son duraciones de clips del artefacto, no latencia del producto ni duración universal que haya que imponer. |
| Hay mirada al puntero, parpadeo, expresión, morph y gesto al interactuar; el wrapper puede habilitarlos por instancia. | Permitir mirada local/hover breve y respuesta al abrir; el estado del job gobierna los gestos de actividad. | Presencia opcional de puntero no significa que todas las instancias oficiales sigan siempre el ratón. |
| La implementación pública tiene variante compacta por debajo de 48 px. | En el acceso pequeño conservar lectura y expresividad sin desplegar los gestos más amplios. | Umbral externo de referencia; concretar tamaños ópticos de DEKOPEN abajo. |
| Se observa tratamiento de reduced motion, pausa fuera de vista y pestaña oculta, ResizeObserver y render incremental del SVG. | Animación local, interrumpible y suspendida cuando no se ve; alternativa estática equivalente. | Lectura estática; no es un benchmark de consumo ni prueba de FPS. |

La fidelidad se juzga en silueta, ojos, pose, ritmo y transición, comparados con las referencias seleccionadas. Ninguna medición anterior acredita una réplica exacta del movimiento completo del producto de escritorio.

## 4. Anatomía concreta del personaje

Usar SVG/vector propio dentro del sistema actual; no generar un PNG de mascota ni incrustar el sitio externo. Una sola primitiva de personaje, con capas de cuerpo, ojos/máscara y transformaciones controladas. El código de movimiento es local, sin peticiones al dominio externo, SDK de Grok, fuente remota o dependencia del proveedor de IA.

- **Silueta:** cuerpo redondo limpio con variación orgánica durante el gesto, bordes precisos y amplio espacio de recorte. Sin antenas, casco, sonrisa añadida, placa facial, destellos ni degradado como sustituto del gesto.
- **Ojos:** dos formas oscuras/negativas redondeadas, capaces de cerrar, entrecerrar, estirar e inclinar. La posición acompaña el giro del cuerpo; no se pega a un punto fijo mientras el volumen mira hacia otro lado.
- **Color:** personaje de un color estable compatible con el acento de DEKOPEN y ojos de alto contraste. En oscuro conserva el mismo carácter. Los estados llevan texto y controles; no dependen de volver rojo o verde todo el personaje. El arcoíris de agentes de la demo no se importa a un único copiloto.
- **Escalas de construcción:** acceso 28–32 px dentro de un blanco interactivo de al menos 44 × 44; cabecera 24–28; presentación voluntaria ampliada 64–96 cuando aporte. Son valores propuestos para esta app, por comprobar en 07. La figura no ocupa el centro de una conversación poblada ni roba área a una cotización.
- **Tamaño óptico:** en pequeño simplificar deformaciones y parpadeos; conservar contorno y separación de ojos. No aplicar el mismo SVG escalado sin comprobar lectura en 24, 28, 32, 64 y 96 px.
- **Marca:** el producto se llama DEKOPEN. El personaje no sustituye el logo ni presenta la aplicación como un producto xAI.

## 5. Estado real → gesto → control

Separar estado de dominio, subtarea y estado de representación. La tabla siguiente es propuesta de integración, no una tabla recuperada del servidor de Grok.

| Situación real | Gesto requerido | Texto/control que conserva la verdad |
|---|---|---|
| Sin trabajo activo y disponible | Reposo vivo: mirada/respiración muy leve y parpadeo esporádico; nada que parezca progreso. | Asistente; abrir popup. No «trabajando» por estar conectado. |
| Persona redactando | Atención breve hacia compositor o puntero local; vuelve a reposo. | Borrador sin enviar. No iniciar llamada o job. |
| QUEUED | Espera contenida, distinta de ejecución. | En cola; cancelar cuando proceda. Sin porcentaje inventado. |
| PLANNING | Gesto de pensamiento, mirada y microdeformación coordinadas. | Preparando; detener. No exponer razonamiento privado. |
| RUNNING con subtarea conocida | Variantes de trabajo: lectura, búsqueda o ejecución solo cuando la herramienta/etapa lo acredita. | Verbo y objeto reales: «Actualizando 3 posiciones». Seguir resultado voluntario. |
| Respuesta de Chat en streaming real | Gesto de respuesta mientras llegan eventos; no simular escritura después del último. | Respuesta recibida; detener según el contrato de transporte. |
| WAITING_FOR_USER | Atención quieta y pregunta agrupada visible. | Esperando datos; responder/abrir origen. No ciclo de trabajo indefinido. |
| WAITING_FOR_APPROVAL | Orientación de atención y gesto único de revisión. | Revisar cambios; aprobar el conjunto o rechazar. |
| SUCCEEDED con postcondiciones cumplidas | Reconocimiento breve y regreso a reposo; éxito no se repite al reabrir. | Recibo persistente y Abrir resultado/Deshacer permitido. |
| Parcial o conflicto | Gesto contenido de atención; sin celebrar. | Parcial/conflicto concreto, checkpoint y continuación posible. No inventar un enum si el API lo representa mediante outcome. |
| FAILED / FAILED_RETRYABLE | Reacción breve y estable, recuperable. | Causa humana, detalle plegado y reintento idempotente. |
| CANCELED | Cierre contenido y reposo. | Detenido; conservar lo aplicado y lo pendiente. |
| Sin proveedor / saldo agotado / red perdida | Pose estática y causa distinguible. | Historial accesible y manual disponible. No fingir actividad ni recurrir a otro modelo sin permiso. |

Un solo selector de estado deriva de la tarea relevante y su versión; no alternar arbitrariamente entre el último job de la ruta y otro hilo. Con varios trabajos, indicar cantidad y permitir elegir; el personaje no suma porcentajes ni borra un resultado privado al cambiar selección.

## 6. Movimiento e interacción, sin convertirlo en decoración

El límite general de 280 ms del contrato visual gobierna transiciones de controles/popup. **No limita a 280 ms los ciclos expresivos del personaje.** Los clips vivos pueden durar varios segundos, como la referencia, y deben ser de amplitud moderada en tamaños pequeños. Esta excepción se documenta en Constitución durante 01; no se usa para animar tablas o figuras del CAD.

| Momento | Construcción propuesta | Criterio |
|---|---|---|
| Abrir copiloto | Popup responde inmediatamente, entrada breve 180–220 ms; personaje saluda con mirada/despertar contenido y luego atiende. | La ventana y los botones funcionan antes de terminar el gesto. |
| Hover y pulsación | Feedback de control inmediato; mirada local con retorno suave, sin perseguir el puntero por todo el CAD. | Sin parpadeo de layout ni retardo del clic. Teclado tiene foco visible. |
| Reposo | Microvariación y parpadeo no sincronizados entre copias; opcional desactivar movimiento de presencia. | En reduced motion queda quieto. No pulso de brillo o spinner eterno. |
| Trabajo | Alternar pocos clips de la misma intención; el paso real cambia el gesto sin reiniciarlo desde una pose imposible. | Mantener orientación/velocidad al interrumpir; no saltar a un keyframe inicial en cada polling. |
| Llegada de resultado | Un gesto de reconocimiento; el badge/recibo permanece hasta lectura aunque el gesto termine. | No roba foco, no abre popup solo y no repite por rerender o recarga. |
| Mover/redimensionar popup | Arrastre 1:1 con offset inicial, captura de puntero y límites de viewport; al soltar asentamiento leve si ayuda. | El gesto del personaje es secundario. Sin resorte entre puntero y ventana durante el arrastre. |
| Cerrar/minimizar | Salida breve y conservación de hilo/job. | Gesto y cierre no cancelan ni consumen crédito. |

Separar el reloj de animación de React/estado de mensajes. No renderizar el árbol de conversación a 60 Hz. Usar transform/opacity para movimiento global y un SVG pequeño para las deformaciones necesarias; el morph de paths debe medirse porque puede pintar. Un bucle local solo existe mientras es visible y necesario, con cleanup de rAF/listeners/observers. Cero telemetría de puntero o llamadas de modelo para animar.

Pausa al ocultar pestaña/fuera de vista; no acumular cientos de segundos para reproducirlos al volver. Si cambia el estado durante la pausa, al regresar muestra el estado vigente mediante una transición corta. Reduced motion conserva expresión estática, texto y resultado; no sustituye todo por una silueta sin significado.

## 7. Estilo de conversación que sí encaja

Cabecera compacta, mensajes legibles, espacio suficiente y compositor estable. Tomar de la referencia su legibilidad y claridad de resultado; adaptar tipografía, color, estados y documentos a [diseño](02-diseno-y-referencias.md) y [referencias profesionales](05-referencias-profesionales.md). No introducir automáticamente lista de siete bots, pantallas remotas, comandos de programación, rutinas, voz o conexiones externas porque aparezcan en la demo.

El popup inicial conserva 420 × 600 y mínimo útil 340 × 420, limitado por viewport. Chat/Trabajo, contexto y destino, historial y autonomía siguen visibles sin una parrilla de chips. El detalle de herramientas va plegado; el recibo muestra objetos y resultados del motor. En ampliación voluntaria puede haber historial y resultado lado a lado dentro de esa ventana, sin cambiar la distribución manual de la página.

## 8. Trabajo para Claude y aceptación final

Revisar primero `frontend/src/features/assistant/Companion.tsx`, `companion.css`, `AiPresence.tsx`, `useAssistantPresence.ts`, `AskDekopen.tsx` y el mapeo de estados de jobs. El Companion actual es un trabajo local previo: preservar contratos útiles y sustituir conscientemente su figura, sin crear dos personajes incompatibles.

| Before | After | Why |
|---|---|---|
| Círculo teal con placa, brillo y aro. | Figura cercana al personaje oficial: cuerpo limpio, ojos negativos y movimiento orgánico. | Es la referencia concreta que pidió el dueño. |
| Pose de trabajo igual a órbita infinita. | Vocabulario de gestos conectado a etapa real, con pausa y recuperación. | Comunica actividad sin fingir progreso. |
| Reposo rígido o pulso genérico. | Vida contenida con parpadeo/mirada y alternativa estática accesible. | La personalidad procede del gesto. |
| Estado visual asociado solo a la ruta. | Tarea/hilo real, persistencia y destino sellado. | Navegar no redirige trabajo ni cambia qué resultado se representa. |

Construir en 05, después de resolver la autoridad visual en 01. Preparar un catálogo interno de poses/estados con reloj controlable para revisión final; no es una nueva pantalla del SaaS ni una demo que sustituye la integración. No ejecutar ahora la campaña de pruebas.

En 07 comparar referencia e implementación en reposo, pensamiento, trabajo, espera, revisión, éxito y fallo; revisar transiciones/interrupciones, repetición tras recarga, foco, teclado, tamaños, tema oscuro, reduced motion y pestaña oculta. Adjuntar evidencia de la app real y una breve grabación seleccionada si el entorno permite capturar movimiento. Una imagen quieta no acredita animación ni postcondiciones de IA.

## 9. Selección visual

Imágenes de la demo oficial, tomadas durante esta revisión; no son propuestas de interfaz DEKOPEN ni tareas reales ejecutadas.

- [Hero y personaje](evidencia/grok-01-hero.png): figura dentro de su contexto de marca.
- [Conversación y recibo de la demo](evidencia/grok-02-chief-thread.png): resultado, compositor y separación de historial.
- [Vista opcional del trabajo](evidencia/grok-04-computer-context.png): reparto interno después de abrir Computer.
- [Personaje ampliado en contexto](evidencia/grok-05-character-in-context.png): silueta y ojos sin placa facial.

Las capturas originales se conservan con su contexto y el manifiesto seleccionado incluye hashes. No presentar un instante de ojos redondos como la única pose neutral: sus formas cambian durante el movimiento.

