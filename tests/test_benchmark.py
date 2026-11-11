# pyrefly: ignore [missing-import]
import pytest
import json
from pathlib import Path
import config
from data.schema import BenchmarkEntry, CustomNanoBEIRDataset
from services.benchmark_service import benchmark_service
from services.custom_eval_service import custom_eval_service

def test_leaderboard_from_results():
    """The leaderboard loads every file in results/ (one per model)."""
    files = benchmark_service.result_files()
    entries = benchmark_service.load_entries(force_reload=True)
    assert len(files) > 0 and len(entries) == len(files)
    assert "openlegalretrieval_de" in config.DATASETS_INFO
    assert "gerdalir" not in config.DATASETS_INFO  # full GerDaLIR is not ranked
    for entry in entries:
        assert entry.notes, entry.id


def test_no_email_submission():
    """Submissions via GitHub pull request only, no email/SMTP path."""
    assert not (config.BASE_DIR / "services" / "email_service.py").exists()
    assert not hasattr(config, "SMTP_HOST") and not hasattr(config, "SUBMISSION_RECEIVER_EMAIL")
    for p in list((config.BASE_DIR / "components").glob("*.py")) + [config.BASE_DIR / "main.py"]:
        src = p.read_text(encoding="utf-8").lower()
        assert "smtp" not in src and "email_service" not in src, p.name
    assert (config.BASE_DIR / "CONTRIBUTING.md").exists()
    assert (config.BENCHMARK_DIR / "run_benchmark.py").exists()

def test_ranking_and_medals():
    """The top 3 get medals 🥇🥈🥉."""
    ranked = benchmark_service.get_ranked_entries(dataset_key="overall")
    assert len(ranked) >= 3
    assert ranked[0]["medal"] == "🥇"
    assert ranked[0]["rank"] == 1
    assert ranked[1]["medal"] == "🥈"
    assert ranked[1]["rank"] == 2
    assert ranked[2]["medal"] == "🥉"
    assert ranked[2]["rank"] == 3
    assert ranked[3]["medal"] is None
    assert ranked[3]["rank"] == 4

    for i in range(len(ranked) - 1):
        assert ranked[i]["ndcg_at_10"] >= ranked[i+1]["ndcg_at_10"]

def test_dataset_switching():
    """Every dataset view returns a ranking."""
    for dataset_key in config.DATASETS_INFO.keys():
        ranked = benchmark_service.get_ranked_entries(dataset_key=dataset_key)
        assert len(ranked) > 0
        assert ranked[0]["rank"] == 1
        assert ranked[0]["ndcg_at_10"] > 0

def test_filtering_and_search():
    """Search and model/embedding type filters."""
    search_res = benchmark_service.get_ranked_entries(search_query="bge-m3")
    assert len(search_res) >= 1
    assert any("bge-m3" in r["id"] for r in search_res)

    open_weights = benchmark_service.get_ranked_entries(model_type_filter="open")
    assert open_weights and all(r["model_type"] == "open" for r in open_weights)

    hybrid_models = benchmark_service.get_ranked_entries(embedding_type_filter="Hybrid")
    assert all(r["embedding_type"] == "Hybrid" for r in hybrid_models)

    moe_models = benchmark_service.get_ranked_entries(embedding_type_filter="MoE")
    assert len(moe_models) >= 1
    assert all(r["embedding_type"] == "MoE" for r in moe_models)

def test_parameters_and_formatting():
    """Parameter counts are present (unknown only for proprietary APIs) and formatted correctly."""
    entries = benchmark_service.load_entries()
    for entry in entries:
        if entry.parameters is None:
            assert entry.model_type.value == "proprietary", entry.id
        else:
            assert entry.parameters >= 1

    assert benchmark_service.format_parameters(1) == "1 (BM25)"
    assert benchmark_service.format_parameters(567_000_000) == "567M"
    assert benchmark_service.format_parameters(7_110_000_000) == "7.11B"
    assert benchmark_service.format_parameters(1_000_000_000) == "1B"
    assert benchmark_service.format_parameters(None) == "–"

