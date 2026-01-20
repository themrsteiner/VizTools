import io
import tempfile
from typing import List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="VizTools", layout="wide")

st.title("VizTools — CSV/Excel Visualizer")
st.caption("Upload a file, map columns, and export the chart (HTML/PNG).")


@st.cache_data(show_spinner=False)
def load_table(file_bytes: bytes, filename: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")


def split_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    other_cols = [c for c in df.columns if c not in numeric_cols]
    return numeric_cols, other_cols


def build_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str],
    symbol: Optional[str],
    size: Optional[str],
    hover: List[str],
    opacity: float,
):
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color if color else None,
        symbol=symbol if symbol else None,
        size=size if size else None,
        hover_data=hover if hover else None,
        opacity=opacity,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), legend_title_text="")
    return fig


def fig_to_png_bytes(fig) -> bytes:
    # More reliable than spinning up a browser + temp files.
    # Requires kaleido (pinned in requirements.txt).
    return fig.to_image(format="png", scale=2)



def fig_to_html_bytes(fig) -> bytes:
    html = fig.to_html(full_html=True, include_plotlyjs="cdn")
    return html.encode("utf-8")


with st.sidebar:
    st.header("1) Upload")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

    st.header("2) Plot options")
    max_rows = st.number_input(
        "Max rows to plot (samples if larger)",
        min_value=200,
        max_value=2_000_000,
        value=50_000,
        step=1000,
    )
    opacity = st.slider("Point opacity", 0.05, 1.0, 0.85, 0.05)

    st.header("3) Export")
    export_name = st.text_input("Base filename", value="chart")


if not uploaded:
    st.info("Upload a CSV or Excel file to begin.")
    st.stop()

file_bytes = uploaded.getvalue()

# Excel sheet selector
sheet = None
if uploaded.name.lower().endswith((".xlsx", ".xls")):
    try:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        sheets = xl.sheet_names
        if len(sheets) > 1:
            sheet = st.selectbox("Select Excel sheet", sheets, index=0)
        else:
            sheet = sheets[0]
    except Exception:
        sheet = None

try:
    df = load_table(file_bytes, uploaded.name, sheet_name=sheet)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

df.columns = [str(c) for c in df.columns]

st.subheader("Data preview")
st.write(f"Rows: **{len(df):,}** | Columns: **{len(df.columns):,}**")
# SECTION A CHANGE: use_container_width -> width
st.dataframe(df.head(200), width="stretch")

numeric_cols, other_cols = split_columns(df)
all_cols = df.columns.tolist()

if len(numeric_cols) < 2:
    st.warning("Need at least **two numeric columns** for X and Y.")
    st.stop()

st.subheader("Mapping")
c1, c2, c3 = st.columns([1.2, 1.2, 1.6])

with c1:
    x = st.selectbox("X axis (numeric)", numeric_cols, index=0)
    y = st.selectbox("Y axis (numeric)", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)

with c2:
    color = st.selectbox("Color (categorical)", ["(none)"] + other_cols, index=0)
    symbol = st.selectbox("Shape / symbol (categorical)", ["(none)"] + other_cols, index=0)
    size = st.selectbox("Size (numeric)", ["(none)"] + numeric_cols, index=0)

with c3:
    tooltip = st.multiselect(
        "Tooltip fields",
        options=all_cols,
        default=[c for c in [x, y] if c in all_cols],
    )

plot_df = df
if len(df) > int(max_rows):
    plot_df = df.sample(int(max_rows), random_state=42)

fig = build_scatter(
    plot_df,
    x=x,
    y=y,
    color=None if color == "(none)" else color,
    symbol=None if symbol == "(none)" else symbol,
    size=None if size == "(none)" else size,
    hover=tooltip,
    opacity=opacity,
)

st.subheader("Chart")
# SECTION A CHANGE: use_container_width -> width
st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

st.subheader("Export")
st.caption(
    "PNG export note: The **Download PNG** button generates a clean, server-rendered image. "
    "Use the chart toolbar’s camera icon exports a PNG that matches theme. "
)
colA, colB = st.columns(2)

with colA:
    html_bytes = fig_to_html_bytes(fig)
    st.download_button(
        "Download interactive HTML",
        data=html_bytes,
        file_name=f"{export_name}.html",
        mime="text/html",
        use_container_width=True,
    )

with colB:
    try:
        png_bytes = fig_to_png_bytes(fig)
        st.download_button(
            "Download PNG",
            data=png_bytes,
            file_name=f"{export_name}.png",
            mime="image/png",
            use_container_width=True,
        )
    except Exception as e:
        st.warning(
            "PNG export failed here. Use the chart toolbar’s 'Download plot as png' button instead.\n\n"
            f"Details: {e}"
        )
