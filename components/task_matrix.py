# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Callable, Optional, Dict, Any, List
from services.benchmark_service import benchmark_service
from components.filters import FilterBar
import config
from i18n import t, ds_text, task_label, ds_abbr

OWN_ORG = "VAGO Solutions"
# sequential colour scale in one hue (VAGO violet), opacity by value within the column
ALPHA_MIN, ALPHA_MAX = 0.05, 0.55


def _cell_style(v: Optional[float], lo: float, hi: float) -> str:
    if v is None or hi <= lo:
        return ""
    a = ALPHA_MIN + (ALPHA_MAX - ALPHA_MIN) * (v - lo) / (hi - lo)
    return f"background: rgba(128, 84, 255, {a:.3f});"


class TaskMatrix:
    """Task performance tab: models × all tasks (overall, five datasets, OpenLegalRetrieval t1–t7), sortable."""

    def __init__(self, lang: str, on_model_click: Optional[Callable] = None):
        self.lang = lang
        self.on_model_click = on_model_click
        self.filters = FilterBar(lang, self.refresh)
        self.container = None

    def _columns(self) -> List[Dict[str, Any]]:
        L = self.lang
        cols = [{"name": "model", "label": t(L, "table.col_model"), "field": "model_name", "align": "left", "sortable": True},
                {"name": "size", "label": t(L, "table.col_size"), "field": "parameters_sort", "align": "right", "sortable": True}]
        for k in config.DATASETS_INFO:
            cols.append({"name": k, "label": "Overall" if k == "overall" else ds_abbr(k), "field": k, "align": "right",
                         "sortable": True, "tip": ds_text(L, k, "name"),
                         "headerClasses": "grp-olr" if k == config.OLR_KEY else "", "classes": "grp-olr" if k == config.OLR_KEY else ""})
        for k in config.OLR_TASKS:
            cols.append({"name": k, "label": k, "sub": config.OLR_TASKS[k]["short"], "field": k, "align": "right",
                         "sortable": True, "tip": task_label(L, k, long=True)})
        return cols

    def render(self):
        L = self.lang
        with ui.column().classes("w-full max-w-7xl mx-auto px-4 pb-16 gap-5"):
            with ui.element("div").classes("ci-card w-full p-5 md:p-6"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("grid_on", size="sm").classes("ci-yellow")
                    ui.label(t(L, "tasks.title")).classes("ci-title text-lg md:text-xl")
                ui.label(t(L, "tasks.lead")).classes("text-sm ci-text mt-1")
                with ui.row().classes("items-center gap-3 mt-3 flex-wrap text-xs ci-muted"):
                    ui.label(t(L, "tasks.legend_low"))
                    ui.element("div").classes("legend-ramp")
                    ui.label(t(L, "tasks.legend_high"))
                    ui.html('<span class="ci-yellow" style="font-weight:800">0.000</span>')
                    ui.label(t(L, "tasks.legend_best"))
                    ui.label("–").classes("ci-faint")
                    ui.label(t(L, "tasks.legend_missing"))
                with ui.expansion(t(L, "tasks.olr_explain")).props("dense dark").classes("w-full mt-2 text-sm"):
                    with ui.column().classes("gap-1 py-1"):
                        ui.label(ds_text(L, config.OLR_KEY, "description")).classes("text-xs ci-muted")
                        for k, info in config.OLR_TASKS.items():
                            with ui.row().classes("items-center gap-2 flex-nowrap"):
                                ui.label(k).classes("text-xs font-bold ci-yellow w-6")
                                ui.label(task_label(L, k, long=True)).classes("text-xs ci-text")
                                ui.label(t(L, "tasks.lengths", q=info["q"], d=info["d"])).classes("text-[11px] ci-faint")

            self.filters.render()
            with ui.element("div").classes("ci-card w-full").style("overflow-x: auto;"):
                self.container = ui.column().classes("w-full gap-0")
            self.refresh()

    def refresh(self):
        if self.container is None:
            return
        L = self.lang
        rows = benchmark_service.get_task_matrix(**self.filters.kwargs())
        self.filters.set_count(len(rows), len(benchmark_service.load_entries()))
        cols = self._columns()
        keys = [c["name"] for c in cols if c["name"] not in ("model", "size")]
        spans = {}
        for k in keys:
            vals = [r["values"][k] for r in rows if r["values"][k] is not None]
            spans[k] = (min(vals), max(vals)) if vals else (0.0, 0.0)

        tab_rows = []
        for r in rows:
            row = {"id": r["id"], "model_name": r["model_name"], "own": r["organization"] == OWN_ORG,
                   "org": r["organization"], "size_text": r["formatted_parameters"],
                   "parameters_sort": r["parameters"] if r["parameters"] and r["parameters"] > 1 else -1}
            for k in keys:
                v = r["values"][k]
                lo, hi = spans[k]
                row[k] = v if v is not None else -1.0          # missing values sort last
                row["t_" + k] = f"{v:.4f}" if v is not None else "–"
                row["s_" + k] = _cell_style(v, lo, hi)
                row["c_" + k] = ("best" if v is not None and abs(v - hi) < 1e-9 else ("missing" if v is None else ""))
                if k == config.OLR_KEY:
                    row["c_" + k] += " grp-olr"
            tab_rows.append(row)

        self.container.clear()
        with self.container:
            if not tab_rows:
                with ui.column().classes("w-full p-12 items-center text-center gap-2"):
                    ui.icon("search_off", size="xl").classes("ci-faint")
                    ui.label(t(L, "table.empty")).classes("text-sm font-semibold ci-muted")
                return
            table = ui.table(columns=cols, rows=tab_rows, row_key="id", pagination=0).props(
                'dense flat dark binary-state-sort column-sort-order="da" :rows-per-page-options="[0]" hide-bottom'
            ).classes("task-matrix")
            table.style("min-width: 100%;")
            table.add_slot("header", r'''
                <q-tr :props="props">
                  <q-th v-for="col in props.cols" :key="col.name" :props="props" :class="col.headerClasses">
                    {{ col.label }}<div v-if="col.sub" style="font-size:9px; font-weight:600; letter-spacing:0.02em; text-transform:none; opacity:0.85">{{ col.sub }}</div>
                    <q-tooltip v-if="col.tip" class="text-body2">{{ col.tip }}</q-tooltip>
                  </q-th>
                </q-tr>''')
            table.add_slot("body", r'''
                <q-tr :props="props">
                  <q-td key="model" :props="props" style="min-width: 200px; max-width: 250px; white-space: normal;">
                    <div style="display:flex; align-items:center; gap:6px; cursor:pointer;"
                         @click="() => $parent.$emit('open_model', props.row.id)">
                      <span v-if="props.row.own" class="ci-drop-dot"></span>
                      <span class="model-name" :class="props.row.own ? 'own' : ''"
                            style="display:block; white-space:normal; overflow-wrap:anywhere; line-height:1.25;">{{ props.row.model_name }}</span>
                    </div>
                    <div class="ci-muted" style="font-size:11px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ props.row.org }}</div>
                  </q-td>
                  <q-td key="size" :props="props" class="ci-text">{{ props.row.size_text }}</q-td>
                  <q-td v-for="col in props.cols.slice(2)" :key="col.name" :props="props"
                        :class="props.row['c_' + col.name]" :style="props.row['s_' + col.name]">{{ props.row['t_' + col.name] }}</q-td>
                </q-tr>''')
            table.on("open_model", self._open)

    def _open(self, e):
        if not self.on_model_click:
            return
        model_id = e.args if isinstance(e.args, str) else (e.args[0] if isinstance(e.args, list) and e.args else None)
        item = benchmark_service.get_model_item(model_id) if model_id else None
        if item:
            self.on_model_click(item)
