import csv
import re
import unicodedata
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Correos Estudiantes", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_PATH = BASE_DIR / "ConsolaGoogle-EnBlanco.csv"

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Oculta textos en inglés del cargador de archivos */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div {
        display: none;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] small {
        display: none;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "Arrastra y suelta el archivo aquí";
        color: #e6e6e6;
        font-size: 0.9rem;
        display: block;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"]::before {
        content: "O selecciona un archivo";
        color: #bdbdbd;
        font-size: 0.8rem;
        display: block;
        margin-top: 0.25rem;
    }
    div[data-testid="stFileUploader"] button {
        color: transparent;
        position: relative;
    }
    div[data-testid="stFileUploader"] button::after {
        content: "Buscar archivos";
        color: inherit;
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
    }
    div.stButton > button {
        background-color: #2e8b57;
        color: #ffffff;
        border: 1px solid #2e8b57;
        padding: 0.45rem 1rem;
        font-weight: 600;
        border-radius: 0.5rem;
    }
    div.stButton > button:hover {
        background-color: #277a4d;
        border-color: #277a4d;
    }
    div.stButton > button:focus {
        outline: 3px solid rgba(46, 139, 87, 0.35);
        outline-offset: 2px;
    }

    /* ── Barra de progreso animada ── */
    @keyframes loading {
        0%   { background-position: 200% center; }
        100% { background-position: -200% center; }
    }
    .loading-bar {
        background: linear-gradient(90deg, #2e8b57 0%, #57c47a 40%, #2e8b57 60%, #1a5c38 100%);
        background-size: 200% auto;
        animation: loading 1.4s linear infinite;
        color: #ffffff;
        font-weight: 700;
        font-size: 1rem;
        text-align: center;
        padding: 0.6rem 1rem;
        border-radius: 0.5rem;
        letter-spacing: 0.03em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def find_column(columns, *candidates):
    norm_map = {normalize_text(col): col for col in columns}
    for cand in candidates:
        key = normalize_text(cand)
        if key in norm_map:
            return norm_map[key]
    return None


def read_csv_any(file_bytes: bytes) -> pd.DataFrame:
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    separators = [",", ";", "\t", "|"]

    for enc in encodings:
        try:
            text = file_bytes.decode(enc)
        except Exception:
            continue

        # Detect delimiter using a small sample
        sample = "\n".join(text.splitlines()[:5])
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=separators)
            sep = dialect.delimiter
        except Exception:
            sep = ","

        try:
            return pd.read_csv(StringIO(text), sep=sep, dtype=str, keep_default_na=False)
        except Exception:
            continue

    raise ValueError("No se pudo leer el CSV con las codificaciones probadas.")


def read_sige(file_bytes: bytes) -> pd.DataFrame:
    # Detect XLS/XLSX binary
    if file_bytes[:2] == b"PK" or file_bytes[:8] == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
        # Try Excel
        return pd.read_excel(BytesIO(file_bytes), dtype=str)

    # Assume HTML disguised as .xls
    html = None
    for enc in ("cp1252", "latin-1", "utf-8"):
        try:
            html = file_bytes.decode(enc)
            break
        except Exception:
            continue
    if html is None:
        raise ValueError("No se pudo decodificar el archivo SIGE.")

    tables = pd.read_html(StringIO(html))
    if not tables:
        raise ValueError("No se encontraron tablas en el archivo SIGE.")
    return tables[0]


def parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    # Avoid day/month warnings when ISO format is present
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    else:
        parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def clean_run(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    text = re.sub(r"\D", "", text)
    return text


def build_course(row) -> str:
    cod_tipo = str(row["cod_tipo_ensenanza"])
    cod_grado = str(row["cod_grado"])
    desc = str(row["desc_grado"])
    letra = str(row["letra_curso"]).strip().upper()

    if cod_tipo == "10":
        desc_norm = normalize_text(desc)
        if "pre" in desc_norm and "kinder" in desc_norm:
            return f"PRE-KINDER {letra}".strip()
        if "kinder" in desc_norm:
            return f"KINDER {letra}".strip()
        return f"KINDER {letra}".strip()

    if cod_tipo == "299":
        return f"OPCION 4 - {cod_grado}{letra}".strip()

    # 110 and default
    return f"{cod_grado}{letra}".strip()


def extract_domain_from_google(df_google: pd.DataFrame) -> str:
    email_col = find_column(df_google.columns, "Email Address [Required]", "Email Address")
    if not email_col:
        return ""
    for val in df_google[email_col].tolist():
        if isinstance(val, str) and "@" in val:
            return val.split("@", 1)[1].strip()
    return ""


def load_template_columns(template_bytes: bytes | None) -> list[str]:
    if template_bytes is None and DEFAULT_TEMPLATE_PATH.exists():
        template_bytes = DEFAULT_TEMPLATE_PATH.read_bytes()
    if not template_bytes:
        return []

    # Parse first line as CSV header
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = template_bytes.decode(enc)
            break
        except Exception:
            text = None
    if text is None:
        raise ValueError("No se pudo leer la plantilla.")

    first_line = text.splitlines()[0]
    reader = csv.reader([first_line])
    return next(reader)


def build_output(
    df_sige: pd.DataFrame,
    df_google: pd.DataFrame,
    template_cols: list[str],
    domain: str,
):
    # Normalize SIGE columns
    required = {
        "ano": "Año",
        "cod_tipo_ensenanza": "Cod Tipo Enseñanza",
        "cod_grado": "Cod Grado",
        "desc_grado": "Desc Grado",
        "letra_curso": "Letra Curso",
        "run": "Run",
        "dv": "Dígito Ver.",
        "nombres": "Nombres",
        "apellido_paterno": "Apellido Paterno",
        "apellido_materno": "Apellido Materno",
        "fecha_nacimiento": "Fecha Nacimiento",
        "fecha_retiro": "Fecha Retiro",
    }

    col_map = {}
    missing = []
    for key, label in required.items():
        col = find_column(df_sige.columns, label)
        if not col:
            missing.append(label)
        else:
            col_map[key] = col

    if missing:
        raise ValueError(f"Faltan columnas en SIGE: {', '.join(missing)}")

    work = df_sige.rename(columns={v: k for k, v in col_map.items()}).copy()

    # Clean core fields
    work["ano"] = work["ano"].astype(str).str.strip().str.replace(".0", "", regex=False)
    work["cod_tipo_ensenanza"] = work["cod_tipo_ensenanza"].astype(str).str.strip().str.replace(".0", "", regex=False)
    work["cod_grado"] = work["cod_grado"].astype(str).str.strip().str.replace(".0", "", regex=False)
    work["letra_curso"] = work["letra_curso"].astype(str).str.strip().replace("nan", "", regex=False)
    work["nombres"] = work["nombres"].astype(str).str.strip()
    work["apellido_paterno"] = work["apellido_paterno"].astype(str).str.strip()
    work["apellido_materno"] = work["apellido_materno"].astype(str).str.strip()

    # Filter by retiro
    retiro_dates = work["fecha_retiro"].apply(parse_date)
    active_mask = retiro_dates.isna() | (retiro_dates == date(1900, 1, 1))
    retired_count = int((~active_mask).sum())

    work = work.loc[active_mask].copy()

    work["run_clean"] = work["run"].apply(clean_run)
    work = work[work["run_clean"] != ""].copy()

    # Deduplicate by email
    work["email"] = work["run_clean"].apply(lambda r: f"{r}@{domain}")
    dup_count = int(work.duplicated("email").sum())
    work = work.drop_duplicates("email", keep="first")

    # Build course and OU
    work["course"] = work.apply(build_course, axis=1)
    work["org_unit"] = work.apply(lambda r: f"/ESCUELAS/E-79 ESCUELA ECUADOR/{r['ano']} Estudiantes/{r['course']}", axis=1)

    # Birth date -> password
    birth_dates = work["fecha_nacimiento"].apply(parse_date)
    work["password"] = birth_dates.apply(lambda d: d.strftime("%d-%m-%Y") if d else "")
    missing_birth = int((work["password"] == "").sum())
    missing_birth_rows = work.loc[work["password"] == ""].copy()

    # Google lookup
    email_col = find_column(df_google.columns, "Email Address [Required]", "Email Address")
    org_col = find_column(df_google.columns, "Org Unit Path [Required]", "Org Unit Path")
    status_col = find_column(df_google.columns, "Status [READ ONLY]", "Status")
    if not email_col:
        raise ValueError("No se encontró la columna 'Email Address' en el archivo de Google.")
    if not org_col:
        raise ValueError("No se encontró la columna 'Org Unit Path' en el archivo de Google.")

    google_map = {}
    google_status = {}
    for _, row in df_google.iterrows():
        email = str(row.get(email_col, "")).strip().lower()
        if not email:
            continue
        google_map[email] = str(row.get(org_col, "")).strip()
        if status_col:
            google_status[email] = str(row.get(status_col, "")).strip()

    output_rows = []
    new_count = 0
    update_count = 0
    reactivate_count = 0
    skipped_no_birth = 0

    for _, row in work.iterrows():
        email = row["email"].lower()
        org_unit = row["org_unit"]
        first_name = row["nombres"]
        last_name = (str(row["apellido_paterno"]) + " " + str(row["apellido_materno"])).strip()
        password = row["password"]

        exists = email in google_map
        status_val = google_status.get(email, "")
        status_norm = normalize_text(status_val)
        is_suspended = "suspend" in status_norm
        needs_update = exists and google_map[email].strip() != org_unit
        is_new = not exists

        if not (is_new or needs_update or is_suspended):
            continue

        if not password:
            skipped_no_birth += 1
            continue

        record = {col: "" for col in template_cols}
        # Required/common fields
        if "First Name [Required]" in record:
            record["First Name [Required]"] = first_name
        if "Last Name [Required]" in record:
            record["Last Name [Required]"] = last_name
        if "Email Address [Required]" in record:
            record["Email Address [Required]"] = email
        if "Password [Required]" in record:
            record["Password [Required]"] = password
        if "Org Unit Path [Required]" in record:
            record["Org Unit Path [Required]"] = org_unit
        if "Change Password at Next Sign-In" in record:
            record["Change Password at Next Sign-In"] = ""
        if "New Status [UPLOAD ONLY]" in record:
            record["New Status [UPLOAD ONLY]"] = "Active"

        output_rows.append(record)
        if is_new:
            new_count += 1
        else:
            update_count += 1
        if is_suspended:
            reactivate_count += 1

    df_out = pd.DataFrame(output_rows, columns=template_cols)

    summary = {
        "total_sige": int(len(df_sige)),
        "active": int(len(work)),
        "retired": retired_count,
        "duplicates": dup_count,
        "missing_birth": missing_birth,
        "new": new_count,
        "updates": update_count,
        "reactivated": reactivate_count,
        "skipped_no_birth": skipped_no_birth,
    }

    return df_out, summary, missing_birth_rows


st.title("Generador de CSV. Crea archivo para actualizar Estudiantes en la Consola de Google de forma masiva")

st.markdown(
    "Sube el archivo de Google, la nómina SIGE y descarga el CSV listo para carga masiva."
)

col_left, col_right = st.columns(2)

with col_left:
    google_file = st.file_uploader("Consola de GOOGLE (CSV de usuarios)", type=["csv"], key="google")
    sige_file = st.file_uploader("Archivo SIGE (HTML .xls)", type=["xls", "xlsx", "html"], key="sige")
    st.caption(
        "Solo se requieren 2 archivos: Google y SIGE. La plantilla se toma desde ConsolaGoogle-EnBlanco.csv local."
    )

with col_right:
    domain_input = st.text_input("Dominio de correo", value="")
    st.caption("La contraseña se asigna siempre como fecha de nacimiento (dd-mm-yyyy).")
    st.caption("No se fuerza el cambio de contraseña al primer inicio.")
    st.caption("Las cuentas en SIGE se reactivan (estado Active) al cargar el CSV.")

process = st.button("Procesar")
status_placeholder = st.empty()

if process:
    if not google_file or not sige_file:
        st.error("Debes subir el archivo de Google y el archivo SIGE.")
        st.stop()

    status_placeholder.markdown(
        '<div class="loading-bar">⏳ Procesando, por favor espera...</div>',
        unsafe_allow_html=True,
    )

    try:
        df_google = read_csv_any(google_file.getvalue())
    except Exception as e:
        st.error(f"Error al leer archivo Google: {e}")
        st.stop()

    try:
        df_sige = read_sige(sige_file.getvalue())
    except Exception as e:
        st.error(f"Error al leer archivo SIGE: {e}")
        st.stop()

    domain = domain_input.strip()
    if not domain:
        domain = extract_domain_from_google(df_google)

    if not domain:
        st.error("No se pudo detectar el dominio de correo. Ingresa el dominio manualmente.")
        st.stop()

    try:
        template_cols = load_template_columns(None)
    except Exception as e:
        st.error(
            "No se pudo leer ConsolaGoogle-EnBlanco.csv desde la carpeta de la app. "
            "Asegúrate de que exista junto a app.py."
        )
        st.stop()

    if not template_cols:
        st.error("No se pudieron obtener las columnas de la plantilla.")
        st.stop()

    try:
        df_out, summary, missing_birth_rows = build_output(
            df_sige,
            df_google,
            template_cols,
            domain,
        )
    except Exception as e:
        status_placeholder.empty()
        st.error(str(e))
        st.stop()

    status_placeholder.empty()

    if not missing_birth_rows.empty:
        st.error("Faltan fechas de nacimiento en la nómina SIGE. Corrige estas filas y vuelve a ejecutar.")
        cols_show = [
            "ano",
            "cod_tipo_ensenanza",
            "cod_grado",
            "desc_grado",
            "letra_curso",
            "run",
            "dv",
            "nombres",
            "apellido_paterno",
            "apellido_materno",
            "fecha_nacimiento",
        ]
        available = [c for c in cols_show if c in missing_birth_rows.columns]
        st.dataframe(missing_birth_rows[available], use_container_width=True)
        st.stop()

    st.subheader("Resumen")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total SIGE", summary["total_sige"])
    c2.metric("Activos", summary["active"])
    c3.metric("Retirados excluidos", summary["retired"])
    c4.metric("Duplicados RUN", summary["duplicates"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Nuevos", summary["new"])
    c6.metric("Actualizar OU", summary["updates"])
    c7.metric("Reactivar suspendidos", summary["reactivated"])
    c8.metric("Omitidos sin contraseña", summary["skipped_no_birth"])

    st.subheader("Vista previa")
    st.dataframe(df_out.head(50), use_container_width=True)

    csv_bytes = df_out.to_csv(index=False).encode("utf-8-sig")
    filename = f"CargaGoogle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    st.download_button(
        "Descargar CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
    )
