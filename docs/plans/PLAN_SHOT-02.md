# Plan de Implementación — SHOT-02: DDL completo + `hardware_kits` + RLS + tests aislamiento (Supabase CLI en CI)

## 1. Contexto y Objetivos
- **Shot ID:** `SHOT-02`
- **PRD Fuente:** `PRD-02 (+Enm. 1 & F1)`
- **Gate de Cierre Innegociable:** SQL aplica en Supabase limpio; test tenant-A≠tenant-B pasa; seed Demo 60 visible global; `payment_events`/`credit_ledger`/`hardware_kits` existen
- **Objetivo Principal:** [Describir en 1-2 párrafos la meta técnica de esta iteración]

## 2. Archivos a Crear y Modificar
- `[NEW] ruta/del/nuevo_archivo.ext` — [Propósito y dependencias]
- `[MODIFY] ruta/del/archivo_existente.ext` — [Cambios puntuales]
- `[PROHIBIDO]` — [Módulos explícitamente fuera del alcance de este shot]

## 3. Estrategia de Pruebas y Validación Autónoma
- **Tests Unitarios:** [Detallar nuevos tests en engine/tests/ o backend/apps/]
- **Casos de Oro (G-Cases):** [Casos evaluados y tolerancias 0.00 mm]
- **Comando de Cierre:** `make dod` (Linters, Tipos estrictos, Pytest, Vitest)

## 4. Riesgos Identificados y [PENDIENTE-DECISIÓN]
- [Si existe alguna ambigüedad en el PRD, aplicar Regla 20: insertar [PENDIENTE-DECISIÓN] sin inventar]
