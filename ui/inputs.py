from __future__ import annotations

from typing import List

import streamlit as st

from data.catalogs import (
    DEFAULT_MODEL,
    DEFAULT_REGION,
    PROGRAMS_DEFAULT,
    REGIONS,
    WASHER_CATALOG,
)
from data.washer_access import supports_extra_dryers
from domain.models import WashProgram
from domain.params import ProParams, SimpleParams
from finance.taxes import TAX_REGIMES_LABELS
from ui.branding import sidebar_logo_html
from ui.model_display import format_effective_power_kw
from ui.presentation_mode import render_presentation_sidebar_marker
from ui.renderers import fmt_money
from ui.scenario_ui import render_scenario_sidebar_block
from ui.water_discharge_ui import (
    render_water_discharge_profile_selector,
    render_water_discharge_usage_guardrail,
)
from ui.ui_labels import SidebarSections, format_sidebar_heading


def render_sidebar_simple() -> SimpleParams:
    """Рендер сайдбара простого режима. Возвращает SimpleParams."""

    with st.sidebar:
        st.markdown(sidebar_logo_html(), unsafe_allow_html=True)
        render_presentation_sidebar_marker()
        st.markdown(format_sidebar_heading(SidebarSections.EQUIPMENT), unsafe_allow_html=True)

        model_options = list(WASHER_CATALOG.keys())
        model_labels = [WASHER_CATALOG[k].name for k in model_options]
        default_idx = model_options.index(DEFAULT_MODEL)

        selected_label = st.selectbox(
            "Модель Leisuwash",
            options=model_labels,
            index=default_idx,
            key="s_model",
        )
        model_code = model_options[model_labels.index(selected_label)]
        model = WASHER_CATALOG[model_code]

        extra_dryers_enabled = False
        if supports_extra_dryers(model_code):
            extra_dryers_enabled = st.checkbox(
                "Доп. сушки (+2 × 5.5 кВт)",
                value=False,
                key="s_extra_dryers",
                help="Дополнительные сушки увеличивают установленную мощность на 11 кВт.",
            )

        # Краткое описание модели
        st.caption(
            f"{model.cars_per_hour} авто/час · "
            f"{format_effective_power_kw(model_code, extra_dryers_enabled=extra_dryers_enabled)} · "
            f"{model.space_required_m2} м²"
        )

        n_robots = st.slider(
            "Количество роботов на площадке",
            min_value=1, max_value=6, value=1, step=1,
            key="s_n_robots",
            help="Несколько роботов на одной площадке. Аренда/охрана/маркетинг не множатся.",
        )

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.LOCATION), unsafe_allow_html=True)

        region_options = list(REGIONS.keys())
        region_labels = [REGIONS[k].name for k in region_options]
        default_reg_idx = region_options.index(DEFAULT_REGION)

        selected_reg = st.selectbox(
            "Регион",
            options=region_labels,
            index=default_reg_idx,
            key="s_region",
        )
        region_key = region_options[region_labels.index(selected_reg)]
        reg = REGIONS[region_key]
        st.caption(
            f"Вода: {reg.water_supply:.0f}+{reg.water_sewage:.0f} ₽/м³ · "
            f"Электр.: {reg.elec_price:.1f} ₽/кВт·ч"
        )
        water_discharge_profile = render_water_discharge_profile_selector(key_prefix="s")

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.INVESTMENT), unsafe_allow_html=True)

        total_investment = st.number_input(
            "Общая сумма вложений, ₽",
            min_value=0,
            value=15_000_000,
            step=500_000,
            key="s_invest",
            help="Оборудование + СМР + помещение + запуск. Единой суммой.",
        )

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.TRAFFIC), unsafe_allow_html=True)

        cars_per_day_avg = st.number_input(
            "Авто/день на 1 робот (среднее)",
            min_value=1.0,
            max_value=float(model.cars_per_hour * 24),
            value=float(min(50, model.cars_per_hour * 12)),
            step=1.0,
            key="s_cars",
            help="С учётом сезонности — берётся среднее за год.",
        )

        work_days_month = st.slider(
            "Рабочих дней в месяце",
            min_value=20, max_value=31, value=30,
            key="s_workdays",
        )

        # Подсказка по загрузке
        max_cars = model.cars_per_hour * 24
        load_pct = cars_per_day_avg / max_cars
        if load_pct > 0.7:
            st.warning(f"Загрузка {load_pct*100:.0f}% — близко к пределу")
        elif load_pct < 0.15:
            st.info(f"Загрузка {load_pct*100:.0f}% — низкая")

        render_water_discharge_usage_guardrail(
            profile=water_discharge_profile,
            cars_per_day=cars_per_day_avg,
            water_per_wash_l=model.water_per_wash_l,
        )

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.PROGRAMS), unsafe_allow_html=True)

        programs: List[WashProgram] = []
        for i, p_def in enumerate(PROGRAMS_DEFAULT):
            with st.expander(f"{p_def.name}", expanded=(i == 0)):
                price = st.number_input(
                    f"Цена «{p_def.name}», ₽",
                    min_value=0,
                    value=int(p_def.price_rub),
                    step=50,
                    key=f"s_prog_price_{p_def.code}",
                )
                share = st.slider(
                    f"Доля «{p_def.name}», %",
                    min_value=0, max_value=100,
                    value=int(p_def.share_default * 100),
                    step=5,
                    key=f"s_prog_share_{p_def.code}",
                )
                programs.append(WashProgram(
                    code=p_def.code,
                    name=p_def.name,
                    price_rub=float(price),
                    duration_min=p_def.duration_min,
                    water_factor=p_def.water_factor,
                    elec_factor=p_def.elec_factor,
                    chem_factor=p_def.chem_factor,
                    share_default=share / 100.0,
                ))

        # Нормализация долей
        total_share = sum(p.share_default for p in programs)
        if total_share > 0 and abs(total_share - 1.0) > 0.001:
            st.caption(f"Сумма долей: {total_share*100:.0f}% — нормализуется автоматически")
            programs = [
                WashProgram(
                    code=p.code, name=p.name, price_rub=p.price_rub,
                    duration_min=p.duration_min,
                    water_factor=p.water_factor, elec_factor=p.elec_factor,
                    chem_factor=p.chem_factor,
                    share_default=p.share_default / total_share,
                )
                for p in programs
            ]

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.STAFF), unsafe_allow_html=True)

        admin_salary = st.number_input(
            "ЗП администратора, ₽/мес (gross)",
            min_value=0,
            value=60_000,
            step=5_000,
            key="s_admin_salary",
            help="1 администратор на площадку. Включая будущий НДФЛ и страховые взносы.",
        )

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.FIXED_COSTS), unsafe_allow_html=True)

        # Аренда — подсказка от модели
        suggested_rent = int(reg.rent_per_m2 * model.space_required_m2 * n_robots)
        rent_month = st.number_input(
            "Аренда, ₽/мес",
            min_value=0,
            value=suggested_rent,
            step=10_000,
            key="s_rent",
            help=f"Подсказка: {reg.rent_per_m2:.0f} ₽/м² × {model.space_required_m2 * n_robots:.0f} м²",
        )

        other_fixed = st.number_input(
            "Прочее (охрана, маркетинг, связь), ₽/мес",
            min_value=0,
            value=40_000,
            step=5_000,
            key="s_other_fixed",
        )

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.TAXES), unsafe_allow_html=True)

        tax_options_simple = ["USN_INCOME", "USN_PROFIT", "PATENT"]
        tax_labels = [TAX_REGIMES_LABELS[k] for k in tax_options_simple]
        tax_choice = st.selectbox(
            "Режим налогообложения",
            options=tax_labels,
            index=0,
            key="s_tax",
        )
        tax_regime = tax_options_simple[tax_labels.index(tax_choice)]

        # ──────────────────────────────────────
        st.markdown(format_sidebar_heading(SidebarSections.HORIZON), unsafe_allow_html=True)

        horizon_years = st.slider(
            "Горизонт расчёта, лет",
            min_value=1, max_value=10, value=5,
            key="s_horizon",
        )
        horizon_months = horizon_years * 12

        simple_params_preview = SimpleParams(
            model_code=model_code,
            extra_dryers_enabled=extra_dryers_enabled,
            n_robots=n_robots,
            region_key=region_key,
            total_investment=float(total_investment),
            cars_per_day_avg=float(cars_per_day_avg),
            work_days_month=work_days_month,
            programs=programs,
            admin_salary_gross=float(admin_salary),
            rent_month=float(rent_month),
            other_fixed=float(other_fixed),
            tax_regime=tax_regime,
            horizon_months=horizon_months,
            water_discharge_profile=water_discharge_profile,
        )
        render_scenario_sidebar_block("simple", simple_params_preview)

    return simple_params_preview


