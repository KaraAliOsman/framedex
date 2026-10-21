# DEKOPEN 2 · Estado de implementación

Encargo del dueño: 21-10-2026. Cada fase se entrega por PR y se fusiona con
Lint & Typecheck, Test Suite, Frontend Build y Database Gate aprobados.
Producción y precios comerciales requieren autorización aparte.

| Fase | Alcance | Estado | Rama / PR |
|---|---|---|---|
| P01 | Catálogo v2: backend, origen, niveles y plantillas | En curso | P01a: `gpt/dk2-p01a-base-verificada`; P01b: modelo y API |
| P02 | Ficha de serie editable | Pendiente | — |
| P03 | Alta de serie y ventana de prueba | Pendiente | — |
| P04 | Precio simple automático | Pendiente | — |
| P05 | Navegación, Hoy y Obras | Pendiente | — |
| P06 | Mesa de la obra y edición directa | Pendiente | — |
| P07 | Cotización y portal | Pendiente | — |
| P08 | Agente v2 | Pendiente | — |
| P09 | Taller e instalación | Pendiente | — |
| P10 | Onboarding, biblioteca Chile y aceptación Proline | Pendiente | — |
| P11 | Pulido y cierre | Pendiente | — |

## Base y comprobaciones previas

- Base de aplicación: `origin/main` en `0207763c`. El paquete de dirección
  todavía está en la [PR #163](https://github.com/KaraAliOsman/framedex/pull/163),
  rama `claude/dekopen2-direccion`, commit `ec3762fe`. Se usa esta rama según
  la alternativa explícita del encargo; solo añade documentación a esa base.
- `main` local tiene cuatro commits propios antiguos y diverge del remoto.
  `git pull --ff-only` lo detectó sin modificar su historia. Se preserva.
- Se preservan los cinco archivos no rastreados preexistentes.
- CI previo de #163: Lint & Typecheck y Frontend Build aprobados; Test Suite
  falló en cinco pruebas de emisión de `ProjectPages.test.tsx`: sus cotizaciones
  vencían el 19-10-2026 y la validación real de vigencia empezó a rechazarlas.
  P01a fija el reloj de esa fixture al 09-10-2026, manteniendo temporizadores
  reales y todas las comprobaciones de revisión y emisión. Las 35 pruebas de
  ese archivo pasan después de la corrección.
- Motor previo en Windows: 1061 aprobadas, dos xfail y tres fallos. Dos se debían
  a leer JSON UTF-8 con la codificación de Windows; el tercero a CRLF introducido
  por `core.autocrlf`. P01a explicita UTF-8 y LF para los goldens. Se restauraron
  únicamente los bytes ya comprometidos en Git, sin ejecutar generación ni
  cambiar fórmulas, parámetros o resultados esperados.
- Ruff, mypy, Django check, ESLint/TypeScript aprobados. Prettier encontró cuatro
  capturas locales en `frontend/.run/`; esa carpeta temporal queda excluida del
  formateo, conservando sus archivos. Suites completas y demás guardas en curso.
- Esta estación no tiene GNU make; se ejecutan los mismos comandos de su
  Makefile mediante Python del proyecto y npm. El CI ejecuta los targets make.
- Primer Database Gate de P01a: 1.483 aserciones pgTAP y 601 pruebas de
  integración aprobaron. El E2E de emisión caducaba el 19-10-2026 y esperaba
  una petición que el control de vigencia rechazaba antes de enviarla. La
  fixture ahora usa una fecha 30 días posterior a la ejecución, conservando
  el reloj real necesario para Magic Link/TOTP y todos los controles de emisión.

## P01 · Trabajo y pendientes

Se revisan las autoridades existentes para conservar compatibilidad e historial
al añadir valores sugeridos. Cotizar admitirá sugeridos identificados; fabricar
exigirá confirmarlos y verificar la serie. La verificación de usuario pertenece
a P03; P01 deja preparado su contrato y su bloqueo.
