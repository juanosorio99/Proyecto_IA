from io import StringIO
from typing import List, Tuple

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="CSV Analyzer 2077",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0,255,255,0.18), transparent 25%),
                radial-gradient(circle at top right, rgba(140,82,255,0.18), transparent 30%),
                linear-gradient(135deg, #07111f 0%, #0b1730 35%, #111827 100%);
            color: #f5f7ff;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
        }

        .hero-box {
            background: linear-gradient(135deg, rgba(0,255,255,0.12), rgba(140,82,255,0.15));
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 0 25px rgba(0,255,255,0.10), 0 0 50px rgba(140,82,255,0.08);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }

        .metric-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
            border: 1px solid rgba(0,255,255,0.18);
            border-radius: 20px;
            padding: 18px;
            text-align: center;
            min-height: 120px;
            box-shadow: inset 0 0 20px rgba(0,255,255,0.03), 0 10px 25px rgba(0,0,0,0.18);
        }

        .metric-title {
            font-size: 0.9rem;
            color: #b7c6ff;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
        }

        .metric-sub {
            font-size: 0.85rem;
            color: #99f6ff;
            margin-top: 8px;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 800;
            margin-bottom: 0.65rem;
            color: #eef4ff;
        }

        .tag {
            display: inline-block;
            padding: 8px 12px;
            margin: 4px;
            border-radius: 999px;
            background: rgba(0,255,255,0.12);
            color: #d8ffff;
            border: 1px solid rgba(0,255,255,0.22);
            font-size: 0.85rem;
        }

        .score-good {
            color: #7CFFB2;
            font-weight: 700;
        }

        .score-mid {
            color: #FFE17A;
            font-weight: 700;
        }

        .score-low {
            color: #FF8E8E;
            font-weight: 700;
        }

        div[data-testid="stFileUploader"] {
            background: rgba(255,255,255,0.04);
            border: 1px dashed rgba(0,255,255,0.28);
            border-radius: 18px;
            padding: 10px;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input,
        div[data-baseweb="select"] > div,
        div[data-testid="stNumberInput"] input {
            background-color: rgba(255,255,255,0.06) !important;
            color: white !important;
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,17,31,0.98), rgba(13,24,47,0.96));
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        div[data-testid="stHorizontalBlock"] {
            align-items: flex-start !important;
        }

        div[data-testid="stHorizontalBlock"] > div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def detect_delimiter(sample_text: str) -> str:
    delimiters = [",", ";", "\t", "|"]
    counts = {d: sample_text.count(d) for d in delimiters}
    return max(counts, key=counts.get) if any(counts.values()) else ","


@st.cache_data
def load_csv(file_bytes: bytes, delimiter: str, encoding: str) -> pd.DataFrame:
    content = file_bytes.decode(encoding, errors="replace")
    return pd.read_csv(StringIO(content), sep=delimiter)


def classify_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [col for col in df.columns if col not in numeric_cols]
    return numeric_cols, categorical_cols


def null_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = pd.DataFrame(
        {
            "columna": df.columns,
            "nulos": df.isnull().sum().values,
            "porcentaje_nulos": (df.isnull().mean().values * 100).round(2),
            "tipo": df.dtypes.astype(str).values,
        }
    )
    return summary.sort_values(["porcentaje_nulos", "nulos"], ascending=False)


def score_quality(df: pd.DataFrame) -> int:
    rows, cols = df.shape
    if rows == 0 or cols == 0:
        return 0

    null_pct = df.isnull().mean().mean() * 100
    duplicated_pct = df.duplicated().mean() * 100 if len(df) > 0 else 0

    score = 100
    score -= min(int(null_pct * 1.2), 45)
    score -= min(int(duplicated_pct * 1.5), 30)

    if cols < 2:
        score -= 15
    if rows < 5:
        score -= 15

    return max(0, min(100, score))


def score_label(score: int) -> str:
    if score >= 80:
        return "score-good"
    if score >= 55:
        return "score-mid"
    return "score-low"


def render_tags(values: List[str]) -> None:
    if not values:
        st.caption("No hay elementos para mostrar.")
        return

    tags_html = "".join([f'<span class="tag">{v}</span>' for v in values])
    st.markdown(tags_html, unsafe_allow_html=True)


inject_css()

