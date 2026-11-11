# pyrefly: ignore [missing-import]
from nicegui import ui, app
import config
from i18n import t, norm_lang
from components.header import render_header
from components.leaderboard_table import LeaderboardTable
from components.task_matrix import TaskMatrix
from components.contribute_dialog import ContributeDialog
from components.metrics_dialog import MetricsDialog
from components.model_detail_dialog import ModelDetailDialog
from components.model_size_chart import ModelSizeChart
from components.custom_eval_view import CustomEvalView
from components.footer import render_footer
from services.benchmark_service import benchmark_service

app.add_static_files("/static", str(config.STATIC_DIR))


@ui.page("/")
def index(lang: str = "de", view: str = "table", ds: str = "overall", model: str = "", dialog: str = ""):
    # Language per page request (?lang=de|en); no global state, so every visitor has their own language.
    # ?view=table|tasks|chart|custom_eval and ?ds=<dataset> make views shareable.
    L = norm_lang(lang)
    ui.dark_mode().enable()
    # Quasar base colours (VAGO violet, SauerkrautLM yellow)
    ui.colors(primary="#8054ff", secondary="#F8D84A", accent="#CC01FE", dark="#0a0614", dark_page="#05010d",
              positive="#34d399", negative="#ff6b81", info="#3E96F7", warning="#F8D84A")
    ui.page_title(t(L, "page.title"))

    import time
    ui.add_head_html(f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="stylesheet" href="/static/styles.css?v={int(time.time())}">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="{t(L, 'page.description')}">
        <script>document.documentElement.lang = "{L}";</script>
    """)

    model_detail_dialog = ModelDetailDialog(L)
    metrics_dialog = MetricsDialog(L)
    leaderboard_table = LeaderboardTable(L, on_model_click=model_detail_dialog.open)
    task_matrix = TaskMatrix(L, on_model_click=model_detail_dialog.open)
    model_size_chart = ModelSizeChart(L, on_model_click=model_detail_dialog.open)
    custom_eval_view = CustomEvalView(L)

    contribute_dialog = ContributeDialog(L)   # submission via GitHub pull request (CONTRIBUTING.md)
    current_view = {"name": view if view in ("table", "tasks", "chart", "custom_eval") else "table"}
    if ds in config.DATASETS_INFO:
        leaderboard_table.current_dataset = ds
        model_size_chart.current_dataset = ds

    with ui.column().classes("w-full min-h-screen p-0 m-0 gap-0"):
        def switch_view(view_name: str):
            current_view["name"] = view_name
            render_view()

        render_header(
            lang=L,
            on_open_submit=contribute_dialog.open,
            on_open_metrics=metrics_dialog.open,
            current_view=current_view,
            on_switch_view=switch_view,
        )

        view_content_container = ui.column().classes("w-full gap-0 mt-4")

        def render_view():
            view_content_container.clear()
            with view_content_container:
                name = current_view["name"]
                if name == "table":
                    leaderboard_table.render()
                elif name == "tasks":
                    task_matrix.render()
                elif name == "chart":
                    model_size_chart.render()
                elif name == "custom_eval":
                    custom_eval_view.render()

        render_view()
        render_footer(L)

    # ?model=<id> opens the model details, ?dialog=submit opens the submission guide (shareable links)
    if dialog == "submit":
        contribute_dialog.open()
    if model:
        item = benchmark_service.get_model_item(model)
        if item:
            model_detail_dialog.open(item)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title=config.APP_TITLE,
        favicon="⚖️",
        port=8080,
        reload=False,
        show=False,
        dark=True,
    )
