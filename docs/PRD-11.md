# PRD-11: MOTOR DE PLANTILLAS Y PERSONALIZACIÓN DE COTIZACIONES PDF (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 2 (Personalización Comercial)  
**Bloquea a:** Ninguno (Módulo terminal de Fase 2)

---

## 1. Misión y Alcance del Módulo

El Motor de Plantillas PDF (Pantalla **S22** y `apps.templates_pdf`) permite a cada carpintería adaptar la presentación gráfica de sus cotizaciones comerciales (colores de marca, tipografías, logotipos, cláusulas legales y distribución de columnas) sin comprometer la integridad matemática de los cálculos.

---

## 2. Los 3 Slots de Plantillas por Organización

Cada organización dispone de 3 ranuras (slots) independientes para configurar formatos de salida según el tipo de cliente:

| Slot | Nombre de Plantilla | Caso de Uso Primario | Características de Diseño |
|---|---|---|---|
| **Slot 1** | **Corporativa / Minimalista** | Clientes particulares y casas residenciales | Diseño limpio a 1 o 2 páginas, enfoque en renders vectoriales grandes, descripción clara de vidrios y valor cuota. |
| **Slot 2** | **Comercial / Detallada** | Oficinas de arquitectura y diseño | Incluye fichas de herrajes, especificaciones acústicas/térmicas certificadas y renderizado de perfiles foliados. |
| **Slot 3** | **Licitación / Constructora** | Licitaciones de edificios y obras de gran escala | Formato compacto tipo tabla de vanos, cronograma de entregas por etapas, desglose de pagos e hitos de faena. |

---

## 3. Arquitectura de Bloques Protegidos

Para evitar que una personalización estética elimine información legal obligatoria o altere datos de cálculo, las plantillas se dividen en **Bloques Editables** y **Bloques Estructurales Protegidos**:

```
┌────────────────────────────────────────────────────────┐
│ [EDITABLE] Encabezado: Logo + Datos Empresa            │
├────────────────────────────────────────────────────────┤
│ [EDITABLE] Datos del Cliente y Proyecto                │
├────────────────────────────────────────────────────────┤
│ 🔒 [BLOQUE PROTEGIDO: Render Vectorial SVG del Vano]   │
│   - El usuario puede cambiar bordes y fondos, pero el  │
│     motor inyecta el SVG canónico de /engine.          │
├────────────────────────────────────────────────────────┤
│ 🔒 [BLOQUE PROTEGIDO: Tabla de Resumen Económico]      │
│   - Subtotal Neto, IVA 19%, Total Bruto y Moneda       │
│     calculados estrictamente por el motor de precios.  │
├────────────────────────────────────────────────────────┤
│ [EDITABLE] Condiciones Comerciales y Validez de Oferta │
├────────────────────────────────────────────────────────┤
│ 🔒 [BLOQUE PROTEGIDO: Sello Criptográfico BOM Hash]    │
│   - Hash SHA-256 inmutable + Número de Revisión.       │
└────────────────────────────────────────────────────────┘
```

---

## 4. Variables Dinámicas de Inyección (Template Tags)

Las plantillas utilizan una sintaxis segura basada en placeholders declarativos:

```html
<header class="company-header" style="border-bottom: 2px solid {{ theme.primary_color }};">
  <img src="{{ org.logo_url }}" alt="{{ org.name }}" class="company-logo" />
  <div class="company-info">
    <h1>{{ org.name }}</h1>
    <p>RUT: {{ org.tax_id }} | Fono: {{ org.phone }}</p>
    <p>{{ org.address }}</p>
  </div>
</header>

<section class="quote-meta">
  <p><strong>Cotización:</strong> {{ project.code }} ({{ project.revision }})</p>
  <p><strong>Fecha Emisión:</strong> {{ project.emitted_date }}</p>
  <p><strong>Validez de la Oferta:</strong> {{ project.validity_days }} días</p>
  <p><strong>Cliente:</strong> {{ client.name }} | RUT: {{ client.tax_id }}</p>
</section>

<!-- El bloque protegido inyecta el bucle de posiciones -->
{{ protected_block_positions_loop }}

<!-- El bloque protegido inyecta los totales económicos -->
{{ protected_block_financial_totals }}

<footer class="legal-terms">
  <h3>Condiciones Generales</h3>
  <p>{{ custom_terms_and_conditions }}</p>
  <div class="integrity-stamp">
    <small>Firma Digital BOM Hash: <code>{{ project.bom_hash }}</code></small>
  </div>
</footer>
```

---

## 5. Función de Restauración a Valores de Fábrica (Reset Sagrado)

En la pantalla **S22**, cada slot dispone de un botón de emergencia:
- `[Restaurar Plantilla Original]`
- Al confirmarse, el sistema sobreescribe el HTML/CSS del slot con el template base oficial de Dekopen versionado en el código fuente, garantizando que una plantilla con sintaxis CSS rota pueda recuperarse instantáneamente en 1 clic.
