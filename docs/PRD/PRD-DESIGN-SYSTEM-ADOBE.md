# PRD: SISTEMA DE DISEÑO, MOTOR CAD Y VERSIÓN WEB MÓVIL ESENCIAL (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Web 100% Cloud • OCR Cuaderno de Obra • Escáner QR Web • Móvil Esencial)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  

---

## 1. Filosofía de la Versión Web Móvil: Simple, Rápida y Esencial

Dekopen es una **plataforma 100% Web en la nube** (se accede desde el navegador Chrome/Safari en cualquier celular o PC con internet/WiFi, conectado directamente a la base de datos PostgreSQL). 

En el celular **NO se necesita tener toda la complejidad del computador**. La versión móvil es un **compañero ágil de terreno** enfocado en 4 tareas esenciales de taller y obra:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               LAS 4 ACCIONES ESENCIALES EN CELULAR                               │
├───────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 📝 1. FOTO AL CUADERNO DE MEDIDAS │ Tomas foto con el celular a tus apuntes a mano en tu libreta │
│    (OCR Inteligente de Terreno)   │ de obra y la IA crea la cotización con los vanos listos.     │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 📲 2. ENVIAR A WHATSAPP EN 1 CLIC │ Abres la cotización, revisas el total y mandas el PDF oficial│
│    (Cierre de Venta Inmediato)    │ al cliente por WhatsApp en 2 segundos.                       │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 📷 3. ESCÁNER QR CON LA CÁMARA    │ Apuntas la cámara del celular a la etiqueta de la ventana en │
│    (Control de Armado y Entrega)  │ obra y abres su plano y el checklist para firma del cliente. │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ ✏️ 4. AJUSTE RÁPIDO DE MEDIDAS    │ Modificas una medida o color con teclado numérico grande sin │
│    (Edición Ligera en Terreno)    │ complicaciones de menús pesados.                             │
└───────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. OCR de Terreno: Foto al Cuaderno o Libreta de Medidas (Tool T1)

El flujo real de cualquier carpintero en obra:
1. Mide los vanos con su distanciómetro láser y anota a mano en su cuaderno o croquis:  
   *`Vano 1: 1500 x 1200 Corredera 2H Nogal Termopanel`*  
   *`Vano 2: 800 x 600 Proyectante Blanco Simple`*  
   *`Vano 3: 2000 x 2100 Puerta Corredera 2H Antracita`*
2. Entra a **dekopen.com** en su celular, presiona **`+ Cotizar desde Foto`** y le saca una foto a la hoja de su cuaderno.
3. El motor de visión (Gemini 3.7 / GPT-5.6) lee los números y textos manuscritos, estructura los vanos y entrega el **borrador de cotización calculado a 0.00 mm en la pantalla del celular**.

---

## 3. Escáner QR Integrado en el Navegador Web (HTML5 Barcode API)

Sin instalar ninguna app de la tienda:
- El instalador entra a la web en su celular y abre el **Escáner QR**.
- Apunta a la etiqueta pegada en el marco de PVC.
- La web abre automáticamente:
  - El detalle de fabricación de esa ventana.
  - El **Checklist de Instalación**: sellado, plomo, funcionamiento de manilla.
  - El botón para que el cliente firme la recepción de la obra con su dedo directamente en la pantalla.

---

## 4. Interfaz Web Móvil Ligera (Cero Sobrecarga)

- **Cero funciones pesadas en celular:** La configuración profunda de fórmulas, catálogos técnicos masivos y matrices de costos complejas se hace cómodamente en la computadora.
- **En el celular todo es táctil y directo:** Botones grandes de $48\text{px}$, texto nítido, carga instantánea y conexión directa a la base de datos central.
