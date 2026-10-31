---
type: synthesis
status: active
updated: 2026-10-11
volatility: high
verified_ref: ff210e7a439b861349d1d602c4137ebe4e65d0c8
sources:
  - scripts/generate_scene3d_fixtures.py
  - frontend/src/features/canvas/poses3d.test.ts
  - frontend/src/features/canvas/Product3DScene.test.ts
---

# Representación física 3D

P19 entrega hechos evaluados D03/D08 a la escena del editor y hechos sellados
a la escena pública. El visor, exportación PNG y miniaturas comparten cámara,
materiales, conversión lineal/sRGB, entorno y transformaciones rígidas.
Las opciones visuales no escriben medidas ni vuelven al motor.

Cada hoja se opera individualmente; un paquete plegable es una cadena
con longitud invariante, con hoja de paso independiente al cerrar el paquete.
HST eleva y PSK separa antes del desplazamiento. Guillotina/pivotes consumen
recorrido, plano y eje de su receta. El despiece separa axialmente capas
cerradas, con guías. Apertura de 240 ms y reducción de movimiento respetada.

Las correderas simples usan la autoridad de layout de P05: el motor histórico
no devuelve `opening_leaves` para ellas. Se conserva su decodificador visual,
dirección declarada y orden de carriles, sin añadir campos físicos al dominio.
Las otras hojas físicas sin evaluación quedan Sin dato y no se inventan.

Se eliminó la textura aleatoria de foliado. El color viene de la carta y la
textura sólo del recurso declarado disponible; en su ausencia se explicita
la aproximación plana. La sección/herraje esquemáticos se declaran como tales.
Interior/exterior muestran las caras distintas del bicolor sellado.

La cámara no gira sola. Detalle apunta a la manilla en su pose y altura del
motor. Los controles tienen teclado, exportación y recuperación tras pérdida
de contexto. Sin WebGL se conserva la alternativa técnica.

Límites verificados: una apertura real sobresale del volumen cerrado al girar,
sin perder eje/longitud. Un muro opcional no es autoridad de montaje. El portal
histórico sin sección sellada usa geometría aproximada, sin Catálogo vivo.
DOC-01 consume SVG técnico y no se reescribe. DEMO continúa sintético.

Intención del dueño: el cliente reconoce su ventana y su apertura; el 3D no
contradice la técnica. Evidencia actual: 40 fixtures, 68 pruebas de poses,
matriz de navegador, bicolor/foliado, recuperación y paridad de render.
La aceptación registra por separado gates locales, revisión y CI de cierre.
