# DEKOPEN — PLAN DE RESOLUCIÓN DE DUPLICACIONES NORMATIVAS (v1.3 MASTER)

> **Estado:** Documento Oficial de Gobernanza Documental
> **Ámbito:** Repositorio Dekopen (`KaraAliOsman/framedex`)
> **Mandato Owner:** Cero Duplicados Constitucionales, Una Sola Constitución (`docs/CONSTITUTION.md`), Cero Pérdida de Información Única.

---

## 1. Mandato Constitucional de Autoridad Única

Por directriz explícita del Owner:
1. **Una Sola Constitución:** Existe una única autoridad constitucional en el repositorio:
   👉 [`docs/CONSTITUTION.md`](../CONSTITUTION.md) (v1.3 MASTER, 23 Reglas Supremas).
   Se eliminó por completo el duplicado secundario `docs/PRD/CONSTITUTION.md`. Queda prohibido volver a bifurcar o crear constituciones secundarias.
2. **Punteros de Redirección Limpia:** Los 22 archivos PRD que residían en la raíz de `/docs/` se han convertido en punteros normativos unificados hacia `docs/PRD/`.
3. **Consolidación de Contenido Único sin Pérdida:** Toda especificación única detectada en archivos de raíz antes de convertirlos en punteros fue transferida a su destino canónico antes del sellado:
   - Esquemas JSON tipados de Tools T2 (`modify_dimensions`) y T3 (`bulk_discount`) $\rightarrow$ consolidados en [`docs/PRD/PRD-10.md`](../PRD/PRD-10.md).
   - Especificaciones de extrusión 3D procedimental, cinemática y shaders $\rightarrow$ consolidados en [`docs/PRD/PRD-12.md`](../PRD/PRD-12.md).
   - Catálogo Global y Moderación Administrativa (Pantalla S28) para SHOT-20 con blindaje de precios $\rightarrow$ preservado en [`docs/PRD/PRD-20-CATALOGO-GLOBAL.md`](../PRD/PRD-20-CATALOGO-GLOBAL.md).

---

## 2. Jerarquía Inequívoca de Autoridad de Fuentes

```text
1. /docs/CONSTITUTION.md (v1.3 MASTER)
   └─► Norma Suprema Inapelable (ÚNICA CONSTITUCIÓN DEL REPOSITORIO).

2. /docs/PRD/PLAN_SHOTS.md (v1.3 MASTER)
   └─► Roadmap y Criterios de Cierre de Shots Oficiales (SHOT-01 a SHOT-24).

3. /docs/PRD/*.md (v1.3 MASTER)
   └─► Especificaciones Funcionales Atómicas Canónicas (ÚNICA FUENTE DE VERDAD PARA PRD).

4. /docs/plans/PLAN_SHOT-XX.md
   └─► Registro Inmutable de Decisiones y Contratos de Shots Cerrados (SHOT-01 a SHOT-06).

5. Compilaciones y Biblias Concatenadas (/docs/DEKOPEN_BIBLIA_*.md)
   └─► GENERATED VIEW / SNAPSHOT (NO NORMATIVO).

6. Archivo Histórico (/docs/archive/**)
   └─► HISTORICAL RECORD (CERO AUTORIDAD NORMATIVA ACTIVA).
```

---

## 3. Matriz Exhaustiva de Consolidación de los 22 Archivos PRD

