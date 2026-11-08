from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from domain.params import ProParams
from domain.results import ProResult, SimpleResult
from ui.chart_builders import build_sorted_horizontal_bar_figure
from ui.card_specs import (
    MetricCardSpec,
    build_pro_config_card_html,
    build_pro_credit_card_specs,
    build_pro_ecology_card_specs,
    build_pro_kpi_card_specs,
    build_simple_config_card_html,
    build_simple_kpi_card_specs,
    render_metric_cards,
)
from ui.chart_specs import (
    build_capacity_throughput_figure,
    build_sensitivity_driver_figure,
    build_sensitivity_takeaway,
    rank_sensitivity_items,
)
from ui.decision_specs import (
    build_pro_capacity_summary_specs,
    build_pro_scenario_card_specs,
    render_scenario_cards_html,
)
from ui.hero_specs import (
    build_pro_executive_hero_spec,
    build_simple_executive_hero_spec,
    render_executive_hero_html,
)
from ui.compare_specs import (
    build_pro_comparison_specs,
    render_comparison_matrix_html,
)
from ui.compare_state import (
    MAX_COMPARE_VARIANTS,
    add_compare_variant,
    get_compare_baseline_id,
    get_compare_draft_name,
    get_compare_export_state,
    get_compare_variants,
    init_compare_state,
    remove_compare_variant,
    set_compare_baseline,
    set_compare_draft_name,
)
from ui.assumption_specs import (
    build_pro_assumption_snapshot,
    render_assumption_snapshot_html,
)
from ui.memo_specs import (
    build_pro_investment_memo,
    render_investment_memo_html,
)
from ui.presentation_mode import is_presentation_mode, presentation_secondary_panel
from ui.presentation_metrics import compute_pro_break_even_estimate
from ui.scenario_specs import (
    build_pro_scenario_chart_specs,
    build_pro_scenario_summary_rows,
    build_pro_scenario_summary_specs,
)
from ui.format_policies import (
    format_breakdown_year1_table,
    format_kpi_npv_compact,
    format_kpi_payback,
    kpi_payback_status,
)
from ui.recommendation_specs import (
    build_simple_hint_specs,
    render_advisory_items,
)
from ui.section_blocks import (
    render_dataframe_section,
    render_narrative_chart_section,
    render_plotly_section,
    render_section_header,
    render_section_subtitle,
    render_section_takeaway,
    render_section_title,
    render_section_spacer,
    render_titled_chart_section,
)
from ui.ui_labels import DetailTabLabels, SectionTitles
from ui.renderers import (
    BRAND,
    empty_chart,
    fmt_money_compact,
    style_plotly,
)
from ui.view_guards import (
    has_active_credit,
    has_visible_sensitivity,
    should_render_capacity_overload_advisory,
    should_render_ecology_block,
    should_show_payback_marker,
)


def render_simple_config_card(res: SimpleResult) -> None:
    st.markdown(build_simple_config_card_html(res), unsafe_allow_html=True)


def render_simple_executive_hero(res: SimpleResult) -> None:
    spec = build_simple_executive_hero_spec(res)
    st.markdown(render_executive_hero_html(spec), unsafe_allow_html=True)
    render_section_spacer(tight=True)


def render_simple_kpi_cards(res: SimpleResult) -> None:
    render_section_header(SectionTitles.KPI)
    render_metric_cards(build_simple_kpi_card_specs(res))
    render_section_spacer(tight=True)


def render_simple_cashflow_chart(res: SimpleResult) -> None:
    p = res.params

    fig1 = go.Figure()
    months_x = np.arange(0, p.horizon_months + 1)
    fig1.add_hline(
        y=0,
        line=dict(color=BRAND["muted"], width=1, dash="dash"),
    )
    fig1.add_trace(go.Scatter(
        x=months_x,
        y=res.cumulative,
        mode="lines",
        line=dict(color=BRAND["primary"], width=3),
        fill="tozeroy",
        fillcolor="rgba(46,134,255,0.15)",
        name="Накопленный поток",
        hovertemplate="<b>Месяц %{x}</b><br>Накопленный поток: %{y:,.0f} ₽<extra></extra>",
    ))
    if should_show_payback_marker(res.payback_months):
        fig1.add_vline(
            x=res.payback_months,
            line=dict(color=BRAND["green"], width=2, dash="dot"),
            annotation_text=f"Окупаемость: {format_kpi_payback(res.payback_months)}",
            annotation_position="top right",
            annotation_font=dict(color=BRAND["green"], size=12),
        )
    fig1.update_layout(
        xaxis_title="Месяц проекта",
        yaxis_title="Накопленный денежный поток, ₽",
    )
    fig1 = style_plotly(fig1, height=420)
    render_titled_chart_section(
        SectionTitles.CASHFLOW,
        fig1,
    )


