# PRD-14: CERTIFICADO DE FABRICABILIDAD Y DOBLE VERIFICADOR CRUZADO (v1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Garantía Técnica de Alto Nivel)  
**Bloquea a:** Ninguno

---

## 1. Misión del Certificado de Fabricabilidad

El Certificado de Fabricabilidad (Tool **T8** `cross_verify_certificate` y Documento **DOC-08**) es una credencial técnica de ingeniería que los fabricantes entregan a arquitectos, calculistas y aseguradoras para certificar que cada ventana cumple con las normas estructurales de viento, seguridad de vidrio y capacidad de carga mecánica.

---

## 2. Parámetros Normativos por País (Enmienda C.5 / Decisión D-30)

- **Versión v1 (Chile):** El certificado valida estrictamente la normativa chilena:
  - **NCh 432:** Cálculo de presión de viento y deflexión máxima admisible ($f_{adm} = \min(L/300, 8.00\text{ mm})$).
  - **NCh 132 / NCh 135:** Vidrios de seguridad obligatorios (laminado / templado) en zonas de riesgo e impacto.
- **Fase 3 (Expansión Internacional):** La capa normativa se parametriza por país (e.g. Normas europeas EN 12464 / EN 12207 / EN 12208, y normas estadounidenses ASTM E283 / E330 / E547). Esta parametrización no bloquea el lanzamiento de la v1.

---

## 3. Arquitectura de Doble Verificación Independiente (Tool T8)

- **Verificador Primario:** `/engine` + Modelo A.
- **Verificador Secundario (Tool T8):** Modelo B independiente en doble ciego (sin acceso al razonamiento del modelo A).
- **Árbitro:** Concordancia al 100% genera el sello digital con código QR validable en `app.dekopen.com/cert/{cert_uuid}`.