| Root file | Canonical candidate | Identical | Unique root content | Unique canonical content | Classification | Action |
|---|---|:---:|---|---|---|---|
| `docs/PRD-00.md` | `docs/PRD/PRD-00.md` | No | Ninguno (borrador preliminar sin D29/D30) | Decisiones D1–D30 completas, 2-tier dependencies, precedence rule | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-01.md` | `docs/PRD/PRD-01.md` | No | Ninguno (borrador 13.8 KB vs 47.4 KB canónico) | Fixture DEMO_60 completo, hardware kits, glass matrix, casos G1–G12 | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-02.md` | `docs/PRD/PRD-02.md` | No | Ninguno (DDL antiguo) | DDL completo PG16/PG17, RLS `current_user_org_ids()`, tablas audit | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-03.md` | `docs/PRD/PRD-03.md` | No | Ninguno (esbozo auth simple) | Paddle Global (USD MoR), Flow (CLP), ledger idempotente, webhooks HMAC | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-04.md` | `docs/PRD/PRD-04.md` | No | `width_mm: number` obligatorio en todos los vanos | `width_mm?: number` opcional para vanos hijos, modelo recursivo split | Superseded minor text | Convertido a puntero normativo |
| `docs/PRD-05.md` | `docs/PRD/PRD-05.md` | No | Ninguno | Motor de costos 5 modos extendido, frontera matemática SHOT-06/SHOT-08 | Strict superset in canon | Convertido a puntero normativo |
| `docs/PRD-06.md` | `docs/PRD/PRD-06.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-07.md` | `docs/PRD/PRD-07.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-08.md` | `docs/PRD/PRD-08.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-09.md` | `docs/PRD/PRD-09.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-10.md` | `docs/PRD/PRD-10.md` | No | Esquemas JSON tipados para Tool T2 (`modify_dimensions`) y Tool T3 (`bulk_discount`) | Action-First Command Bar, protocolo Undo sagrado | Active normative unique content (schemas) | **Migrado contenido único a `docs/PRD/PRD-10.md`**; raíz convertido a puntero |
| `docs/PRD-11.md` | `docs/PRD/PRD-11.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-12.md` | `docs/PRD/PRD-12.md` | No | Extrusión 3D procedimental, cinemática de apertura (giro, oscilo, corredera), shaders | Enlace público `/view/`, tokenless bundle, exportador CAD 2D DXF | Active normative unique content (3D & kinematics) | **Consolidado en `docs/PRD/PRD-12.md` (v1.3 MASTER)** para SHOT-19; raíz convertido a puntero |
| `docs/PRD-13.md` | `docs/PRD/PRD-13.md` / `docs/PRD/PRD-20-CATALOGO-GLOBAL.md` | No | Catálogo Global y Moderación S28 (SHOT-20) con blindaje de precios | AI Gateway, white-label routing, credit caps, fallbacks (SHOT-13) | Active normative unique content (displaced module) | **Preservado en `docs/PRD/PRD-20-CATALOGO-GLOBAL.md`**; SHOT-20 actualizado en PLAN_SHOTS; raíz convertido a dual pointer |
| `docs/PRD-14.md` | `docs/PRD/PRD-14.md` | No | Ninguno (borrador v1.1) | Verificación doble ciego multi-modelo (T8), sello DOC-08, QR | Superseded minor text | Convertido a puntero normativo |
| `docs/PRD-15.md` | `docs/PRD/PRD-15.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-16.md` | `docs/PRD/PRD-16.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-17.md` | `docs/PRD/PRD-17.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-18.md` | `docs/PRD/PRD-18.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-19.md` | `docs/PRD/PRD-19.md` | No | Ninguno (borrador v1.1.0) | NFR maestros v1.2 sellados, SLOs de latencia, retención de auditoría | Superseded minor text | Convertido a puntero normativo |
| `docs/PRD-ANIMATIONS-INTERACTIONS.md` | `docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md` | No | Ninguno | Feedback táctil/auditivo para tablet de taller, microinteracciones framer-motion | Strict superset in canon | Convertido a puntero normativo |
| `docs/PRD-FRONTEND-APIS-COMPONENTS.md` | `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` | No | Ninguno (borrador sin tipos de SHOT-04/05/06) | Firmas de componentes Canvas 2D, contratos SVG split nodes, tipos frontend | Obsolete subset | Convertido a puntero normativo |

---

## 4. Auditoría Forense de Hashes SHA-256 (Before vs After)

Base canónica evaluada: `39005492b8dbd5f7a3b90f76876a0ad6e63f3714`
Rama de reforma: `normative-capability-cleanup`

