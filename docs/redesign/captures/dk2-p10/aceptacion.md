# P10 · Aceptación Proline: un taller nuevo hasta su primera cotización aprobada

Verificación local del 23-10-2026 en `claude/dk2-p10-proline`, sobre `main`
`f7023c46`. Stack Supabase propio y desechable (`dekopen-ci`, puertos 2534x),
servidor Django, trabajador de trabajos y Vite locales. No se tocaron REVIEW, el
stack del dueño ni producción. La prueba es
[`proline-acceptance.spec.ts`](../../../../frontend/tests/e2e/proline-acceptance.spec.ts)
y corre a 1440 × 900 y 390 × 844 con axe (WCAG 2.1 AA) y sin desborde
horizontal en cada captura.

## Qué recorre

Una persona que no existe en DEKOPEN:

1. Pide en `/registro` un enlace que crea su cuenta (Mailpit local).
2. Nombra su taller: Chile, pesos, IVA 19 %, en prueba. Configura su segundo
   factor de dueño.
3. Hoy le muestra «Prepara tu taller». Completa empresa (RUT), condiciones
   (plazo, instalación, exclusiones, garantía) y documentos.
4. Elige **PRO6004 · 60 mm** en la biblioteca. «Desde una plantilla» llega con
   fabricante, nombre, código, 60 mm y 4 cámaras; abre el alta guiada.
5. Carga su ficha técnica con la plantilla oficial: 43 filas sintéticas
   rotuladas «sin certificación» (perfiles, cortes, refuerzos y sus barras,
   límites, carta blanca, vidrios, herrajes). Revisa y publica.
6. Carga su lista de compra (19 precios sintéticos) y la confirma.
7. Compara la ventana de prueba con su ficha (marco 1 206 mm para 1 200 mm más
   3 mm de soldadura por extremo) y la confirma: la serie queda cotizable y
   fabricable.
8. Crea la obra «Casa Rodrigo · ensayo» con PRO6004 y dibuja tres ventanas: fijo
   del living, oscilobatiente del dormitorio y fijo del baño, con termopanel.
9. Prepara el PDF, lo revisa y emite: el cliente recibe el enlace por correo.
10. El cliente abre el enlace en otro navegador, con su nombre, RUT y
    consentimiento, y aprueba la propuesta.

## Tiempos (máquina, sin pausas humanas)

| Paso                   | 1440 px | 390 px |
| ---------------------- | ------: | -----: |
| Registro               |   1,6 s |  1,6 s |
| Taller y segundo factor |  2,3 s |  2,0 s |
| Empresa                |   2,6 s |  2,4 s |
| Serie de la biblioteca |   2,8 s |  2,6 s |
| Ficha técnica          |  22,7 s | 23,4 s |
| Precios                |   2,2 s |  2,2 s |
| Ventana de prueba      |   5,3 s |  4,8 s |
| Obra                   |   1,9 s |  1,9 s |
| Tres ventanas          |   8,7 s |  8,5 s |
| Emisión y correo       |  10,4 s | 10,4 s |
| Aprobación del cliente |   4,0 s |  4,1 s |
| **Total**              |  64,4 s | 64,0 s |

La publicación de la ficha es el paso lento: 43 filas con evidencia por campo,
en un único trabajo. Detalle en [`tiempos.json`](tiempos.json).

## Lo que la aceptación encontró y se corrigió

- **No existía alta autónoma.** Quien entraba sin membresía veía «Contacta al
  propietario». Ahora `private.create_own_workshop` (correo confirmado, sin
  membresías, una vez) crea el taller y su membresía de dueño (pgTAP 262).
- **Ninguna vía de taller declaraba la compra del acero.** La hoja «Refuerzos»
  guardaba la regla, pero solo las semillas DEMO tenían barras de refuerzo. La
  cobertura daba la serie por cotizable y el precio fallaba al dibujar. Ahora
  la plantilla oficial tiene «Barras de refuerzo» (migración y pgTAP 263). La
  cobertura bloquea una regla sin su barra (prueba de integración nueva).
- **Primer uso:** la biblioteca compartía caché con el catálogo en otra forma y
  abrir una serie rompía la pantalla. Hoy no llevaba al primer uso. En 390 px
  la guía desbordaba a 427 px. El botón Asistente quedaba sin nombre
  accesible en móvil. Documentos podía pisar lo escrito con una lectura tardía.
- La biblioteca va primero para un taller sin serie propia; monograma de tres
  letras; una sola acción primaria en Hoy durante el primer uso.

## Límites declarados

- Los datos técnicos y de precio son sintéticos y lo dicen en cada fila. La
  biblioteca solo aporta la identidad de PRO6004; no hay medidas de Proline
  verificadas. Una aceptación con el manual real requiere ese documento.
- La ficha se generó con `scripts/catalog_interchange_fixture.py --system-code
  PRO6004 --openings --bar-purchases --rename …` (orden completo en el commit).
  Su carta de colores es solo blanco y el perfil de corte es el global DEMO.
- P07 (cotización y portal v2) y P09 (taller) siguen pendientes. Esta
  aceptación usa el portal y la emisión existentes.

## Capturas

Cada paso a 1440 y 390 px: `f1-registro`, `f1-taller`, `f1-hoy`, `f1-empresa`,
`f1-biblioteca`, `f1-serie`, `f1-manual`, `f1-precios`, `f1-ventana`,
`f1-obra`, `f1-cotizacion`, `f1-portal` y `f1-aprobada`.
