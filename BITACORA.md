# Bitácora — App Correos Estudiantes

> Documento de contexto. Entrégalo al asistente al inicio de cada sesión para restaurar el contexto completo del proyecto.

---

## ¿Qué hace esta app?

Genera un **CSV listo para carga masiva en Google Workspace Admin** (Consola de Google).

Compara la nómina de alumnos del SIGE con la lista actual de usuarios de Google y determina qué cuentas hay que:
- **Crear** — estudiantes nuevos sin correo
- **Mover** — estudiantes que cambiaron de curso (cambia la Unidad Organizativa)
- **Reactivar** — cuentas suspendidas que vuelven a estar activos en el SIGE

---

## Repositorio

- **GitHub:** `https://github.com/lll-ghac/Goo-SIGE-ImporEstudiantes`
- **Rama principal:** `main`
- **Deploy:** Streamlit Community Cloud → `https://goo-sige-imporestudiantes-[hash].streamlit.app`

---

## Estructura de archivos

```
APP/
├── app.py                          ← Router de navegación (st.navigation)
├── pages/
│   ├── E_Ecuador.py                ← App original E-79 ESCUELA ECUADOR (NO TOCAR)
│   ├── Otra_Escuelita.py           ← Copia configurable para otras escuelas
│   └── Tutorial.py                 ← Página de ayuda y OUs requeridas
├── ConsolaGoogle-EnBlanco.csv      ← Plantilla de columnas para el CSV de salida
├── requirements.txt
├── Abrir_App.bat                   ← Abre la app localmente (Windows)
├── Instalar.bat
└── BITACORA.md                     ← Este archivo
```

---

## Navegación

`app.py` usa `st.navigation()` (Streamlit 1.55+) con tres páginas:

| Nombre en menú | Archivo |
|---|---|
| E-Ecuador | `pages/E_Ecuador.py` |
| Otra Escuelita | `pages/Otra_Escuelita.py` |
| Tutorial | `pages/Tutorial.py` |

El sidebar arranca **colapsado** (`initial_sidebar_state="collapsed"`) — se abre con el botón `>>` arriba a la izquierda.

---

## Página E-Ecuador (app original)

**Regla fundamental: no modificar la lógica de esta página.**

- OU hardcodeada: `/ESCUELAS/E-79 ESCUELA ECUADOR/{año} Estudiantes/{curso}`
- Contraseña: siempre fecha de nacimiento (`dd-mm-yyyy`)
- Email: `{rut}@{dominio}` — dominio se detecta automáticamente del CSV de Google o se ingresa manualmente
- No fuerza cambio de contraseña al primer inicio
- Reactiva cuentas suspendidas automáticamente

---

## Página Otra Escuelita (configurable)

Copia de E-Ecuador con campos adicionales en la UI para adaptarse a otras escuelas.

### Campos configurables en la UI

| Campo | Descripción |
|---|---|
| **Unidad educativa en la OU** | Reemplaza `E-79 ESCUELA ECUADOR` en la ruta. Ej: `E-89 ESCUELA OTRA` |
| **Dominio de correo** | Se detecta automáticamente del CSV de Google o se ingresa manual |
| **Sufijo RUT (opcional)** | Se agrega al final del RUT. Ej: `e80` → `12345678e80@dominio.cl` |
| **Incluir DV en el correo** | Checkbox. Agrega el dígito verificador. Ej: `12345678k@dominio.cl` |
| **Contraseña** | Radio: Fecha de nacimiento / Columna del SIGE (desplegable) / Texto fijo |

### Formato del email según opciones

```
RUT + DV (si activo) + Sufijo (si hay) @ dominio

Ejemplos:
- Solo RUT:          12345678@colegio.cl
- Con DV:            12345678k@colegio.cl
- Con sufijo:        12345678e80@colegio.cl
- Con DV + sufijo:   12345678ke80@colegio.cl
```

### Constante a modificar si se copia para nueva escuela

```python
NOMBRE_ESCUELA_OU = "OTRA ESCUELITA"   # línea ~20 del archivo
```

---

