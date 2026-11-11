# pyrefly: ignore [missing-import]
from nicegui import ui, events, run
from typing import Dict, Any
import json
import csv
import io
import config
from services.custom_eval_service import custom_eval_service
from i18n import t


def model_label(lang: str, spec: Dict[str, Any]) -> str:
    return spec.get("label_de", spec["label"]) if lang == "de" else spec["label"]


class CustomEvalView:
    """
    Evaluation of custom datasets in NanoBEIR format (corpus, queries, qrels), nDCG@10 as the primary metric,
    at most 50 corpus documents. Approved models at pinned revisions only (see config.ALLOWED_EVAL_MODELS).
    """

    def __init__(self, lang: str):
        self.lang = lang
        self.model_name = config.DEFAULT_EVAL_MODEL
        self.encoder_mode = "auto"
        self.precision_label = "FP32"
        self.batch_size = 32
        self.custom_dataset_name = "NanoBEIR-DE-Legal-Sample (BGB & BGH)"
        self.active_input_tab = "files"
        self.json_editor = None
        self.corpus_editor = None
        self.queries_editor = None
        self.qrels_editor = None
        self.dataset_name_input = None
        self.status_label = None
        self.stats_row = None
        self.eval_btn = None
        self.spinner = None
        self.results_container = None
        self._validated_dataset = None

    def render(self):
        L = self.lang
        with ui.element("div").classes("w-full max-w-7xl mx-auto px-4 pb-16"):
            with ui.element("div").classes("ci-card w-full p-5 md:p-8"):
                with ui.row().classes("w-full justify-between items-start flex-wrap gap-4 mb-4"):
                    with ui.column().classes("gap-1 flex-1 min-w-[260px]"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("science", size="sm").classes("ci-yellow")
                            ui.label(t(L, "custom.title")).classes("ci-title text-lg md:text-xl")
                        ui.label(t(L, "custom.lead", n=config.MAX_CUSTOM_CORPUS_DOCS)).classes("text-xs md:text-sm ci-muted leading-relaxed")
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.button(t(L, "custom.load_sample"), on_click=self._load_sample_dataset, icon="auto_fix_high").props(
                            "outline dense no-caps").classes("action-btn text-xs px-3 py-1.5")
                        ui.button(t(L, "custom.download_sample"), icon="download",
                                  on_click=lambda: ui.download(config.DATA_DIR / "sample_nanobeir_dataset.json", "sample_nanobeir_dataset.json")
                                  ).props("flat dense no-caps").classes("btn-ghost text-xs")

                with ui.row().classes("items-center gap-2 mb-6 flex-wrap text-xs"):
                    for icon, text in (("verified", t(L, "custom.badge_format")), ("analytics", t(L, "custom.badge_metric")),
                                       ("library_books", t(L, "custom.badge_limit", n=config.MAX_CUSTOM_CORPUS_DOCS))):
                        with ui.row().classes("items-center gap-1.5 px-3 py-1 ci-subcard"):
                            ui.icon(icon, size="xs").classes("ci-yellow")
                            ui.label(text).classes("ci-text font-semibold")
                    rt = custom_eval_service.get_runtime_status()
                    with ui.row().classes("items-center gap-1.5 px-3 py-1 ci-subcard"):
                        ui.icon("memory" if rt["ready"] else "downloading", size="xs").classes("ci-violet")
                        if rt["ready"]:
                            mv = t(L, "custom.engine_mv") if rt["has_multivector"] else t(L, "custom.engine_dense")
                            ui.label(t(L, "custom.engine", v=rt["st_version"], mode=mv, device=rt["device"])).classes("ci-text font-semibold")
                        else:
                            ui.label(t(L, "custom.engine_missing")).classes("ci-text font-semibold")

                # 1. model
                with ui.element("div").classes("ci-subcard w-full p-4 mb-5"):
                    ui.label(t(L, "custom.step1")).classes("ci-kicker mb-3")
                    with ui.row().classes("w-full items-center gap-4 flex-wrap"):
                        ui.select(options={k: model_label(L, v) for k, v in config.ALLOWED_EVAL_MODELS.items()},
                                  value=self.model_name, label=t(L, "custom.model_select")).props(
                            "outlined dense dark options-dense").classes("flex-1 min-w-[260px]").bind_value(self, "model_name")
                        ui.select(options=["FP32", "FP16", "BF16"], value="FP32", label=t(L, "custom.precision")).props(
                            "outlined dense dark options-dense").classes("w-28").bind_value(self, "precision_label")

                # 2. dataset
                with ui.element("div").classes("ci-subcard w-full p-4"):
                    with ui.row().classes("w-full justify-between items-center flex-wrap gap-2 mb-3"):
                        ui.label(t(L, "custom.step2", n=config.MAX_CUSTOM_CORPUS_DOCS)).classes("ci-kicker")
                        self.stats_row = ui.row().classes("items-center gap-2 text-xs")

                    with ui.row().classes("w-full justify-between items-center flex-wrap gap-4 mb-3"):
                        self.dataset_name_input = ui.input(
                            label=t(L, "custom.name_label"), placeholder=t(L, "custom.name_placeholder"),
                            on_change=lambda _: self._sync_split_to_combined() if self.active_input_tab == "split" else None,
                        ).props("outlined dense dark").classes("w-80 max-w-full")
                        self.dataset_name_input.bind_value(self, "custom_dataset_name")
                        with ui.tabs().props("dense dark no-caps") as input_tabs:
                            tab_combined = ui.tab("combined", label=t(L, "custom.tab_combined"), icon="data_object")
                            tab_split = ui.tab("split", label=t(L, "custom.tab_split"), icon="folder_copy")

                    with ui.tab_panels(input_tabs, value=tab_combined).props("dark animated").classes("w-full bg-transparent p-0"):
                        with ui.tab_panel(tab_combined).classes("p-0 gap-3"):
                            with ui.row().classes("w-full items-center gap-4 mb-3 flex-wrap"):
                                ui.upload(label=t(L, "custom.upload_combined"), on_upload=self._handle_file_upload, auto_upload=True,
                                          max_file_size=5_000_000).props('accept=".json,.jsonl" dark').classes("w-full max-w-md")
                                ui.html(t(L, "custom.structure_html", n=config.MAX_CUSTOM_CORPUS_DOCS)).classes("text-xs ci-muted")
                            self.json_editor = ui.textarea(
                                label=t(L, "custom.editor_label"),
                                placeholder='{\n  "name": "...",\n  "corpus": [{"_id": "d1", "title": "...", "text": "..."}],\n  "queries": [{"_id": "q1", "text": "..."}],\n  "qrels": [{"query-id": "q1", "corpus-id": "d1", "score": 1}]\n}',
                                on_change=self._validate_current_dataset,
                            ).props('outlined rows="10" dark').classes("w-full text-xs")
                            self.json_editor.style("font-family: ui-monospace, SFMono-Regular, Menlo, monospace;")

                        with ui.tab_panel(tab_split).classes("p-0 gap-3"):
                            ui.label(t(L, "custom.split_hint")).classes("text-xs ci-muted mb-2")
                            with ui.element("div").classes("w-full grid grid-cols-1 md:grid-cols-3 gap-4"):
                                self.corpus_editor = self._split_column(t(L, "custom.upload_corpus", n=config.MAX_CUSTOM_CORPUS_DOCS),
                                                                        self._handle_corpus_upload, "corpus (JSON / JSONL)",
                                                                        '[{"_id": "d1", "title": "§ 823 BGB", "text": "..."}]')
                                self.queries_editor = self._split_column(t(L, "custom.upload_queries"), self._handle_queries_upload,
                                                                         "queries (JSON / JSONL)", '[{"_id": "q1", "text": "..."}]')
                                self.qrels_editor = self._split_column(t(L, "custom.upload_qrels"), self._handle_qrels_upload,
                                                                       "qrels (JSON / JSONL / TSV)", '[{"query-id": "q1", "corpus-id": "d1", "score": 1}]')

                    with ui.row().classes("w-full justify-between items-center mt-4 flex-wrap gap-3"):
                        self.status_label = ui.label("").classes("text-xs font-semibold")
                        with ui.row().classes("items-center gap-3"):
                            self.spinner = ui.spinner(size="md").classes("hidden ci-yellow")
                            self.eval_btn = ui.button(t(L, "custom.run"), on_click=self._run_evaluation, icon="play_arrow").props(
                                "no-caps").classes("btn-primary px-5 py-2 text-xs")
                            self.eval_btn.disable()

                self.results_container = ui.column().classes("w-full mt-6 gap-4")
                self._load_sample_dataset()

    def _split_column(self, upload_label: str, handler, editor_label: str, placeholder: str):
        with ui.column().classes("w-full gap-2"):
            ui.upload(label=upload_label, on_upload=handler, auto_upload=True, max_file_size=5_000_000).props(
                'accept=".json,.jsonl,.csv,.tsv" dark').classes("w-full")
            ed = ui.textarea(label=editor_label, placeholder=placeholder, on_change=self._sync_split_to_combined).props(
                'outlined rows="7" dark').classes("w-full text-xs")
            ed.style("font-family: ui-monospace, SFMono-Regular, Menlo, monospace;")
        return ed

    def _load_sample_dataset(self):
        sample_path = config.DATA_DIR / "sample_nanobeir_dataset.json"
        if sample_path.exists() and self.json_editor is not None:
            content = sample_path.read_text(encoding="utf-8")
            self.json_editor.value = content
            try:
                parsed = json.loads(content)
                self.custom_dataset_name = parsed.get("name", "NanoBEIR-DE-Legal-Sample")
                for ed, key in ((self.corpus_editor, "corpus"), (self.queries_editor, "queries"), (self.qrels_editor, "qrels")):
                    if ed:
                        ed.value = json.dumps(parsed.get(key, []), indent=2, ensure_ascii=False)
            except Exception:
                pass
            self._validate_current_dataset()

    @staticmethod
    def _parse_subset_content(raw_text: str) -> list:
        """Parses a NanoBEIR part from a JSON array, JSONL or TSV/CSV."""
        text = (raw_text or "").strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            pass
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines and lines[0].startswith("{"):
            return [json.loads(ln) for ln in lines]
        delimiter = "\t" if "\t" in lines[0] else ","
        return [dict(row) for row in csv.DictReader(io.StringIO(text), delimiter=delimiter)]

    def _sync_split_to_combined(self):
        try:
            combined = {
                "name": self.custom_dataset_name or "Custom Legal NanoBEIR",
                "corpus": self._parse_subset_content(self.corpus_editor.value if self.corpus_editor else ""),
                "queries": self._parse_subset_content(self.queries_editor.value if self.queries_editor else ""),
                "qrels": self._parse_subset_content(self.qrels_editor.value if self.qrels_editor else ""),
            }
            if self.json_editor:
                self.json_editor.value = json.dumps(combined, indent=2, ensure_ascii=False)
            self._validate_current_dataset()
        except Exception as ex:
            if self.status_label:
                self.status_label.text = "⚠️ " + t(self.lang, "custom.split_error", err=str(ex))
                self.status_label.classes(replace="text-xs font-semibold text-rose-300")

    async def _read(self, e: events.UploadEventArguments) -> str:
        return await e.file.text("utf-8")   # NiceGUI >= 3: file via e.file

    async def _handle_corpus_upload(self, e: events.UploadEventArguments):
        await self._handle_part(e, self.corpus_editor, "Corpus")

    async def _handle_queries_upload(self, e: events.UploadEventArguments):
        await self._handle_part(e, self.queries_editor, "Queries")

    async def _handle_qrels_upload(self, e: events.UploadEventArguments):
        await self._handle_part(e, self.qrels_editor, "Qrels")

    async def _handle_part(self, e, editor, what: str):
        try:
            content = await self._read(e)
            if editor:
                editor.value = content
            self._sync_split_to_combined()
            ui.notify(t(self.lang, "msg.part_loaded", what=what, name=e.file.name), type="positive")
        except Exception as ex:
            ui.notify(t(self.lang, "msg.file_error", err=str(ex)), type="negative")

    async def _handle_file_upload(self, e: events.UploadEventArguments):
        try:
            content = await self._read(e)
            self.json_editor.value = content
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    if parsed.get("name"):
                        self.custom_dataset_name = parsed["name"]
                    for ed, key in ((self.corpus_editor, "corpus"), (self.queries_editor, "queries"), (self.qrels_editor, "qrels")):
                        if ed and key in parsed:
                            ed.value = json.dumps(parsed[key], indent=2, ensure_ascii=False)
            except Exception:
                pass
            self._validate_current_dataset()
            ui.notify(t(self.lang, "msg.file_loaded", name=e.file.name), type="positive")
        except Exception as ex:
            ui.notify(t(self.lang, "msg.file_error", err=str(ex)), type="negative")

    def _validate_current_dataset(self):
        L = self.lang
        raw_val = (self.json_editor.value or "").strip() if self.json_editor else ""
        if not raw_val:
            if self.status_label:
                self.status_label.text = ""
            if self.stats_row:
                self.stats_row.clear()
            if self.eval_btn:
                self.eval_btn.disable()
            self._validated_dataset = None
            return
        valid, msg, dataset = custom_eval_service.parse_and_validate_dataset(raw_val, L)
        if not valid or dataset is None:
            self._validated_dataset = None
            if self.status_label:
                self.status_label.text = f"⚠️ {msg}"
                self.status_label.classes(replace="text-xs font-semibold text-rose-300")
            if self.stats_row:
                self.stats_row.clear()
            if self.eval_btn:
                self.eval_btn.disable()
            return
        self._validated_dataset = dataset
        n_docs, n_q = len(dataset.corpus), len(dataset.queries)
        n_rel = len([q for q in dataset.qrels if q.score > 0])
        if self.status_label:
            self.status_label.text = "✅ " + t(L, "custom.valid", docs=n_docs, max=config.MAX_CUSTOM_CORPUS_DOCS, q=n_q, rel=n_rel)
            self.status_label.classes(replace="text-xs font-semibold text-emerald-300")
        if self.stats_row:
            self.stats_row.clear()
            with self.stats_row:
                ui.html(f'<span class="badge badge-yellow">{t(L, "custom.stat_corpus", n=n_docs, max=config.MAX_CUSTOM_CORPUS_DOCS)}</span>')
                ui.html(f'<span class="badge badge-violet">Queries: {n_q}</span>')
        if self.eval_btn:
            self.eval_btn.enable()

    async def _run_evaluation(self):
        L = self.lang
        if not self._validated_dataset:
            ui.notify(t(L, "custom.need_dataset", n=config.MAX_CUSTOM_CORPUS_DOCS), type="warning")
            return
        self.eval_btn.disable()
        self.spinner.classes(remove="hidden")
        try:
            res = await run.io_bound(custom_eval_service.evaluate_dataset_sync, self._validated_dataset, self.model_name,
                                     self.encoder_mode, self.precision_label, self.batch_size, L)
            self._render_results(res)
            ui.notify(t(L, "custom.done", v=f"{res['ndcg_at_10']:.4f}"), type="positive", duration=5)
        except Exception as e:
            ui.notify(t(L, "custom.error", err=str(e)), type="negative", duration=8)
        finally:
            self.eval_btn.enable()
            self.spinner.classes(add="hidden")

    def _render_results(self, res: Dict[str, Any]):
        L = self.lang
        if not self.results_container:
            return
        self.results_container.clear()
        with self.results_container:
            ui.element("div").classes("ci-band my-2")
            if res.get("warning"):
                with ui.row().classes("ci-subcard w-full p-3 items-center gap-2"):
                    ui.icon("info").classes("ci-yellow")
                    ui.label(res["warning"]).classes("text-xs ci-text font-medium")
            with ui.row().classes("w-full justify-between items-center flex-wrap gap-2"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("emoji_events").classes("ci-yellow text-xl")
                    ui.label(t(L, "custom.result_title", name=res["dataset_name"])).classes("text-base font-extrabold uppercase tracking-wider")
                ui.label(t(L, "custom.result_meta", model=res["model_name"], enc=res["encoder_used"], prec=res["precision"],
                           s=res["elapsed_seconds"])).classes("text-xs ci-muted num")
            with ui.element("div").classes("w-full grid grid-cols-2 md:grid-cols-4 gap-4"):
                with ui.element("div").classes("ci-subcard p-4 text-center").style("border-color: #F8D84A;"):
                    ui.label(t(L, "custom.kpi_ndcg")).classes("ci-kicker ci-yellow")
                    ui.label(f"{res['ndcg_at_10']:.4f}").classes("text-3xl font-extrabold num mt-1")
                for label, val in (("Recall@10", f"{res['recall_at_10']:.2f}%"), ("MRR@10", f"{res['mrr_at_10']:.2f}%"),
                                   (t(L, "custom.kpi_scope"), f"{res['num_corpus']} Docs / {res['num_queries']} Queries")):
                    with ui.element("div").classes("ci-subcard p-4 text-center"):
                        ui.label(label).classes("ci-kicker")
                        ui.label(val).classes("text-xl font-bold num mt-1 ci-text")

            details = res.get("query_details", [])
            if details:
                ui.label(t(L, "custom.per_query")).classes("ci-kicker mt-2")
                with ui.element("div").classes("ci-subcard w-full overflow-x-auto"):
                    with ui.row().classes("lb-head w-full px-4 py-2.5 items-center flex-nowrap min-w-[640px]"):
                        ui.label("Query ID").classes("h w-24")
                        ui.label(t(L, "custom.col_query")).classes("h flex-1 min-w-[200px]")
                        ui.label(t(L, "custom.col_top1")).classes("h w-48")
                        ui.label("Hits@10").classes("h w-24 text-center")
                        ui.label("nDCG@10").classes("h score w-28 text-right")
                    for qd in details:
                        with ui.row().classes("lb-row w-full px-4 py-3 text-xs items-center flex-nowrap min-w-[640px]"):
                            ui.label(qd["query_id"]).classes("w-24 font-bold ci-violet")
                            ui.label(qd["query_text"]).classes("flex-1 min-w-[200px] ci-text")
                            with ui.row().classes("w-48 items-center gap-1 flex-nowrap"):
                                ok = qd.get("top_doc_is_relevant", False)
                                ui.icon("check_circle" if ok else "cancel").classes("text-sm " + ("text-emerald-300" if ok else "text-rose-300"))
                                ui.label(qd["top_doc_id"]).classes("ci-text truncate")
                            ui.label(f"{qd['hits_at_10']}/{qd['relevant_count']}").classes("w-24 text-center ci-muted num")
                            ui.label(f"{qd['ndcg_at_10']:.4f}").classes("w-28 text-right font-bold ci-yellow num")
