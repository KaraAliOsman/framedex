---
type: concept
status: active
updated: 2026-10-10
volatility: medium
sources:
  - docs/redesign/P14-ACEPTACION.md
  - engine/src/dekopen_engine/cnc_authorization.py
  - supabase/migrations/20270120000000_cnc_authority.sql
---

# Autoridad física CNC

El intercambio nuevo exige capacidad, ejes, carrera, margen, mordazas revisadas,
herramientas con geometría/profundidad/fuente, sección sellada y montaje por
perfil. El montaje liga la huella de sección, orientación mecánica y origen.
La orientación de un dibujo no acredita la carga de la máquina.

X siempre parte del extremo inicial, incluso cuando la cara es el extremo
final. El plano completo del extremo no es una trayectoria de fresa. Las
coordenadas del vano no sustituyen Y/Z de herramienta. Una mordaza se evalúa
contra todo el tramo de penetración.

La vista previa compara plan/semilla, operaciones, máquina/herramientas y
declaraciones pendientes. Confirmar revalida esa huella bajo locks; el replay
devuelve el mismo programa y bytes. Una OT anulada no genera, tampoco mediante
replay. Los datos históricos quedan intactos y los archivos conservan hashes.
La condición reemplazada se proyecta al leer sin reescribir el manifiesto.

Máquinas/herramientas tienen org/RLS, escritura OWNER/WORKSHOP_MANAGER,
retiro lógico e historial append-only. La UI compara antes de guardar y envía
la revisión que el humano vio. Restaurar prepara un nuevo cambio auditado.

Actualmente existe solo intercambio neutro. Una preparación puntual, un
formato propietario o una autoridad física ausente no son capacidad ejecutable.
Las declaraciones sin emisor se muestran con sus causas. La aceptación usa
DEMO y no certifica mecanizado industrial. Ver la evidencia P14 antes de
afirmar una nueva capacidad física.

El recorrido de emisión espera la simulación concreta de vidrio antes de
comprobar su selección. El precio indicativo comparte el endpoint, por lo que
identificar solo su URL no demuestra que el vidrio haya sido validado. La
regresión de CI y su corrección quedan registradas en la aceptación P14.

La repetición local detectó también esperas de proyección de precio y de lista
de proyectos. Cada recorrido registra la espera antes de la acción y verifica
la respuesta y su contenido. Una aprobación solo avanza tras recibir APPLIED.
Las pruebas mantienen los límites de tiempo y la autoridad comercial original.
