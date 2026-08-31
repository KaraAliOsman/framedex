# PRD-07: INSPECTOR TÉCNICO DE TALLER Y REGLAS DE FABRICABILIDAD (v1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-06, PRD-08, PRD-14

---

## 1. Misión y Filosofía del Inspector

El Inspector Técnico de Dekopen (`/engine/inspector.py` y Pantalla **S07**) actúa como el "Jefe de Taller Digital". Su objetivo es detectar incompatibilidades físicas, excesos de peso y fallas normativas en tiempo real durante el diseño 2D, antes de cortar un solo perfil.

### Regla Constitucional de Comunicación
Ningún hallazgo del inspector puede presentarse como un código de error crudo o traza técnica. Todo hallazgo debe expresarse en lenguaje claro de taller de PVC, indicando:
1. **Qué ocurre** (Diagnóstico claro).
2. **Por qué es un problema** (Riesgo físico: descuelgue de hoja, filtración, rotura de vidrio).
3. **Cómo solucionarlo en 1 Clic** (Acción correctiva automatizada).

---

## 2. Las 14 Reglas Canónicas de Validación (§6.6 + Enmienda B.4)

Todas las constantes son configurables y overridibles por sistema de perfiles en base de datos.

| # | Regla | Condición Matemática de Fallo | Severidad | Acción Correctiva en 1 Clic |
|---|---|---|---|---|
| **R01** | **Peso Máximo de Hoja** | $P_{total\_sash} = P_{pvc} + P_{acero} + P_{vidrio} > P_{max\_herraje}$ *(e.g. $> 100\text{ kg}$ en herraje estándar)* | 🔴 **ROJO** | *"Actualizar a kit de bisagras reforzadas 130 kg"* o *"Dividir vano en 2 hojas"*. |
| **R02** | **Relación de Aspecto (Proporción)** | $H_{sash} / W_{sash} > 2.5$ O $H_{sash} / W_{sash} < 0.4$ | 🟡 **AMARILLO** | *"Ajustar división a proporción recomendada 1:1.5"*. |
| **R03** | **Dimensiones Mínimas / Máximas** | $W_{sash} < 350\text{ mm}$ O $W_{sash} > 1600\text{ mm}$ O $H_{sash} > 2400\text{ mm}$ | 🔴 **ROJO** | *"Redimensionar vano al límite permitido por la serie"*. |
| **R04** | **Área vs. Espesor de Vidrio** | Monolítico 4mm: Área $> 1.80\text{ m}^2$ / DVH 4-12-4: Área $> 2.60\text{ m}^2$ | 🔴 **ROJO** | *"Aumentar cristal a 6 mm templado o termopanel 6-12-6"*. |
| **R05** | **Inercia Eólica en Travesaños (NCh 432)** | Momento de inercia del refuerzo $I_x < I_{req}$ para luz $> 1800\text{ mm}$ | 🔴 **ROJO** | *"Cambiar a refuerzo de acero pesado 2.0 mm (SKU: RF-HEAVY)"*. |
| **R06** | **Matriz Junquillo–Vidrio** | $\text{Espesor Vidrio} \notin \text{glazing\_bead\_matrix}(\text{system\_id})$ | 🔴 **ROJO** | *"Seleccionar espesor estándar (20 mm o 24 mm) disponible en catálogo"*. |
| **R07** | **Desagües y Descompresión** | Ancho vano $> 800\text{ mm}$ requiere $\ge 3$ orificios de desagüe inferiores | 🟡 **AMARILLO** | *"Añadir orificio de desagüe central automáticamente"*. |
| **R08** | **Espaciado de Cerraderos Perimetrales** | Distancia entre puntos de cierre consecutivos $> 800\text{ mm}$ | 🟡 **AMARILLO** | *"Añadir reenvío de esquina con punto de cierre adicional"*. |
| **R09** | **Junta de Dilatación Térmica** | Ancho continuo $> 4000\text{ mm}$ en blanco ($> 3000\text{ mm}$ foliado) sin acople | 🔴 **ROJO** | *"Insertar perfil de acople de dilatación con junta elástica"*. |
| **R10** | **Tolerancia Diagonal de Marco** | Diferencia teórica $|D_1 - D_2| > 1.50\text{ mm}$ | 🔴 **ROJO** | *"Recalcular escuadra ortogonal de marco"*. |
| **R11** | **Holgura Perimetral de Cámara** | Holgura entre hoja y marco fuera del rango $12.0\text{ mm} \pm 1.5\text{ mm}$ | 🔴 **ROJO** | *"Restablecer solape nominal de 8.0 mm"*. |
| **R12** | **Inercia en Corredera 3 Hojas** | Corredera 3 hojas con vano $> 4500\text{ mm}$ exige refuerzo con $I_x \ge 45\text{ cm}^4$ | 🔴 **ROJO** | *"Cambiar a refuerzo pesado (SKU RF-HEAVY)"*. |
| **R13** | **Proyectante de Gran Altura** | Proyectante con $H > 1200\text{ mm}$ exige compás doble | 🟡 **AMARILLO** | *"Añadir segundo compás"*. |
| **R14** | **Carga de Carros Monoriel** | Corredera `rail_type='mono'` con hoja $> 150\text{ kg}$ exige 4 carros de carga ($\ge 80\text{ kg/rueda}$) | 🔴 **ROJO** | *"Configurar kit monoriel cuádruple"*. |

---

## 3. Comportamiento del Semáforo y Bloqueo de Producción

1. **Estado VERDE (Aprobado):** Cero infracciones. Habilita botón *"Aprobar para Taller"*.
2. **Estado AMARILLO (Advertencia de Taller):** Alerta no estructural (e.g. compás doble sugerido). Permite cotizar y deja constancia en la OT.
3. **Estado ROJO (Bloqueo Crítico P0):** Infracción de seguridad o ensamble. Bloquea físicamente la emisión de la orden de producción.
