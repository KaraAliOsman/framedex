# PRD: DESIGN SYSTEM PROFESIONAL & MOTOR CAD CANVAS (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Prohibición de Vibe-Coding • Motor Canvas 2D GPU • Estándar Figma/AutoCAD)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  

---

## 1. Prohibición Absoluta de Vibe-Coding e Ilustraciones de IA

Queda **terminantemente prohibido** el uso de patrones típicos de diseño generativo ("vibe-coding"):
- ❌ **Prohibido:** Efectos de resplandor neón (*glow*), sombras borrosas (*drop-shadows* excesivos) o filtros de desenfoque (*backdrop-blur* tipo vidrio falso).
- ❌ **Prohibido:** Rectángulos redondeados caricaturescos o dibujos planos que parezcan ilustraciones infantiles.
- ❌ **Prohibido:** Colores con degradados saturados que hagan parecer la aplicación un demo de IA.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ❌ EL ERROR DEL VIBE CODING (Falso e Infantil) │ ⚡ EL ESTÁNDAR CAD PROFESIONAL (Figma / AutoCAD) │
├────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
│ • SVGs con sombras y brillos borrosos.         │ • Motor Canvas 2D / PixiJS acelerado por GPU.   │
│ • Tarjetas con bordes brillantes y glow.       │ • Líneas vectoriales técnicas nítidas de 1px.   │
│ • Texto plano sin alineación geométrica.       │ • Cotas arquitectónicas con tipografía tabular. │
│ • Degradados morados/azules genéricos de IA.   │ • Interfaz neutra estilo Adobe Studio / Linear. │
└────────────────────────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 2. Motor de Renderizado: Canvas 2D Técnico Acelerado por GPU (`Konva.js` / `PixiJS`)

En lugar de incrustar SVGs estáticos con estilos de CSS, el dibujo de carpintería se renderiza sobre un **Viewport CAD Interactivo de Alto Rendimiento**:

1. **Rendimiento a 60/120 FPS:** Renderizado en Canvas 2D / WebGL acelerado por hardware para soportar proyectos de 50+ ventanas sin lag.
2. **Viewport Profesional con Zoom y Pan Infinito:**
   - Zoom suave con la rueda del ratón ($0.1\times$ a $10\times$).
   - Desplazamiento panorámico (*Pan*) con barra espaciadora o botón central del ratón.
   - Rejilla de ingeniería (*Grid*) con ajuste magnético (*Snapping*) a $1\text{ mm}$, $5\text{ mm}$ y $10\text{ mm}$.
3. **Líneas de Espesor Técnico CAD Normalizado:**
   - Líneas de corte exterior: `1.5px` sólido.
   - Líneas de traslape interior: `1.0px` sólido.
   - Líneas de cota y extensión: `0.75px` neutro con puntas de flecha DIN a 45°.
   - Líneas de apertura cinemática: `0.75px` discontinuo (`dash: [4, 4]`).

---

## 3. Sistema de Componentes UI: Estándar Radix UI + Adobe Spectrum Tokens

La interfaz de usuario no utiliza plantillas genéricas. Se construye sobre **primitivas accesibles y ultra-limpias**:

- **Librería de Componentes:** **Radix UI Primitives** (menús, modales, tooltips y sliders sin estilos basura).
- **Tipografía Técnica:** 
  - Textos de interfaz: **Inter** o **Geist Sans** (limpia, legible y profesional).
  - Cotas, medidas y números de dinero: **Geist Mono** o **JetBrains Mono** (tipografía tabular con números monoespaciados para que las cifras no bailen).
- **Paleta de Colores Neutra y Sobria (Estilo Linear / Adobe):**
  - Fondo Canvas Claro: `--theme-canvas-bg: #F8FAFC` (Gris técnico suave).
  - Fondo Canvas Oscuro: `--theme-canvas-bg: #0F172A` (Grafito arquitectónico).
  - Líneas de Perfil: `--theme-cad-line: #0F172A` (en claro) / `--theme-cad-line: #F1F5F9` (en oscuro).
  - Acentos de Selección: `--theme-accent: #0284C7` (Azul técnico de ingeniería).

---

## 4. Cotizaciones Ejecutivas en PDF (Vectorial Puro con WeasyPrint & Cairo)

Para los presupuestos comerciales (DOC-01):
- **Cero Artefactos de Rasterizado:** Los dibujos técnicos se incrustan como vectores vectoriales puros a `300 DPI` de impresión.
- **Tipografía Incrustada:** Todos los números y símbolos técnicos se compilan con fuentes vectoriales nativas, garantizando que el PDF se vea impecable tanto en un teléfono como impreso en papel en la obra.
