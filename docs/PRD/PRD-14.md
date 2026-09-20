# PRD-14: CERTIFICADO DE FABRICABILIDAD Y DOBLE VERIFICADOR (v1.2)
**Estado:** Bloqueado / Congelado
**Versión:** 1.2
**Fase:** 3 (Garantía y Certificación)
**Bloquea a:** PRD-15

---

## 1. Misión del certificado

El Certificado de Fabricabilidad (DOC-08 y Tool T8) valida que un proyecto cumple las normas de
resistencia al viento, seguridad de acristalamiento, límites dimensionales y capacidades de
herrajes de los sistemas utilizados. La decisión usa únicamente datos técnicos certificados,
la salida de /engine y reglas explícitas del contrato.

## 2. Doble verificación cruzada

T8 recibe el árbol paramétrico, BOM y memoria de cálculo y ejecuta dos evaluaciones mediante
rutas de runtime independientes. Las rutas deben ser independientes para la evidencia del
arbitraje; sus proveedores y modelos se configuran en ai_routes y no se congelan aquí.

Cada evaluación devuelve un resultado tipado. Un árbitro determinista compara las salidas:

- coincidencia total: emite DOC-08, hash y QR público sin costos ni despiece confidencial;
- discrepancia superior a 0.00 mm en holguras o 0.1 kg en peso: bloquea la emisión y genera una
  alerta para revisión del taller.

## 3. Reglas normativas de T8

1. La operación estándar consume el crédito definido por el contrato de billing y utiliza dos
   rutas independientes configuradas para doble verificación.
2. Una ruta alternativa puede cambiarse por configuración operativa o fallback, siempre que se
   conserve la independencia, la auditoría previa y el arbitraje determinista.
3. La concordancia matemática es obligatoria: cualquier desviación sobre los umbrales definidos
   bloquea el certificado.
4. La emisión genera DOC-08 con identificador criptográfico y QR que solo expone el estado de
   fabricación autorizado.
5. Ninguna evaluación de IA sustituye al motor determinista ni escribe números directamente.
