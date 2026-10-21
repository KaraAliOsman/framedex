# P05 · Navegación nueva, Hoy y Obras

**Rama:** `gpt/dk2-p05-navegacion` · **Depende de:** P04 · **Siguiente:** P06

## Objetivo

Cinco destinos claros, una pantalla **Hoy** que dice qué hacer ahora, y una lista
única de **Obras** por etapa. Limpieza total de jerga en la interfaz.

Especificación: `04-experiencia-y-diseno.md` §1, §3.1, §3.2 y §4 (glosario).
Mockups: `mockups/Hoy.dc.html`, `mockups/Obras.dc.html`. Revisa
`frontend/src/app/navigation.ts`, `AppShell.tsx`, `DashboardPage.tsx`,
`features/projects/ProjectsHome.tsx`, `features/quotations/`, `features/projects/ClientsPage.tsx`.

## Qué construir

1. **Barra lateral:** Hoy · Obras · Taller · Catálogo · Empresa (ocultar lo que un
   rol no usa). Clientes se mueve dentro de la obra y a la búsqueda Ctrl K
   (mantén la ruta `/clients` funcionando para enlaces existentes). Cotizaciones
   se integra en Obras. Analítica pasa a tarjetas en Hoy y a Empresa › Informes.
   Funciones avanzadas (CNC, cohortes, cierres de costos, rectificación de
   terreno) quedan accesibles en **Empresa › Funciones avanzadas**, no en la barra.
2. **Hoy:** saludo y fecha; máximo tres tarjetas de métricas; tarjeta «DEKOPEN
   preparó N cosas · Revisar» (alimentada por la bandeja de la IA cuando exista;
   en esta fase, cotizaciones creadas por el asistente); cola **Para hacer** con
   filas verbo + objeto + botón (enviar cotización, pasar a taller, confirmar
   sugeridos, recordar cliente, cobrar saldo). Usa el backend de «hoy»
   existente (`backend/analytics`, `useToday`) y extiéndelo.
3. **Obras:** lista densa (estilo Linear) con etapas Cotizando → Enviada →
   Aceptada → En taller → Instalada → Por cobrar → Cerrada, filtro segmentado
   con conteos, búsqueda en píldora, fila completa clicable, botón **Nueva
   cotización**. Deriva la etapa del estado real de la obra.
4. **Purga de lenguaje:** aplica el glosario en **toda** la aplicación
   (`frontend/src/i18n/es-CL.ts` y textos en componentes): «Sin dato» → «Falta ·
   Completar» o «Sugerido»; «sellado/sellada» → «emitida»; «fuente/autoridad/
   procedencia» → «origen» con texto humano; «posición/vano» → «ventana»;
   «encargo/recibo» → «tarea/resumen». Extiende la regla de `check_guards.py`
   de P02 a toda la interfaz.

## Criterios de aceptación

- [ ] Capturas comparadas con los mockups en 1440 × 900 y 390 × 844 para cada rol
      (dueño, vendedor, jefe de taller, operario, instalador).
- [ ] e2e actualizados (`frontend/tests/e2e/`) para la navegación nueva; los
      enlaces antiguos redirigen.
- [ ] Recuento de «Sin dato», «sellad», «autoridad», «fuente», «procedencia» en
      textos de interfaz = 0 (guardián activo).
- [ ] `break-ui` en Obras con 500 obras y nombres largos.
- [ ] Todo verde; wiki y ESTADO.md actualizados.
