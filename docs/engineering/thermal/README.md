# Cálculo térmico y alcance OGUC

El motor calcula Uw con áreas visibles, no con las medidas de corte del vidrio:
`(ΣAg·Ug + Af·Uf + Σlg·Ψg) / (Ag + Af)`. Usa `Decimal` con precisión local de
50 dígitos y no redondea entradas ni resultados intermedios. La presentación
redondea; los informes sellados conservan la traza exacta.

## Autoridad

Uf necesita la combinación exacta de perfiles; Ug y g necesitan el vidrio y su
composición; Ψg necesita ese vidrio, separador y perfiles. Las fuentes registran
documento, URL, página, laboratorio, norma, fechas, rango de dimensiones y
aperturas. El servidor liga catálogo y composición. Una revisión humana válida
no promueve datos sintéticos, vencidos, contradictorios ni de otro catálogo.

Las clases de aire, agua y viento se ligan además a la huella física del producto
ensayado: dimensiones, distribución, aperturas, vidrio y herraje. La selección
de una posición reproduce el espécimen; el servidor calcula su huella. El
alcance conservador acepta solo esa construcción exacta. Declarar un rango en
el informe no autoriza extender una clase a otra medida o tipología. Un ensayo
sin esta ligadura queda Sin dato. Aire requiere 100 Pa, NCh3296/3297 e inscripción
MINVU del laboratorio declarada y cotejada por el revisor.

Geometrías con solapes de paños, rellenos opacos o conjuntos sin un método
implementado quedan Sin dato. Uf y Ψg se aplican solo a combinaciones cubiertas;
el alcance dimensional de todos los informes se contrasta conservadoramente
con la medida completa de la ventana. No se extienden ensayos por semejanza.

## Normativa verificada

[Transcripción con citas y hashes](oguc-ds15-transcripcion.json) conserva las
tablas 3, 9, 12 y 16 del DS15/2024, publicado en el Diario Oficial del 27-05-2024
y vigente desde el 28-11-2025. Se cotejaron las páginas originales rasterizadas
con OGUC consolidada MINVU de marzo de 2026: páginas PDF 254, 262, 267 y 272.
Las fuentes descargadas para cotejo permanecen locales; el repo incluye la
transcripción de los datos y sus citas, sin redistribuir las publicaciones.

Oriente y Poniente se evalúan por separado. Gobierna el mayor Uw de cada grupo,
sin promediar ni interpolar columnas. El denominador incluye vanos y medianeros.
OGT se deriva cuando la superficie expuesta es menor del 60 % de los muros.
Salud, educación y hoteles conservan su tabla propia; techumbre conserva su
exigencia independiente. No se deduce la zona por comuna.

El responsable declara alcance normativo, uso, fuente de zona, memoria de
cálculo cotejada con NCh3137/1 y /2, todas las ventanas y, cuando corresponde,
muros. Elegir orientación no declara fachada. El resultado solo evalúa ventanas;
no acredita condensación, ventilación ni cumplimiento del edificio. El plan
local de descontaminación debe cotejarse por el responsable.

## Revisión y documentos

El estimador y el dueño declaran envolvente; taller consulta. Dueño o encargado
de taller registran y revisan fuentes. SQL/RLS conserva org_id, separa tenants,
impide cambiar fuentes y sella las entradas al emitir. Revocar afecta cálculos
nuevos; el informe y el PDF emitidos permanecen byte a byte.

La alternativa recorre las combinaciones evaluables de vidrio y sistema del
catálogo visible. Solo ofrece candidatos que el motor acredita como Cumple y
que tienen precio; elige el menor precio total y muestra el Δ. Cualquier cambio
requiere simulación, revisión y clic humano; se puede deshacer. No promete un
mínimo fuera de ese catálogo ni suplanta datos faltantes.

El anexo DOC-01 es opcional. Las emisiones nuevas imprimen únicamente valores
del informe térmico sellado; no reutilizan un Ug declarado sin revisión en las
propiedades genéricas del vidrio. Las revisiones históricas conservan su
representación anterior. DEMO nunca se presenta como certificado.