| Archivo en Raíz `/docs/` | SHA-256 Base (`3900549`) | SHA-256 Actual (Puntero Reformado) | SHA-256 Canónico Activo (`docs/PRD/`) |
|---|---|---|---|
| `docs/PRD-00.md` | `f43b8e217cda3bab0380ffccefbc3b1ae6465c7d70a6df48aabffa6df0fae840` | `8c6e48417583f0a783e3312096a7b18d74204db34e7f5a22ad13d1acd15e22a2` | `b00d966009af43b5cf4c87701a1bdc730cb871461c81994e4f65ac76000b1781` |
| `docs/PRD-01.md` | `824d33be065e2bf05b628e915fe3d6e2cc3b9788e0ce9c4795305adc4c6da80c` | `3aec399dc5ee2e2d50095a85c1b85532312b76699057fa52a47207435a3a03b6` | `c26e8e711edd70eebc3a6ac1d1da12166423781ddc5cd69c7125e1525ca072b6` |
| `docs/PRD-02.md` | `bc6d43088dc3511c5160b3cef9d8fd5d31135fc2ac9d9237bd4ddd7fc22c39f6` | `acb521ba0dd7d29dace44567dcbd6957a1a5db136f3b23e6c9dd7327e0584068` | `666f668b0421fc47bea9d8b06378d335d509869a89d5f5350bdb4400e71d2f0b` |
| `docs/PRD-03.md` | `6acd37d2b580af3d0119017c81d08230fb3950f1b3f2e73abd12f50c3fac8fed` | `771aed969b15cba34d7ad19e7def8256dfaecdd8ef4c9598568cda770bc7e6a0` | `962a329d75bcebd37de1cff7ada6eef303b0dcd762ee30aa97871b7830a882cb` |
| `docs/PRD-04.md` | `c6b97f45ed0d7a75543c071b4e0a5b2bb3f0b358a5641c84cd9aa338a4e6ffa2` | `ea3aadd28b871e0f431f3fb8a4a0d45d95cb1643d97c545a12f33b5972a06edd` | `772a62f02ccf352e06fc0e7020a940419b3142cdebd3281155a4b8720af98cbc` |
| `docs/PRD-05.md` | `a499bb79ec0cbd73c67ff94ea4fc780a1e2978efbd30197c2d9394c755dd9fcc` | `6e1dee35ad8a935b1eb85181d1b9d0b64e32a5b7904a299b6968ad345cf31573` | `0b87c8c16299f29d646fdfb6d10e3960e0e39d76031b7169b2cb06213322b378` |
| `docs/PRD-06.md` | `865749db44bc78bf43865a51aeecc8ae0cc71f82f9d48431f4e56c686b72bca9` | `0f84a0d6283d38e9d6302e2a3b606ee28791b897dd1efa79a7b8198c46a3f97c` | `d9fbd6cbe9eccba233cfeb146c0195129f2a8f0df2a0c40c755c0a26b46dcd80` |
| `docs/PRD-07.md` | `c8724d24dd9e8976a354984c05d17a71228888b2dafd1a43730151c5da67b7e2` | `13bc39f78a2acd0c973eac34b39a620b182acd27774700c4e602a86e84b960fd` | `4bad02371886827f83e59504e3750f6fa216f4009cf09110cc7925d872b5f7d2` |
| `docs/PRD-08.md` | `04bfef8209fd31562b3320841ef2e3940569aa2a92f6731b98e21229be127466` | `55f825d336151958590b3431be5141ada3dd92979ba598e9c1b94c0a97c71df0` | `ad9418e7d06f1bee346482f2fa12fcb3eae268e23c5755716a0edfb85bb0aec6` |
| `docs/PRD-09.md` | `287a6fd2bc72e3c2070477f187d1879bc1b1f25293a6512268166078386d987f` | `3ffc7f7ec3d2499ac09c322956e2410a9899a71ec6598b4f048a5079171dfa5b` | `16601e31f80f491bb2d0f8aed756883cf4004cdb444e4b53b2e6311f9fd47266` |
| `docs/PRD-10.md` | `18bf30c05f5faae4d2a0c1882523259c3dfed7593b2ed37df705f27596d6ba62` | `0a8cd22822e2abc49c8da1a36357ca6ae8f59835d28b1c9258eff70e66f03461` | `fd18211ad2e8ed17faea096770effb6f74ff2ba83e7b75641d2a7cb0f1e562f3` |
| `docs/PRD-11.md` | `a9fecc34b9e8e5887341b78d62a4199f54727d7698c3caae8f718716eea5456a` | `5e63c279ebf8e9ad623d51f14ba34e74f18186d49da4ae7704aaa6ac2225c9a3` | `a4025adcf01712c65eb5f5b03cd0e01cd009db02e2e8fb78a6ccf9b771ca9590` |
| `docs/PRD-12.md` | `8c7fcba1e2a2ff75db15bf68d8df5a944ad89a7da9331d34f25476274969d805` | `2d9de462a28139b2672f479b5b7299ebc31fd10339f9b3a94e97e2d580a19b93` | `bbedaf29b77ee18cdac067380a72a9eba92aeb03ab463342428fe6969fb679c5` |
| `docs/PRD-13.md` | `f4258ac98bb2e6206a7d377dc290213945dbe5acdfa43a121c2a74bcde777810` | `63e17c6d47cebd18fa9e7dd0e58be3579d6058a9862b3f03ca6980b0db2510a8` | `b5815dbd1d7ca657312b9962e973081323ed8857597b2a73ee9815f9d266fc9d` |
| `docs/PRD-14.md` | `96dc6b3ad5ea934b3e1dbaee1ef9a65d3641d5800e42525419bad4fa3101b382` | `188ef45ec8ee9d87e31913d01398467e98c4a29f72161d6254a95cb06bb0804d` | `5ca4b19663a74f4a8fd7b08f235ae905956058b361082505dbed37e7e95b1052` |
| `docs/PRD-15.md` | `bf3675c1c53a9a67371506fab6be2c6f630a1911b52f913de28e4dbf5afb5602` | `6e16f6b05f4d41446357e047a9e6524ff8363c4754ddfc90976de5dfda0714e0` | `c9cb69fa3d6112be0acad1ccbea14962ca06a5aec4f902f9cc8c6d47a5900dcb` |
| `docs/PRD-16.md` | `7d4fc9bfb5162b41ccf012717d20745dd01a3ff6d18ff03f48b1e68aa9614eaf` | `4a742d711339b2e3dbeac29033f385df44f8041cc877880008ab8b7d829f16e4` | `f57ba556410ea18763f3f7ff77f8d7742d4f143d932bfc527e0d57028f054f33` |
| `docs/PRD-17.md` | `2dc43ccfa56a1a63c6500ef4b3a2576a6f524a30cea6a43480ef23c7e3e32920` | `eb216e069f502aa9d1d0164db518ecd28952df25cf27127988f60d5a10afc14c` | `8fc2ba1157ef850018ad85ef6f45e153df03ac23196b44329429f46f434255e4` |
| `docs/PRD-18.md` | `920d48bb36e59bcbe888c268a2805dd39e02d478b3be6f5db7e4cf3c471fead1` | `fcbbb3bc0908baaafbe1b8a5c23d9beb2e3d5cb412a8ec51079383b09aeff142` | `eb792794f907836cb82de7dec05771680d33977944a60728d62ff68a91981f4d` |
| `docs/PRD-19.md` | `c15c24f4a37f9a500ba3df8985a3d6e30d6cbe1290cda830b688a01eed73f0ac` | `a146eba5a289c311dbb5540f246804db10cef1f30fcb587250f241b27ec9d101` | `d73c4ab8b6a65332197dc01ed3c217dc12a34a0e881dd38bb1afc6ea7789010a` |
| `docs/PRD-ANIMATIONS-INTERACTIONS.md` | `943fcbc9a4f13bad828fcab9577115142370aad51f30708c21e7ca96f1092f10` | `97571a6832db9b268420103c013b36cf8b2279ebeaf9d51ceed8a785d6b0f670` | `3942350fc7c624eb6840143ce856519646e943bc3b416d0d4b88ce8eccd563fe` |
| `docs/PRD-FRONTEND-APIS-COMPONENTS.md` | `7be7c61ed7c2d6b1028b606ff1ec28f094c9543772f55428ada3c250cca55646` | `bc43c70b82194cd6dbf3c74fb34d1e7ab00beeaa5c029f4995a40606e16df26c` | `e2af7bc4616502accf08e9492d60b0c22bda9d7b7b1d89110bc5c76fbc2cb290` |

