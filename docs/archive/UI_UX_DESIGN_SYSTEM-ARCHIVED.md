# ARCHIVED v1.2 — SUPERSEDED. Usar PRD-DESIGN-SYSTEM-ADOBE v1.2 como fuente única.

# DEKOPEN — UI/UX DESIGN SYSTEM (v1.0 - SUPERSEDED FOR TOKENS)
**Estado:** SUPERSEDED en tokens y colores por `PRD-DESIGN-SYSTEM-ADOBE.md` (v1.2 Dual).  
**Vigencia:** Las especificaciones anatómicas y de componentes (§4) son válidas y deben implementarse usando exclusivamente los tokens de `PRD-DESIGN-SYSTEM-ADOBE.md`.

---

> [!IMPORTANT]
> **Precedencia de Tokens:** `PRD-DESIGN-SYSTEM-ADOBE.md` es el estándar normativo e inapelable para tokens de color, contrastes, tipografía y soporte Dual (Modo Claro / Modo Oscuro). Cero valores hexadecimales hardcodeados.

---

## 1. Filosofía de Interfaz

La interfaz de Dekopen combina la precisión milimétrica de un software CAD con la agilidad y elegancia de las aplicaciones web modernas para la industria de la construcción.

---

## 2. Anatomía de Componentes y Reglas de Experiencia

1. **Botones de Acción Técnica:**
   - Botón Primario: Verde Esmeralda (`--theme-emerald-action`), reservado exclusivamente para aprobación final, guardado de proyecto y emisión de documentos formales.
   - Botón Secundario: Contorno gris estructural (`--theme-border-subtle`) con texto interactivo.
   - Botón Destructivo: Rojo Carmesí (`--theme-crimson-alert`) con confirmación en modal.
2. **Tablas de Datos de Alta Densidad:**
   - Filas de $36\text{ px}$ de altura con fuente tabular `JetBrains Mono` en valores numéricos y alineación a la derecha.
3. **Diálogos Modales y Drawers:**
   - Fondo con sombreado difuminado (`backdrop-blur-sm`) y cierre mediante tecla `Escape`.
