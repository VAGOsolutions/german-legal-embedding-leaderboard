# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Dict, Any
import config
from i18n import t, ds_text, model_type_label, embedding_type_label, task_label, notes_for, license_label


class ModelDetailDialog:
    def __init__(self, lang: str):
        self.lang = lang
        self.dialog = ui.dialog().classes("w-full")
        self.container = None
        self._build()

    def _build(self):
        with self.dialog, ui.element("div").classes("ci-dialog w-full max-w-3xl p-5 md:p-6").style("width: min(760px, 94vw);"):
            self.container = ui.column().classes("w-full gap-4")

    def _spec(self, label: str, value: str, accent: bool = False):
        with ui.element("div").classes("ci-subcard p-3 text-center"):
            ui.label(label).classes("text-[11px] ci-muted font-semibold")
            ui.label(value).classes("text-lg font-bold num " + ("ci-yellow" if accent else "ci-text"))

    def open(self, item: Dict[str, Any]):
        L = self.lang
        self.container.clear()
        with self.container:
            with ui.row().classes("w-full justify-between items-start flex-nowrap gap-3"):
                with ui.column().classes("gap-1 min-w-0"):
                    with ui.row().classes("items-center gap-2"):
                        if item.get("organization") == "VAGO Solutions":
                            ui.element("span").classes("ci-drop-dot")
                        ui.label(item.get("model_name")).classes("text-xl font-bold")
                    ui.label(" · ".join([
                        item.get("organization") or "",
                        model_type_label(L, item.get("model_type")),
                        embedding_type_label(L, item.get("embedding_type")),
                    ])).classes("text-sm ci-violet")
                ui.button(icon="close", on_click=self.dialog.close).props(f'flat round dense aria-label="{t(L, "common.close")}"').classes("btn-ghost")
            ui.element("div").classes("ci-band")

            dim = item.get("dimension")
            ctx = item.get("max_tokens")
            score = item.get("overall")
            with ui.element("div").classes("w-full grid grid-cols-2 sm:grid-cols-5 gap-3"):
                self._spec(t(L, "detail.dimension"), f"{dim}" if dim not in (None, "-") else "–")
                self._spec(t(L, "detail.context"), f"{ctx:,}".replace(",", "." if L == "de" else ",") if isinstance(ctx, int) else "–")
                self._spec(t(L, "detail.params"), item.get("formatted_parameters") or "–")
                self._spec(t(L, "detail.license"), license_label(L, item.get("license")))
                self._spec("Overall (nDCG@10)", f"{score:.4f}" if isinstance(score, (int, float)) else "–", accent=True)

            # provenance: measured by VAGO Solutions, submitted via PR (benchmark script) or publicly reported MTEB score
            provenance = [t(L, f"source.{item.get('source') or 'vago'}")]
            if item.get("protocol_version"):
                provenance.append(t(L, "detail.protocol", v=item["protocol_version"]))
            if item.get("model_revision"):
                provenance.append(t(L, "detail.revision", rev=str(item["model_revision"])[:12]))
            with ui.row().classes("w-full items-center gap-2 flex-wrap text-xs"):
                ui.label(t(L, "detail.source")).classes("ci-kicker")
                ui.label(" · ".join(provenance)).classes("ci-text")
                if item.get("contamination"):
                    ui.label("⚠ " + t(L, "detail.contamination", ds=", ".join(ds_text(L, k, "short") for k in item["contamination"]))).classes("ci-yellow")

            notes = notes_for(item)
            if notes:
                with ui.element("div").classes("ci-subcard w-full p-4"):
                    ui.label(t(L, "detail.notes")).classes("ci-kicker")
                    ui.label(notes).classes("text-sm ci-text leading-relaxed mt-1")

            ui.label(t(L, "detail.per_dataset")).classes("text-sm font-bold mt-1")
            with ui.element("div").classes("ci-subcard w-full overflow-hidden"):
                metrics = item.get("all_metrics", {})
                for d_key, d_info in config.DATASETS_INFO.items():
                    if d_key == "overall":
                        continue
                    val = metrics.get(d_key)
                    with ui.row().classes("w-full px-4 py-2.5 items-center justify-between border-t border-white/5 flex-nowrap gap-2"):
                        with ui.row().classes("items-center gap-2 flex-nowrap min-w-0"):
                            ui.icon(d_info["icon"], size="xs").classes("ci-yellow")
                            ui.label(ds_text(L, d_key, "short")).classes("font-semibold text-sm truncate")
                        with ui.row().classes("items-center gap-3 flex-nowrap"):
                            ui.label(f"{val:.4f}" if isinstance(val, (int, float)) else "–").classes(
                                "font-bold num " + ("ci-yellow" if isinstance(val, (int, float)) else "ci-faint"))
                            if d_info.get("url"):
                                ui.link(t(L, "detail.dataset_link"), d_info["url"], new_tab=True).classes("ci-link text-xs")
                            else:
                                ui.label(t(L, "olr.license")).classes("text-[11px] ci-faint")

            subs = item.get("subtasks") or {}
            if subs:
                ui.label(t(L, "detail.olr_breakdown")).classes("text-sm font-bold mt-1")
                with ui.element("div").classes("ci-subcard w-full overflow-hidden"):
                    top = max(subs.values()) if subs else 1.0
                    for k, info in config.OLR_TASKS.items():
                        v = subs.get(k)
                        with ui.row().classes("w-full px-4 py-2 items-center gap-3 border-t border-white/5 flex-nowrap"):
                            ui.label(k).classes("text-xs font-bold ci-yellow w-6")
                            with ui.column().classes("gap-0 flex-1 min-w-0"):
                                ui.label(task_label(L, k, long=True)).classes("text-xs ci-text truncate")
                                ui.label(t(L, "tasks.lengths", q=info["q"], d=info["d"])).classes("text-[10px] ci-faint")
                            bar = 0 if not isinstance(v, (int, float)) else max(4, int(100 * v / max(top, 1e-9)))
                            ui.html(f'<div style="width:90px;height:6px;border-radius:3px;background:rgba(255,255,255,0.08);overflow:hidden">'
                                    f'<div style="width:{bar}%;height:100%;background:#F8D84A;border-radius:3px"></div></div>')
                            ui.label(f"{v:.4f}" if isinstance(v, (int, float)) else "–").classes("text-sm font-bold num w-14 text-right")

            with ui.row().classes("w-full justify-between items-center mt-1 flex-wrap gap-2"):
                with ui.row().classes("gap-2"):
                    if item.get("model_url"):
                        ui.button(t(L, "detail.model_link"), icon="open_in_new",
                                  on_click=lambda: ui.navigate.to(item["model_url"], new_tab=True)).props("outline dense no-caps").classes("action-btn text-xs")
                    if item.get("paper_url"):
                        ui.button(t(L, "detail.paper_link"), icon="article",
                                  on_click=lambda: ui.navigate.to(item["paper_url"], new_tab=True)).props("outline dense no-caps").classes("action-btn text-xs")
                ui.button(t(L, "common.close"), on_click=self.dialog.close).props("flat no-caps").classes("btn-ghost")

        self.dialog.open()
