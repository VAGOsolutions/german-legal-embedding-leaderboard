# pyrefly: ignore [missing-import]
from nicegui import ui
import config
from i18n import t

# Submission as in MTEB: result file via pull request, added on merge. No upload in the app.
STEPS = ("contrib.step1", "contrib.step2", "contrib.step3", "contrib.step4")
COMMAND = (
    "pip install -r benchmark/requirements.txt\n"
    "python benchmark/run_benchmark.py \\\n"
    "    --model <org>/<model> --revision <commit> \\\n"
    "    --model-type open --embedding-type dense \\\n"
    "    --license <spdx> --trained-on none \\\n"
    "    --out results/"
)


class ContributeDialog:
    def __init__(self, lang: str):
        self.lang = lang
        self.dialog = ui.dialog().classes("w-full")
        self._build()

    def _build(self):
        L = self.lang
        with self.dialog, ui.element("div").classes("ci-dialog w-full p-5 md:p-6").style("width: min(860px, 94vw);"):
            with ui.column().classes("w-full gap-4"):
                with ui.row().classes("w-full justify-between items-center flex-nowrap"):
                    with ui.row().classes("items-center gap-2 flex-nowrap"):
                        ui.icon("merge_type", size="sm").classes("ci-yellow")
                        with ui.column().classes("gap-0"):
                            ui.label(t(L, "contrib.title")).classes("text-xl font-bold")
                            ui.label(t(L, "contrib.sub")).classes("text-xs ci-muted")
                    ui.button(icon="close", on_click=self.dialog.close).props(f'flat round dense aria-label="{t(L, "common.close")}"').classes("btn-ghost")
                ui.element("div").classes("ci-band")

                with ui.element("div").classes("ci-subcard w-full p-4"):
                    ui.label(t(L, "contrib.how")).classes("font-bold mb-2")
                    with ui.element("ol").classes("contrib-steps"):
                        for i, key in enumerate(STEPS, start=1):
                            with ui.element("li").classes("text-sm ci-text leading-relaxed"):
                                ui.label(t(L, key, n=i))

                with ui.element("div").classes("ci-subcard w-full p-4"):
                    ui.label(t(L, "contrib.cmd_title")).classes("font-bold mb-1")
                    ui.code(COMMAND, language="bash").classes("w-full text-xs")
                    ui.label(t(L, "contrib.cmd_hint")).classes("text-xs ci-muted mt-1")

                with ui.element("div").classes("ci-subcard w-full p-4").style("border-color: rgba(128,84,255,0.45);"):
                    ui.label(t(L, "contrib.review_title")).classes("font-bold ci-violet mb-1")
                    ui.label(t(L, "contrib.review")).classes("text-sm ci-text leading-relaxed")
                    ui.label(t(L, "contrib.olr")).classes("text-xs ci-muted mt-2")

                with ui.row().classes("w-full justify-between items-center gap-2 flex-wrap"):
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.button(t(L, "contrib.open_guide"), icon="open_in_new",
                                  on_click=lambda: ui.navigate.to(config.CONTRIBUTING_URL, new_tab=True)).props("no-caps").classes("btn-primary")
                        ui.button(t(L, "contrib.open_script"), icon="terminal",
                                  on_click=lambda: ui.navigate.to(config.BENCHMARK_README_URL, new_tab=True)).props("outline no-caps").classes("action-btn")
                        ui.button(t(L, "act.sample"), icon="download",
                                  on_click=lambda: ui.download(config.BENCHMARK_DIR / "example_result.json", "example_result.json")
                                  ).props("outline no-caps").classes("action-btn")
                    ui.button(t(L, "common.close"), on_click=self.dialog.close).props("flat no-caps").classes("btn-ghost")

    def open(self):
        self.dialog.open()