def render_simple_revenue_expenses_chart(res: SimpleResult) -> None:
    total_costs_month = (
        res.var_costs_month
        + res.fix_costs_month
        + res.salary_total_month
        + res.tax_month
    )

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=res.months,
        y=res.revenue_month,
        name="Выручка",
        marker_color=BRAND["primary"],
        hovertemplate="<b>Месяц %{x}</b><br>Выручка: %{y:,.0f} ₽<extra></extra>",
    ))
    fig2.add_trace(go.Bar(
        x=res.months,
        y=-total_costs_month,
        name="Расходы (всего)",
        marker_color=BRAND["red"],
        hovertemplate="<b>Месяц %{x}</b><br>Расходы: %{y:,.0f} ₽<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=res.months,
        y=res.profit_month,
        name="Чистая прибыль",
        mode="lines+markers",
        line=dict(color=BRAND["green"], width=3),
        marker=dict(size=6, color=BRAND["green"]),
        hovertemplate="<b>Месяц %{x}</b><br>Прибыль: %{y:,.0f} ₽<extra></extra>",
    ))
    fig2.update_layout(
        barmode="relative",
        xaxis_title="Месяц проекта",
        yaxis_title="₽",
    )
    fig2 = style_plotly(fig2, height=420)
    render_titled_chart_section(SectionTitles.REVENUE_EXPENSES, fig2)


def render_simple_breakdown_block(res: SimpleResult) -> None:
    with presentation_secondary_panel(
        SectionTitles.EXPENSE_BREAKDOWN,
        tier="secondary",
    ):
        if not is_presentation_mode():
            render_section_header(SectionTitles.EXPENSE_BREAKDOWN)

        labels = list(res.breakdown_year1.keys())
        values = list(res.breakdown_year1.values())

        if any(value > 0 for value in values):
            fig3 = build_sorted_horizontal_bar_figure(
                labels,
                values,
                palette="cost",
                height=360,
                xaxis_title="₽ за 1-й год",
            )
            render_plotly_section(fig3)
        else:
            render_plotly_section(empty_chart("Нет данных"))

        df_break = pd.DataFrame([
            {"Статья": k, "Сумма за год": v, "Доля": v / sum(values) if sum(values) > 0 else 0}
            for k, v in res.breakdown_year1.items()
            if v > 0
        ]).sort_values("Сумма за год", ascending=False)

        df_show = format_breakdown_year1_table(df_break)
        render_dataframe_section(df_show, height=260)


def render_simple_hints(res: SimpleResult) -> None:
    with presentation_secondary_panel(
        SectionTitles.RECOMMENDATIONS,
        tier="tertiary",
    ):
        render_advisory_items(build_simple_hint_specs(res))


def render_pro_config_card(res: ProResult) -> None:
    st.markdown(build_pro_config_card_html(res), unsafe_allow_html=True)


def render_pro_executive_verdict(res: ProResult) -> None:
    spec = build_pro_executive_hero_spec(res)
    st.markdown(render_executive_hero_html(spec), unsafe_allow_html=True)
    render_section_spacer(tight=True)


def render_pro_kpi_cards(res: ProResult) -> None:
    render_section_header(SectionTitles.KPI)
    render_metric_cards(build_pro_kpi_card_specs(res))
    render_section_spacer(tight=True)


