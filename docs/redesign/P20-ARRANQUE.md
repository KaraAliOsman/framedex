# P20 · arranque reproducible y carga de la propuesta

Corrección separada hacia `integracion/v1`, sobre `3afe9697`. La aceptación
global de P20 continúa después de este cambio; no declara terminados sus
catorce recorridos.

## Resultado verificado

El inicio de revisión construye API, worker y nginx, inicia Supabase aislado y
prepara cinco cuentas por rol, dos empresas, catálogo v7, doce posiciones con
bow/conjunto reales y la obra de cien posiciones. Un manifiesto y etiquetas
verifican la propiedad antes de detener recursos. No adopta una base ajena ni
resetea datos. Las credenciales permanecen en memoria; Docker recibe los nombres
de variables. El relay mantiene el issuer de Supabase dentro de los contenedores.

La imagen del frontend conserva la guía de activación en su ruta de fuente.
El build elimina las direcciones de desarrollo y comprueba residuos. El portal
usa un arranque público con sus mismas rutas, dibujos y operaciones; cargarlo
no requiere inicializar la sesión del personal. La sesión interna conserva
el reset síncrono de un lienzo cargado y nace vacía cuando aún no existe.

El portal verifica cada snapshot completo una vez dentro de su consulta, con
hash, organización, proyecto e inclusión literal de la alternativa. Otra
consulta vuelve a validar y conserva revocación/consentimiento vivos. El
recorrido canónico de JSON nativo evita comprobaciones de modelos en cada hoja,
mantiene la conversión original para clases tipadas y conserva bytes/goldens.
Se elimina la segunda transferencia del snapshot que solo repetía su binding.

Nginx comprime JS/CSS/JSON y da caché immutable únicamente a `/assets/`.
No se añade caché de capacidades ni de respuestas privadas. Las posiciones
usan lista/fila y sus controles reales, evitando controles interactivos anidados
en opciones ARIA; mantienen selección, teclado y virtualización.

## Evidencia

- [Antes](captures/aceptacion-final/antes/): build P24 conservado.
- [Stack limpio](captures/aceptacion-final/stack-limpio/): Magic Link solicitado
  desde la UI, Mailpit, entrada real, doce posiciones y editor, ambos temas;
  axe de la lista sin serious/critical. El fixture se construyó por sus APIs.
- Doce contextos fríos por caso; autenticación fuera del intervalo y lectura
  visible más dos cuadros. Portal 390 × 844 con 150 ms de latencia,
  1,6 Mbps de descarga y 750 kbps de subida: antes p50 8.871,22 ms /
  p95 9.373,35 ms; después p50 2.949,26 ms / p95 2.972,86 ms.
  La medición final se realizó sin gates ni otra captura concurrente.
- 37 pruebas focales de canon, portal y autoridad; cuatro negativas/reuso de
  `test_offered_options.py`. Tres pruebas protegen propiedad y dotenv del stack.
  23 pruebas de Auth/App y 15 de ciclo/decisión del portal pasan.
  La prueba de cien posiciones conserva `<15` filas montadas y la selección.
- La guía y la matriz completa se amplían durante la aceptación final. El
  tiempo de apertura en contexto frío y el de interacción se documentan por
  separado; cien posiciones pertenecen a una obra con cien OT, no a una OT ficticia.

## Pase editorial

Ronda 1: se quitaron el import eager del lienzo en autenticación, las rutas DEV
del producto compilado y la semántica de opción que escondía controles de fila.
La descarga pública, el foco por teclado y la prueba de virtualización mejoraron.

Ronda 2: se quitó la descarga duplicada de autoridad, el arranque de autenticación
en el enlace público y la dependencia del fixture de una familia demo histórica.
Se conservaron las huellas, dibujo/DIN y consentimiento humano. Los fixtures no
afirman anticipos, despacho o instalación que no registraron.

| R | Resultado | Evidencia en el alcance de la corrección |
|---|---|---|
| R1 | PASA | Formatos comunes; canon exacto sin cambio de números |
| R2 | PASA | Tokens existentes; ninguna nueva geometría decorativa |
| R3 | PASA | Lista/documento existentes y una lectura pública |
| R4 | PASA | Intervención y marca conservan su significado |
| R5 | PASA | Paleta técnica común |
| R6 | PASA | Carga y recuperación en español; DEMO explícito |
| R7 | PASA | Controles y virtualización conservados |
| R8 | PASA | Ciclo vigente/revocado/caducado y permisos existentes |
| R9 | PASA | Papel, mesa y elevación preservados |
| R10 | PASA | Lista conserva contorno/selección y aria-current |
| R11 | PASA | Mismo dibujo DIN y vista declarada |
| R12 | PASA | Controles etiquetados, selección y teclado; axe |
| R13 | PASA | Sin movimiento nuevo; dos cuadros de estabilización |
| R14 | PASA | Revisar/aprobar/pagar mantienen clic humano |
| R15 | PASA | Hash completo por consulta e inclusión literal |
| R16 | PASA | Sin degradados, blur, brillos ni croma nuevo |
| R17 | PASA | Arranque/editor y listas en tamaños exigidos por sus matrices |
| R18 | PASA | Una definición de rutas públicas; imágenes Docker construidas |
| R19 | PASA | F2/F6/F11, huellas y revisión sellada conservados |
| R20 | PASA | Alternativas y autoridad siguen siendo operaciones reales |

## Límites

No se cambian fórmulas, esquema ni contratos HTTP. La fuente y el cliente
generado permanecen reproducibles. DEMO no certifica fabricación. Flow/SII y
correo conservan sandbox y su activación explícita. La guía completa, IA real,
matriz global y sus mediciones restantes pertenecen a la aceptación de P20.
