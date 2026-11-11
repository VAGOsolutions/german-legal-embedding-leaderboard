# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Callable, Optional, Tuple
import config
from i18n import t, model_type_label, embedding_type_label


def format_size_log(lang: str, x: float, upper: bool = False) -> str:
    """Slider value (log10 parameters) as a readable size; slider ends = no limit."""
    if upper and x >= config.SIZE_LOG_MAX - 1e-9:
        return t(lang, "size.max_open")
    if not upper and x <= config.SIZE_LOG_MIN + 1e-9:
        return t(lang, "size.min_open")
    v = 10 ** x
    if v >= 1e9:
        s = f"{v / 1e9:.1f}".rstrip("0").rstrip(".") + "B"
    elif v >= 1e6:
        s = (f"{v / 1e6:.1f}".rstrip("0").rstrip(".") if v < 1e7 else f"{v / 1e6:.0f}") + "M"
    else:
        s = f"{v / 1e3:.0f}k"
    return s


class FilterBar:
    """Search, model type, embedding type and size slider, shared by table and task matrix (separate state per view)."""

    def __init__(self, lang: str, on_change: Callable[[], None]):
        self.lang = lang
        self.on_change = on_change
        self.search_query = ""
        self.model_type_filter = "all"
        self.embedding_type_filter = "all"
        self.size_range = {"min": config.SIZE_LOG_MIN, "max": config.SIZE_LOG_MAX}
        self.include_unsized = True
        self.results_label = None
        self._size_label = None
        self._unsized_switch = None

    # values for the service
    @property
    def size_log_range(self) -> Tuple[float, float]:
        return (float(self.size_range["min"]), float(self.size_range["max"]))

    def kwargs(self) -> dict:
        return dict(search_query=self.search_query, model_type_filter=self.model_type_filter,
                    embedding_type_filter=self.embedding_type_filter, size_log_range=self.size_log_range,
                    include_unsized=self.include_unsized)

    def _changed(self, *_):
        self._update_size_label()
        self.on_change()

    def _update_size_label(self):
        lo, hi = self.size_log_range
        if self._size_label is not None:
            self._size_label.text = f"{format_size_log(self.lang, lo)} – {format_size_log(self.lang, hi, upper=True)}"
        if self._unsized_switch is not None:
            full = lo <= config.SIZE_LOG_MIN + 1e-9 and hi >= config.SIZE_LOG_MAX - 1e-9
            if full:
                self._unsized_switch.enable()
            else:
                self._unsized_switch.disable()

    def reset(self):
        self.search_query = ""
        self.model_type_filter = "all"
        self.embedding_type_filter = "all"
        self.size_range = {"min": config.SIZE_LOG_MIN, "max": config.SIZE_LOG_MAX}
        self.include_unsized = True
        self._changed()

    def render(self):
        L = self.lang
        with ui.element("div").classes("ci-card w-full p-4"):
            with ui.row().classes("w-full justify-between items-center flex-wrap gap-3"):
                with ui.row().classes("items-center flex-1 min-w-[240px] gap-2"):
                    ui.input(placeholder=t(L, "filter.search"), on_change=self._changed).props(
                        'outlined dense clearable dark'
                    ).classes("w-full").bind_value(self, "search_query")
                with ui.row().classes("items-center gap-3 flex-wrap"):
                    ui.select(
                        options={"all": t(L, "filter.all"), "open": model_type_label(L, "open"),
                                 "proprietary": model_type_label(L, "proprietary")},
                        label=t(L, "filter.type"), on_change=self._changed,
                    ).props("outlined dense dark options-dense").classes("w-44").bind_value(self, "model_type_filter")
                    ui.select(
                        options={"all": t(L, "filter.all"), **{v: embedding_type_label(L, v)
                                 for v in ("Dense", "Late-Interaction", "Hybrid", "MoE", "BM25")}},
                        label=t(L, "filter.embedding"), on_change=self._changed,
                    ).props("outlined dense dark options-dense").classes("w-44").bind_value(self, "embedding_type_filter")
                self.results_label = ui.label("").classes("ci-kicker")

            # size slider (log scale)
            with ui.row().classes("w-full items-center gap-x-5 gap-y-1 mt-3 flex-wrap"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("straighten", size="xs").classes("ci-yellow")
                    ui.label(t(L, "size.label")).classes("ci-kicker")
                    self._size_label = ui.label("").classes("text-sm font-bold ci-yellow num")
                with ui.element("div").classes("flex-1 min-w-[220px] px-2"):
                    rng = ui.range(min=config.SIZE_LOG_MIN, max=config.SIZE_LOG_MAX, step=0.1, on_change=self._changed).props(
                        f'dark aria-label="{t(L, "size.label")}"'
                    ).classes("size-slider w-full").bind_value(self, "size_range")
                    rng._props["markers"] = 1
                    rng._props["marker-labels"] = {"6": "1M", "7": "10M", "8": "100M", "9": "1B", "10": "10B+"}
                self._unsized_switch = ui.switch(t(L, "size.unsized"), on_change=self._changed).props("dark dense").classes(
                    "text-xs ci-muted").bind_value(self, "include_unsized")
                self._unsized_switch.tooltip(t(L, "size.unsized_hint"))
            self._update_size_label()

    def set_count(self, shown: int, total: int):
        if self.results_label is not None:
            self.results_label.text = t(self.lang, "filter.count", shown=shown, total=total)
