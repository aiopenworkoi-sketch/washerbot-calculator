from __future__ import annotations

import re
from contextlib import contextmanager

import pytest

import ui.presentation_mode as pm
from ui.layout_styles import build_layout_css
from ui.theme_palette import BRAND


class _FakeSessionState(dict):
    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class _FakeQueryParams(dict):
    def get(self, key: str, default=None):
        return super().get(key, default)


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> _FakeSessionState:
    state = _FakeSessionState()
    monkeypatch.setattr(pm.st, "session_state", state)
    return state


def test_init_presentation_mode_from_query(session: _FakeSessionState, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({"present": "1"}))
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is True


def test_presentation_mode_off_without_query(session: _FakeSessionState, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({}))
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is False


def test_query_param_clears_after_disable(session: _FakeSessionState, monkeypatch: pytest.MonkeyPatch) -> None:
    qp = _FakeQueryParams({"present": "1", "mode": "pro"})
    monkeypatch.setattr(pm.st, "query_params", qp)
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is True

    pm.disable_presentation_mode()
    assert pm.is_presentation_mode() is False
    assert "present" not in qp
    assert qp.get("mode") == "pro"


def test_session_reset_after_toggle_off(session: _FakeSessionState, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({"presentation": "1"}))
    pm.enable_presentation_mode()
    assert pm.is_presentation_mode() is True

    pm.disable_presentation_mode()
    assert pm.is_presentation_mode() is False
    assert session.presentation_mode_user_set is True

    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({}))
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is False


def test_navigating_away_from_query_resets_sticky_session(
    session: _FakeSessionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({"present": "1"}))
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is True

    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({}))
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is False


def test_user_toggle_on_persists_without_query(
    session: _FakeSessionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({}))
    pm.enable_presentation_mode()
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is True


def test_present_zero_forces_normal_mode(
    session: _FakeSessionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session.presentation_mode = True
    monkeypatch.setattr(pm.st, "query_params", _FakeQueryParams({"present": "0"}))
    pm.init_presentation_mode()
    assert pm.is_presentation_mode() is False
    assert session.presentation_mode_user_set is True


def test_recovery_control_renders_sidebar_actions(
    session: _FakeSessionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session.presentation_mode = True
    labels: list[str] = []

    def fake_button(label: str, **kwargs):
        labels.append(label)
        return False

    def fake_columns(spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)

        class _Col:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return [_Col() for _ in range(count)]

    monkeypatch.setattr(pm.st, "button", fake_button)
    monkeypatch.setattr(pm.st, "columns", fake_columns)
    monkeypatch.setattr(pm.st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(pm.st, "caption", lambda *a, **k: None)

    pm.render_presentation_recovery_control()
    assert "Открыть панель настроек" in labels
    assert "Вернуться к рабочему режиму" in labels


def test_request_sidebar_attention_sets_pulse_flag(session: _FakeSessionState) -> None:
    pm.request_sidebar_attention()
    assert session.wb_sidebar_pulse is True


def test_presentation_secondary_panel_passthrough_when_off(session: _FakeSessionState) -> None:
    session.presentation_mode = False
    seen: list[str] = []

    with pm.presentation_secondary_panel("Title", tier="utility"):
        seen.append("inside")

    assert seen == ["inside"]


def test_presentation_secondary_panel_expander_when_on(
    session: _FakeSessionState,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session.presentation_mode = True
    entered: list[str] = []

    @contextmanager
    def fake_expander(label: str, *, expanded: bool = False):
        entered.append(f"expander:{label}:{expanded}")
        yield

    markdown_calls: list[str] = []

    def fake_markdown(html: str, **kwargs) -> None:
        markdown_calls.append(html)

    monkeypatch.setattr(pm.st, "expander", fake_expander)
    monkeypatch.setattr(pm.st, "markdown", fake_markdown)

    with pm.presentation_secondary_panel("Экспорт", subtitle="CSV", tier="utility"):
        pass

    assert entered == ["expander:Экспорт — CSV:False"]
    assert any("wb-tier-panel--utility" in call for call in markdown_calls)


def test_presentation_css_does_not_hard_hide_sidebar() -> None:
    css = build_layout_css(BRAND)
    sidebar_blocks = re.findall(
        r'section\[data-testid="stSidebar"\][^{]*\{[^}]*\}',
        css,
    )
    assert sidebar_blocks, "expected sidebar presentation rules"
    forbidden = ("display:none", "width:0", "visibility:hidden", "left:-9999")
    for block in sidebar_blocks:
        normalized = block.replace(" ", "").lower()
        for token in forbidden:
            assert token not in normalized, block


def test_presentation_css_scoped_to_main_not_app_container() -> None:
    css = build_layout_css(BRAND)
    assert '[data-testid="stMain"]:has(.wb-presentation-flag)' in css
    assert '[data-testid="stAppViewContainer"]:has(.wb-presentation-flag)' not in css
