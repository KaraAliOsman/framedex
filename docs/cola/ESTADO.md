| ID | Ola | Estado | PR | SHA | Notas |
|---|---|---|---|---|---|
| P00 | 0 | mergeado | https://github.com/KaraAliOsman/framedex/pull/114 | a096f85b2e56e21eda024c1ec92a456ed9d30b03 | CI 4/4 verde; PR mergeado en integracion/v1. |
| P01 | 0b | mergeado | https://github.com/KaraAliOsman/framedex/pull/117 | 023b8ba303b680ca50b6e10119ce4ee4514c9c38 | CI 4/4 verde; material v2, validación y evidencia antes/después aceptados. |
| IA1 | 0b | mergeado | https://github.com/KaraAliOsman/framedex/pull/118 | 2c9bbebc1cca6df125a4e0eeae14b22b71478b9e | CI 4/4 verde; 26 casos aislados, línea base MiMo 3/26 y MOCK 0/26, 48 regresiones de oráculos. |
| D01 | 0b | mergeado | https://github.com/KaraAliOsman/framedex/pull/119 | d8fbe5071fdb346555f7ef4df3e91160cfb5dfe0 | CI 4/4 verde; cinco series cotizables, revisión/undo, 936 pgTAP, 274 RLS, 11 E2E y 28/28 mutaciones. |
| D02 | D1 | mergeado | https://github.com/KaraAliOsman/framedex/pull/120 | 407f4ffd609a2dd4536e3e3c765eb7117c69715f | CI 4/4 verde; recetas con autoridad, reglas con fuente, 12 OT y 24 etiquetas, 959 pgTAP, 280 RLS, 11 E2E y 28/28 mutaciones. |
| D03 | D1 | pendiente |  |  |  |
| D04 | D1 | pendiente |  |  |  |
| D05 | D2 | pendiente |  |  |  |
| D06 | D2 | pendiente |  |  |  |
| D07 | D2 | pendiente |  |  |  |
| IA2 | D2 | pendiente |  |  |  |
| IA3 | D2 | pendiente |  |  |  |
| P02 | 1 | pendiente |  |  |  |
| P25 | 1 | pendiente |  |  |  |
| P04 | 1 | pendiente |  |  |  |
| P05 | 1 | pendiente |  |  |  |
| P09 | 1 | pendiente |  |  |  |
| P07 | 1 | pendiente |  |  |  |
| P03 | 1 | pendiente |  |  |  |
| P12 | 1 | pendiente |  |  |  |
| P17 | 1 | pendiente |  |  |  |
| ED1 | ED1 | pendiente |  |  |  |
| P06 | 2 | pendiente |  |  |  |
| P08 | 2 | pendiente |  |  |  |
| P13 | 2 | pendiente |  |  |  |
| P15 | 2 | pendiente |  |  |  |
| P11 | 2 | pendiente |  |  |  |
| P14 | 2 | pendiente |  |  |  |
| P16 | 2 | pendiente |  |  |  |
| ED2 | ED2 | pendiente |  |  |  |
| P21 | 3 | pendiente |  |  |  |
| P10 | 3 | pendiente |  |  |  |
| P22 | 3 | pendiente |  |  |  |
| P23 | 3 | pendiente |  |  |  |
| D08 | 3 | pendiente |  |  |  |
| P19 | 3 | pendiente |  |  |  |
| P18 | 3 | pendiente |  |  |  |
| P24 | 4 | pendiente |  |  |  |
| P20 | 5 | pendiente |  |  |  |

Arranque completado: PR [#116](https://github.com/KaraAliOsman/framedex/pull/116), squash `739704ab8f81ded8f860d44d44adba0c33f96db4` en `integracion/v1`; cuatro checks de CI PASA. Los cuatro commits locales se trasladaron conservando el arreglo de P00 y la evidencia preparada del fixture. `main` local no se modificó.

Ola 0b cerrada: P01, IA1 y D01 integrados con sus cuatro checks verdes.
P01 deja tokens, formatos exactos, primitivas y guardas; IA1 mide MiMo 3/26 y MOCK 0/26 sin atribuir reparaciones pendientes.
D01 separa familias y autoridades, preserva datos históricos y conecta plantilla/IA con diff, revisión, publicación y deshacer reales.
Capturas clave: `docs/redesign/captures/sistema-diseno/`, `diagnostico-evals/` y `sistemas-catalogo/`; catálogo D01 sin hallazgos nuevos.
Riesgos: catálogo DEMO sin certificación, escaneos sin OCR verificado y dominio D02–D07/IA2–IA3 pendientes de su propia aceptación.
