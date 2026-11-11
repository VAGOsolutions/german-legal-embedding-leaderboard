import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import config
from data.schema import BenchmarkEntry, DatasetMetrics, ModelType, EmbeddingType

class BenchmarkService:
    """Reads the leaderboard from results/*.json (one file per model, added via pull request)."""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir: Path = results_dir or config.RESULTS_DIR
        self._cache: Optional[List[BenchmarkEntry]] = None

    @staticmethod
    def result_files(results_dir: Optional[Path] = None) -> List[Path]:
        """All result files; files starting with '_' are ignored."""
        d = results_dir or config.RESULTS_DIR
        if not d.exists():
            return []
        return sorted(p for p in d.glob("*.json") if not p.name.startswith("_"))

    def load_entries(self, force_reload: bool = False) -> List[BenchmarkEntry]:
        """Loads all entries from results/. Invalid files are reported and skipped
        (tests/test_results.py prevents them from being merged)."""
        if self._cache is not None and not force_reload:
            return self._cache
        entries = []
        for path in self.result_files(self.results_dir):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entries.append(BenchmarkEntry(**json.load(f)))
            except Exception as e:
                print(f"Invalid result file {path.name}: {e}")
        self._cache = entries
        return entries

    def has_dataset(self, entry: BenchmarkEntry, dataset_key: str) -> bool:
        """Overall requires all datasets; otherwise the selected dataset must be measured (missing = '–', never 0)."""
        if dataset_key == "all":
            return True
        if dataset_key == "overall":
            return all(k in entry.metrics for k in config.DATASETS_INFO if k != "overall")
        return dataset_key in entry.metrics

    def get_dataset_score(self, entry: BenchmarkEntry, dataset_key: str) -> DatasetMetrics:
        """Metrics for one dataset or the aggregated overall score."""
        if dataset_key == "overall":
            # mean over all available datasets
            ndcg_vals = [m.ndcg_at_10 for k, m in entry.metrics.items() if k in config.DATASETS_INFO and m.ndcg_at_10 is not None]
            recall_vals = [m.recall_at_10 for k, m in entry.metrics.items() if k in config.DATASETS_INFO and m.recall_at_10 is not None]
            mrr_vals = [m.mrr_at_10 for k, m in entry.metrics.items() if k in config.DATASETS_INFO and m.mrr_at_10 is not None]
            map_vals = [m.map_at_10 for k, m in entry.metrics.items() if k in config.DATASETS_INFO and m.map_at_10 is not None]

            return DatasetMetrics(
                ndcg_at_10=round(sum(ndcg_vals) / len(ndcg_vals), 4) if ndcg_vals else 0.0,
                recall_at_10=round(sum(recall_vals) / len(recall_vals), 2) if recall_vals else None,
                mrr_at_10=round(sum(mrr_vals) / len(mrr_vals), 2) if mrr_vals else None,
                map_at_10=round(sum(map_vals) / len(map_vals), 2) if map_vals else None,
            )
        
        return entry.metrics.get(dataset_key, DatasetMetrics(ndcg_at_10=0.0))

    @staticmethod
    def size_range_is_full(size_log_range: Optional[Tuple[float, float]]) -> bool:
        if not size_log_range:
            return True
        lo, hi = size_log_range
        return lo <= config.SIZE_LOG_MIN + 1e-9 and hi >= config.SIZE_LOG_MAX - 1e-9

    @classmethod
    def matches_size(cls, parameters: Optional[int], size_log_range: Optional[Tuple[float, float]] = None,
                     include_unsized: bool = True) -> bool:
        """Size filter (log10 of the parameter count); the slider ends mean "no limit".
        Models without a size (APIs) or without parameters (BM25 = 1) only match when the slider covers the
        full range and unsized models are included."""
        full = cls.size_range_is_full(size_log_range)
        if parameters is None or parameters <= 1:
            return include_unsized and full
        if full:
            return True
        lo, hi = size_log_range
        if lo > config.SIZE_LOG_MIN + 1e-9 and parameters < 10 ** lo:
            return False
        if hi < config.SIZE_LOG_MAX - 1e-9 and parameters > 10 ** hi:
            return False
        return True

    @staticmethod
    def _is_all(v: Optional[str]) -> bool:
        return not v or v in ("all", "All")

    def filter_entries(
        self,
        dataset_key: str = "overall",
        search_query: str = "",
        model_type_filter: Optional[str] = None,
        embedding_type_filter: Optional[str] = None,
        size_log_range: Optional[Tuple[float, float]] = None,
        include_unsized: bool = True,
    ) -> List[BenchmarkEntry]:
        """Shared filter for the table and the task matrix."""
        query = (search_query or "").strip().lower()
        filtered = []
        for entry in self.load_entries():
            if not self.has_dataset(entry, dataset_key):
                continue
            # search: model name, organisation, notes
            if query:
                hay = " ".join([entry.model_name, entry.organization, entry.notes or ""]).lower()
                if query not in hay:
                    continue
            if not self._is_all(model_type_filter) and entry.model_type.value != model_type_filter:
                continue
            if not self._is_all(embedding_type_filter) and entry.embedding_type.value != embedding_type_filter:
                continue
            if not self.matches_size(entry.parameters, size_log_range, include_unsized):
                continue
            filtered.append(entry)
        return filtered

    def get_ranked_entries(
        self,
        dataset_key: str = "overall",
        search_query: str = "",
        model_type_filter: Optional[str] = None,
        embedding_type_filter: Optional[str] = None,
        sort_metric: str = "ndcg_at_10",
        ascending: bool = False,
        size_log_range: Optional[Tuple[float, float]] = None,
        include_unsized: bool = True,
    ) -> List[Dict[str, Any]]:
        """Filters and sorts the entries and adds ranks and medals."""
        filtered = self.filter_entries(dataset_key, search_query, model_type_filter, embedding_type_filter,
                                       size_log_range, include_unsized)

        ranked_list = []
        for entry in filtered:
            score = self.get_dataset_score(entry, dataset_key)
            sort_val = getattr(score, sort_metric, 0.0) or 0.0

            ranked_list.append({
                "entry": entry,
                "score": score,
                "sort_val": sort_val,
            })

        ranked_list.sort(key=lambda x: x["sort_val"], reverse=not ascending)

        results = []
        for idx, item in enumerate(ranked_list, start=1):
            entry = item["entry"]
            score = item["score"]

            medal = None
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"

            results.append(self._make_item(entry, score, idx, medal))

        return results

    def _make_item(self, entry: BenchmarkEntry, score: Optional[DatasetMetrics], rank: Optional[int] = None,
                   medal: Optional[str] = None) -> Dict[str, Any]:
        """Display record of a model (table, detail dialog, chart)."""
        return {
            "rank": rank,
            "medal": medal,
            "id": entry.id,
            "model_name": entry.model_name,
            "organization": entry.organization,
            "model_type": entry.model_type.value,
            "embedding_type": entry.embedding_type.value,
            "dimension": entry.dimension or "-",
            "max_tokens": entry.max_tokens or "-",
            "parameters": entry.parameters,
            "formatted_parameters": self.format_parameters(entry.parameters),
            "model_url": entry.model_url,
            "paper_url": entry.paper_url,
            "notes": entry.notes,
            "ndcg_at_10": score.ndcg_at_10 if score is not None else None,
            "recall_at_10": score.recall_at_10 if score is not None else None,
            "mrr_at_10": score.mrr_at_10 if score is not None else None,
            "map_at_10": score.map_at_10 if score is not None else None,
            "all_metrics": {k: entry.metrics[k].ndcg_at_10 for k in config.DATASETS_INFO.keys() if k != "overall" and k in entry.metrics},
            "overall": self.get_dataset_score(entry, "overall").ndcg_at_10 if self.has_dataset(entry, "overall") else None,
            "subtasks": dict(entry.metrics[config.OLR_KEY].subtasks or {}) if config.OLR_KEY in entry.metrics else {},
            "source": entry.source,
            "model_revision": entry.model_revision,
            "license": entry.license,
            "protocol_version": entry.protocol.version if entry.protocol else None,
            "protocol_script": entry.protocol.script if entry.protocol else None,
            "contamination": list(entry.contamination),
        }

    def get_model_item(self, model_id: str, dataset_key: str = "overall") -> Optional[Dict[str, Any]]:
        """One model for the detail dialog (from task matrix/chart)."""
        entry = next((e for e in self.load_entries() if e.id == model_id), None)
        if entry is None:
            return None
        key = dataset_key if self.has_dataset(entry, dataset_key) else None
        score = self.get_dataset_score(entry, key) if key else None
        return self._make_item(entry, score)

    def task_columns(self) -> List[str]:
        """Task matrix columns: overall, the datasets, then the OpenLegalRetrieval subtasks."""
        return list(config.DATASETS_INFO.keys()) + list(config.OLR_TASKS.keys())

    def get_task_matrix(
        self,
        search_query: str = "",
        model_type_filter: Optional[str] = None,
        embedding_type_filter: Optional[str] = None,
        size_log_range: Optional[Tuple[float, float]] = None,
        include_unsized: bool = True,
    ) -> List[Dict[str, Any]]:
        """All filtered models with every score (missing = None), sorted by overall."""
        rows = []
        for entry in self.filter_entries("all", search_query, model_type_filter, embedding_type_filter,
                                         size_log_range, include_unsized):
            vals: Dict[str, Optional[float]] = {}
            for k in config.DATASETS_INFO:
                if k == "overall":
                    vals[k] = self.get_dataset_score(entry, k).ndcg_at_10 if self.has_dataset(entry, k) else None
                else:
                    vals[k] = entry.metrics[k].ndcg_at_10 if k in entry.metrics else None
            subs = (entry.metrics[config.OLR_KEY].subtasks or {}) if config.OLR_KEY in entry.metrics else {}
            for t in config.OLR_TASKS:
                vals[t] = subs.get(t)
            rows.append({
                "id": entry.id, "model_name": entry.model_name, "organization": entry.organization,
                "model_type": entry.model_type.value, "embedding_type": entry.embedding_type.value,
                "parameters": entry.parameters, "formatted_parameters": self.format_parameters(entry.parameters),
                "values": vals,
            })
        rows.sort(key=lambda r: (r["values"]["overall"] is None, -(r["values"]["overall"] or 0.0)))
        return rows

    @staticmethod
    def format_parameters(params: Optional[int]) -> str:
        """Human-readable parameter count (e.g. 567M, 7.1B, 1 (BM25))."""
        if params is None:
            return "–"
        if params == 1:
            return "1 (BM25)"
        if params >= 1_000_000_000:
            val = params / 1_000_000_000
            val_str = f"{val:.2f}".rstrip("0").rstrip(".")
            return f"{val_str}B"
        if params >= 1_000_000:
            val = params / 1_000_000
            val_str = f"{val:.1f}".rstrip("0").rstrip(".")
            return f"{val_str}M"
        if params >= 1_000:
            val = params / 1_000
            val_str = f"{val:.1f}".rstrip("0").rstrip(".")
            return f"{val_str}k"
        return str(params)

    def get_scatter_plot_data(self, dataset_key: str = "overall") -> List[Dict[str, Any]]:
        """Data points for the performance-vs-model-size scatter plot."""
        entries = self.load_entries()
        scatter_points = []
        for entry in entries:
            if not self.has_dataset(entry, dataset_key) or not entry.parameters:
                continue  # missing score or unknown size (APIs): not in the size chart
            score = self.get_dataset_score(entry, dataset_key)
            params = entry.parameters if (entry.parameters is not None and entry.parameters > 0) else 1
            dimension = entry.dimension if (entry.dimension is not None and entry.dimension > 0) else 768
            max_tokens = entry.max_tokens if (entry.max_tokens is not None and entry.max_tokens > 0) else 512

            scatter_points.append({
                "id": entry.id,
                "model_name": entry.model_name,
                "organization": entry.organization,
                "model_type": entry.model_type.value,
                "embedding_type": entry.embedding_type.value,
                "parameters": params,
                "formatted_parameters": self.format_parameters(entry.parameters),
                "dimension": dimension,
                "max_tokens": max_tokens,
                "score": score.ndcg_at_10,
                "entry": entry
            })
        return scatter_points

benchmark_service = BenchmarkService()
