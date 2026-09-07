# PRD-20: CATÁLOGO GLOBAL Y MODERACIÓN ADMINISTRATIVA (v1.3 MASTER)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.3 MASTER (Preservación Normativa SHOT-20 / Pantalla S28)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Comunidad y Red)  
**Bloquea a:** Ninguno

---

## 1. Misión del Catálogo Global Comunitario

Permitir que las organizaciones publiquen sus sistemas de perfiles verificados (`is_global = TRUE`) para que cualquier taller en la plataforma pueda utilizarlos sin tener que compilar el catálogo desde cero.

---

## 2. Flujo de Moderación y Cola de Aprobación (Capacidad S28)

La pantalla/superficie **S28** (`/admin/queue`, rol exclusivo: `SUPERADMIN`) administra la cola de series enviadas por los usuarios para su publicación global.

```
[ Taller solicita publicar serie ] ──► [ Cola de Moderación S28 ] ──► [ QC Dimensional ]
                                                                             │
[ Publicación Global is_global=TRUE ] ◄── [ Doble Firma Admin ] ◄── [ Test G-Cases 0.00mm ]
```

### Reglas de Blindaje de Precios
- **Aislamiento Estricto:** La publicación global solo incluye geometría de perfiles, matriz de junquillos y kits de herrajes. **Los precios, listas de costo y proveedores son estrictamente privados y jamás se transfieren al catálogo global**.
- Los superadministradores **no pueden** consultar las listas de costo privadas de ningún tenant desde la cola S28.
