# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Callable, Optional, Dict, Any, List
from services.benchmark_service import benchmark_service
from components.filters import FilterBar
import config
from i18n import t, ds_text, model_type_label, embedding_type_label, task_label, ds_abbr, license_label

EMB_CLASS = {"Dense": "badge-emb-dense", "Late-Interaction": "badge-emb-late", "Hybrid": "badge-emb-hybrid",
             "MoE": "badge-emb-moe", "BM25": "badge-emb-bm25"}
OWN_ORG = "VAGO Solutions"


def type_badge(lang: str, model_type: str):
    cls = "badge-open" if model_type == "open" else "badge-prop"
    ui.html(f'<span class="badge {cls}"><span class="dot"></span>{model_type_label(lang, model_type)}</span>')


def emb_badge(lang: str, emb: str):
    ui.html(f'<span class="badge {EMB_CLASS.get(emb, "")}"><span class="dot"></span>{embedding_type_label(lang, emb)}</span>')


class LeaderboardTable:
    def __init__(self, lang: str, on_model_click: Optional[Callable] = None):
        self.lang = lang
        self.on_model_click = on_model_click
        self.current_dataset = "overall"
        self.sort_metric = "ndcg_at_10"
        self.sort_ascending = False
        self.filters = FilterBar(lang, self.refresh_table)
        self.table_container = None
        self.tabs_container = None
        self.desc_label = None

    # columns next to the main score: the five datasets in Overall, the seven subtasks for OpenLegalRetrieval
    def _extra_columns(self) -> List[Dict[str, str]]:
        L = self.lang
        if self.current_dataset == "overall":
            return [{"key": k, "head": ds_abbr(k), "tip": ds_text(L, k, "name"), "kind": "ds"}
                    for k in config.DATASETS_INFO if k != "overall"]
        if self.current_dataset == config.OLR_KEY:
            return [{"key": k, "head": k, "tip": task_label(L, k, long=True), "kind": "sub"} for k in config.OLR_TASKS]
        return []

    def render(self):
        L = self.lang
        with ui.column().classes("w-full max-w-7xl mx-auto px-4 pb-16 gap-5"):
            with ui.column().classes("w-full items-center gap-2 mt-1"):
                ui.label(t(L, "table.dataset_label")).classes("ci-kicker text-center")
                self.tabs_container = ui.row().classes("justify-center items-center gap-2 flex-wrap max-w-5xl mx-auto")
                self._render_tabs()
                self.desc_label = ui.label("").classes("text-xs ci-muted text-center max-w-3xl")

            self.filters.render()

            with ui.element("div").classes("ci-card w-full overflow-hidden"):
                self.table_container = ui.column().classes("w-full gap-0")

            self.refresh_table()

    def _render_tabs(self):
        if not self.tabs_container:
            return
        self.tabs_container.clear()
        with self.tabs_container:
            for d_key, d_info in config.DATASETS_INFO.items():
                active = d_key == self.current_dataset
                ui.button(d_info["short_name"], icon=d_info["icon"], on_click=lambda k=d_key: self._set_dataset(k)).props(
                    f'flat no-caps aria-pressed="{str(active).lower()}"'
                ).classes("dataset-pill" + (" active" if active else ""))

    def _set_dataset(self, dataset_key: str):
        self.current_dataset = dataset_key
        self._render_tabs()
        self.refresh_table()

    def refresh_table(self):
        if self.table_container is None:
            return
        L = self.lang
        ranked = benchmark_service.get_ranked_entries(
            dataset_key=self.current_dataset, sort_metric=self.sort_metric, ascending=self.sort_ascending,
            **self.filters.kwargs(),
        )
        total = sum(1 for e in benchmark_service.load_entries() if benchmark_service.has_dataset(e, self.current_dataset))
        self.filters.set_count(len(ranked), total)
        if self.desc_label is not None:
            self.desc_label.text = ds_text(L, self.current_dataset, "description")

        extra = self._extra_columns()
        # best value per extra column among the shown models (highlighted in yellow)
        best: Dict[str, float] = {}
        for c in extra:
            vals = [self._extra_value(it, c) for it in ranked]
            vals = [v for v in vals if v is not None]
            if vals:
                best[c["key"]] = max(vals)
        olr = self.current_dataset == config.OLR_KEY
        overall = self.current_dataset == "overall"
        # visibility per screen width (Overall/OLR need room for the extra columns)
        cls_type = "vis-xl"
        cls_emb = "vis-xl" if olr else ("vis-lg" if overall else "vis-md")
        cls_extra = "vis-lg"

        self.table_container.clear()
        with self.table_container:
            if not ranked:
                with ui.column().classes("w-full p-12 items-center text-center gap-2"):
                    ui.icon("search_off", size="xl").classes("ci-faint")
                    ui.label(t(L, "table.empty")).classes("text-sm font-semibold ci-muted")
                    ui.button(t(L, "table.reset"), on_click=self.filters.reset).props("outline dense no-caps").classes("btn-ghost text-xs mt-2")
                return

            if extra:
                with ui.row().classes(f"{cls_extra} w-full px-5 pt-3 pb-1 gap-x-4 gap-y-1 flex-wrap text-[11px] ci-faint"):
                    for c in extra:
                        ui.label(f"{c['head']} = {c['tip']}")

            with ui.row().classes("lb-head w-full px-3 md:px-5 py-3 items-center gap-2 flex-nowrap"):
                ui.label("#").classes("h w-8 md:w-10 text-center")
                ui.label(t(L, "table.col_model")).classes("h flex-1 min-w-[120px] md:min-w-[200px]")
                ui.label(t(L, "table.col_size")).classes("h w-14 md:w-16 text-right")
                with ui.row().classes(f"{cls_type} w-[136px] justify-center"):
                    ui.label(t(L, "table.col_type")).classes("h")
                with ui.row().classes(f"{cls_emb} w-[124px] justify-center"):
                    ui.label(t(L, "table.col_embedding")).classes("h")
                for c in extra:
                    with ui.row().classes(f"{cls_extra} w-[56px] justify-end"):
                        lab = ui.label(c["head"]).classes("h")
                        lab.tooltip(c["tip"])
                score_head = "Overall" if overall else "nDCG@10"
                ui.label(f"{score_head} ▾").classes("h score w-16 md:w-20 text-right")
                ui.label("").classes("vis-md w-9")

            for item in ranked:
                own = item["organization"] == OWN_ORG
                with ui.row().classes("lb-row w-full px-3 md:px-5 py-3 items-center gap-2 flex-nowrap" + (" own" if own else "")):
                    with ui.row().classes("w-8 md:w-10 justify-center"):
                        r = item["rank"]
                        ui.label(str(r)).classes("rank-badge " + (f"rank-{r}" if r <= 3 else "rank-regular"))

                    with ui.column().classes("flex-1 min-w-[120px] md:min-w-[200px] gap-0.5 overflow-hidden"):
                        with ui.row().classes("items-start gap-1.5 flex-nowrap"):
                            if own:
                                ui.element("span").classes("ci-drop-dot mt-1")
                            name = ui.label(item["model_name"]).classes(
                                "model-name text-sm cursor-pointer leading-tight" + (" own" if own else "")).style("overflow-wrap: anywhere;")
                            name.props('role="button" tabindex="0"')
                            if self.on_model_click:
                                name.on("click", lambda _, it=item: self.on_model_click(it))
                                name.on("keydown.enter", lambda _, it=item: self.on_model_click(it))
                        meta = [item["organization"]]
                        if item.get("dimension") not in (None, "-"):
                            meta.append(f"{item['dimension']}d")
                        if item.get("max_tokens") not in (None, "-"):
                            meta.append(f"{item['max_tokens']:,} tok".replace(",", "." if L == "de" else ","))
                        if item.get("license"):
                            meta.append(t(L, "table.model_license", lic=license_label(L, item["license"])))
                        # w-full: otherwise the label is as wide as its text and truncate never applies;
                        # this way the line ends with "…" and the full text is in the tooltip.
                        meta_txt = " · ".join(meta)
                        meta_lbl = ui.label(meta_txt).classes("text-[11px] ci-muted truncate w-full")
                        meta_lbl._props["title"] = meta_txt  # set directly, no props-string parsing

                    ui.label(item["formatted_parameters"]).classes("w-14 md:w-16 text-right text-xs font-semibold ci-text num")
                    with ui.row().classes(f"{cls_type} w-[136px] justify-center"):
                        type_badge(L, item["model_type"])
                    with ui.row().classes(f"{cls_emb} w-[124px] justify-center"):
                        emb_badge(L, item["embedding_type"])
                    for c in extra:
                        v = self._extra_value(item, c)
                        with ui.row().classes(f"{cls_extra} w-[56px] justify-end"):
                            if v is None:
                                ui.label("–").classes("metric-cell missing")
                            else:
                                ui.label(f"{v:.3f}").classes("metric-cell" + (" best" if abs(v - best.get(c["key"], -1)) < 1e-9 else ""))
                    ui.label(f"{item['ndcg_at_10']:.4f}").classes("metric-primary w-16 md:w-20 text-right")
                    with ui.row().classes("vis-md w-9 justify-center"):
                        ui.button(icon="visibility", on_click=lambda _, it=item: self.on_model_click(it) if self.on_model_click else None
                                  ).props(f'flat round dense size=sm aria-label="{t(L, "table.details")}"').classes("btn-ghost")

    @staticmethod
    def _extra_value(item: Dict[str, Any], c: Dict[str, str]) -> Optional[float]:
        if c["kind"] == "ds":
            return item.get("all_metrics", {}).get(c["key"])
        return (item.get("subtasks") or {}).get(c["key"])
