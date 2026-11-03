# WasherBot Calculator — dev / deploy notes

## Run locally

```bash
pip install -r requirements.txt
$env:PYTHONPATH = "."
streamlit run app.py
```

Default URL: `http://localhost:8501/`

Presentation demo link: `http://localhost:8501/?present=1`  
Force normal mode: `http://localhost:8501/?present=0`

Sidebar expand control (Streamlit 1.53): `button[data-testid="stExpandSidebarButton"]` in `stHeader` / `stToolbar`. Do not set `visibility: hidden` on `stToolbar` — it hides the expand control when sidebar is collapsed.

## After UI shell / presentation changes

1. **Restart Streamlit** — hot reload does not always refresh injected CSS or session flags.
2. Verify **normal mode**: `http://localhost:8501/` — sidebar inputs visible, presentation toggle off.
3. Verify **presentation mode**: `/?present=1` — recovery affordance visible, sidebar still reachable.
4. Toggle presentation **off** — URL should drop `present` / `presentation` / `demo` params.
5. Optional dev banner: `WB_DEV=1 streamlit run app.py` or `?dev=1`.

## Tests

```bash
$env:PYTHONPATH = "."
python -m pytest -q
```

## Common pitfall

If code is fixed but UX looks broken, an **old Streamlit process** or **stale browser tab** may still show pre-fix behavior. Stop other `streamlit run` instances and hard-refresh the browser.
