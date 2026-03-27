from io import StringIO
from typing import List, Tuple
import re

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Property Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXPECTED_COLUMNS = [
    "ALQUILER_VARIABLE",
    "NRO_PERIODO",
    "FECHA_INICIAL",
    "FECHA_FINAL",
    "FECHA_GRUPO",
    "FECHA_VENCIMIENTO",
    "IMPORTE_REAL",
    "ESTADO",
    "NOMBRE_CLIENTE",
    "TIPO_1",
    "TIPO_2",
    "CICLO_FACTURACION",
]

DATE_COLUMNS = ["FECHA_INICIAL", "FECHA_FINAL", "FECHA_GRUPO", "FECHA_VENCIMIENTO"]

SPANISH_MONTHS = {
    "ENE": "01",
    "FEB": "02",
    "MAR": "03",
    "ABR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AGO": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DIC": "12",
}


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
            padding-top: 1.1rem;
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
            line-height: 1.2;
            word-break: break-word;
        }

        .metric-sub {
            font-size: 0.85rem;
            color: #99f6ff;
            margin-top: 8px;
        }

        .section-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 0.6rem;
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
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="tag"] {
            background-color: rgba(255,255,255,0.06) !important;
            color: white !important;
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,17,31,0.98), rgba(13,24,47,0.96));
            border-right: 1px solid rgba(255,255,255,0.08);
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


def score_label(score: int) -> str:
    if score >= 80:
        return "score-good"
    if score >= 55:
        return "score-mid"
    return "score-low"


def score_quality(df: pd.DataFrame) -> int:
    rows, cols = df.shape
    if rows == 0 or cols == 0:
        return 0

    null_pct = df.isnull().mean().mean() * 100
    duplicated_pct = df.duplicated().mean() * 100 if len(df) > 0 else 0
    missing_expected = sum(1 for c in EXPECTED_COLUMNS if c not in df.columns)

    score = 100
    score -= min(int(null_pct * 1.1), 35)
    score -= min(int(duplicated_pct * 1.5), 25)
    score -= missing_expected * 6
    return max(0, min(100, score))