def test_scatter_plot_data():
    """Data points for the size scatter plot."""
    scatter_data = benchmark_service.get_scatter_plot_data(dataset_key="overall")
    expected = [e for e in benchmark_service.load_entries() if benchmark_service.has_dataset(e, "overall") and e.parameters]
    assert len(scatter_data) == len(expected) > 0
    for pt in scatter_data:
        assert "id" in pt
        assert "model_name" in pt
        assert "parameters" in pt
        assert "score" in pt
        assert "dimension" in pt
        assert "max_tokens" in pt
        assert pt["parameters"] >= 1
        assert pt["score"] > 0
        assert pt["dimension"] >= 0
        assert pt["max_tokens"] >= 512

def test_custom_nanobeir_validation_and_max_50_docs():
    """NanoBEIR validation and the 50-document limit."""
    sample_nanobeir_file = config.DATA_DIR / "sample_nanobeir_dataset.json"
    assert sample_nanobeir_file.exists()

    raw_json = sample_nanobeir_file.read_text(encoding="utf-8")
    valid, msg, dataset = custom_eval_service.parse_and_validate_dataset(raw_json)
    assert valid is True, msg
    assert dataset is not None
    assert len(dataset.corpus) <= 50

    # BM25 evaluation
    eval_res = custom_eval_service.evaluate_dataset_sync(
        dataset=dataset,
        model_name="BM25-Baseline",
        encoder_mode="bm25",
    )
    assert "ndcg_at_10" in eval_res
    assert 0.0 < eval_res["ndcg_at_10"] <= 1.0
    assert eval_res["num_corpus"] == len(dataset.corpus)
    assert len(eval_res["query_details"]) == len(dataset.queries)

    # more than 50 documents are rejected
    too_large_data = {
        "name": "Too Large Corpus",
        "corpus": [{"_id": f"d{i}", "title": f"Doc {i}", "text": f"Inhalt {i}"} for i in range(51)],
        "queries": [{"_id": "q1", "text": "Inhalt 1"}],
        "qrels": [{"query-id": "q1", "corpus-id": "d1", "score": 1}],
    }
    valid_large, msg_large, ds_large = custom_eval_service.parse_and_validate_dataset(json.dumps(too_large_data))
    assert valid_large is False
    assert ds_large is None
    assert "50" in msg_large


def test_overall_requires_all_datasets():
    """Missing scores never count as 0: Overall lists only models with all datasets, dataset views only measured ones."""
    keys = [k for k in config.DATASETS_INFO if k != "overall"]
    entries = {e.id: e for e in benchmark_service.load_entries()}
    for r in benchmark_service.get_ranked_entries(dataset_key="overall"):
        assert all(k in entries[r["id"]].metrics for k in keys)
    for k in keys:
        for r in benchmark_service.get_ranked_entries(dataset_key=k):
            assert k in entries[r["id"]].metrics


def test_live_eval_only_allowed_models():
    """Security: arbitrary HF repos (remote code) must not be loaded on the public Space."""
    ds = CustomNanoBEIRDataset(
        name="t",
        corpus=[{"_id": "d1", "text": "Der Vermieter darf die Miete erhöhen."}],
        queries=[{"_id": "q1", "text": "Mieterhöhung"}],
        qrels=[{"query-id": "q1", "corpus-id": "d1", "score": 1}],
    )
    with pytest.raises(ValueError):
        custom_eval_service.evaluate_dataset_sync(ds, model_name="someone/unknown-model-with-remote-code")


def test_allow_list_pinned_without_foreign_remote_code():
    for mid, spec in config.ALLOWED_EVAL_MODELS.items():
        if spec["mode"] != "bm25":
            assert spec["revision"] and len(spec["revision"]) == 40, mid
        if spec["trust_remote_code"]:
            assert mid.startswith("VAGOsolutions/"), mid


