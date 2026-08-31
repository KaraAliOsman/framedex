# PRD-15: AUTOPILOT MAX — COTIZACIÓN AUTOMÁTICA DESASISTIDA (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Automatización de Alto Nivel)  
**Bloquea a:** Ninguno

---

## 1. Misión de Autopilot Max

Autopilot Max (Tool **T9** `draft_autopilot`, **30 + 2 créditos / página**) procesa solicitudes de cotización entrantes (PDFs de licitación, cuadros de vanos por correo) y genera un **borrador de cotización 100% calculado y listo para revisión humana**.

---

## 2. Invariable Constitucional: Espera Humana Obligatoria

Ninguna cotización generada por Autopilot se envía directamente al cliente sin el clic de aprobación y firma de un usuario con rol `OWNER` o `ESTIMATOR` (Regla 11 de la Constitución).

---

## 3. Pipeline de Ejecución y Reglas del Inspector (R01–R14)

1. Ingestión y OCR del archivo con Tool `T1`.
2. Asignación automática de la serie por defecto (`profile_systems`) y color.
3. Despiece determinista en `/engine`.
4. Evaluación estricta de las **14 Reglas Canónicas del Inspector Técnico (R01 a R14)**.
5. Si el semáforo arroja 🔴 **Rojo**, Autopilot marca las partidas afectadas con sugerencias de 1-clic fix y bloquea la emisión hasta la resolución manual.
