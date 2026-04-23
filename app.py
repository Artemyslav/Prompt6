import streamlit as st
import pandas as pd
import time
import random
import plotly.graph_objects as go

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Прогнозирование спроса", layout="wide")

# Тексты интерфейса
TEXTS = {
    "static": {
        "title": "Панель прогнозирования спроса",
        "stock_label": "Текущий остаток, шт.",
        "forecast_label": "Прогноз спроса, шт.",
        "rec_label": "Рекомендация к закупке, шт."
    },
    "dynamic": {
        "optimal": "Статус: Оптимальный баланс. Закупки не требуются.",
        "deficit": "ВНИМАНИЕ: высокий риск дефицита. Прогноз превышает остаток на {diff}%.",
        "overstock": "ВНИМАНИЕ: риск перезатара. Остаток превышает прогноз на {diff}%."
    },
    "alerts": {
        "buy_now": "СРОЧНАЯ ЗАКУПКА: требуется пополнение {qty} ед.",
        "hold": "ЗАДЕРЖАТЬ ЗАКУПКУ: текущих остатков достаточно на 2+ цикла.",
        "data_error": "Ошибка формата. Требуются колонки: timestamp, product_id, plan_qty, fact_sales, current_stock"
    }
}

# -------------------- STYLES (CSS) --------------------
# Этот блок красит интерфейс в темную тему
st.markdown("""
<style>
    /* Основной фон и текст */
    body, .block-container, .main {
        background-color: #12141A !important;
        color: #E2E8F0 !important;
    }
    
    /* Боковая панель (Sidebar) */
    .css-1lcbmhc, .css-1r6slb0, .stSidebar {
        background-color: #161B22 !important;
        border-right: 1px solid #30363D !important;
    }
    
    /* Метрики */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        color: #E2E8F0 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
    }
    
    /* Заголовки */
    h1, h2, h3, h4, h5, h6 {
        color: #E2E8F0 !important;
    }
    
    /* Кнопки */
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------
st.title(TEXTS["static"]["title"])
st.markdown("---")

# -------------------- SIDEBAR --------------------
st.sidebar.header("⚙️ Управление данными")

uploaded_file = st.sidebar.file_uploader(
    "Загрузите CSV с историей продаж", 
    type=["csv"],
    help="Файл должен содержать колонки: timestamp, product_id, plan_qty, fact_sales, current_stock"
)

df = None

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Проверка наличия требуемых колонок
        required_cols = {"timestamp", "product_id", "plan_qty", "fact_sales", "current_stock"}
        if not required_cols.issubset(df.columns):
            st.error(TEXTS["alerts"]["data_error"])
            st.stop()
        
        # Преобразование timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
    except Exception as e:
        st.error(f"Ошибка чтения файла: {str(e)}")
        st.stop()

# Если файл не загружен
if df is None:
    st.info("📂 Загрузите CSV-файл для начала анализа")
    st.stop()

# -------------------- FILTERS --------------------
st.sidebar.markdown("---")
st.sidebar.header("📊 Фильтры")

products = sorted(df["product_id"].unique())
selected_product = st.sidebar.selectbox(
    "Выберите товар (SKU)", 
    products,
    index=0
)

filtered_df = df[df["product_id"] == selected_product].sort_values("timestamp")

if filtered_df.empty:
    st.warning("Нет данных для выбранного товара")
    st.stop()

min_t = filtered_df["timestamp"].min().to_pydatetime()
max_t = filtered_df["timestamp"].max().to_pydatetime()

time_range = st.sidebar.slider(
    "Период анализа",
    min_value=min_t,
    max_value=max_t,
    value=(min_t, max_t),
    format="DD.MM.YYYY"
)

filtered_df = filtered_df[
    (filtered_df["timestamp"] >= time_range[0]) & 
    (filtered_df["timestamp"] <= time_range[1])
].copy()

if filtered_df.empty:
    st.warning("Нет данных за выбранный период")
    st.stop()

# -------------------- ML SIMULATION --------------------
st.sidebar.markdown("---")

# Имитация "мышления" ИИ
with st.spinner("🤖 Анализ исторических данных и расчёт прогноза..."):
    time.sleep(random.uniform(0.6, 0.9))
    
    # Берём последние данные
    latest = filtered_df.iloc[-1]
    
    # Симуляция ML-прогноза
    last_fact = latest["fact_sales"]
    trend_factor = random.uniform(1.05, 1.25)
    forecast = last_fact * trend_factor
    
    current_stock = latest["current_stock"]
    
    # Логика определения статуса
    if current_stock == 0:
        status = "deficit"
        diff = 999
        rec = int(forecast)
    elif current_stock < forecast * 0.8:
        status = "deficit"
        diff = round(((forecast - current_stock) / current_stock) * 100, 1)
        rec = max(0, int(forecast - current_stock + (current_stock * 0.1)))
    elif current_stock > forecast * 1.3:
        status = "overstock"
        diff = round(((current_stock - forecast) / forecast) * 100, 1)
        rec = 0
    else:
        status = "optimal"
        diff = 0
        rec = 0

# -------------------- METRICS --------------------
st.markdown("### 📈 Ключевые показатели")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label=TEXTS["static"]["stock_label"],
        value=f"{current_stock:.0f}",
        delta=None
    )

with col2:
    st.metric(
        label=TEXTS["static"]["forecast_label"],
        value=f"{forecast:.0f}",
        delta=f"{trend_factor*100-100:.1f}%"
    )

with col3:
    st.metric(
        label=TEXTS["static"]["rec_label"],
        value=f"{rec:.0f}",
        delta=None
    )

st.markdown("---")

# -------------------- ALERTS --------------------
if status == "deficit":
    st.error(f"🚨 {TEXTS['alerts']['buy_now'].format(qty=rec)}")
    st.error(f"⚠️ {TEXTS['dynamic']['deficit'].format(diff=diff)}")
elif status == "overstock":
    st.warning(f"⏸️ {TEXTS['alerts']['hold']}")
    st.warning(f"📦 {TEXTS['dynamic']['overstock'].format(diff=diff)}")
else:
    st.success(f"✅ {TEXTS['dynamic']['optimal']}")

# -------------------- PLOT --------------------
st.markdown("### 📊 Динамика продаж")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=filtered_df["timestamp"],
    y=filtered_df["plan_qty"],
    mode="lines",
    name="План",
    line=dict(color="#3B82F6", width=2),
    hovertemplate="<b>План</b><br>Дата: %{x}<br>Количество: %{y}<extra></extra>"
))

fig.add_trace(go.Scatter(
    x=filtered_df["timestamp"],
    y=filtered_df["fact_sales"],
    mode="lines",
    name="Факт",
    line=dict(color="#10B981", width=2),
    hovertemplate="<b>Факт</b><br>Дата: %{x}<br>Количество: %{y}<extra></extra>"
))

last_date = filtered_df["timestamp"].max()
next_date = last_date + pd.Timedelta(days=1)

fig.add_trace(go.Scatter(
    x=[last_date, next_date],
    y=[last_fact, forecast],
    mode="lines+markers",
    name="Прогноз ИИ",
    line=dict(color="#F59E0B", width=2, dash="dash"),
    marker=dict(size=8),
    hovertemplate="<b>Прогноз</b><br>Дата: %{x}<br>Количество: %{y}<extra></extra>"
))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#12141A",
    plot_bgcolor="#12141A",
    font=dict(color="#E2E8F0", family="Inter", size=12),
    margin=dict(l=40, r=20, t=30, b=40),
    height=500,
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

fig.update_xaxes(gridcolor="#1E293B", showgrid=True)
fig.update_yaxes(gridcolor="#1E293B", showgrid=True)

st.plotly_chart(fig, use_container_width=True)

# -------------------- DATA TABLE --------------------
with st.expander("📋 Просмотр данных за выбранный период"):
    display_df = filtered_df.copy()
    display_df["timestamp"] = display_df["timestamp"].dt.strftime("%d.%m.%Y")
    st.dataframe(display_df, use_container_width=True)

# -------------------- FOOTER --------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #94A3B8; font-size: 12px;'>"
    "Лабораторная работа №6 | Промпт-инжиниринг | Вариант 15 | ВятГУ, 2026"
    "</div>",
    unsafe_allow_html=True
)
