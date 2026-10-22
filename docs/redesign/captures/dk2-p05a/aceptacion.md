# P05a · Navegación por rol

Revisión local del 22-10-2026 en `gpt/dk2-p05a-navegacion`, sobre P04g.
Stack sintético propio: Supabase 25421, API 8010 y build de producción 5175.
No se modifica REVIEW. Los usuarios, catálogos y empresas son de ensayo.

## Alcance ejercitado

Hoy es el inicio de los cinco roles. Dueño, vendedor y jefe de taller ven
Hoy, Obras, Taller, Catálogo y Empresa. Operario e instalador ven Hoy y
Taller, con sus herramientas autorizadas. Cada ruta conserva la autorización
del backend. La búsqueda incluye Clientes para oficina y la ruta `/clients`
continúa disponible; no se agrega un sexto destino.

Empresa contiene Informes y Funciones avanzadas. Esta última enlaza a CNC,
cohortes/cierres, rectificación y precios según el rol. Los enlaces abren
herramientas existentes, donde se selecciona la orden, obra o visita concreta.
La enmienda de Constitución §5.1/5.2 registra el encargo vigente.

Esta sub-PR cambia el shell y las direcciones. El nuevo contenido de Hoy,
las etapas de Obras y el glosario global se completan en las siguientes
sub-PR P05. `/quotes` mantiene temporalmente su índice y todos sus filtros
para conservar el seguimiento mientras se integra en la lista única.

## Comparación con Hoy/Obras.dc.html

| Antes                                                     | Después                                          | Motivo                                                            |
| --------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------- |
| Proyectos, Clientes, Catálogos, Taller                    | Hoy, Obras, Taller, Catálogo, Empresa            | Orden y nombres del mockup; Clientes queda en la búsqueda         |
| Inicio diferente por rol                                  | Hoy con acceso directo a taller/agenda           | Una entrada para las acciones pendientes, sin quitar herramientas |
| Analítica y listas comerciales como secciones principales | Informes y Funciones avanzadas dentro de Empresa | Mantener el rigor accesible sin ocupar el recorrido cotidiano     |

Se conserva el riel de 232 px, fondo, tipografía, control de búsqueda y color
de selección del sistema vigente. En 390 px se convierte en drawer con
Escape y restauración de foco; no se comprime el contenido bajo el riel.
Las capturas de navegación muestran el contenido anterior de Hoy: todavía
no representan la aceptación final de esa pantalla.

## Evidencia por rol

| Rol            | 1440 × 900                                                                                         | 390 × 844                                                                                        |
| -------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Dueño          | [Navegación](owner-1440-navigation.png) · [Avanzadas](owner-1440-advanced.png)                     | [Navegación](owner-390-navigation.png) · [Avanzadas](owner-390-advanced.png)                     |
| Vendedor       | [Navegación](estimator-1440-navigation.png) · [Avanzadas](estimator-1440-advanced.png)             | [Navegación](estimator-390-navigation.png) · [Avanzadas](estimator-390-advanced.png)             |
| Jefe de taller | [Navegación](workshop-manage-1440-navigation.png) · [Avanzadas](workshop-manage-1440-advanced.png) | [Navegación](workshop-manage-390-navigation.png) · [Avanzadas](workshop-manage-390-advanced.png) |
| Operario       | [Navegación](operator-1440-navigation.png)                                                         | [Navegación](operator-390-navigation.png)                                                        |
| Instalador     | [Navegación](installer-1440-navigation.png)                                                        | [Navegación](installer-390-navigation.png)                                                       |

`navigation.spec.ts` usa Magic Link real y TOTP para el dueño, con la membresía
real de cada rol. El seeder conserva su prueba de propiedad: prepara el tenant
como dueño y solo después la fixture cambia su propia membresía al rol del
ensayo. Ninguna credencial de servicio entra al navegador.

Diez recorridos pasan en ambos tamaños; comprueban destinos, activo, Clientes
en la paleta, direcciones conservadas y denegación de funciones a operario e
instalador. Axe A/AA/2.1 AA cubre riel, cabecera y pantalla avanzada; sin
desborde de página. Se conservan 16 capturas. Los extremos de 500 obras y
las métricas de Hoy/Obras se registran al cerrar sus sub-PR funcionales.

Validación final: los diez recorridos vuelven a pasar tras comprobar también
el filtro de búsqueda de `/quotes`; 1.184 pruebas frontend en 108 archivos,
ESLint, TypeScript, guardas, Prettier y build de producción aprobados.
