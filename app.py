import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf

# ══════════════════════════════════════════════════════════════
# THEME / BRAND
# ══════════════════════════════════════════════════════════════
APP_NAME = "WasherBot"
LOGO_PATH = "assets/logo.png"

NAVY_900 = "#071225"
NAVY_800 = "#0B1B33"
NAVY_700 = "#102A4C"
ACCENT = "#2E86FF"
ACCENT_2 = "#38BDF8"
GOOD = "#22C55E"
BAD = "#EF4444"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"
BORDER = "rgba(255,255,255,0.08)"

st.set_page_config(
    page_title=f"{APP_NAME} — Калькулятор окупаемости",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# CSS STYLES
# ══════════════════════════════════════════════════════════════
st.markdown(
    f"""
<style>
.stApp {{
    background: radial-gradient(1200px 700px at 15% 0%, {NAVY_700} 0%, {NAVY_900} 55%, #050A14 100%);
    color: {TEXT};
}}
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {NAVY_800} 0%, {NAVY_900} 100%);
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{
    color: {TEXT};
}}
.block-container {{
    padding-top: 2.5rem;
}}
div[data-testid="stMetric"] {{
    background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.03) 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 14px 14px 10px 14px;
}}
div[data-testid="stMetric"] label {{
    color: {MUTED} !important;
}}
div[data-testid="stMetricValue"] {{
    color: {TEXT} !important;
    font-weight: 800 !important;
}}
h1, h2, h3 {{
    color: {TEXT};
}}
.small-muted {{
    color: {MUTED};
    font-size: 14px;
}}
div[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 14px;
    overflow: hidden;
}}
div[data-testid="stPlotlyChart"] {{
    background: transparent;
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 10px;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════
def rub(x):
    try:
        return f"{x:,.0f} ₽".replace(",", " ")
    except:
        return f"{x} ₽"

def pct(x):
    try:
        return f"{x:.1f}%"
    except:
        return f"{x}%"

def style_plotly_dark(fig, title: str):
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=440,
        margin=dict(l=20, r=20, t=70, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=14),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    return fig

# ══════════════════════════════════════════════════════════════
# HEADER WITH LOGO
# ══════════════════════════════════════════════════════════════
try:
    c_logo, c_title = st.columns([1, 5])
    with c_logo:
        st.image(LOGO_PATH, use_container_width=True)
    with c_title:
        st.markdown(f"<h1 style='margin-bottom:0'>{APP_NAME} — Калькулятор окупаемости</h1>", unsafe_allow_html=True)
        st.markdown("<div class='small-muted'>Рассчитайте прибыльность роботизированной мойки за 2 минуты</div>", unsafe_allow_html=True)
except:
    st.title(f"🤖 {APP_NAME} — Калькулятор окупаемости")
    st.caption("Рассчитайте прибыльность роботизированной мойки за 2 минуты")

st.write("")

# ══════════════════════════════════════════════════════════════
# SIDEBAR: INPUT PARAMETERS
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("1. Параметры Мойки")
    traffic = st.slider("Плановый трафик (авто/сутки)", 20, 200, 50)
    capex = st.number_input("Инвестиции (₽)", value=6_000_000, step=100_000)

    st.header("2. Региональные Тарифы")
    col1, col2 = st.columns(2)
    with col1:
        price_kw = st.number_input("Эл-во (₽/кВт)", value=8.5, step=0.5)
        price_water = st.number_input("Вода+Сток (₽/м³)", value=68.0, step=1.0)
    with col2:
        tax_system = st.selectbox("Система налогов", ["УСН 6% (Доходы)", "УСН 15% (Д-Р)", "Патент"])
        acquiring = st.number_input("Эквайринг (%)", value=2.0, step=0.1) / 100

    if tax_system == "УСН 6% (Доходы)":
        tax_rate_income = 0.06
        tax_rate_profit = 0.0
        tax_fix_val = 0
    elif tax_system == "УСН 15% (Д-Р)":
        tax_rate_income = 0.0
        tax_rate_profit = 0.15
        tax_fix_val = 0
    else:
        tax_rate_income = 0.0
        tax_rate_profit = 0.0
        tax_fix_val = st.number_input("Патент (₽/мес)", value=5000)

    st.header("3. Постоянные Расходы")
    rent = st.number_input("Аренда (мес)", value=100_000, step=5000)
    salary = st.number_input("ФОТ (мес)", value=120_000, step=5000)
    marketing = st.number_input("Маркетинг (мес)", value=15_000, step=1000)
    waste = st.number_input("Илосос (мес)", value=15_000, step=1000)

    st.header("4. Опции")
    use_osmos = st.checkbox("Осмос / Умягчение", value=True)
    use_recycle = st.checkbox("Рециркуляция воды", value=False)

    with st.expander("⚙️ Расширенные настройки"):
        osmos_cost = st.number_input("Расх. осмос (₽/авто)", value=5.0) if use_osmos else 0.0
        recycle_savings = st.slider("Экономия воды (%)", 0, 80, 70) if use_recycle else 0
        recycle_energy = st.number_input("Доп. энергия (кВт)", value=0.5) if use_recycle else 0.0
        st.divider()
        price_std = st.number_input("Цена 'Стандарт'", value=450)
        price_prm = st.number_input("Цена 'Премиум'", value=750)
        chem_std = st.number_input("Химия 'Стандарт'", value=16.0)
        chem_prm = st.number_input("Химия 'Премиум'", value=25.0)

# ══════════════════════════════════════════════════════════════
# CALCULATIONS
# ══════════════════════════════════════════════════════════════
# Ресурсы на 1 авто
res_std = {"water": 130, "energy": 1.2, "chem": chem_std}
res_prm = {"water": 320, "energy": 1.5, "chem": chem_prm}

# Модификаторы
water_mult = (100 - recycle_savings) / 100 if use_recycle else 1.0
energy_add = recycle_energy if use_recycle else 0.0
supply_add = (osmos_cost if use_osmos else 0.0) + (2.0 if use_recycle else 0.0)

def calc_cogs(res):
    water_cost = (res["water"] * water_mult / 1000) * price_water
    energy_cost = (res["energy"] + energy_add) * price_kw
    return water_cost + energy_cost + res["chem"] + supply_add

cogs_std = calc_cogs(res_std)
cogs_prm = calc_cogs(res_prm)

# Средние (60% Стандарт, 40% Премиум)
avg_check = (price_std * 0.6) + (price_prm * 0.4)
avg_cogs = (cogs_std * 0.6) + (cogs_prm * 0.4)

# Точка безубыточности
fixed_costs = rent + salary + marketing + waste + tax_fix_val

if tax_system == "УСН 6% (Доходы)":
    margin_per_car = avg_check * (1 - acquiring - tax_rate_income) - avg_cogs
else:
    margin_per_car = avg_check * (1 - acquiring) - avg_cogs

break_even = (fixed_costs / margin_per_car / 30) if margin_per_car > 0 else 999

# Симуляция 36 месяцев
seasonality = [1.1, 1.05, 1.15, 0.85, 0.80, 0.90, 0.90, 0.95, 1.00, 1.10, 1.25, 1.30]
data = []
balance = -capex
payback_idx = None
cash_flows = [-capex]

for m in range(36):
    season = seasonality[m % 12]
    ramp = [0.5, 0.7, 0.9][m] if m < 3 else 1.0
    cars = traffic * 30 * season * ramp
    
    revenue = cars * avg_check
    var_cogs = cars * avg_cogs
    var_acq = revenue * acquiring
    
    if tax_system == "УСН 6% (Доходы)":
        tax = revenue * tax_rate_income
    elif tax_system == "УСН 15% (Д-Р)":
        base = revenue - var_cogs - var_acq - (rent + salary + marketing + waste)
        tax = max(0, base * tax_rate_profit)
    else:
        tax = tax_fix_val
    
    maintenance = 60000 if (m + 1) % 4 == 0 else 0
    expenses = var_cogs + var_acq + rent + salary + marketing + waste + tax + maintenance
    profit = revenue - expenses
    balance += profit
    cash_flows.append(profit)
    
    if balance >= 0 and payback_idx is None:
        payback_idx = m + 1
    
    data.append({
        "Месяц": m + 1,
        "Трафик": int(cars),
        "Выручка": int(revenue),
        "Расходы": int(expenses),
        "Прибыль": int(profit),
        "Баланс": int(balance)
    })

df = pd.DataFrame(data)

# IRR
try:
    irr_m = npf.irr(cash_flows)
    irr_annual = ((1 + irr_m) ** 12 - 1) * 100 if irr_m and np.isfinite(irr_m) else 0
except:
    irr_annual = 0

# ══════════════════════════════════════════════════════════════
# KPI METRICS
# ══════════════════════════════════════════════════════════════
st.subheader("📊 Ключевые показатели")

payback_text = f"{payback_idx} мес." if payback_idx else "> 36 мес."

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Окупаемость", payback_text)
m2.metric("Точка безубыточности", f"{break_even:.0f} авто/день")
m3.metric("Средний чек", rub(avg_check))
m4.metric("Себестоимость", rub(avg_cogs))
m5.metric("IRR (годовой)", pct(irr_annual))

st.divider()

a1, a2, a3 = st.columns(3)
a1.metric("Выручка / мес (средняя)", rub(df["Выручка"].mean()))
a2.metric("Прибыль / мес (средняя)", rub(df["Прибыль"].mean()))
a3.metric("Баланс через 3 года", rub(df["Баланс"].iloc[-1]))

# ══════════════════════════════════════════════════════════════
# CHARTS
# ══════════════════════════════════════════════════════════════
t1, t2 = st.tabs(["💰 Денежный поток", "📉 Точка безубыточности"])

with t1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Месяц"], y=df["Прибыль"],
        name="Прибыль",
        marker_color="rgba(46,134,255,0.6)",
        hovertemplate="Месяц %{x}<br>Прибыль: %{y:,.0f} ₽<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df["Месяц"], y=df["Баланс"],
        name="Накопленный баланс",
        line=dict(color=ACCENT_2, width=3),
        hovertemplate="Месяц %{x}<br>Баланс: %{y:,.0f} ₽<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=BAD, opacity=0.7)
    if payback_idx:
        fig.add_vline(x=payback_idx, line_dash="dot", line_color=GOOD,
                      annotation_text=f"Окупаемость: {payback_idx} мес", annotation_font_color=TEXT)
    fig = style_plotly_dark(fig, "Денежный поток и окупаемость")
    st.plotly_chart(fig, use_container_width=True)

with t2:
    max_x = max(150, traffic * 1.5, break_even * 1.4)
    x_arr = np.linspace(0, max_x, 150)
    y_rev = x_arr * 30 * avg_check
    y_cost = []
    for tr in x_arr:
        rev = tr * 30 * avg_check
        cogs = tr * 30 * avg_cogs
        acq = rev * acquiring
        if tax_system == "УСН 6% (Доходы)":
            tx = rev * tax_rate_income
        elif tax_system == "УСН 15% (Д-Р)":
            tx = max(0, (rev - cogs - acq - fixed_costs) * tax_rate_profit)
        else:
            tx = tax_fix_val
        y_cost.append(fixed_costs + cogs + acq + tx)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_arr, y=y_rev, name="Выручка", line=dict(color=GOOD, width=3)))
    fig2.add_trace(go.Scatter(x=x_arr, y=y_cost, name="Расходы", line=dict(color=BAD, width=3)))
    fig2.add_trace(go.Scatter(
        x=x_arr, y=np.maximum(np.array(y_rev) - np.array(y_cost), 0),
        name="Прибыль", fill="tozeroy", fillcolor="rgba(34,197,94,0.1)", line=dict(width=0)
    ))
    fig2.add_vline(x=break_even, line_dash="dash", line_color="white", opacity=0.5,
                   annotation_text=f"BEP: {break_even:.0f}", annotation_font_color=TEXT)
    fig2.add_vline(x=traffic, line_dash="dot", line_color=ACCENT,
                   annotation_text=f"План: {traffic}", annotation_font_color=TEXT)
    fig2 = style_plotly_dark(fig2, "Точка безубыточности")
    st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TABLE & EXPORT
# ══════════════════════════════════════════════════════════════
with st.expander("📑 Детальная таблица по месяцам"):
    st.dataframe(df, use_container_width=True)

col_dl, col_cta = st.columns([1, 2])
with col_dl:
    st.download_button(
        "📥 Скачать отчёт (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        "washerbot_model.csv",
        "text/csv"
    )

# ══════════════════════════════════════════════════════════════
# CTA (Call to Action)
# ══════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
### 🚀 Хотите узнать больше?

Получите персональный расчёт для вашего региона и консультацию по выбору оборудования.

**📞 Телефон:** +7 (XXX) XXX-XX-XX  
**📧 Email:** info@washerbot.ru  
**🌐 Сайт:** [washerbot.ru](https://washerbot.ru)
""")

st.caption("© 2024 WasherBot — Роботизированные мойки автомобилей")
