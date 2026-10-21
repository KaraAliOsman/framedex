# P10 · Primer uso, biblioteca LatAm y prueba de aceptación Proline

**Rama:** `gpt/dk2-p10-onboarding` · **Depende de:** P03, P08, P09 · **Siguiente:** P11

## Objetivo

Que un taller nuevo emita su **primera cotización real en ≤ 15 minutos** desde
el registro, y demostrarlo con la serie que falló en NuveraPRO: **Proline PRO6004**.

Especificación: `04-experiencia-y-diseno.md` §2 (F1); `03-catalogo-y-calculo.md`
§7, §10; `02-estrategia-producto.md` §6.

## Qué construir

1. **Primer uso (F1):** registro con enlace mágico → nombre del taller y país
   (CLP, IVA 19 % preconfigurados para Chile) → «¿Qué series fabricas?» con
   buscador de la biblioteca (logos/monogramas de fabricantes) → «Pon tus
   precios» (Excel o lista del proveedor, P03) → ventana de prueba (P03) →
   primera cotización con un cliente de ejemplo editable. Reanudable; cada paso
   se puede saltar con valores sugeridos visibles.
2. **Biblioteca LatAm fase 1 (Chile):** fichas de serie precargadas como datos
   versionados del sistema (no del tenant): Proline PRO6004 y PRO7005 (vía
   Aluminios & PVC 2000), y las líneas de aluminio y PVC más vendidas en Chile que
   puedas documentar con fuentes públicas. Perfiles y reglas con
   `origin=MANUAL` **solo** si citas una fuente pública verificable (URL o
   documento y página en `source_ref`); lo demás SUGGESTED desde plantilla.
   **Sin precios** (siempre del taller). Si no encuentras datos públicos de una
   serie, déjala con plantilla y marca «Necesita manual del fabricante».
3. **Prueba de aceptación Proline** (e2e Playwright de punta a punta,
   cronometrada): registro → elegir PRO6004 → importar precios de prueba →
   ventana de prueba confirmada → obra con 3 ventanas → enviar cotización por
   enlace → portal acepta. Debe completarse sin pasos ocultos; registra el
   tiempo en la PR (meta: flujo de usuario ≤ 15 min de interacción humana simulada).

## Criterios de aceptación

- [ ] e2e de aceptación Proline en verde en CI.
- [ ] Toda serie precargada con `origin=MANUAL` tiene `source_ref` público; una
      prueba lo verifica.
- [ ] Capturas de cada paso de F1 en 1440 × 900 y 390 × 844.
- [ ] Todo verde; wiki (`brand-identity.md`/onboarding, `catalog-authority.md`) y ESTADO.md.
