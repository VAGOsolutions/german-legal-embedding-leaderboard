# pyrefly: ignore [missing-import]
from nicegui import ui
import config
from i18n import t, ds_text, task_label


class MetricsDialog:
    def __init__(self, lang: str):
        self.lang = lang
        self.dialog = ui.dialog().classes("w-full")
        self._build()

    def _build(self):
        L = self.lang
        with self.dialog, ui.element("div").classes("ci-dialog w-full p-5 md:p-6").style("width: min(860px, 94vw);"):
            with ui.column().classes("w-full gap-4"):
                with ui.row().classes("w-full justify-between items-center flex-nowrap"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("insights", size="sm").classes("ci-yellow")
                        ui.label(t(L, "metrics.title")).classes("text-xl font-bold")
                    ui.button(icon="close", on_click=self.dialog.close).props(f'flat round dense aria-label="{t(L, "common.close")}"').classes("btn-ghost")
                ui.element("div").classes("ci-band")

                with ui.element("div").classes("ci-subcard w-full p-4"):
                    with ui.row().classes("items-center gap-2 mb-1"):
                        ui.html(f'<span class="badge badge-yellow">{t(L, "metrics.primary")}</span>')
                        ui.label("nDCG@10 (Normalized Discounted Cumulative Gain)").classes("font-bold")
                    ui.label(t(L, "metrics.ndcg")).classes("text-sm ci-text leading-relaxed")

                with ui.element("div").classes("w-full grid grid-cols-1 sm:grid-cols-3 gap-3"):
                    for name, key in (("Recall@10", "metrics.recall"), ("MRR@10", "metrics.mrr"), ("MAP@10", "metrics.map")):
                        with ui.element("div").classes("ci-subcard p-3.5"):
                            ui.label(name).classes("font-bold text-xs")
                            ui.label(t(L, key)).classes("text-xs ci-muted mt-1")

                with ui.element("div").classes("ci-subcard w-full p-4").style("border-color: rgba(128,84,255,0.45);"):
                    ui.label(t(L, "metrics.protocol_title")).classes("font-bold ci-violet mb-1")
                    ui.label(t(L, "metrics.protocol")).classes("text-sm ci-text leading-relaxed")

                ui.label(t(L, "metrics.datasets_title")).classes("font-bold mt-1")
                with ui.column().classes("w-full gap-3"):
                    for k, info in config.DATASETS_INFO.items():
                        if k == "overall":
                            continue
                        with ui.element("div").classes("ci-subcard w-full p-4"):
                            with ui.row().classes("w-full justify-between items-start flex-nowrap gap-2"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon(info["icon"], size="xs").classes("ci-yellow")
                                    ui.label(ds_text(L, k, "name")).classes("font-bold")
                                if info.get("url"):
                                    ui.link(t(L, "metrics.source") + " ↗", info["url"], new_tab=True).classes("ci-link text-xs")
                                else:
                                    ui.label(t(L, "olr.license")).classes("text-xs ci-faint")
                            ui.label(ds_text(L, k, "description")).classes("text-xs ci-muted mt-2 leading-relaxed")
                            if k == config.OLR_KEY:
                                ui.label(t(L, "olr.attribution")).classes("text-[11px] ci-faint mt-1")
                                with ui.column().classes("w-full gap-1 mt-2"):
                                    for tk, ti in config.OLR_TASKS.items():
                                        with ui.row().classes("items-center gap-2 flex-nowrap"):
                                            ui.label(tk).classes("text-xs font-bold ci-yellow w-6")
                                            ui.label(task_label(L, tk, long=True)).classes("text-xs ci-text")
                                            ui.label(t(L, "tasks.lengths", q=ti["q"], d=ti["d"])).classes("text-[11px] ci-faint")

                    with ui.element("div").classes("ci-subcard w-full p-4"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("balance", size="xs").classes("ci-faint")
                            ui.label(t(L, "metrics.gerdalir_full_title")).classes("font-bold")
                        ui.label(t(L, "metrics.gerdalir_full")).classes("text-xs ci-muted mt-2 leading-relaxed")

                    with ui.element("div").classes("ci-subcard w-full p-4"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("science", size="xs").classes("ci-yellow")
                            ui.label(t(L, "metrics.custom_title", n=config.MAX_CUSTOM_CORPUS_DOCS)).classes("font-bold")
                        ui.label(t(L, "metrics.custom")).classes("text-xs ci-muted mt-2 leading-relaxed")

                with ui.row().classes("w-full justify-end mt-1"):
                    ui.button(t(L, "common.close"), on_click=self.dialog.close).props("flat no-caps").classes("btn-ghost")

    def open(self):
        self.dialog.open()
