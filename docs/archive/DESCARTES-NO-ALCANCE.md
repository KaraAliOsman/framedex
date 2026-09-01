# REGISTRO DE DESCARTES Y FUNCIONALIDADES FUERA DE ALCANCE (V1)
**Estado:** Inmutable / Archivo de Control de Alcance  
**Referencia Normativa:** PRD-00 §5.4 y CONSTITUTION.md (Regla 20)

Este documento registra formalmente todas las ideas, conceptos o características exploratorias que quedan **ESTRICTAMENTE FUERA DE ALCANCE** para los 24 shots de Dekopen V1. La IA constructora tiene **PROHIBIDO** crear modelos, tablas, rutas, componentes o código para cualquiera de estos puntos.

---

## 1. Características Técnicas y Geométricas Descartadas

1. **Bow Windows / Ventanas en Bahía / Curvas:**
   - **Estado:** FUERA DE ALCANCE según PRD-00 §5.4.
   - **Instrucción:** NO construir. El motor `/engine` soporta exclusivamente: Fijo (FIXED), Proyectante (AWNING), Oscilobatiente (TILT_TURN), Corredera 2/3/4 hojas (SLIDING), y Puerta batiente/multipunto (DOOR).
2. **Conexión Directa a Maquinaria CNC / Tronzadoras Industriales (G-Code):**
   - **Estado:** FUERA DE ALCANCE (Postergado 18 meses a Fase Industrial / V2).
   - **Instrucción:** NO construir drivers, generadores G-code ni módulos CNC en el monorepo.
3. **Módulo de Realidad Aumentada (AR) / 3D Volumétrico Pesado:**
   - **Estado:** FUERA DE ALCANCE en V1 (Diferido a V2).
   - **Instrucción:** En V1 se utiliza exclusivamente el Canvas 2D Vectorial y el Enlace Web de Proyecto `/view/[token]`.

---

## 2. Nomenclatura y Modelos de IA Estándar

1. **Modelos de IA Canónicos:**
   - Para tareas de extracción visual y OCR de planos: **Gemini 1.5 Pro / Flash** (o OpenAI Vision según configuración en `.env`).
   - Para interpretación de comandos y estructuración: **OpenAI GPT-4o / GPT-4o-mini** (o LLM compatible estándar vía AI Gateway).
   - Cualquier nombre interno exploratorio (*Luna*, *Neural Core*, *Vision CAD*, *Titan Engine*, *Kimi*) queda archivado aquí como referencia de brainstorming conceptual y no representa dependencias obligatorias de código.

---

## 3. Normativa de Dibujo

- Las flechas y triángulos de apertura se rigen por la **simbología estándar de carpintería técnica**, sin implementar motores de validación de normativas extranjeras que no apliquen a Latinoamérica.