def render_sidebar_pro() -> ProParams:
    """Расширенный сайдбар для углублённого режима."""

    with st.sidebar:
        st.markdown(sidebar_logo_html(), unsafe_allow_html=True)
        render_presentation_sidebar_marker()
        # ── Оборудование ──
        st.markdown(format_sidebar_heading(SidebarSections.EQUIPMENT), unsafe_allow_html=True)

        model_options = list(WASHER_CATALOG.keys())
        model_labels = [WASHER_CATALOG[k].name for k in model_options]
        default_idx = model_options.index(DEFAULT_MODEL)

        selected_label = st.selectbox(
            "Модель Leisuwash",
            options=model_labels, index=default_idx, key="p_model",
        )
        model_code = model_options[model_labels.index(selected_label)]
        model = WASHER_CATALOG[model_code]

        extra_dryers_enabled = False
        if supports_extra_dryers(model_code):
            extra_dryers_enabled = st.checkbox(
                "Доп. сушки (+2 × 5.5 кВт)",
                value=False,
                key="p_extra_dryers",
                help="Дополнительные сушки увеличивают установленную мощность на 11 кВт.",
            )

        st.caption(
            f"{model.cars_per_hour} авто/час · "
            f"{format_effective_power_kw(model_code, extra_dryers_enabled=extra_dryers_enabled)} · "
            f"{model.water_per_wash_l} л/мойку · {model.space_required_m2} м²"
        )

        n_robots = st.slider(
            "Роботов на площадке", 1, 6, 1, 1, key="p_n_robots",
            help="Аренда/охрана/маркетинг — на площадку, не множатся",
        )

        # ── Локация ──
        st.markdown(format_sidebar_heading(SidebarSections.LOCATION), unsafe_allow_html=True)
        region_options = list(REGIONS.keys())
        region_labels = [REGIONS[k].name for k in region_options]
        default_reg_idx = region_options.index(DEFAULT_REGION)
        selected_reg = st.selectbox(
            "Регион", region_labels, index=default_reg_idx, key="p_region",
        )
        region_key = region_options[region_labels.index(selected_reg)]
        reg = REGIONS[region_key]
        st.caption(f"Вода: {reg.water_supply:.0f}+{reg.water_sewage:.0f} ₽/м³ · Эл.: {reg.elec_price:.1f} ₽/кВт·ч")
        water_discharge_profile = render_water_discharge_profile_selector(key_prefix="p")

        # ── CAPEX по статьям ──
        st.markdown(format_sidebar_heading(SidebarSections.CAPEX), unsafe_allow_html=True)

        # Подсказка по оборудованию
        equip_default = int(model.price_rub * n_robots)
        capex_equipment = st.number_input(
            "Оборудование (роботы), ₽",
            min_value=0, value=equip_default, step=500_000,
            key="p_capex_equip",
            help=f"Подсказка: {model.price_rub:,.0f} ₽ × {n_robots}",
        )
        capex_construction = st.number_input(
            "СМР, фундамент, навес, ₽",
            min_value=0, value=2_500_000, step=100_000, key="p_capex_smr",
        )
        capex_engineering = st.number_input(
            "Инженерные сети (вода/эл-во/слив), ₽",
            min_value=0, value=1_500_000, step=100_000, key="p_capex_eng",
        )
        capex_premises = st.number_input(
            "Помещение (доработка/покупка), ₽",
            min_value=0, value=0, step=500_000, key="p_capex_prem",
            help="0 — если арендуете готовое",
        )
        capex_launch = st.number_input(
            "Запуск, ПНР, маркетинг старта, ₽",
            min_value=0, value=500_000, step=50_000, key="p_capex_launch",
        )
        capex_other = st.number_input(
            "Прочее, резерв (5–10%), ₽",
            min_value=0, value=500_000, step=50_000, key="p_capex_other",
        )

        capex_total = (
            capex_equipment + capex_construction + capex_engineering
            + capex_premises + capex_launch + capex_other
        )
        st.markdown(
            f'<div class="wb-info">Итого CAPEX: <b>{fmt_money(capex_total)}</b></div>',
            unsafe_allow_html=True,
        )

        # ── Кредит ──
        st.markdown(format_sidebar_heading(SidebarSections.FINANCING), unsafe_allow_html=True)
        use_credit = st.checkbox("Использовать кредит", value=False, key="p_use_credit")

        if use_credit:
            credit_amount = st.number_input(
                "Сумма кредита, ₽ (не более CAPEX)",
                min_value=0, max_value=int(capex_total), value=int(capex_total * 0.5),
                step=500_000, key="p_credit_amount",
            )
            credit_rate = st.slider(
                "Ставка, % годовых",
                5.0, 30.0, 22.0, 0.5, key="p_credit_rate",
            ) / 100.0
            credit_term = st.slider(
                "Срок, мес", 12, 84, 48, 6, key="p_credit_term",
            )
            credit_grace = st.slider(
                "Отсрочка тела долга, мес", 0, 12, 3, 1, key="p_credit_grace",
            )
        else:
            credit_amount, credit_rate = 0.0, 0.0
            credit_term, credit_grace = 0, 0

        # ── Трафик ──
        st.markdown(format_sidebar_heading(SidebarSections.TRAFFIC), unsafe_allow_html=True)
        cars_per_day_avg = st.number_input(
            "Авто/день/робот (среднее)",
            min_value=1.0, max_value=float(model.cars_per_hour * 24),
            value=float(min(60, model.cars_per_hour * 12)),
            step=1.0, key="p_cars",
        )
        work_days_month = st.slider("Рабочих дней/мес", 20, 31, 30, key="p_workdays")
        seasonality_strength = st.slider(
            "Влияние сезонности",
            0.0, 1.0, 1.0, 0.1, key="p_seas_strength",
            help="1.0 = полная сезонность, 0.0 = выключена",
        )

        render_water_discharge_usage_guardrail(
            profile=water_discharge_profile,
            cars_per_day=cars_per_day_avg,
            water_per_wash_l=model.water_per_wash_l,
        )

        # ── Программы (5 шт.) ──
        st.markdown(format_sidebar_heading(SidebarSections.PROGRAMS_PRO), unsafe_allow_html=True)

        programs: List[WashProgram] = []
        for i, p_def in enumerate(PROGRAMS_DEFAULT):
            with st.expander(f"{p_def.name}", expanded=(i == 0)):
                price = st.number_input(
                    "Цена, ₽", min_value=0, value=int(p_def.price_rub),
                    step=50, key=f"p_prog_price_{p_def.code}",
                )
                share = st.slider(
                    "Доля, %", 0, 100,
                    int(p_def.share_default * 100), 5,
                    key=f"p_prog_share_{p_def.code}",
                )
                programs.append(WashProgram(
                    code=p_def.code, name=p_def.name,
                    price_rub=float(price), duration_min=p_def.duration_min,
                    water_factor=p_def.water_factor,
                    elec_factor=p_def.elec_factor,
                    chem_factor=p_def.chem_factor,
                    share_default=share / 100.0,
                ))

        # Нормализация
        total_share = sum(p.share_default for p in programs)
        if total_share > 0 and abs(total_share - 1.0) > 0.001:
            st.caption(f"Сумма долей: {total_share*100:.0f}% — нормализуется")
            programs = [
                WashProgram(
                    code=p.code, name=p.name, price_rub=p.price_rub,
                    duration_min=p.duration_min,
                    water_factor=p.water_factor, elec_factor=p.elec_factor,
                    chem_factor=p.chem_factor,
                    share_default=p.share_default / total_share,
                )
                for p in programs
            ]

        # ── Персонал ──
        st.markdown(format_sidebar_heading(SidebarSections.STAFF), unsafe_allow_html=True)
        n_admins = st.slider("Администраторов", 1, 4, 1, key="p_n_admins")
        admin_salary = st.number_input(
            "ЗП администратора, ₽/мес (gross)",
            min_value=0, value=60_000, step=5_000, key="p_admin_salary",
        )
        n_managers = st.slider("Управляющих", 0, 2, 0, key="p_n_managers")
        manager_salary = st.number_input(
            "ЗП управляющего, ₽/мес (gross)",
            min_value=0, value=120_000, step=5_000, key="p_manager_salary",
        )

        # ── OPEX ──
        st.markdown(format_sidebar_heading(SidebarSections.OPEX), unsafe_allow_html=True)
        suggested_rent = int(reg.rent_per_m2 * model.space_required_m2 * n_robots)
        rent = st.number_input(
            "Аренда, ₽/мес", min_value=0, value=suggested_rent, step=10_000,
            key="p_rent",
            help=f"Подсказка: {reg.rent_per_m2:.0f} ₽/м² × {model.space_required_m2 * n_robots:.0f} м²",
        )
        utilities_extra = st.number_input(
            "Коммуналка (отопление, интернет, освещение), ₽/мес",
            min_value=0, value=20_000, step=5_000, key="p_util",
        )
        security = st.number_input(
            "Охрана, видеонаблюдение, ₽/мес",
            min_value=0, value=15_000, step=5_000, key="p_security",
        )
        marketing = st.number_input(
            "Маркетинг, ₽/мес",
            min_value=0, value=20_000, step=5_000, key="p_marketing",
        )
        maintenance = st.number_input(
            "ТО и расходники, ₽/мес",
            min_value=0, value=int(8_000 * n_robots), step=2_000, key="p_maint",
        )
        insurance = st.number_input(
            "Страхование оборудования, ₽/мес",
            min_value=0, value=int(capex_equipment * 0.005 / 12), step=1_000,
            key="p_insurance",
        )
        other_opex = st.number_input(
            "Прочее, ₽/мес", min_value=0, value=10_000, step=2_000, key="p_other_opex",
        )

        # ── Налоги ──
        st.markdown(format_sidebar_heading(SidebarSections.TAXES), unsafe_allow_html=True)
        tax_options = list(TAX_REGIMES_LABELS.keys())
        tax_labels = [TAX_REGIMES_LABELS[k] for k in tax_options]
        tax_choice = st.selectbox("Режим", tax_labels, index=0, key="p_tax")
        tax_regime = tax_options[tax_labels.index(tax_choice)]

        # ── Амортизация ──
        st.markdown(format_sidebar_heading(SidebarSections.AMORTIZATION), unsafe_allow_html=True)
        amort_years = st.slider(
            "Срок амортизации оборудования, лет",
            5, 15, 7, 1, key="p_amort",
            help="Учитывается только в режиме УСН Доходы−Расходы и ОСН",
        )

        # ── Сценарии ──
        st.markdown(format_sidebar_heading(SidebarSections.SCENARIOS), unsafe_allow_html=True)
        scenario_pessim = st.slider(
            "Пессимистичный (трафик)", 0.5, 1.0, 0.7, 0.05, key="p_pessim",
        )
        scenario_optim = st.slider(
            "Оптимистичный (трафик)", 1.0, 1.8, 1.3, 0.05, key="p_optim",
        )

        # ── Экология ──
        st.markdown(format_sidebar_heading(SidebarSections.ECOLOGY), unsafe_allow_html=True)
        eco_recycle = st.slider(
            "Оборотная вода, %", 0, 95, 0, 5, key="p_eco_recycle",
            help="Сколько воды вторично используется (снижает потребление)",
        ) / 100.0
        eco_chem = st.checkbox(
            "Биоразлагаемая химия (+15% к стоимости химии)",
            value=False, key="p_eco_chem",
        )

        # ── Горизонт ──
        st.markdown(format_sidebar_heading(SidebarSections.HORIZON), unsafe_allow_html=True)
        horizon_years = st.slider(
            "Горизонт, лет", 1, 10, 7, key="p_horizon",
        )
        horizon_months = horizon_years * 12

        pro_params_preview = ProParams(
            model_code=model_code,
            extra_dryers_enabled=extra_dryers_enabled,
            n_robots=n_robots,
            region_key=region_key,
            capex_equipment=float(capex_equipment),
            capex_construction=float(capex_construction),
            capex_engineering=float(capex_engineering),
            capex_premises=float(capex_premises),
            capex_launch=float(capex_launch),
            capex_other=float(capex_other),
            use_credit=use_credit,
            credit_amount=float(credit_amount),
            credit_rate_annual=credit_rate,
            credit_term_months=credit_term,
            credit_grace_months=credit_grace,
            cars_per_day_avg=float(cars_per_day_avg),
            work_days_month=work_days_month,
            seasonality_strength=seasonality_strength,
            programs=programs,
            n_admins=n_admins,
            admin_salary_gross=float(admin_salary),
            n_managers=n_managers,
            manager_salary_gross=float(manager_salary),
            rent_month=float(rent),
            utilities_extra=float(utilities_extra),
            security_month=float(security),
            marketing_month=float(marketing),
            maintenance_month=float(maintenance),
            insurance_month=float(insurance),
            other_opex=float(other_opex),
            tax_regime=tax_regime,
            amort_years_equipment=amort_years,
            horizon_months=horizon_months,
            scenario_pessim_factor=scenario_pessim,
            scenario_optim_factor=scenario_optim,
            eco_water_recycle_pct=eco_recycle,
            eco_chem_premium=eco_chem,
            water_discharge_profile=water_discharge_profile,
        )
        render_scenario_sidebar_block("pro", pro_params_preview)

    return pro_params_preview
