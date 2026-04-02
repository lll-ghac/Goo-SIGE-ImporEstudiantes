import streamlit as st

st.set_page_config(page_title="Tutorial", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Tutorial — Cómo usar la app")
st.markdown("---")

col_a, col_b = st.columns(2, gap="large")

with col_a:
    st.subheader("① ¿Qué hace esta app?")
    st.markdown(
        """
        Genera un archivo **CSV listo para carga masiva** en la Consola de Google Workspace.

        Compara la nómina del SIGE con los usuarios actuales de Google y determina qué cuentas hay que:
        - **Crear** (estudiantes nuevos que no tienen correo)
        - **Mover** (estudiantes que cambiaron de curso → cambia la Unidad Organizativa)
        - **Reactivar** (cuentas suspendidas que vuelven a estar activos en SIGE)
        """
    )

    st.subheader("② Archivos necesarios")
    st.markdown(
        """
        | Archivo | Cómo obtenerlo |
        |---|---|
        | **CSV de Google** | Consola de Admin → Usuarios → Descargar lista (todos los usuarios) |
        | **Nómina SIGE** | SIGE → Reportes → Nómina de alumnos → Exportar como `.xls` |
        """
    )

    st.subheader("③ Pasos")
    st.markdown(
        """
        1. Abre la página **E-Ecuador** u **Otra Escuelita** según corresponda
        2. Sube el archivo CSV de Google y la nómina SIGE
        3. Completa los campos de configuración (dominio, OU, contraseña)
        4. Haz clic en **Procesar**
        5. Revisa el resumen y la vista previa
        6. Descarga el CSV generado
        7. Ve a la Consola de Google → Usuarios → **Subir usuarios en bloque** → sube el CSV
        """
    )

with col_b:
    st.subheader("④ Unidades Organizativas requeridas")
    st.markdown(
        """
        Antes de subir el CSV a Google, estas **Unidades Organizativas deben existir** en la
        Consola de Admin. Si no existen, la carga fallará para los usuarios de ese curso.

        La app genera rutas con este formato:
        ```
        /ESCUELAS/{nombre escuela}/{año} Estudiantes/{curso}
        ```
        """
    )

    st.markdown("**Estructura mínima a crear en Google Admin:**")
    st.code(
        """/ESCUELAS/
└── E-79 ESCUELA ECUADOR/          ← (o el nombre de tu escuela)
    └── 2026 Estudiantes/
        ├── PRE-KINDER A
        ├── PRE-KINDER B
        ├── KINDER A
        ├── KINDER B
        ├── 1A
        ├── 1B
        ├── 2A
        ├── 2B
        ├── ...hasta...
        ├── 8A
        ├── 8B
        └── OPCION 4 - 1A          ← solo si hay enseñanza tipo 299""",
        language="text",
    )

    st.info(
        "**¿Cómo crear OUs en Google Admin?**  \n"
        "Consola de Admin → Directorio → Unidades organizativas → "
        "hacer clic en **+** para crear cada nivel de la jerarquía.",
        icon="ℹ️",
    )

    st.subheader("⑤ Notas importantes")
    st.markdown(
        """
        - La **contraseña inicial** es la fecha de nacimiento del estudiante: `dd-mm-yyyy`
        - **No** se fuerza el cambio de contraseña al primer inicio de sesión
        - Los estudiantes **retirados** en SIGE son excluidos automáticamente
        - Si un RUT aparece duplicado, se conserva solo el primero
        - El dominio se detecta automáticamente desde el archivo de Google, o puedes ingresarlo manualmente
        """
    )
