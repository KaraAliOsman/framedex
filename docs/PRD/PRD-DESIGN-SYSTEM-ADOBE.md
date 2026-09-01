# PRD: DESIGN SYSTEM ADOBE, MOTOR CAD Y ARQUITECTURA MOBILE-FIRST PWA (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Estándar Mobile Pro • Ergonomía de Pulgar • Gestos CAD • PWA Offline)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  

---

## 1. Filosofía Móvil: Una App Nativa Pro en el Teléfono (Cero Web Comprimida)

El 70% del tiempo de un dueño de taller, vendedor o instalador transcurre fuera de la oficina: en la camioneta, visitando clientes o en una obra en construcción. 

Dekopen en el celular **NO es una página web de escritorio encogida donde tienes que hacer zoom con los dedos**: está diseñado como una **Progressive Web App (PWA) de nivel profesional (tipo Uber, Figma Mobile o Revolut)** con ergonomía de pulgar, teclado numérico de obra y soporte offline.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               ARQUITECTURA MÓVIL "THUMB ZONE" (PWA)                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 📱 PANTALLA PRINCIPAL EN CELULAR                                                                 │
│                                                                                                  │
│ ┌────────────────────────────────────────────────────────────┐                                   │
│ │ [≡] Dekopen Pro             Proyecto: Casa Peñalolén   [⚙️]│ <── Barra superior minimalista    │
│ ├────────────────────────────────────────────────────────────┤                                   │
│ │                                                            │                                   │
│ │                     [ CANVAS CAD TÁCTIL ]                  │ <── Viewport con gestos multitouch│
│ │              • Pinch-to-zoom suave (2 dedos)               │     (Pellizcar, arrastrar, tap)   │
│ │              • Doble tap para centrar ventana              │                                   │
│ │                                                            │                                   │
│ ├────────────────────────────────────────────────────────────┤                                   │
│ │  Posición 1: 1.500 × 1.200 mm  •  Serie Proline 60  [Nogal]│ <── Tarjeta de resumen de posición│
│ ├────────────────────────────────────────────────────────────┤                                   │
│ │  ⚡ TOTAL: $285.000 CLP                                    │                                   │
│ │  [ 📄 WhatsApp PDF ]         [ ✏️ Modificar con Cmd+K ]     │ <── ZONA DE PULGAR (Bottom Sheet) │
│ └────────────────────────────────────────────────────────────┘     (Botones de 48px accesibles)  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Los 5 Pilares de la Experiencia Móvil Pro

### 2.1. Ergonomía de la "Zona del Pulgar" (*Thumb Zone Architecture*)
- Todos los controles críticos (cambiar serie, cambiar color, agregar división, ajustar ganancia, enviar cotización) están ubicados en la mitad inferior de la pantalla en **paneles deslizables (*Bottom Sheets*)**.
- El usuario opera la aplicación completa con **una sola mano mientras camina por la obra**.
- Los botones tienen un área táctil mínima de **$48 \times 48\text{ px}$** con micro-vibración háptica (*Haptic Feedback*) al tocar.

### 2.2. Teclado Numérico CAD de Obra (Oversized CAD Numpad)
- Al tocar el ancho o el alto de una ventana, **NO se abre el teclado genérico del celular** (que estorba y tapa el dibujo).
- Se despliega un **teclado numérico gigante integrado con accesos directos de taller**:
  `[ 1.000 ]  [ 1.200 ]  [ 1.500 ]  [ 2.000 ]  [ +50mm ]  [ ⌫ ]`
- Permite ingresar cotas exactas en 2 segundos, incluso usando guantes de trabajo.

### 2.3. Gestos Multitáctiles en el Canvas 2D
- **Pellizcar para Zoom (*Pinch-to-Zoom*):** Acerca y aleja la ventana con inercia física suave a 60 FPS.
- **Doble Tap:** Centra y encuadra la ventana automáticamente en la pantalla.
- **Tap en un Paño:** Despliega un menú radial táctil (*Radial Context Menu*):
  `[ Cambiar a Oscilobatiente ] • [ Poner Fijo ] • [ Cambiar Vidrio ] • [ Eliminar ]`

### 2.4. Flujo "Cotización en Terreno en 60 Segundos"
Diseñado para cerrar la venta directamente frente al cliente en su casa:
1. Tocar **`+ Nueva Cotización`**.
2. Tomar foto al plano con la cámara $\rightarrow$ la IA detecta los vanos al instante.
3. Elegir color tocando la muestra real de textura (**Nogal**, **Blanco**, **Antracita**).
4. El precio total se calcula en tiempo real con margen protegido.
5. Presionar **`Compartir por WhatsApp`**: genera el PDF comercial oficial y el enlace interactivo en un solo toque.

### 2.5. Modo PWA Instalable & Soporte Offline en Obra
- **Instalación en 1 Clic:** Se instala en iOS (Safari $\rightarrow$ *"Agregar a inicio"*) y Android como una aplicación nativa con icono propio y pantalla de carga sin barra de navegador.
- **Modo Offline:** Si estás en un subterráneo o en una obra rural sin señal 4G/5G, puedes seguir diseñando ventanas y guardando cotizaciones. Cuando recuperas internet, se sincroniza automáticamente con la nube.
- **Escáner QR Integrado con la Cámara:** Permite a los instaladores escanear la etiqueta de la ventana en obra para ver el plano de armado y checklist de entrega.
