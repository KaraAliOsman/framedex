---
type: concept
status: active
updated: 2026-10-07
volatility: medium
sources:
  - docs/cola/prompts/D07-vano-fabricacion.md
  - engine/src/dekopen_engine/mounting.py
  - backend/projects/mounting.py
  - supabase/migrations/20270104000000_opening_mounting.sql
  - docs/redesign/captures/vano-fabricacion/aceptacion.md
---

# Vano, montaje y fabricación

## Autoridad y cálculo

La regla pertenece a organización y serie. Declara tipo, fuente, condición
sintética, tolerancia y holgura/premarco/ensanche/traslape de cada lado.
Guardar crea una revisión de autoridad; no cambia reglas de medidas anteriores.
Los ensanches exigen un accesorio físico compatible en los lados deducidos.
Cada regla se resuelve por tenant, serie, código y revisión inmutable, incluso
si una autoridad posterior ya fue publicada. Medir otro marco no obliga a
actualizar reglas anteriores; un cambio de serie requiere su propia autoridad.
La selección independiente de accesorios permanece separada de las piezas
exigidas por montaje. Cambiar regla retira solo las exigencias anteriores y
conserva los lados o accesorios independientes; destinos contradictorios
requieren corrección explícita. La propuesta del inspector se invalida ante
cambios de diseño o de regla durante la espera.

El motor toma una o tres medidas positivas por eje y conserva mínimo y
dispersión con Decimal a 0,01 mm. Fabricación suma al mínimo los traslapes y
resta holgura, marco y ensanche. La fijación manual necesita motivo; su
desviación, descuadre y desplome se comparan con la tolerancia declarada.
El tipo de muro es obligatorio y empieza sin selección: no se presume un
material que el usuario no haya observado.
Los cuatro tipos tienen golden generado mediante `make goldgen`.

## Evidencia y revisión

Cada generación de evidencia es append-only y liga regla, entradas y resultado
al diseño guardado mediante SHA. Guardar no admite geometría que discrepe de
su derivación. Eliminar un borrador conserva su historial; el trigger SQL
verifica tenant/proyecto/posición al insertar sin impedir ese borrado legítimo.

OWNER, ESTIMATOR y WORKSHOP_MANAGER pueden confirmar con timestamp y generación
actuales, cobertura de todos los marcos y reconocimiento de avisos. La función
estrecha de lock no concede permiso de edición general al encargado.
INSTALLER continuará su flujo específico en P23.

Rectificar una revisión cotizada/aprobada simula el proyecto completo con
Precios y muestra el Δ de venta neta. Aplicar requiere un token ligado a la
propuesta y precio vigentes. Abre la sucesora, guarda las medidas de obra y
requiere nueva confirmación. El precio y PDF de la revisión anterior no cambian.
La copia de antecedentes a una sucesora acepta solamente evidencia vigente:
no vuelve a ligar un vano obsoleto a un diseño distinto.

Las nuevas emisiones sellan `measurements_required=true`; backend y SQL impiden
liberar OT con evidencia pendiente o ajena al diseño. Los snapshots históricos
sin esa marca conservan su comportamiento anterior. Una corrección de un
proyecto ya en producción se gestiona con el encargado, sin reescribir lo
liberado.

## Representación y límites

El editor dibuja vano y fabricación con ajustes asimétricos del motor. «¿De
dónde sale?» presenta sus deducciones. Cotización y portal muestran ambas
medidas; taller solo fabricación. El portal proyecta los datos comerciales y
omite actor y motivos privados.

Las reglas reales deben aportarse en Ajustes › Vano y montaje para cada serie.
Una regla DEMO no certifica montaje ni capacidad estructural. Las superficies
completas del editor, documentos y captura móvil continúan en P04/P05/P09/P23.
