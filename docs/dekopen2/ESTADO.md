# DEKOPEN 2 · Estado de implementación

Encargo del dueño: 21-10-2026. Cada fase se entrega por PR y se fusiona con
Lint & Typecheck, Test Suite, Frontend Build y Database Gate aprobados.
Producción y precios comerciales requieren autorización aparte.

| Fase | Alcance | Estado | Rama / PR |
|---|---|---|---|
| P01 | Catálogo v2: backend, origen, niveles y plantillas | En curso | [P01a #164](https://github.com/KaraAliOsman/framedex/pull/164); P01b: `gpt/dk2-p01b-traza-sugeridos` |
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

## P01 · Trabajo y pendientes

Se revisan las autoridades existentes para conservar compatibilidad e historial
al añadir valores sugeridos. Cotizar admitirá sugeridos identificados; fabricar
exigirá confirmarlos y verificar la serie. La verificación de usuario pertenece
a P03; P01 deja preparado su contrato y su bloqueo.

### P01b · Traza de valores sugeridos

- `SystemParams.value_origins` aporta metadatos resueltos sin modificar cifras.
  El resultado añade `assumptions` solo para reglas SUGGESTED consumidas.
- El cálculo registra consultas a reglas de corte/refuerzo, vidrios, límites,
  herrajes y acabados; los módulos contribuyen al conjunto sin duplicados.
  Los contextos no se filtran entre hilos ni después de un error.
- Los campos nuevos se omiten al serializar contratos históricos que nunca
  los declararon. La comprobación de bytes dorados pasa sin regenerarlos.
- OpenAPI y orval regenerados. Las pruebas de inventario de parámetros ahora
  enumeran 37 campos y clasifican `value_origins` como metadato; mantienen la
  comprobación exhaustiva y apuntan al consumidor real tras extraer el wrapper.
- Pendiente de P01: persistencia/historial por celda, cuatro plantillas,
  niveles de uso, endpoints por pestaña/lote y bloqueos por dependencia.
  Esta sub-PR todavía no habilita una serie para cotizar ni fabricar.
