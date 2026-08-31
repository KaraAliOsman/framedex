# PRD-09: INTÉRPRETE MULTIMODAL DE PLANOS Y CUADROS DE VANOS (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia Operativa)  
**Bloquea a:** PRD-10, PRD-15, PRD-17

---

## 1. Misión y Flujo de Procesamiento

El Intérprete de Planos (Tool **T1** `extract_positions` y Pantalla **S27** `/ai/extract-positions`, roles: `OWNER`, `ESTIMATOR`) permite a los cotizadores subir planos de arquitectura en PDF, imágenes de cuadros de vanos o fotos de croquis de taller y convertirlos en proyectos estructurados con múltiples posiciones en menos de 3 minutos.

---

## 2. Esquema JSON de Salida y Semáforo Unificado (Enmienda C.3)

Cada dato extraído por el modelo multimodal recibe un índice de confianza normalizado:
- **Verde ($\ge 90\%$):** Coincidencia visual y textual nítida.
- **Amarillo ($70\% - 89\%$):** Tipografía ambigua, manuscrito o inferencia por escala.
- **Rojo ($< 70\%$):** Cota faltante o tipología incierta (requiere corrección obligatoria antes de importar).

```typescript
export interface ExtractedPositionCandidate {
  tag: { value: string; confidence: number };
  width_mm: { value: number; confidence: number };
  height_mm: { value: number; confidence: number };
  quantity: { value: number; confidence: number };
  typology: { value: string; confidence: number };
  glass_spec: { value: string; confidence: number };
  bounding_box: { page: number; x: number; y: number; w: number; h: number };
}
```

---

## 3. Normalización de Unidades
- Valores $\le 10.00$ (e.g. $1.50 \times 1.20$) $\rightarrow$ Multiplica por $1000 \rightarrow 1500 \times 1200\text{ mm}$.
- Valores en rango $[25.0, 500.0]$ (e.g. $150 \times 120$) $\rightarrow$ Normaliza a $1500 \times 1200\text{ mm}$.