def render_pro_compare_block(
    res: ProResult,
    *,
    calculate_pro_fn: Callable[[ProParams], ProResult],
) -> None:
    _ = calculate_pro_fn  # snapshots synced in render_pro_ui via compare_state
    init_compare_state()
    with st.expander(
        f"{SectionTitles.COMPARE} — сопоставление вариантов",
        expanded=False,
    ):
        st.markdown('<div class="wb-compare-secondary wb-tier-panel wb-tier-panel--secondary">', unsafe_allow_html=True)
        render_section_subtitle(SectionTitles.COMPARE_SUB)

        draft_name = st.text_input(
            "Имя варианта",
            value=get_compare_draft_name(),
            key="pro_compare_draft_name_input",
            placeholder="Например: 2 робота, Москва",
        )
        set_compare_draft_name(draft_name)

        variants = get_compare_variants()
        add_col, info_col = st.columns([1.1, 2.4], gap="small")
        with add_col:
            if st.button(
                SectionTitles.COMPARE_ADD,
                key="pro_compare_add_btn",
                type="secondary",
                use_container_width=True,
                disabled=len(variants) >= MAX_COMPARE_VARIANTS,
            ):
                if add_compare_variant(res.params, draft_name):
                    st.rerun()
                else:
                    st.warning(f"Максимум {MAX_COMPARE_VARIANTS} варианта для сравнения.")
        with info_col:
            st.markdown(
                f'<p class="wb-section-caption">Сохранено вариантов: '
                f"{len(variants)} / {MAX_COMPARE_VARIANTS}. "
                f"Текущие параметры сайдбара будут зафиксированы при добавлении.</p>",
                unsafe_allow_html=True,
            )

        if variants:
            st.markdown(
                f'<p class="wb-detail-subheading">{SectionTitles.COMPARE_VARIANTS}</p>',
                unsafe_allow_html=True,
            )
            for variant in variants:
                baseline_id = get_compare_baseline_id()
                cols = st.columns([3, 1, 1], gap="small")
                with cols[0]:
                    is_base = variant.variant_id == baseline_id
                    suffix = " (база)" if is_base else ""
                    st.markdown(
                        f'<span class="wb-compare-variant-name">{variant.label}{suffix}</span>',
                        unsafe_allow_html=True,
                    )
                with cols[1]:
                    if st.button(
                        SectionTitles.COMPARE_BASELINE,
                        key=f"pro_compare_baseline_{variant.variant_id}",
                        type="secondary",
                        disabled=is_base,
                        use_container_width=True,
                    ):
                        set_compare_baseline(variant.variant_id)
                        st.rerun()
                with cols[2]:
                    if st.button(
                        "Удалить",
                        key=f"pro_compare_remove_{variant.variant_id}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        remove_compare_variant(variant.variant_id)
                        st.rerun()

        if len(variants) < 2:
            st.markdown(
                f'<div class="wb-compare-empty">{SectionTitles.COMPARE_EMPTY}</div>',
                unsafe_allow_html=True,
            )
            render_section_spacer(tight=True)
            st.markdown("</div>", unsafe_allow_html=True)
            return

        compare_state = get_compare_export_state()
        if compare_state is None:
            st.markdown(
                f'<div class="wb-compare-empty">{SectionTitles.COMPARE_EMPTY}</div>',
                unsafe_allow_html=True,
            )
            render_section_spacer(tight=True)
            st.markdown("</div>", unsafe_allow_html=True)
            return

        snapshots, baseline_id = compare_state.snapshots, compare_state.baseline_id
        spec = build_pro_comparison_specs(snapshots, baseline_id=baseline_id)

        for bullet in spec.narrative:
            render_section_takeaway(bullet)

        summary_cards = []
        for snapshot in spec.variants:
            is_base = snapshot.variant_id == spec.baseline_id
            title = f"{snapshot.label}{' · база' if is_base else ''}"
            summary_cards.append(
                MetricCardSpec(
                    title,
                    format_kpi_npv_compact(snapshot.result.npv),
                    (
                        f"Окупаемость {format_kpi_payback(snapshot.result.payback_months)} · "
                        f"собств. {format_kpi_npv_compact(snapshot.result.own_funds)}"
                    ),
                    "primary" if is_base else "",
                )
            )
        render_metric_cards(tuple(summary_cards), cols_per_row=min(3, len(summary_cards)))

        st.markdown(
            f'<p class="wb-section-caption">{SectionTitles.COMPARE_DELTA_NOTE}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="wb-compare-panel">{render_comparison_matrix_html(spec)}</div>',
            unsafe_allow_html=True,
        )
        render_plotly_section(spec.chart)
        render_section_spacer(tight=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_pro_scenarios_block(res: ProResult) -> None:
    p = res.params
    scenario_specs = build_pro_scenario_summary_specs(res)
    render_section_header(
        SectionTitles.SCENARIOS,
        subtitle=SectionTitles.SCENARIOS_SUB,
    )

    scenario_cards = build_pro_scenario_card_specs(scenario_specs)
    st.markdown(render_scenario_cards_html(scenario_cards), unsafe_allow_html=True)

    months_x = np.arange(0, p.horizon_months + 1)
    fig_sc = go.Figure()
    fig_sc.add_hline(y=0, line=dict(color=BRAND["muted"], width=1, dash="dash"))

    for spec in build_pro_scenario_chart_specs(res):
        line = dict(color=spec.line_color, width=spec.line_width)
        if spec.line_dash:
            line["dash"] = spec.line_dash

        trace_kwargs = dict(
            x=months_x,
            y=spec.cumulative,
            mode="lines",
            name=spec.chart_name,
            line=line,
            hovertemplate=f"<b>Месяц %{{x}}</b><br>{spec.hover_label}: %{{y:,.0f}} ₽<extra></extra>",
        )
        if spec.fill_to_zero and spec.fill_color:
            trace_kwargs["fill"] = "tozeroy"
            trace_kwargs["fillcolor"] = spec.fill_color

        fig_sc.add_trace(go.Scatter(**trace_kwargs))

    if should_show_payback_marker(res.payback_months):
        fig_sc.add_vline(
            x=res.payback_months,
            line=dict(color=BRAND["primary"], width=1.5, dash="dot"),
            annotation_text=f"База: {format_kpi_payback(res.payback_months)}",
            annotation_position="top",
            annotation_font=dict(color=BRAND["primary"], size=11),
        )

    fig_sc.update_layout(
        xaxis_title="Месяц проекта",
        yaxis_title="Накопленный денежный поток, ₽",
        legend=dict(orientation="h", y=-0.18),
    )
    fig_sc = style_plotly(fig_sc, height=400)
    render_section_takeaway(
        "Базовый сценарий — опорная траектория; пессимистичный и оптимистичный "
        "задают реалистичный диапазон окупаемости при изменении трафика."
    )
    render_plotly_section(fig_sc)

    sc_table = pd.DataFrame(
        build_pro_scenario_summary_rows(scenario_specs)
    )
    render_dataframe_section(sc_table, height=160)
    render_section_spacer(tight=True)


def render_pro_sensitivity_block(res: ProResult) -> None:
    if not has_visible_sensitivity(res.sensitivity):
        return

    sorted_items = rank_sensitivity_items(res.sensitivity)
    takeaway = build_sensitivity_takeaway(sorted_items)
    fig_sens = build_sensitivity_driver_figure(sorted_items)

    render_narrative_chart_section(
        SectionTitles.SENSITIVITY,
        fig_sens,
        subtitle=SectionTitles.SENSITIVITY_SUB,
        takeaway=takeaway,
        caption="Δ NPV — относительное изменение при +10% к параметру; "
        "ранжирование по убыванию влияния.",
    )


def render_pro_break_even_block(res: ProResult) -> None:
    estimate = compute_pro_break_even_estimate(res)
    render_section_header(
        SectionTitles.BREAK_EVEN,
        subtitle=SectionTitles.BREAK_EVEN_SUB,
    )

    if estimate.operational_cars_per_month is None:
        be_value = "—"
        be_hint = "маржинальный вклад на авто недостаточен для оценки"
        headroom_text = "Недостаточно данных для сравнения с фактическим потоком"
    else:
        be_value = f"{estimate.operational_cars_per_month:,.0f}"
        be_hint = (
            f"при марже {estimate.unit_contribution_rub:,.0f} ₽/авто "
            f"и фикс. {estimate.monthly_fixed_ops_rub:,.0f} ₽/мес"
        )
        if estimate.headroom_ratio is not None:
            headroom_pct = estimate.headroom_ratio * 100
            headroom_text = (
                f"Фактический поток {estimate.avg_actual_cars_per_month:,.0f} авто/мес — "
                f"{headroom_pct:.0f}% от порога покрытия затрат."
            )
        else:
            headroom_text = ""

    cards = (
        MetricCardSpec(
            "Порог авто/мес",
            f"{be_value} авто/мес",
            be_hint,
            "",
            "primary",
        ),
        MetricCardSpec(
            "Окупаемость капитала",
            format_kpi_payback(res.payback_months),
            f"NPV {format_kpi_npv_compact(res.npv)} · отдельно от порога затрат",
            kpi_payback_status(res.payback_months),
            "secondary",
        ),
        MetricCardSpec(
            "Средний чек",
            fmt_money_compact(res.avg_check),
            "выручка на авто по модели",
        ),
        MetricCardSpec(
            "Фактический поток",
            f"{estimate.avg_actual_cars_per_month:,.0f} авто/мес",
            "среднее по горизонту",
        ),
    )
    render_metric_cards(cards, cols_per_row=4)
    if headroom_text:
        render_section_takeaway(headroom_text)
    st.markdown(
        f'<p class="wb-section-caption">{estimate.formula_note}</p>',
        unsafe_allow_html=True,
    )
    render_section_spacer(tight=True)


def render_pro_capacity_block(res: ProResult) -> None:
    render_section_header(
        SectionTitles.CAPACITY,
        subtitle=SectionTitles.CAPACITY_SUB,
    )

    capacity_cards = [
        MetricCardSpec(spec.label, spec.value, spec.hint, spec.status)
        for spec in build_pro_capacity_summary_specs(res)
    ]
    render_metric_cards(tuple(capacity_cards), cols_per_row=min(4, len(capacity_cards)))

    if should_render_capacity_overload_advisory(res):
        takeaway = (
            "Мощность ограничивает проект: часть спроса не обслуживается. "
            "Рассмотрите увеличение пропускной способности или корректировку трафика."
        )
    else:
        takeaway = (
            "На горизонте модели фактический поток не упирается в расчётную мощность."
        )
    render_section_takeaway(takeaway)

    fig_cap = build_capacity_throughput_figure(res)
    render_plotly_section(fig_cap)
    st.markdown(
        '<p class="wb-section-caption">Фактический поток — обслуженный спрос после '
        "ограничения мощности; линия мощности — упрощённая оценка по тем же допущениям, "
        "что и в расчёте.</p>",
        unsafe_allow_html=True,
    )
    render_section_spacer(tight=True)


def render_pro_assumptions_snapshot(res: ProResult) -> None:
    spec = build_pro_assumption_snapshot(res)
    with presentation_secondary_panel(
        SectionTitles.ASSUMPTIONS,
        subtitle=SectionTitles.ASSUMPTIONS_SUB,
        tier="secondary",
    ):
        if not is_presentation_mode():
            render_section_header(
                SectionTitles.ASSUMPTIONS,
                subtitle=SectionTitles.ASSUMPTIONS_SUB,
            )
        st.markdown(render_assumption_snapshot_html(spec), unsafe_allow_html=True)
        render_section_spacer(tight=True)


def render_pro_investment_memo(res: ProResult) -> None:
    memo = build_pro_investment_memo(res)
    render_section_header(
        SectionTitles.MEMO,
        subtitle=SectionTitles.MEMO_SUB,
    )
    st.markdown(render_investment_memo_html(memo), unsafe_allow_html=True)
    render_section_spacer(tight=True)


def render_pro_detail_layer(res: ProResult) -> None:
    with presentation_secondary_panel(
        SectionTitles.DETAIL_MODEL,
        subtitle="Углублённая проверка модели — графики и структура затрат",
        tier="secondary",
    ):
        if not is_presentation_mode():
            render_section_header(
                SectionTitles.DETAIL_MODEL,
                subtitle="Углублённая проверка модели — графики и структура затрат",
            )

        st.markdown('<div class="wb-detail-tabs-rail" aria-hidden="true"></div>', unsafe_allow_html=True)
        tab_dyn, tab_fin, tab_cost = st.tabs([
            DetailTabLabels.DYNAMICS,
            DetailTabLabels.FINANCING,
            DetailTabLabels.COSTS,
        ])

        with tab_dyn:
            render_section_subtitle(SectionTitles.DETAIL_DYNAMICS_SUB)
            render_section_takeaway(
                "Сравните динамику выручки, EBITDA и прибыли; накопленный поток показывает "
                "момент окупаемости собственных средств."
            )
            render_pro_pl_chart(res, embedded=True)
            render_pro_cumulative_cashflow_chart(res)

        with tab_fin:
            render_section_subtitle(SectionTitles.DETAIL_FINANCING_SUB)
            if has_active_credit(res.params):
                render_section_takeaway(
                    "Оцените ежемесячную долговую нагрузку: тело кредита и проценты "
                    "влияют на свободный cashflow."
                )
                render_pro_credit_block(res, embedded=True)
            else:
                st.markdown(
                    '<p class="wb-section-caption">Кредит не используется — '
                    "проект финансируется полностью собственными средствами.</p>",
                    unsafe_allow_html=True,
                )

        with tab_cost:
            render_section_subtitle(SectionTitles.DETAIL_COSTS_SUB)
            render_section_takeaway(
                "CAPEX — единовременные вложения; OPEX первого года показывает "
                "структуру операционных расходов."
            )
            render_pro_capex_opex_block(res, embedded=True)

        render_section_spacer(tight=True)


def render_pro_detail_financial_section(res: ProResult) -> None:
    """Legacy wrapper — delegates to tabbed detail layer."""
    render_pro_detail_layer(res)


def render_pro_pl_chart(res: ProResult, *, embedded: bool = False) -> None:
    fig_pl = go.Figure()
    fig_pl.add_trace(go.Scatter(
        x=res.months, y=res.revenue_month,
        name="Выручка", mode="lines",
        line=dict(color=BRAND["primary"], width=2.5),
        fill="tozeroy", fillcolor="rgba(46,134,255,0.10)",
        hovertemplate="<b>Месяц %{x}</b><br>Выручка: %{y:,.0f} ₽<extra></extra>",
    ))
    fig_pl.add_trace(go.Scatter(
        x=res.months, y=res.ebitda_month,
        name="EBITDA", mode="lines",
        line=dict(color=BRAND["accent"], width=2.5),
        hovertemplate="<b>Месяц %{x}</b><br>EBITDA: %{y:,.0f} ₽<extra></extra>",
    ))
    fig_pl.add_trace(go.Scatter(
        x=res.months, y=res.profit_month,
        name="Чистая прибыль", mode="lines",
        line=dict(color=BRAND["green"], width=2.5),
        hovertemplate="<b>Месяц %{x}</b><br>Прибыль: %{y:,.0f} ₽<extra></extra>",
    ))
    fig_pl.add_hline(y=0, line=dict(color=BRAND["muted"], width=1, dash="dash"))
    fig_pl.update_layout(
        xaxis_title="Месяц",
        yaxis_title="₽",
        legend=dict(orientation="h", y=-0.18),
    )
    fig_pl = style_plotly(fig_pl, height=400)
    if embedded:
        st.markdown(
            f'<p class="wb-detail-subheading">{SectionTitles.PL_MONTHLY}</p>',
            unsafe_allow_html=True,
        )
        render_plotly_section(fig_pl)
    else:
        render_titled_chart_section(SectionTitles.PL_MONTHLY, fig_pl)


def render_pro_cumulative_cashflow_chart(res: ProResult) -> None:
    p = res.params
    fig1 = go.Figure()
    months_x = np.arange(0, p.horizon_months + 1)
    fig1.add_hline(
        y=0,
        line=dict(color=BRAND["muted"], width=1, dash="dash"),
    )
    fig1.add_trace(go.Scatter(
        x=months_x,
        y=res.cumulative,
        mode="lines",
        line=dict(color=BRAND["primary"], width=3),
        name="Накопленный поток",
        hovertemplate="<b>Месяц %{x}</b><br>Накопленный поток: %{y:,.0f} ₽<extra></extra>",
    ))
    # Стартовые инвестиции — отдельная точка, чтобы график читался без заливки минуса
    fig1.add_trace(go.Scatter(
        x=[0],
        y=[res.cumulative[0]],
        mode="markers+text",
        marker=dict(color=BRAND["red"], size=9),
        text=[f"Инвестиции {res.cumulative[0]:,.0f} ₽".replace(",", " ")],
        textposition="bottom right",
        textfont=dict(color=BRAND["red"], size=11),
        name="Инвестиции",
        hoverinfo="skip",
    ))
    if should_show_payback_marker(res.payback_months):
        fig1.add_vline(
            x=res.payback_months,
            line=dict(color=BRAND["green"], width=2, dash="dot"),
            annotation_text=f"Окупаемость: {format_kpi_payback(res.payback_months)}",
            annotation_position="top right",
            annotation_font=dict(color=BRAND["green"], size=11),
        )
    fig1.update_layout(
        xaxis_title="Месяц проекта",
        yaxis_title="Накопленный денежный поток, ₽",
        legend=dict(orientation="h", y=-0.18),
    )
    fig1 = style_plotly(fig1, height=380)
    st.markdown(
        f'<p class="wb-detail-subheading">{SectionTitles.CASHFLOW}</p>',
        unsafe_allow_html=True,
    )
    render_plotly_section(fig1)


def render_pro_capex_opex_block(res: ProResult, *, embedded: bool = False) -> None:
    if not embedded:
        render_section_title(SectionTitles.CAPEX_OPEX)
    else:
        st.markdown(
            f'<p class="wb-detail-subheading">{SectionTitles.CAPEX_OPEX}</p>',
            unsafe_allow_html=True,
        )

    col_capex, col_opex = st.columns(2, gap="large")

    with col_capex:
        st.markdown(
            f'<div style="color:{BRAND["muted"]}; font-size:13px; margin-bottom:6px;">'
            f'CAPEX (единовременно)</div>',
            unsafe_allow_html=True,
        )
        labels = list(res.capex_breakdown.keys())
        values = list(res.capex_breakdown.values())
        if any(value > 0 for value in values):
            fig_cx = build_sorted_horizontal_bar_figure(
                labels,
                values,
                palette="capex",
                height=320,
                xaxis_title="₽",
            )
            render_plotly_section(fig_cx)

    with col_opex:
        st.markdown(
            f'<div style="color:{BRAND["muted"]}; font-size:13px; margin-bottom:6px;">'
            f'Затраты 1-го года</div>',
            unsafe_allow_html=True,
        )
        labels = list(res.opex_breakdown_year1.keys())
        values = list(res.opex_breakdown_year1.values())
        if any(value > 0 for value in values):
            fig_ox = build_sorted_horizontal_bar_figure(
                labels,
                values,
                palette="cost",
                height=320,
                xaxis_title="₽ за год",
            )
            render_plotly_section(fig_ox)


def render_pro_credit_block(res: ProResult, *, embedded: bool = False) -> None:
    p = res.params
    if not has_active_credit(p):
        return

    if not embedded:
        render_section_title(SectionTitles.CREDIT_SCHEDULE)
        render_section_subtitle(SectionTitles.DETAIL_FINANCING_SUB)

    fig_cr = go.Figure()
    fig_cr.add_trace(go.Bar(
        x=res.months,
        y=res.credit_principal_month,
        name="Тело долга",
        marker_color=BRAND["primary"],
        hovertemplate="<b>Месяц %{x}</b><br>Тело: %{y:,.0f} ₽<extra></extra>",
    ))
    fig_cr.add_trace(go.Bar(
        x=res.months,
        y=res.credit_interest_month,
        name="Проценты",
        marker_color=BRAND["red"],
        hovertemplate="<b>Месяц %{x}</b><br>Проценты: %{y:,.0f} ₽<extra></extra>",
    ))
    fig_cr.update_layout(
        barmode="stack",
        xaxis_title="Месяц",
        yaxis_title="Платёж, ₽",
        legend=dict(orientation="h", y=-0.18),
    )
    fig_cr = style_plotly(fig_cr, height=340)
    render_plotly_section(fig_cr)

    render_metric_cards(build_pro_credit_card_specs(res), cols_per_row=3)


def render_pro_ecology_block(res: ProResult) -> None:
    p = res.params
    if not should_render_ecology_block(p):
        return

    with presentation_secondary_panel(
        SectionTitles.ECOLOGY,
        tier="tertiary",
    ):
        if not is_presentation_mode():
            render_section_header(SectionTitles.ECOLOGY)
        render_metric_cards(build_pro_ecology_card_specs(res), cols_per_row=3)


def render_pro_recommendations(res: ProResult) -> None:
    """Legacy entry — delegates to structured investment memo."""
    render_pro_investment_memo(res)
