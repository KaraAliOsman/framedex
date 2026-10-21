# 99 · Bucle continuo: GPT trabaja sin parar hasta terminar DEKOPEN 2

> Úsalo después de pegar [`00-contexto-maestro.md`](00-contexto-maestro.md).
> Este mensaje hace que GPT recorra todas las fases en orden sin esperar
> instrucciones entre una y otra.

---

Vas a construir DEKOPEN 2 completo, de principio a fin, sin detenerte entre
fases. Las fases están en `docs/research/2026-10-21-competencia/prompts/`:

| Orden | Archivo | Resultado |
|---|---|---|
| 1 | `P01-catalogo-v2-backend.md` | Serie real cotizable con valores sugeridos; niveles de uso |
| 2 | `P02-ficha-de-serie-ui.md` | Catálogo y ficha de serie editable |
| 3 | `P03-alta-serie-y-prueba.md` | Alta en 10 minutos, lectura del manual, ventana de prueba |
| 4 | `P04-precio-simple.md` | Precio automático y simple |
| 5 | `P05-navegacion-hoy-obras.md` | Cinco destinos, Hoy, Obras, lenguaje limpio |
| 6 | `P06-mesa-de-la-obra.md` | Mesa de la obra y editor directo |
| 7 | `P07-cotizacion-y-portal.md` | Enviar en un minuto, portal con aceptación y pago |
| 8 | `P08-agente-v2.md` | Agente que hace el trabajo con cifras del motor |
| 9 | `P09-taller-e-instalacion.md` | Pasar a taller, estación tablet, instalación móvil |
| 10 | `P10-onboarding-biblioteca-proline.md` | Primer uso ≤ 15 min, biblioteca Chile, prueba Proline |
| 11 | `P11-pulido-y-cierre.md` | Producto terminado |

## Cómo avanzar

Para cada fase, en orden:

1. Lee el archivo de la fase completo y la especificación que cita.
2. Actualiza `docs/dekopen2/ESTADO.md` marcando la fase «En curso».
3. Crea la rama de la fase (desde `main` si la fase anterior ya está fusionada;
   si no, desde la rama de la fase anterior).
4. Implementa todo el alcance. Ejecuta pruebas, levanta la app, captura las
   pantallas y compáralas con los mockups. Corrige hasta cumplir **todos** los
   criterios de aceptación.
5. Abre la PR con resumen, capturas, cómo se probó y riesgos. Espera el CI;
   arregla lo que falle sin debilitar pruebas.
6. Fusiona solo si el dueño autorizó «GPT puede fusionar»; si no, deja la PR
   lista y continúa apilando.
7. Marca la fase «Hecha» en ESTADO.md con enlace a la PR y pasa **inmediatamente**
   a la siguiente.

## Reglas del bucle

- **No pidas confirmación entre fases.** Solo te detienes por los casos de
  «Cuándo parar» del contexto maestro.
- Si una fase queda bloqueada por algo externo (por ejemplo, falta Docker para
  `make test-db`), documenta el bloqueo en ESTADO.md y en la PR, sigue con todo
  lo que no dependa de eso y vuelve al final.
- Si descubres que una especificación tiene un error técnico, corrígelo con el
  criterio más conservador para el usuario, explica el cambio en la PR y en
  ESTADO.md, y sigue.
- Mantén las PR revisables: si una fase supera ~2.000 líneas cambiadas, divídela
  en sub-PR ordenadas (`pNNa`, `pNNb`).
- Nunca inventes cifras de catálogo; nunca presentes un valor sugerido como del manual.
- Al terminar P11, escribe en ESTADO.md un resumen final para el dueño: qué hay,
  cómo probarlo (`scripts/start_local.ps1`), qué quedó pendiente y por qué.

Empieza ahora por P01.