def test_no_package_installation_at_runtime():
    src = (config.BASE_DIR / "services" / "custom_eval_service.py").read_text(encoding="utf-8")
    assert "subprocess" not in src
    assert '"pip"' not in src


def test_olr_subtasks_and_main_score():
    """OpenLegalRetrieval-DE: main score = macro mean of the seven subtasks (rounded)."""
    n = 0
    for e in benchmark_service.load_entries():
        m = e.metrics.get(config.OLR_KEY)
        if m is None:
            continue
        assert m.subtasks and set(m.subtasks) == set(config.OLR_TASKS), e.id
        assert abs(sum(m.subtasks.values()) / 7 - m.ndcg_at_10) < 6e-4, e.id
        n += 1
    assert n >= 25


def test_overall_is_mean_of_five():
    keys = [k for k in config.DATASETS_INFO if k != "overall"]
    assert len(keys) == 5
    for r in benchmark_service.get_ranked_entries(dataset_key="overall"):
        vals = [r["all_metrics"][k] for k in keys]
        assert abs(sum(vals) / 5 - r["ndcg_at_10"]) < 1e-4, r["id"]


def test_api_model_names_no_other_model():
    entries = benchmark_service.load_entries()
    api = [e for e in entries if e.id == "sauerkrautlm-legal-api"]
    assert len(api) == 1
    e = api[0]
    assert e.model_type.value == "proprietary" and e.license == "commercial-api"
    text = " ".join([e.model_name, e.notes or "", e.protocol.script if e.protocol else ""]).lower()
    for other in entries:
        if other.organization != "VAGO Solutions":
            assert other.organization.lower() not in text, other.organization
    assert all(k in e.metrics for k in config.DATASETS_INFO if k != "overall")


def test_size_filter():
    everything = benchmark_service.get_ranked_entries(dataset_key="overall")
    small = benchmark_service.get_ranked_entries(dataset_key="overall", size_log_range=(6.0, 8.0))
    assert 0 < len(small) < len(everything)
    assert all(r["parameters"] and 1 < r["parameters"] <= 1e8 for r in small)
    large = benchmark_service.get_ranked_entries(dataset_key="overall", size_log_range=(9.5, 10.0))
    assert all(r["parameters"] >= 10 ** 9.5 for r in large)
    # unsized entries (APIs from MTEB, BM25) only with the full range and the switch on
    full = benchmark_service.get_ranked_entries(dataset_key="legalquad")
    assert any(r["parameters"] is None for r in full)
    assert not any(r["parameters"] is None for r in benchmark_service.get_ranked_entries(dataset_key="legalquad", include_unsized=False))
    assert not any(r["parameters"] is None or r["parameters"] <= 1
                   for r in benchmark_service.get_ranked_entries(dataset_key="legalquad", size_log_range=(6.0, 9.0)))


def test_task_matrix_complete():
    rows = benchmark_service.get_task_matrix()
    assert len(rows) == len(benchmark_service.load_entries())
    columns = benchmark_service.task_columns()
    assert columns[:1] == ["overall"] and columns[-7:] == list(config.OLR_TASKS)
    for r in rows:
        assert set(r["values"]) == set(columns)


def test_validation_errors_readable_and_translated():
    """Schema errors of custom datasets: short (no raw Pydantic dump) and in the UI language."""
    raw = json.loads((config.DATA_DIR / "sample_nanobeir_dataset.json").read_text(encoding="utf-8"))
    raw["qrels"] = [{"query-id": "does-not-exist", "corpus-id": "does-not-exist", "score": 1}]
    for lang, expected in (("de", "Keine gültigen Qrels"), ("en", "No valid qrels")):
        ok, msg, ds = custom_eval_service.parse_and_validate_dataset(json.dumps(raw), lang)
        assert not ok and ds is None
        assert expected in msg
        assert "input_value" not in msg and "errors.pydantic.dev" not in msg
