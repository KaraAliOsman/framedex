# Etapa 02 — recorrido principal y proyectos

Continúa el encargo de implementación de DEKOPEN. Lee 03-experiencia-y-arquitectura, los contratos pertinentes de 13 y la evidencia 01; usa AGENTS y la base visual de 01. Preserva datos y cambios ajenos.

Reconstruye la entrada al trabajo: proyectos, nueva cotización, cliente en contexto y colección de ventanas. El usuario no debe entender módulos del backend antes de dibujar.

1. Organiza las áreas habituales Proyectos, Clientes, Catálogos y Taller, con Empresa en acceso secundario y entradas por rol. Mantén enlaces profundos y permisos; no borrar una capacidad al simplificar navegación.
2. Sustituye el inicio dominado por códigos/alertas por recientes, búsqueda, nueva cotización y pocas decisiones agrupadas por obra.
3. Nueva cotización debe llegar pronto a tipología/dibujo y usar preferencias válidas. Separa datos imprescindibles para dibujar, cotizar y emitir. Comprueba las restricciones actuales antes de introducir un borrador incompleto explícito; no crear clientes falsos ni duplicados.
4. Reúne Ventanas, Cotización, Materiales y Actividad en el proyecto. Nombre/cliente primero; código técnico en detalle. Evita franjas y pestañas redundantes.
5. Diseña colección visual y tabla para obras grandes, con duplicación y acciones de lote sobre selección clara.
6. Implementa herencia empresa→proyecto→ventana, excepción visible y vuelta al valor habitual. No alterar silenciosamente revisiones emitidas.
7. Renombra textos técnicos según el trabajo concreto. Elimina explicaciones repetidas y campos sin efecto en la etapa.

La IA tendrá un acceso estable y contexto del proyecto; su ejecución completa se aborda en 04. No simules una cotización calculando números en frontend. Si cambias contratos, parte del backend y regenera OpenAPI/orval.

Resultado: una persona puede empezar, reconocer sus ventanas, duplicar/cambiar y continuar a una oferta sin recorrer administración innecesaria. Mantén registro de pendientes, sin campañas de pruebas/bugs hasta 10. Continúa con 03.
