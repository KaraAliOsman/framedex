# Cómo usar estos prompts con GPT (Codex)

## Opción recomendada: trabajo continuo

1. Abre Codex (CLI, IDE o app) con la carpeta `C:\Users\alios\Downloads\framedex`.
   Codex lee `AGENTS.md` y las skills de `~/.agents/skills` y `.agents/skills`.
2. Pega como primer mensaje el contenido completo de
   [`00-contexto-maestro.md`](00-contexto-maestro.md).
3. Si quieres que fusione solo cuando el CI esté verde, escribe en ese mismo
   mensaje: **«GPT puede fusionar»**. Si no, apilará PR y tú fusionas en orden.
4. Pega [`99-bucle-continuo.md`](99-bucle-continuo.md). GPT recorrerá P01 → P11
   sin pedir confirmación entre fases y llevará el avance en `docs/dekopen2/ESTADO.md`.

## Opción por fases

Pega `00-contexto-maestro.md` y luego una fase (`P01` … `P11`) por sesión. Útil
si quieres revisar cada PR antes de seguir.

## Fases

| Fase | Resultado |
|---|---|
| [P01](P01-catalogo-v2-backend.md) | Modelo de catálogo v2: origen de valores, niveles de uso, plantillas |
| [P02](P02-ficha-de-serie-ui.md) | Catálogo y ficha de serie editable |
| [P03](P03-alta-serie-y-prueba.md) | Alta guiada, lectura del manual con IA, ventana de prueba y caso dorado |
| [P04](P04-precio-simple.md) | Precio simple y automático |
| [P05](P05-navegacion-hoy-obras.md) | Navegación de cinco destinos, Hoy, Obras, lenguaje limpio |
| [P06](P06-mesa-de-la-obra.md) | Mesa de la obra y editor con edición directa |
| [P07](P07-cotizacion-y-portal.md) | Envío en un minuto, revisión automática, portal con aceptación y pago |
| [P08](P08-agente-v2.md) | Agente v2 con herramientas, origen de cada dato y evaluación |
| [P09](P09-taller-e-instalacion.md) | Pasar a taller, estación tablet, compras propuestas, instalación móvil |
| [P10](P10-onboarding-biblioteca-proline.md) | Primer uso ≤ 15 min, biblioteca Chile, prueba de aceptación Proline |
| [P11](P11-pulido-y-cierre.md) | Pulido, rendimiento, accesibilidad y cierre |

## Qué vigilar como dueño

- `docs/dekopen2/ESTADO.md` para el avance.
- Las PR: cada una trae capturas comparadas con los mockups y cómo se probó.
- La prueba de aceptación Proline (P10): es la prueba de que DEKOPEN 2 resuelve
  lo que falló en NuveraPRO.
