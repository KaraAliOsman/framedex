# PRD: DESIGN SYSTEM ADOBE & MOTOR VECTORIAL TÉCNICO CAD (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Estándar de Dibujo Técnico DIN/ISO vs Arte Genérico de IA)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  

---

## 1. Filosofía Visual: Cero "Vibe Coding", Dibujo Técnico Industrial Real

En Dekopen, el dibujo de ventanas y las cotizaciones **NO son ilustraciones genéricas de IA ni rectángulos planos de CSS**. Siguen estrictamente el estándar de dibujo arquitectónico e industrial de software profesional (como NuveraPro, Moxisys, LogiKal o Orgadata):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ❌ EL ERROR COMÚN DE LAS IAs        │ 📐 EL ESTÁNDAR VECTORIAL CAD DE DEKOPEN (Norma DIN / ISO) │
├─────────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ • Rectángulos planos de colores.    │ • Perfiles extruidos reales: marco, hoja, junquillo y T. │
│ • Dibujos infantiles o cartoon.     │ • Simbología cinemática estandarizada (Triángulos DIN).  │
│ • Cotas dibujadas como texto plano. │ • Cadenas de cotas de ingeniería con flechas y extensión.│
│ • Colores CSS básicos (#ff0000).    │ • Texturas arquitectónicas reales de foliado (Renolit).  │
│ • PDFs que parecen resúmenes de chat│ • Cuadro Técnico de Carpinterías estilo Ejecutivo/Apple. │
└─────────────────────────────────────┴──────────────────────────────────────────────────────────┘
```

---

## 2. Capas de Renderizado Vectorial SVG (Multi-Layer Technical Engine)

Cada ventana en el Canvas y en los PDFs se construye matemáticamente en 6 capas vectoriales independientes:

```
[ CAPA 6: COTAS DE INGENIERÍA ] ──► Líneas de extensión, cotas exteriores y luz libre
[ CAPA 5: SIMBOLOGÍA DIN 18055] ──► Triángulos de apertura (Línea discontinua / continua)
[ CAPA 4: JUNQUILLOS (Beads) ]  ──► Perfil retenedor con bisel a 45° según espesor de vidrio
[ CAPA 3: VIDRIO Y TERMOPANEL ] ──► Shading multicapa con reflejo de cámara (Low-E / Laminado)
[ CAPA 2: HOJA MÓVIL (Sash) ]   ──► Geometría de traslape con holgura perimetral exacta
[ CAPA 1: MARCO EXTERIOR ]      ──► Perfil perimetral soldado con cámara de desagüe
```

---

## 3. Simbología Cinemática Estandarizada (Norma DIN 18055 / ISO)

Los sentidos de apertura siguen la convención técnica internacional que entienden los talleres y arquitectos:

1. **Oscilobatiente (Tilt & Turn):** Triángulo doble punteado. El vértice superior indica apertura proyectante superior; el vértice lateral indica apertura practicable hacia el interior.
2. **Practicable Interior (Side-Hung):** Triángulo con vértice en el lado de la manilla y base en las bisagras.
3. **Corredera (Sliding):** Flechas horizontales vectoriales ($\leftarrow / \rightarrow$) sobre las hojas móviles y símbolo $\mathbf{O}$ o $\mathbf{X}$ en las hojas fijas.
4. **Proyectante / Fricción (Awning):** Triángulo con vértice inferior hacia el pestillo.

---

## 4. Texturas y Acabados Arquitectónicos Reales (Foliados Renolit / Hornschuch)

En lugar de colores planos genéricos, el motor de renderizado aplica filtros SVG y patrones CSS de texturas reales de PVC:

| Código Acabado | Nombre Comercial | Render Vectorial / Shader |
|---|---|---|
| `PVC_WHITE_9016` | Blanco Puro RAL 9016 | Acabado satinado suave con sombra interior de cámara $1.5\text{px}$. |
| `FOIL_NOGAL_70` | Nogal / Walnut (Renolit) | Veta de madera oscura con líneas de relieve longitudinales y tinte cálido. |
| `FOIL_ROBLE_DOR` | Roble Dorado / Golden Oak | Tono miel amaderado con micro-sombreado de fibra natural. |
| `FOIL_ANTRACITA` | Gris Antracita RAL 7016 | Micro-textura arenada mate con absorción de luz. |
| `FOIL_NEGRO_MAT` | Negro Grafito RAL 9005 | Acabado arquitectónico mate contemporáneo. |

---

## 5. Diseño Ejecutivo de Cotizaciones (DOC-01: Architectural Schedule)

El presupuesto comercial que recibe el cliente final parece un **dossier de arquitectura de alta gama**:

1. **Encabezado Corporativo Limpio:** Logotipo del taller, datos del cliente, dirección de obra, validez de oferta y número de cotización único.
2. **Grilla de Posiciones (Cuadro de Vanos):**
   - Dibujo vectorial nítido en alta resolución con sus cotas de fabricación.
   - Etiqueta de posición (`P01`, `P02`, etc.) y ubicación en la casa (*"Living principal"*, *"Dormitorio 2"*).
   - Ficha técnica de la posición: Serie de perfil, color, composición del termopanel (ej: `5mm Incoloro + 12mm Cámara Argón + 5mm Low-E`), herraje y transmitancia térmica $U_w$.
3. **Resumen Financiero y Métodos de Pago:**
   - Desglose neto, IVA y total con tipografía clara y contrastada.
   - Hitos de pago configurables (*50% anticipo, 40% entrega, 10% instalación*).
4. **Firma Digital y Código QR:** Enlace directo al visor interactivo web y al Certificado de Fabricabilidad.
