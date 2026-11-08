from __future__ import annotations

import re

import pytest

from ui.presentation_query import read_presentation_query_directive, resolve_presentation_mode
from ui.streamlit_shell_css import (
    SIDEBAR_EXPAND_CONTROL_SELECTOR,
    build_normal_streamlit_shell_css,
    build_presentation_streamlit_shell_css,
)


def test_present_query_on() -> None:
    assert read_presentation_query_directive({"present": "1"}) == "on"


def test_present_query_off() -> None:
    assert read_presentation_query_directive({"present": "0"}) == "off"


def test_demo_query_off_overrides_on_key_order() -> None:
    assert read_presentation_query_directive({"present": "1", "demo": "0"}) == "off"


def test_resolve_presentation_mode_user_set_persists() -> None:
    assert (
        resolve_presentation_mode(directive="none", user_set=True, session_value=True)
        is True
    )
    assert (
        resolve_presentation_mode(directive="none", user_set=True, session_value=False)
        is False
    )


def test_normal_shell_css_keeps_header_visible() -> None:
    css = build_normal_streamlit_shell_css()
    normalized = css.replace(" ", "").lower()
    assert "stexpandsidebarbutton" in normalized
    assert 'sttoolbar"]{visibility:hidden' not in normalized
    assert "visibility:visible!important" in normalized


def test_presentation_shell_preserves_header_rail_for_sidebar_expand() -> None:
    css = build_presentation_streamlit_shell_css()
    normalized = css.replace(" ", "").lower()
    assert ":has(.wb-presentation-flag)" in normalized
    assert "stexpandsidebarbutton" in normalized
    assert 'header[data-testid="stheader"]{visibility:hidden' not in normalized
    assert "height:0!important" not in normalized.split("stheader")[1].split("}")[0]


def test_sidebar_expand_selector_guarded_in_shell_css() -> None:
    for css in (build_normal_streamlit_shell_css(), build_presentation_streamlit_shell_css()):
        assert SIDEBAR_EXPAND_CONTROL_SELECTOR in css
        assert "visibility: visible !important" in css
        assert "max-width: 768px" in css
        assert "min-height: 46px" in css


def test_presentation_shell_does_not_hide_sidebar_section() -> None:
    css = build_presentation_streamlit_shell_css()
    assert 'section[data-testid="stSidebar"]' not in css
    assert "stSidebarCollapseButton" in css


def test_app_inject_css_includes_shell_fragments() -> None:
    import inspect

    import app

    source = inspect.getsource(app.inject_css)
    assert "build_normal_streamlit_shell_css" in source
    assert "build_presentation_streamlit_shell_css" in source


def test_layout_css_sidebar_pulse_without_hard_hide() -> None:
    from ui.layout_styles import build_layout_css
    from ui.theme_palette import BRAND

    css = build_layout_css(BRAND)
    assert "wb-sidebar-pulse-marker" in css
    sidebar_blocks = re.findall(
        r'section\[data-testid="stSidebar"\][^{]*\{[^}]*\}',
        css,
    )
    for block in sidebar_blocks:
        normalized = block.replace(" ", "").lower()
        assert "display:none" not in normalized
        assert "width:0" not in normalized


def test_layout_css_compact_export_tiles() -> None:
    from ui.layout_styles import build_layout_css
    from ui.theme_palette import BRAND

    css = build_layout_css(BRAND)
    assert "wb-export-tile" in css
    assert "wb-export-board" in css
    assert "min-height: 124px" not in css
    assert "wb-export-monthly-block" in css


def test_layout_css_premium_detail_tabs_and_footer() -> None:
    from ui.layout_styles import build_layout_css
    from ui.theme_palette import BRAND

    css = build_layout_css(BRAND)
    assert "wb-detail-tabs-rail" in css
    assert 'aria-selected="true"' in css
    assert "wb-footer-grid" in css
    assert "wb-footer-pill" in css


def test_results_detail_layer_uses_tabs_rail_marker() -> None:
    import inspect

    from ui import results

    source = inspect.getsource(results.render_pro_detail_layer)
    assert "wb-detail-tabs-rail" in source
    assert "st.tabs" in source


def test_footer_premium_markup() -> None:
    import inspect

    from ui.renderers import render_footer

    source = inspect.getsource(render_footer)
    assert "wb-footer-grid" in source
    assert "wb-footer-pill" in source
    assert "wb-footer-legal" in source


def test_no_mobile_in_page_parameters_cta() -> None:
    import inspect

    from ui import presentation_mode

    module_source = inspect.getsource(presentation_mode)
    controls_source = inspect.getsource(presentation_mode.render_presentation_mode_controls)
    assert "render_mobile_sidebar_affordance" not in module_source
    assert "wb_open_settings_mobile" not in module_source
    assert 'st.button(\n            "Параметры"' not in module_source
    assert "render_normal_sidebar_affordance" not in controls_source


def test_scenario_panel_is_structured_for_mobile() -> None:
    import inspect

    from ui import scenario_ui

    source = inspect.getsource(scenario_ui.render_scenario_sidebar_block)
    assert "SidebarSections.SCENARIO_SAVE" in source
    assert "SidebarSections.SCENARIO_FILE_IO" in source
    assert "Загрузить JSON" in source
    assert "Дополнительно: компактный JSON" in source
    assert "wb-scenario-mobile-zone" in source


def test_layout_css_mobile_touch_rules_present() -> None:
    from ui.layout_styles import build_layout_css
    from ui.theme_palette import BRAND

    css = build_layout_css(BRAND)
    assert "wb-mobile-sidebar-affordance" not in css
    assert "font-size: 16px !important" in css
    assert "min-height: 46px" in css