## Lógica de procesamiento (común a ambas páginas)

1. **Lee CSV de Google** → detecta dominio, OU actual, estado (activo/suspendido)
2. **Lee nómina SIGE** → soporta `.xls` HTML (exportación SIGE) y Excel real
3. **Filtra retirados** → excluye filas con `Fecha Retiro` distinta de vacío/1900-01-01
4. **Limpia RUTs** → elimina caracteres no numéricos, quita `.0` de floats
5. **Deduplica por email** → mantiene primera ocurrencia
6. **Construye OU** → `/ESCUELAS/{escuela}/{año} Estudiantes/{curso}`
7. **Construye curso** según `Cod Tipo Enseñanza`:
   - `10` → PRE-KINDER o KINDER
   - `110` → `{grado}{letra}` (ej: `1A`)
   - `299` → `OPCION 4 - {grado}{letra}`
8. **Asigna contraseña** → fecha de nacimiento `dd-mm-yyyy` (o lo configurado en Otra Escuelita)
9. **Compara con Google** → incluye solo cuentas nuevas, con OU distinta, o suspendidas
10. **Genera CSV** con columnas de la plantilla `ConsolaGoogle-EnBlanco.csv`

---

## Unidades Organizativas requeridas en Google Admin

Deben existir **antes** de subir el CSV. Si no existen, la carga falla para esos usuarios.

```
/ESCUELAS/
└── {NOMBRE ESCUELA}/
    └── {AÑO} Estudiantes/
        ├── PRE-KINDER A
        ├── PRE-KINDER B
        ├── KINDER A
        ├── KINDER B
        ├── 1A, 1B
        ├── 2A, 2B
        ├── ...
        ├── 8A, 8B
        └── OPCION 4 - 1A  (solo si hay tipo enseñanza 299)
```

Crear en: **Google Admin → Directorio → Unidades organizativas**

---

## Archivos de entrada

| Archivo | Origen | Formato |
|---|---|---|
| CSV de Google | Admin → Usuarios → Descargar lista | `.csv` (UTF-8 o cp1252) |
| Nómina SIGE | SIGE → Reportes → Nómina alumnos → Exportar | `.xls` HTML o Excel real |
| Plantilla | `ConsolaGoogle-EnBlanco.csv` (en la carpeta de la app) | `.csv` |

---

## Bugs corregidos relevantes

| Problema | Causa | Solución |
|---|---|---|
| `can only concatenate str (not "float") to str` | Columnas del SIGE llegan como float cuando hay NaN | `str()` explícito en `build_course`, `make_email` y construcción de apellidos |
| DV llegaba como float | Celda vacía en SIGE | `fillna("")` antes del `astype(str)` |
| Sufijo incluía `+` | Error de digitación en código | Eliminado el `+` |

---

## UI / CSS destacado

- `layout="wide"` en todas las páginas
- `initial_sidebar_state="collapsed"` en Otra Escuelita y Tutorial
- `padding-top: 1.5rem` en `.block-container` para reducir espacio superior
- Título usando `st.markdown("### ...")` en vez de `st.title()` para menor altura
- Barra animada CSS al procesar (verde degradado, reemplaza `st.spinner` que no era visible)
- Botón Procesar centrado con `st.columns([1, 2, 1])`
- Responsive: `@media (max-width: 768px)` apila columnas

---

## Cómo correr localmente

```
Abrir_App.bat
```
O manualmente:
```bash
cd "APP/"
streamlit run app.py
# → http://localhost:8501
```

---

## Decisiones de diseño importantes

- **E-Ecuador nunca se toca** — es la app en producción que funciona. Cualquier experimento va en Otra Escuelita.
- **La plantilla `ConsolaGoogle-EnBlanco.csv` es la fuente de verdad** de las columnas del CSV de salida. Si Google cambia el formato, solo hay que actualizar ese archivo.
- **`BASE_DIR`** en las páginas dentro de `pages/` apunta a `parent.parent` para encontrar la plantilla en la raíz.
- **No se fuerza cambio de contraseña** al primer inicio (campo `Change Password at Next Sign-In` queda vacío).