def validate_expected_structure(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    extra = [col for col in df.columns if col not in EXPECTED_COLUMNS]
    return missing, extra


def parse_property_date(value):
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip().upper()

    if not text or text in {"NONE", "NULL", "NAN"}:
        return pd.NaT

    match = re.match(r"^(\d{1,2})-([A-ZÁÉÍÓÚ]{3})-(\d{2,4})$", text)
    if match:
        day, month_txt, year = match.groups()
        month_txt = (
            month_txt.replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
        )
        month_num = SPANISH_MONTHS.get(month_txt)

        if month_num:
            if len(year) == 2:
                year = f"20{year}"
            return pd.to_datetime(f"{year}-{month_num}-{int(day):02d}", errors="coerce")

    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data.columns = [str(c).strip().upper() for c in data.columns]

    for col in DATE_COLUMNS:
        if col in data.columns:
            data[col] = data[col].apply(parse_property_date)

    if "IMPORTE_REAL" in data.columns:
        data["IMPORTE_REAL"] = pd.to_numeric(data["IMPORTE_REAL"], errors="coerce")

    if "NRO_PERIODO" in data.columns:
        data["NRO_PERIODO"] = pd.to_numeric(data["NRO_PERIODO"], errors="coerce")

    for col in ["ESTADO", "NOMBRE_CLIENTE", "TIPO_1", "TIPO_2", "CICLO_FACTURACION"]:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip()

    return data


def render_tags(values: List[str]) -> None:
    if not values:
        st.caption("No hay elementos para mostrar.")
        return
    html = "".join([f'<span class="tag">{v}</span>' for v in values])
    st.markdown(html, unsafe_allow_html=True)


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


def format_cop(value) -> str:
    if pd.isna(value):
        return ""
    return f"$ {value:,.0f}".replace(",", ".")


def format_number(value, decimals: int = 2) -> str:
    if pd.isna(value):
        return ""
    return f"{value:,.{decimals}f}"


def format_metric_number(value) -> str:
    if pd.isna(value):
        return ""
    return f"{value:,.0f}"


def make_bar_chart(series: pd.Series, title: str, xlabel: str, ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    series.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def make_line_chart(series: pd.Series, title: str, xlabel: str, ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    series.plot(kind="line", marker="o", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


def make_histogram(series: pd.Series, title: str, xlabel: str):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(series.dropna(), bins=20)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frecuencia")
    fig.tight_layout()
    return fig


inject_css()

st.markdown(
    """
    <div class="hero-box">
        <h1 style="margin-bottom: 8px; font-size: 3rem;">🚀 Property Analyzer</h1>
        <p style="font-size: 1.08rem; color: #dbe7ff; max-width: 1000px;">
            Analizador especializado para Property.<br>
            Hecho por:<br>
            - Juan<br>
            - Leon<br>
            - Gina<br>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    encoding = st.selectbox("Codificación", ["utf-8", "latin-1", "cp1252"], index=0)
    delimiter_option = st.selectbox("Separador", ["Auto detectar", ",", ";", "Tab", "|"])
    preview_rows = st.slider("Filas a previsualizar", min_value=5, max_value=50, value=10, step=5)
    top_n_clients = st.slider("Top clientes en gráficos", min_value=5, max_value=20, value=10, step=1)
    show_null_table = st.toggle("Mostrar tabla de nulos", value=True)
    show_duplicates = st.toggle("Mostrar duplicados", value=True)

    st.markdown("---")
    st.markdown("**Archivo esperado:** CSV exportado de Property con la consulta estándar de alquiler variable.")

upload_col, info_col = st.columns([1.15, 0.85], gap="small")

with upload_col:
    st.markdown('<div class="section-title">📁 Cargar CSV de Property</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"], label_visibility="collapsed")

with info_col:
    st.markdown('<div class="section-title">🧾 Estructura esperada</div>', unsafe_allow_html=True)
    st.text_area(
        "Estructura",
        value="ALQUILER_VARIABLE, NRO_PERIODO, FECHA_INICIAL, FECHA_FINAL, FECHA_GRUPO, FECHA_VENCIMIENTO, IMPORTE_REAL, ESTADO, NOMBRE_CLIENTE, TIPO_1, TIPO_2, CICLO_FACTURACION",
        height=160,
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
        raw_df = load_csv(file_bytes, delimiter, encoding)
        df = prepare_dataframe(raw_df)
    except Exception as exc:
        st.error(f"No se pudo procesar el CSV: {exc}")
        st.stop()

    missing_cols, extra_cols = validate_expected_structure(df)
    quality = score_quality(df)
    duplicates_count = int(df.duplicated().sum())
    total_nulls = int(df.isnull().sum().sum())

    filtered_df = df.copy()

    st.markdown("## 🎛️ Selector de importe por tipo de facturación")
    tipo2_options_for_metric = ["TODOS"]
    if "TIPO_2" in filtered_df.columns:
        tipo2_options_for_metric += sorted(filtered_df["TIPO_2"].dropna().unique().tolist())

    selected_tipo2_metric = st.selectbox(
        "Calcular el importe total para este tipo de facturación",
        tipo2_options_for_metric,
        index=0,
    )

    if selected_tipo2_metric == "TODOS":
        importe_metric_df = filtered_df.copy()
    else:
        importe_metric_df = filtered_df[filtered_df["TIPO_2"] == selected_tipo2_metric].copy()

    st.markdown("###")
    c1, c2, c3, c4, c5 = st.columns(5, gap="small")

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Calidad</div>
                <div class="metric-value {score_label(quality)}">{quality}%</div>
                <div class="metric-sub">estructura y consistencia</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Registros</div>
                <div class="metric-value">{len(filtered_df)}</div>
                <div class="metric-sub">filas cargadas</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        total_clientes = filtered_df["NOMBRE_CLIENTE"].nunique() if "NOMBRE_CLIENTE" in filtered_df.columns else 0
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Clientes</div>
                <div class="metric-value">{total_clientes}</div>
                <div class="metric-sub">clientes únicos</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        importe_total = importe_metric_df["IMPORTE_REAL"].sum() if "IMPORTE_REAL" in importe_metric_df.columns else 0
        subtitulo_importe = "suma del período"
        if selected_tipo2_metric != "TODOS":
            subtitulo_importe = f"suma para {selected_tipo2_metric}"

        if selected_tipo2_metric == "VENTAS":
            importe_display = format_cop(importe_total)
        else:
            importe_display = format_metric_number(importe_total)

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Importe total</div>
                <div class="metric-value">{importe_display}</div>
                <div class="metric-sub">{subtitulo_importe}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Nulos</div>
                <div class="metric-value">{total_nulls}</div>
                <div class="metric-sub">celdas vacías</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("## 🎛️ Filtros de análisis")
    f1, f2, f3 = st.columns(3, gap="small")

    with f1:
        clientes = (
            sorted(filtered_df["NOMBRE_CLIENTE"].dropna().unique().tolist())
            if "NOMBRE_CLIENTE" in filtered_df.columns else []
        )
        selected_clients = st.multiselect("NOMBRE_CLIENTE", clientes)

    with f2:
        ciclos = (
            sorted(filtered_df["CICLO_FACTURACION"].dropna().unique().tolist())
            if "CICLO_FACTURACION" in filtered_df.columns else []
        )
        selected_cycles = st.multiselect("CICLO_FACTURACION", ciclos)

    with f3:
        estados = (
            sorted(filtered_df["ESTADO"].dropna().unique().tolist())
            if "ESTADO" in filtered_df.columns else []
        )
        selected_states = st.multiselect("ESTADO", estados)

    if selected_clients:
        filtered_df = filtered_df[filtered_df["NOMBRE_CLIENTE"].isin(selected_clients)]
    if selected_cycles:
        filtered_df = filtered_df[filtered_df["CICLO_FACTURACION"].isin(selected_cycles)]
    if selected_states:
        filtered_df = filtered_df[filtered_df["ESTADO"].isin(selected_states)]

    # sincroniza el selector principal con el resto del análisis monetario
    if selected_tipo2_metric == "TODOS":
        analysis_df = filtered_df.copy()
    else:
        analysis_df = filtered_df[filtered_df["TIPO_2"] == selected_tipo2_metric].copy()

    st.markdown("## 👀 Vista previa del dataframe")
    st.dataframe(filtered_df.head(preview_rows), use_container_width=True)

    left_panel, right_panel = st.columns([1.05, 0.95], gap="small")

    with left_panel:
        st.markdown("## 🧠 Diagnóstico de negocio")
        st.write(f"**Separador usado:** `{repr(delimiter)}`")
        st.write(f"**Codificación usada:** `{encoding}`")
        st.write(f"**Duplicados detectados:** {duplicates_count}")
        st.write(f"**Columnas faltantes esperadas:** {len(missing_cols)}")
        st.write(f"**Columnas extra:** {len(extra_cols)}")

        if missing_cols:
            st.warning("Faltan columnas esperadas en el archivo.")
            render_tags(missing_cols)
        else:
            st.success("La estructura del archivo coincide con la consulta esperada.")

        if extra_cols:
            st.info("Se detectaron columnas adicionales.")
            render_tags(extra_cols)

        if "CICLO_FACTURACION" in filtered_df.columns:
            st.write("**Ciclos presentes:**")
            render_tags(sorted(filtered_df["CICLO_FACTURACION"].dropna().unique().tolist()))

        if "ESTADO" in filtered_df.columns:
            st.write("**Estados presentes:**")
            render_tags(sorted(filtered_df["ESTADO"].dropna().unique().tolist()))

    with right_panel:
        st.markdown("## 📊 Estadísticos por tipo de facturación sobre IMPORTE_REAL")
        if {"TIPO_2", "IMPORTE_REAL"}.issubset(filtered_df.columns):
            stats_by_tipo2 = (
                filtered_df.dropna(subset=["TIPO_2", "IMPORTE_REAL"])
                .groupby("TIPO_2")["IMPORTE_REAL"]
                .agg([
                    ("registros", "count"),
                    ("suma", "sum"),
                    ("promedio", "mean"),
                    ("mediana", "median"),
                    ("minimo", "min"),
                    ("maximo", "max"),
                    ("desv_estandar", "std"),
                ])
                .reset_index()
                .sort_values("suma", ascending=False)
            )

            stats_by_tipo2_display = stats_by_tipo2.copy()
            money_cols = ["suma", "promedio", "mediana", "minimo", "maximo", "desv_estandar"]

            ventas_mask = stats_by_tipo2_display["TIPO_2"].astype(str).str.upper() == "VENTAS"
            for col in money_cols:
                stats_by_tipo2_display.loc[ventas_mask, col] = stats_by_tipo2_display.loc[ventas_mask, col].apply(format_cop)
                stats_by_tipo2_display.loc[~ventas_mask, col] = stats_by_tipo2_display.loc[~ventas_mask, col].apply(
                    lambda x: format_number(x, 2)
                )

            stats_by_tipo2_display = stats_by_tipo2_display.rename(columns={"TIPO_2": "tipo de facturación"})
            st.dataframe(stats_by_tipo2_display, use_container_width=True, hide_index=True)

    g1, g2 = st.columns(2, gap="small")

    with g1:
        st.markdown("## 📈 Importe por cliente")
        if {"NOMBRE_CLIENTE", "IMPORTE_REAL"}.issubset(analysis_df.columns):
            client_amount = (
                analysis_df.groupby("NOMBRE_CLIENTE", dropna=False)["IMPORTE_REAL"]
                .sum()
                .sort_values(ascending=False)
                .head(top_n_clients)
            )
            st.pyplot(make_bar_chart(client_amount, "Top clientes por importe", "Cliente", "Importe"))

    with g2:
        st.markdown("## 🌀 Registros por ciclo")
        if "CICLO_FACTURACION" in filtered_df.columns:
            cycle_count = filtered_df["CICLO_FACTURACION"].value_counts().sort_values(ascending=False)
            st.pyplot(make_bar_chart(cycle_count, "Cantidad de registros por ciclo", "Ciclo", "Registros"))

    g3, g4 = st.columns(2, gap="small")

    with g3:
        st.markdown("## 💰 Importe por ciclo")
        if {"CICLO_FACTURACION", "IMPORTE_REAL"}.issubset(analysis_df.columns):
            cycle_amount = analysis_df.groupby("CICLO_FACTURACION")["IMPORTE_REAL"].sum().sort_values(ascending=False)
            st.pyplot(make_bar_chart(cycle_amount, "Importe por ciclo de facturación", "Ciclo", "Importe"))

    with g4:
        st.markdown("## 📌 Registros por estado")
        if "ESTADO" in filtered_df.columns:
            status_count = filtered_df["ESTADO"].value_counts().sort_values(ascending=False)
            st.pyplot(make_bar_chart(status_count, "Cantidad de registros por estado", "Estado", "Registros"))

    st.markdown("## 🧪 Comparativo estadístico por tipo de facturación")
    if {"TIPO_2", "IMPORTE_REAL"}.issubset(filtered_df.columns):
        selected_tipo2_for_stats = st.multiselect(
            "Selecciona valores del tipo de facturación para comparar estadísticos de IMPORTE_REAL",
            sorted(filtered_df["TIPO_2"].dropna().unique().tolist()),
            default=sorted(filtered_df["TIPO_2"].dropna().unique().tolist())[:5],
        )

        if selected_tipo2_for_stats:
            compare_stats = (
                filtered_df[filtered_df["TIPO_2"].isin(selected_tipo2_for_stats)]
                .groupby("TIPO_2")["IMPORTE_REAL"]
                .agg([
                    ("registros", "count"),
                    ("suma", "sum"),
                    ("promedio", "mean"),
                    ("mediana", "median"),
                    ("minimo", "min"),
                    ("maximo", "max"),
                    ("desv_estandar", "std"),
                ])
                .reset_index()
                .sort_values("suma", ascending=False)
            )

            compare_stats_display = compare_stats.copy()
            money_cols = ["suma", "promedio", "mediana", "minimo", "maximo", "desv_estandar"]

            ventas_mask = compare_stats_display["TIPO_2"].astype(str).str.upper() == "VENTAS"
            for col in money_cols:
                compare_stats_display.loc[ventas_mask, col] = compare_stats_display.loc[ventas_mask, col].apply(format_cop)
                compare_stats_display.loc[~ventas_mask, col] = compare_stats_display.loc[~ventas_mask, col].apply(
                    lambda x: format_number(x, 2)
                )

            compare_stats_display = compare_stats_display.rename(columns={"TIPO_2": "tipo de facturación"})
            st.dataframe(compare_stats_display, use_container_width=True, hide_index=True)

    st.markdown("## 📅 Evolución temporal por FECHA_GRUPO")
    if {"FECHA_GRUPO", "IMPORTE_REAL"}.issubset(analysis_df.columns):
        time_amount = (
            analysis_df.dropna(subset=["FECHA_GRUPO"])
            .groupby("FECHA_GRUPO")["IMPORTE_REAL"]
            .sum()
            .sort_index()
        )
        if len(time_amount) > 0:
            st.pyplot(make_line_chart(time_amount, "Importe total por fecha de grupo", "Fecha grupo", "Importe"))

    chart_left, chart_right = st.columns(2, gap="small")

    with chart_left:
        st.markdown("## 🧮 Distribución del importes")
        if "IMPORTE_REAL" in analysis_df.columns:
            st.pyplot(make_histogram(analysis_df["IMPORTE_REAL"], "Histograma de IMPORTE_REAL", "IMPORTE_REAL"))

    with chart_right:
        st.markdown("## 🧾 Resumen por cliente")
        if {"NOMBRE_CLIENTE", "IMPORTE_REAL", "ALQUILER_VARIABLE"}.issubset(analysis_df.columns):
            summary_client = (
                analysis_df.groupby("NOMBRE_CLIENTE")
                .agg(
                    alquileres=("ALQUILER_VARIABLE", "nunique"),
                    registros=("ALQUILER_VARIABLE", "count"),
                    importe_total=("IMPORTE_REAL", "sum"),
                    importe_promedio=("IMPORTE_REAL", "mean"),
                )
                .sort_values("importe_total", ascending=False)
                .reset_index()
            )

            summary_client_display = summary_client.copy()

            if selected_tipo2_metric == "VENTAS":
                summary_client_display["importe_total"] = summary_client_display["importe_total"].apply(format_cop)
                summary_client_display["importe_promedio"] = summary_client_display["importe_promedio"].apply(format_cop)
            else:
                summary_client_display["importe_total"] = summary_client_display["importe_total"].apply(
                    lambda x: format_number(x, 2)
                )
                summary_client_display["importe_promedio"] = summary_client_display["importe_promedio"].apply(
                    lambda x: format_number(x, 2)
                )

            st.dataframe(summary_client_display.head(top_n_clients), use_container_width=True, hide_index=True)


    if show_duplicates and duplicates_count > 0:
        st.markdown("## ♻️ Filas duplicadas")
        st.dataframe(filtered_df[filtered_df.duplicated()].head(50), use_container_width=True)

else:
    st.info("Sube el CSV de Property para iniciar el análisis especializado.")

st.caption("Proyecto Curso IA EOH • análisis especializado de Property ")