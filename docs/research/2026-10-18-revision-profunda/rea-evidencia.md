# REA: evidencia real y límites

18-10-2026. REA se usó para renderizar páginas públicas y analizar dos fragmentos JavaScript públicos de WindowCC/WindoorCraft. No se usó para sustituir la lectura normal del repositorio DEKOPEN ni se atribuye acceso a software industrial privado.

## Capturas de navegador

`capture_browser_scenario` lanzó Edge con viewport declarado, abrió páginas públicas y retuvo screenshot, DOM, accesibilidad y URL. El índice local `.run/revision-profunda/rea/capturas-index.json` contiene **16 registros** con ID de evidencia y huella de la captura, no 16 programas distintos. Algunas son la misma página antes/después de cookies o popup.

Se conservaron páginas de NuveraPRO, Winart, WinMaker, Klaes, Logikal, RA, FeneVision, Matrix, Windowmaker y WindowCC, además de un intento de PrefSuite con challenge. La [selección visual](evidencia-visual.md) distingue página comercial, imagen de manual y galería ejecutada. Rechazar cookies/cerrar popup solo acredita acceso al contenido; no una función del producto.

Ejemplo: Nuvera primeros pasos, evidencia `ev_d77bfcda4cd2c5149619bc0bd213a1ee7dea30bcd00de8be8866e2697291d66f`. WindowCC cargó una galería funcional en canvas, pero los intentos posteriores de cambiar a 3D no entregaron una captura de éxito y tuvieron que abandonarse por timeout. **No se declara probado su botón 3D, deshacer o importación.**

El bundle de exportación quedó en `.run/revision-profunda/rea/evidence-bundle.json`; `extract_evidence.py` extrajo PNG/DOM/AX y verificó SHA256. No se incorpora el bundle ni DOM minificado al repositorio como documentación pública. El JSON visual guarda una selección de evidencia con origen y límites.

## Análisis estático de artefactos públicos

Los scripts se obtuvieron de URLs observadas en la página pública. Proveniencia en `.run/revision-profunda/rea/public-windoorcraft/sources.json`. No se buscaron credenciales ni se accedió a endpoints privados.

| Artefacto | Bytes | SHA256 |
|---|---:|---|
| `app.dcd63620.js` | 88 953 | `6701051f2fa84319feb85939a189f4dd0f8f21398a6f3a600234149fd5265f0e` |
| `chunk-7941a2dc.a7fa4450.js` | 6 129 | `9e457fb7d0c61d5af55d2df29403051eae9d2c39d66a5d6840db6332b6a02b61` |
| `chunk-044f6f92.f59d46e6.js` | 2 533 205 | `066bfd692b30bcde84d0461e713a064d84ae9d53c323b660060037e764cedf6d` |

La llamada exitosa a `analyze_javascript_application` incluyó los **dos primeros archivos**, límite 20 segundos, 3000 nodos semánticos globales/2000 por archivo y 768 MB de heap. Retuvo 95 082 bytes, parseó 2 archivos, visitó 6619 nodos AST y produjo 19 findings. Esos conteos de AST no significan cobertura completa del grafo semántico.

- Evidencia padre: `ev_da9ed71d4e6e56dc7112ef7d5ed2e11f8c8ae07c4706e66f56eda58eaa42b019`.
- Vista de resumen: `ev_967b21b5667ac527aaaa70b7ed2f9bb4b8965e90c34d7173bbd5627220927ee5`.
- Huella del artefacto raíz en esa evidencia: `e46e8e31bb91af1f11f44098aa74b13b15b5d9da2ff16ba92e0aeedf90b427e2`.
- Extracto local: `.run/revision-profunda/rea/public-analysis-summary.json`.

Se identifican declaraciones de rutas como `/gallery`, `/market`, `/pricing`, `/license`, `/privacy`, `/home`, `/develop-platform` y `detail/:product_id`. Esto respalda separación del shell público entre edición/galería, oferta y plataforma. Una ruta en JS **no acredita autorización del servidor, persistencia de datos, calidad de un módulo ni que todo su código se ejecute**.

La cobertura se marcó **parcial**, con límite del grafo semántico y desconocidos. El campo de exportación no truncado no convierte el análisis en completo. El intento sobre el chunk grande de geometría agotó su tiempo; dejó evidencia parcial `ev_7bd1edaec2e58260690b681493572e93cb0480ee949bd57b72dec6b80224bb5c`. No se reconstruyeron fórmulas, algoritmos de corte, compatibilidades físicas ni validación de manufactura.

## Conclusión utilizable

REA aporta trazabilidad de lo que realmente se cargó y una lectura parcial del shell entregado al navegador. Las lecciones de producto son galería ligada al editor, separación de tareas y acceso a configuraciones. DEKOPEN debe implementar esas capacidades con su propio modelo y motor, no copiar artefactos ni convertir inferencias de JS en autoridad industrial.

Los manuales y fuentes primarias aportan mucho más detalle del flujo industrial que el shell minificado. Mantener esa distinción permite investigar con profundidad sin fingir una ingeniería inversa de quince aplicaciones completas.
