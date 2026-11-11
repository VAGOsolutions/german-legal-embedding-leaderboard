# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Callable, Optional, Dict, Any
import config
from i18n import t, ds_text

VIEWS = (("table", "view.table", "leaderboard"), ("tasks", "view.tasks", "grid_on"),
         ("chart", "view.chart", "scatter_plot"), ("custom_eval", "view.custom", "science"))


def render_header(
    lang: str,
    on_open_submit: Callable,
    on_open_metrics: Callable,
    current_view: Optional[Dict[str, Any]] = None,
    on_switch_view: Optional[Callable] = None,
):
    """Header: brand row, language switch, title, view switch, about box, actions."""
    L = lang
    state = {"expanded": False}

    with ui.column().classes("w-full max-w-7xl mx-auto px-4 pt-5 pb-2 gap-5 relative overflow-hidden"):
        with ui.element("div").classes("header-watermark-wrapper"):
            ui.label("§").classes("watermark-para p1")
            ui.label("§").classes("watermark-para p2")

        # brand row + language
        with ui.row().classes("brand-row w-full justify-between items-center z-10 flex-nowrap gap-3"):
            with ui.row().classes("items-center gap-3 flex-nowrap"):
                ui.html('<img class="sk-logo" src="/static/sauerkrautlm-logo.svg" alt="SauerkrautLM">')
                ui.label(t(L, "brand.by")).classes("brand-by")
                with ui.link(target="https://www.vago-solutions.ai", new_tab=True).classes("flex items-center"):
                    ui.html('<img class="vago-logo" src="/static/vago-solutions-white.svg" alt="VAGO Solutions">')
            with ui.element("div").classes("lang-switch").props(f'role="group" aria-label="{t(L, "lang.aria")}"'):
                for code in ("de", "en"):
                    ui.button(code.upper(), on_click=lambda c=code: ui.navigate.to(
                        f"/?lang={c}&view={(current_view or {}).get('name', 'table')}")).props(
                        f'flat dense no-caps aria-pressed="{str(code == L).lower()}" title="{t(L, "lang." + code)}"'
                    ).classes("lang-btn" + (" active" if code == L else ""))

        # title
        with ui.column().classes("w-full items-center text-center gap-2 z-10"):
            ui.html('<h1 class="hero-title text-3xl md:text-5xl" style="margin:0">German Legal <span class="hl">Embedding</span> Benchmark</h1>')
            ui.label(t(L, "hero.subtitle")).classes("hero-subtitle text-xs md:text-sm")
            with ui.row().classes("items-center justify-center gap-2 mt-1"):
                ui.html(f'<span class="badge badge-yellow">{t(L, "hero.badge1")}</span>')
                ui.html('<span class="badge badge-violet">nDCG@10</span>')
                ui.html(f'<span class="badge">{t(L, "hero.badge3")}</span>')
            ui.element("div").classes("ci-band mt-3").style("max-width: 420px")

        # views
        render_switch = None
        if current_view is not None and on_switch_view is not None:
            switch_container = ui.row().classes("w-full justify-center z-10")

            def render_switch():
                switch_container.clear()
                with switch_container:
                    with ui.element("div").classes("view-switch").props(f'role="tablist" aria-label="{t(L, "view.aria")}"'):
                        active = current_view.get("name", "table")
                        for key, label_key, icon in VIEWS:
                            ui.button(t(L, label_key), icon=icon,
                                      on_click=lambda k=key: (on_switch_view(k), render_switch())).props(
                                f'flat dense no-caps role="tab" aria-selected="{str(active == key).lower()}"'
                            ).classes("view-btn" + (" active" if active == key else ""))

            render_switch()

        # about the benchmark
        with ui.element("div").classes("ci-card w-full p-5 md:p-6 z-10"):
            with ui.column().classes("w-full gap-2.5 leading-relaxed"):
                with ui.row().classes("w-full justify-between items-center cursor-pointer select-none") as about_head:
                    with ui.row().classes("items-center gap-2"):
                        ui.element("span").classes("ci-drop-dot")
                        ui.label(t(L, "about.title")).classes("ci-kicker")
                    chevron_icon = ui.icon("expand_more", size="sm").classes("ci-muted")
                ui.label(t(L, "about.lead")).classes("text-sm ci-text")

                detail_container = ui.column().classes("w-full gap-2 hidden pt-1")
                with detail_container:
                    ui.label(t(L, "about.list_intro")).classes("text-sm ci-text")
                    with ui.column().classes("w-full gap-1.5 pl-1"):
                        for k in [k for k in config.DATASETS_INFO if k != "overall"]:
                            info = config.DATASETS_INFO[k]
                            with ui.row().classes("items-start gap-2 flex-nowrap"):
                                ui.icon(info["icon"], size="xs").classes("ci-yellow mt-0.5")
                                with ui.column().classes("gap-0"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.label(ds_text(L, k, "name")).classes("text-sm font-bold")
                                        if info.get("url"):
                                            ui.link("↗", info["url"], new_tab=True).classes("ci-link text-xs")
                                    ui.label(ds_text(L, k, "description")).classes("text-xs ci-muted")
                    ui.label(t(L, "about.footnote")).classes("text-xs ci-muted mt-1")

                toggle_btn = ui.label(t(L, "about.more")).classes("text-xs font-semibold ci-yellow cursor-pointer w-fit select-none")

                def toggle_expand():
                    state["expanded"] = not state["expanded"]
                    if state["expanded"]:
                        detail_container.classes(remove="hidden")
                        toggle_btn.text = t(L, "about.less")
                        chevron_icon.name = "expand_less"
                    else:
                        detail_container.classes(add="hidden")
                        toggle_btn.text = t(L, "about.more")
                        chevron_icon.name = "expand_more"

                about_head.on("click", toggle_expand)
                toggle_btn.on("click", toggle_expand)

        # actions
        with ui.row().classes("w-full justify-center items-center gap-2.5 flex-wrap z-10"):
            ui.button(t(L, "act.metrics"), icon="insights", on_click=on_open_metrics).props("flat no-caps").classes("action-btn px-4 py-2")
            ui.button(t(L, "act.submit"), icon="merge_type", on_click=on_open_submit).props("flat no-caps").classes("action-btn px-4 py-2")
            if on_switch_view is not None:
                ui.button(t(L, "act.custom"), icon="science",
                          on_click=lambda: (on_switch_view("custom_eval"), render_switch() if render_switch else None)
                          ).props("flat no-caps").classes("action-btn px-4 py-2")
            with ui.button(t(L, "act.datasets"), icon="menu_book").props("flat no-caps").classes("action-btn px-4 py-2"):
                with ui.menu():
                    for k in ("legalquad", "gerdalir_small", "gerlayqa", "gerlerb"):
                        info = config.DATASETS_INFO[k]
                        ui.menu_item(f"{info['short_name']} ↗", lambda u=info["url"]: ui.navigate.to(u, new_tab=True))
                    ui.menu_item(f"OpenLegalRetrieval-DE · {t(L, 'olr.license')}").props("disable")
            ui.button(t(L, "act.sample"), icon="download",
                      on_click=lambda: ui.download(config.BENCHMARK_DIR / "example_result.json", "example_result.json")
                      ).props("flat no-caps").classes("action-btn px-4 py-2")