st.markdown(
    """
    <div class="hero-box">
        <h1 style="margin-bottom: 8px; font-size: 3rem;">🚀 CSV Analyzer 2077</h1>
        <p style="font-size: 1.1rem; color: #dbe7ff; max-width: 1000px;">
            Sube un archivo CSV, conviértelo en dataframe y obtén un análisis visual, futurista y útil:
            calidad de datos, tipos de columnas, nulos, duplicados, estadísticas y exploración rápida.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    st.write("Personaliza la carga y el análisis del CSV.")

    encoding = st.selectbox("Codificación", ["utf-8", "latin-1", "cp1252"], index=0)
    delimiter_option = st.selectbox("Separador", ["Auto detectar", ",", ";", "Tab", "|"])
    preview_rows = st.slider("Filas a previsualizar", min_value=5, max_value=100, value=10, step=5)
    show_null_table = st.toggle("Mostrar tabla de nulos", value=True)
    show_stats_table = st.toggle("Mostrar estadísticas numéricas", value=True)
    show_duplicates = st.toggle("Mostrar duplicados", value=True)

    st.markdown("---")
    st.markdown(
        """
        **Formato soportado:** CSV  
        **Ideal para:** exploración, profiling rápido, calidad de datos y validación inicial.
        """
    )

upload_col, info_col = st.columns([1.15, 0.85], gap="small")

with upload_col:
    st.markdown('<div class="section-title">📁 Cargar CSV</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"], label_visibility="collapsed")

with info_col:
    st.markdown('<div class="section-title">🧪 Información de análisis</div>', unsafe_allow_html=True)
    st.text_area(
        "Resumen",
        value="El archivo se leerá como dataframe para analizar estructura, calidad, columnas numéricas, categóricas, nulos y duplicados.",
        height=180,
        label_visibility="collapsed",
        disabled=True,
    )

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    try:
        sample = file_bytes[:5000].decode(encoding, errors="replace")
        detected_delimiter = detect_delimiter(sample)

        delimiter_map = {
            "Auto detectar": detected_delimiter,
            ",": ",",
            ";": ";",
            "Tab": "\t",
            "|": "|",
        }
        delimiter = delimiter_map[delimiter_option]

        df = load_csv(file_bytes, delimiter, encoding)

    except Exception as exc:
        st.error(f"No se pudo procesar el CSV: {exc}")
        st.stop()

    numeric_cols, categorical_cols = classify_columns(df)
    quality = score_quality(df)
    duplicates_count = int(df.duplicated().sum())
    total_nulls = int(df.isnull().sum().sum())

    st.markdown("###")

    m1, m2, m3, m4 = st.columns(4, gap="small")

    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Calidad del dataset</div>
                <div class="metric-value {score_label(quality)}">{quality}%</div>
                <div class="metric-sub">estimación general</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Filas / Registros</div>
                <div class="metric-value">{df.shape[0]}</div>
                <div class="metric-sub">observaciones cargadas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Columnas</div>
                <div class="metric-value">{df.shape[1]}</div>
                <div class="metric-sub">variables detectadas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Nulos totales</div>
                <div class="metric-value">{total_nulls}</div>
                <div class="metric-sub">celdas vacías</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("###")

    left_panel, right_panel = st.columns([1.08, 0.92], gap="small")

    with left_panel:
        st.markdown("## 👀 Vista previa del dataframe")
        st.dataframe(df.head(preview_rows), use_container_width=True)

        st.markdown("## 🧠 Diagnóstico rápido")
        st.write(f"**Separador usado:** `{repr(delimiter)}`")
        st.write(f"**Codificación usada:** `{encoding}`")
        st.write(f"**Duplicados detectados:** {duplicates_count}")
        st.write(f"**Columnas numéricas:** {len(numeric_cols)}")
        st.write(f"**Columnas categóricas:** {len(categorical_cols)}")

        recommendations = []
        if duplicates_count > 0:
            recommendations.append("Hay filas duplicadas; conviene revisarlas o depurarlas.")
        if total_nulls > 0:
            recommendations.append("El dataset tiene valores nulos; valida si deben imputarse o eliminarse.")
        if len(numeric_cols) == 0:
            recommendations.append("No se detectaron columnas numéricas; revisa el separador o el formato del CSV.")
        if df.shape[0] < 10:
            recommendations.append("El dataset tiene pocas filas; el análisis estadístico puede ser limitado.")
        if quality >= 85:
            recommendations.append("La calidad general del dataset luce buena para un análisis inicial.")

        st.write("**Recomendaciones:**")
        for rec in recommendations:
            st.info(rec)

    with right_panel:
        st.markdown("## 🏷️ Tipos de columnas")
        st.write("**Numéricas**")
        render_tags(numeric_cols)

        st.write("**Categóricas / texto**")
        render_tags(categorical_cols[:30])

        if show_stats_table and numeric_cols:
            st.markdown("## 📊 Estadísticas numéricas")
            st.dataframe(df[numeric_cols].describe().T, use_container_width=True)

    if show_null_table:
        st.markdown("## 🧩 Resumen de nulos y tipos")
        st.dataframe(null_summary(df), use_container_width=True, hide_index=True)

    if show_duplicates and duplicates_count > 0:
        st.markdown("## ♻️ Filas duplicadas")
        st.dataframe(df[df.duplicated()].head(50), use_container_width=True)

else:
    st.info("Sube un CSV para iniciar el análisis del dataframe.")

st.caption("Diseño futurista en Streamlit • análisis de CSV a dataframe • profiling inicial de datos")