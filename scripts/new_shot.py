#!/usr/bin/env python3
"""
Dekopen Shot Initialization Helper (2026 Global Alignment Standard)
Usage: python scripts/new_shot.py SHOT-01
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/new_shot.py SHOT-XX")
        sys.exit(1)
        
    shot_id = sys.argv[1].upper()
    if not re.match(r"^SHOT-\d{2}$", shot_id):
        print(f"Error: Invalid shot format '{shot_id}'. Must be SHOT-01 to SHOT-24.")
        sys.exit(1)
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan_file = os.path.join(base_dir, "docs", "plans", f"PLAN_{shot_id}.md")
    shots_table_file = os.path.join(base_dir, "docs", "PRD", "PLAN_SHOTS.md")
    
    source_prd = "docs/PRD/PRD-XX.md"
    gate_desc = "Verificar cumplimiento de criterios de aceptación y `make dod`"
    shot_name = f"Implementación de {shot_id}"
    
    if os.path.exists(shots_table_file):
        with open(shots_table_file, "r", encoding="utf-8") as f:
            for line in f:
                if f"**{shot_id}**" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 6:
                        source_prd = parts[3]
                        shot_name = parts[4].replace("**", "")
                        gate_desc = parts[5].replace("**", "")
                    break

    template = f"""# Plan de Implementación — {shot_id}: {shot_name}

## 1. Contexto y Visión Global del Sistema
- **Shot ID:** `{shot_id}`
- **PRD Fuente:** `{source_prd}`
- **Gate de Cierre Innegociable:** {gate_desc}
- **Objetivo Principal:** [Describir en 1-2 párrafos la meta técnica de esta iteración]

### 1.1. Conexión y Alineación con otros Shots (Cero Desconexión)
- **Módulos Anteriores que Consume (Upstream):** [Indicar qué contratos o modelos de shots anteriores se utilizan]
- **Módulos Futuros que Consumirán este Código (Downstream):** [Indicar qué shots futuros dependerán de lo que construyamos hoy para no romper contratos futuros]

## 2. Archivos a Crear y Modificar
- `[NEW] ruta/del/nuevo_archivo.ext` — [Propósito y dependencias]
- `[MODIFY] ruta/del/archivo_existente.ext` — [Cambios puntuales]
- `[PROHIBIDO]` — [Módulos explícitamente fuera del alcance de este shot]

## 3. Estrategia de Pruebas y Validación Gauntlet
- **Tests Unitarios:** [Detallar nuevos tests en engine/tests/ o backend/apps/]
- **Casos de Oro (G-Cases):** [Casos evaluados y tolerancias 0.00 mm]
- **Comando de Cierre:** `python scripts/check_dod.py all` (o `make dod`)

## 4. Riesgos Identificados y [PENDIENTE-DECISIÓN]
- [Si existe alguna ambigüedad en el PRD, aplicar Regla 20: insertar [PENDIENTE-DECISIÓN] sin inventar reglas]
"""

    os.makedirs(os.path.dirname(plan_file), exist_ok=True)
    if not os.path.exists(plan_file):
        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"[OK] Created implementation plan scaffold at: {plan_file}")
    else:
        print(f"[INFO] Implementation plan already exists at: {plan_file}")


if __name__ == "__main__":
    main()
