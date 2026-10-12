---
type: concept
status: active
updated: 2026-10-11
volatility: medium
sources:
  - engine/src/dekopen_engine/thermal.py
  - backend/projects/thermal.py
  - supabase/migrations/20270127000000_thermal_authority.sql
  - docs/engineering/thermal/README.md
  - docs/engineering/thermal/oguc-ds15-transcripcion.json
  - docs/redesign/P18-ACEPTACION.md
---

# Autoridad térmica de ventanas

**Hecho de repo verificado:** Uw usa áreas visibles del motor y `Decimal`;
Uf, Ug, Ψg y clases provienen de informes revisados y ligados al catálogo.
PERFORMANCE liga además el espécimen exacto, incluyendo vidrio y herraje.
Sin datos, con fuentes contradictorias o DEMO, no se afirma cumplimiento.

El panel explica Uw mediante F6 y conserva norma, laboratorio y alcance. La
alternativa más barata se limita al catálogo evaluable con precio, pasa por el
diff común y permite deshacer. La envolvente requiere declaración explícita;
el motor deriva OGT y compara cada orientación con el mayor Uw del grupo.

**Intención del dueño:** saber si cada ventana cumple y por qué, sin transformar
un cálculo o un catálogo de muestra en certificación. El anexo opcional conserva
las fuentes al emitir. Revocar un ensayo no modifica las revisiones selladas.

**Investigación externa:** DS15/2024 y OGUC consolidada MINVU, tablas transcritas
con citas y hashes en `docs/engineering/thermal/`. La fuente normativa no prueba
que un producto real esté ensayado ni que un edificio cumpla toda la OGUC.

**Límites actuales:** no hay FEM, Up para opacos, método para paños solapados ni
extensión de ensayos por rango. La zona no se deriva de comuna. Los datos reales,
la revisión profesional y el plan de descontaminación se conectan por obra.
