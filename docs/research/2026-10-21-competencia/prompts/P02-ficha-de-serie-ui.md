# P02 · Catálogo en la interfaz: fabricantes, series y ficha editable

**Rama:** `gpt/dk2-p02-ficha-serie` · **Depende de:** P01 · **Siguiente:** P03

## Objetivo

Que el dueño del taller vea y edite su serie como una **hoja de cálculo clara**,
con el origen de cada valor a la vista y los pendientes en una franja con acción.

Especificación: `03-catalogo-y-calculo.md` §1–§3 y `04-experiencia-y-diseno.md`
§3.4. Mockup de referencia: `mockups/Serie.dc.html` (cópialo en jerarquía, espaciado
y textos).

## Qué construir

1. **Catálogo › inicio:** lista de fabricantes con logo (o monograma) y sus
   series; buscador en píldora; botón **Agregar serie** (desde biblioteca,
   desde plantilla, desde cero). Las series DEMO sintéticas se mueven a una
   sección **Ejemplos** plegada al final; no aparecen en indicadores ni en el
   selector de serie del editor salvo que el usuario active «Mostrar ejemplos».
2. **Ficha de serie:** cabecera (fabricante, nombre, etiqueta de nivel con
   texto humano, botón **Ventana de prueba**), franja de pendientes («3 valores
   sugeridos por confirmar antes de fabricar · Ir al primero»), y seis pestañas:
   Perfiles · Reglas · Herrajes · Vidrios y colores · Tipologías · Precios.
3. **Tabla editable reutilizable** (`frontend/src/ui/`): celdas numéricas con
   `Decimal` en texto y formato chileno (coma decimal), navegación por teclado
   (flechas, Enter, Tab), **pegar desde Excel** (bloques de celdas), deshacer de
   la última edición, guardado en lote con indicador «Guardado», validación en
   línea junto a la celda que falla con la corrección propuesta. Columna
   **Origen** con punto de color + texto: «Del manual · pág. 14», «Taller · Juan,
   21-10», «Sugerido» con botón **Confirmar**. Historial al abrir la celda.
4. **Confirmar en lote:** seleccionar filas sugeridas → Confirmar.
5. **Lenguaje:** aplica el glosario de `04-experiencia-y-diseno.md` §4 en todo
   Catálogo. Prohibido en pantalla: «autoridad», «sellado», «fuente»,
   «procedencia», «Sin dato», «Referencia · no cotizable».

## Criterios de aceptación

- [ ] Capturas 1440 × 900 y 390 × 844 de Catálogo y de cada pestaña, comparadas con el mockup.
- [ ] e2e: abrir PRO6004 → pegar 5 filas desde portapapeles en Reglas → confirmar
      2 sugeridos → el nivel y la franja se actualizan sin recargar.
- [ ] `break-ui`: serie con 300 perfiles, nombres de 80 caracteres, valores con 4 decimales.
- [ ] Teclado completo en la tabla; foco visible; contraste AA.
- [ ] Búsqueda de las palabras prohibidas en `frontend/src` (excluye tests y
      generados) devuelve 0 en Catálogo; agrega una regla en
      `scripts/check_guards.py` que impida reintroducirlas en textos de interfaz.
- [ ] `make lint typecheck test build` en verde; wiki y ESTADO.md actualizados.