---

## 5. Auditoría de Archivos de Configuración de Agentes

Se auditaron todos los archivos de configuración de agentes y contexto del repositorio:

1. [`.cursorrules`](../../.cursorrules):
   - Actualizado a v1.3 MASTER.
   - Referencia explícitamente las **23 reglas** de `docs/CONSTITUTION.md`.
   - Cero duplicación o fork de reglas constitucionales.
2. [`.codexrules`](../../.codexrules):
   - Actualizado a v1.3 MASTER (2026 Loop Engineering Standard).
   - Invariante fijado en `docs/CONSTITUTION.md (v1.3 MASTER — 23 Rules)`.
3. [`AGENTS.md`](../../AGENTS.md):
   - Sección 4 sincronizada con Constitución v1.3 MASTER (23 Reglas Supremas).
   - Tech-neutralizado el visor 3D para SHOT-19.
4. [`README.md`](../../README.md):
   - Tabla de documentos apunta a `docs/CONSTITUTION.md` (23 reglas, v1.3 MASTER).
5. [`docs/PLAYBOOK_SHOTS.md`](../PLAYBOOK_SHOTS.md):
   - Procedimiento de ejecución alineado con lectura JIT de `CONSTITUTION.md` + `docs/PRD/PRD-{XX}.md`.

Búsqueda en todo el árbol de Git (`git grep -i "22 reg" / "21 reg"`):
- `21 reglas`: Únicamente presente en el snapshot archivado `docs/archive/BIBLIA-v1.1.2-SEALED.md` (registro histórico no normativo).
- `22 reglas`: Erradicado de todos los archivos activos.
- `23 reglas`: Estandarizado en el 100% de los archivos normativos y de agentes.
