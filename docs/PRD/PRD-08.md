# PRD-08: COMPILADOR ASISTIDO DE CATÁLOGOS TÉCNICOS (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia de Catálogo)  
**Bloquea a:** PRD-09, PRD-10, PRD-13

---

## 1. Misión y Pipeline de Ingestión

El Compilador de Catálogos (Tool **T6** y Pantalla **S14**) permite a una carpintería cargar el catálogo técnico en PDF o planilla Excel de cualquier fabricante de perfiles de PVC (Aluplast, Rehau, VEKA, Kömmerling, Deceuninck, Proline, etc.) y transformarlo en un sistema paramétrico operable en menos de 24 horas.

*Costo de consumo:* **25 + 2 créditos / página** (mínimo 25 créditos) según el tamaño del PDF (Parche P1-2).

```
[ PDF / Excel ] ---> [ OCR Multimodal Gemini ] ---> [ Staging en DB ]
                           (Tool T6)               (profile_systems_draft)
                                                            |
[ Publicación v1 ] <--- [ Verif. /engine ] <--- [ Preguntas Quirúrgicas ]
                             (G-Cases)                    (Tool T4)
```

---

## 2. Parámetros Críticos Extraídos y Semáforo Unificado (Enmienda 3 M1)

El compilador extrae obligatoriamente los siguientes parámetros de sistema para alimentar `/engine`:
- `depth_mm`, `chamber_count`, `frame_face_width_mm`, `sash_face_width_mm`, `mullion_face_width_mm`, `rebate_depth_mm`.
- `welding_loss_per_corner` ($3.00\text{ mm}$ default), `sash_overlap_mm` ($8.00\text{ mm}$ default).
- `glass_clearance_white_mm` ($3.00\text{ mm}$ default, $5.00\text{ mm}$ en Demo 60), `glass_clearance_foil_mm` ($5.00\text{ mm}$).
- **Parámetros Críticos Adicionales (M1):** `rail_type` (`'dual'` | `'mono'`), `pulley_height_mm` ($12.00\text{ mm}$ default), `central_overlap_mm` ($35.00\text{ mm}$ default), `door_threshold_mm` ($30.00\text{ mm}$), `door_bottom_clearance_mm` ($20.00\text{ mm}$), `sliding_lateral_clearance_mm` ($0.00\text{ mm}$).
- Matriz junquillo-vidrio completa (`glazing_bead_matrix`).

### Semáforo de Confianza
- **Verde ($\ge 90\%$):** Extraído directamente de una tabla técnica o plano acotado con cota explícita.
- **Amarillo ($70\% - 89\%$):** Inferido por proximidad visual o cálculo geométrico indirecto. Requiere confirmación visual.
- **Rojo ($< 70\%$ o Faltante):** No encontrado en el documento. Dispara pregunta quirúrgica (Tool T4).

---

## 3. Fixtures Verificados de Compilador (Enmienda B.6)

El compilador cuenta con 4 suites de fixtures reales congeladas para tests de regresión:

1. **VEKA Softline 70:** Profundidad $70.00\text{ mm}$ · 5 cámaras · Vidrio máx $42\text{ mm}$ · Soldadura $3.0\text{ mm}$ · Solape $8\text{ mm}$ · Clase A.
2. **Aluplast Ideal 4000:** Profundidad $70.00\text{ mm}$ · Vidrio máx $48\text{ mm}$ · Soldadura $3.0\text{ mm}$.
3. **Rehau Euro-Design 70:** Profundidad $70.00\text{ mm}$ · $U_w = 0.8\text{ W/m}^2\text{K}$.
4. **Proline Pro6004 (Plantilla PRIVADA):** Profundidad $60.00\text{ mm}$ · 3 cámaras · Soldadura $2.5\text{ mm}$ · Barra $5800.00\text{ mm}$.

> [!NOTE]
> [PENDIENTE-DECISIÓN: ficha v1 completa pre-F2 con standard_ref, doble QC dimensional+fusión y sanity check peso/densidad antes de abrir compilar libre a usuarios en Fase 2].
