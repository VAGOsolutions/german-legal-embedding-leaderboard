"""Checks every result file in results/; runs on every pull request (.github/workflows/validate-results.yml).

Deliberately lightweight (pydantic + pytest only), so CI needs no torch/nicegui.
Rules (CONTRIBUTING.md):
  - one file per model: results/<organisation>__<model>.json, valid JSON, schema data/schema.py:BenchmarkEntry
  - file name matches the Hugging Face ID (model_url), unique IDs
  - known datasets only; nDCG@10 in (0, 1]; OpenLegalRetrieval-DE only with all seven subtasks (mean = main score)
  - submissions (source "submission"): public HF model with a 40-character revision, protocol of the current
    benchmark script version, sizes per task exactly as in the protocol, training data declaration present
"""
import json
import re
from pathlib import Path

import pytest

import config
from data.schema import BenchmarkEntry

RESULTS = Path(config.RESULTS_DIR)
FILES = sorted(p for p in RESULTS.glob("*.json") if not p.name.startswith("_"))
NAME = re.compile(r"^[A-Za-z0-9._-]+__[A-Za-z0-9._-]+\.json$")
# size per task in the fixed protocol (benchmark/run_benchmark.py); submissions must match exactly
SIZES = {"legalquad": (200, 200), "gerdalir_small": (12234, 9969), "gerlayqa": (2152, 2377), "gerlerb": (367, 89851)}
SIZES_OLR = {"t1": (1178, 111555), "t2": (555, 52543), "t3": (819, 111555), "t4": (310, 111555), "t5": (6373, 111555),
              "t6": (2151, 2377), "t7": (12234, 9969)}


def _load(p: Path) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_results_exist():
    assert FILES, "results/ is empty"


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_file_valid(path: Path):
    assert NAME.match(path.name), f"file name must be <organisation>__<model>.json: {path.name}"
    raw = _load(path)
    assert isinstance(raw, dict), "one file = one model (JSON object, not a list)"
    e = BenchmarkEntry(**raw)
    assert e.id and e.model_name and e.organization
    assert e.source in config.RESULT_SOURCES
    allowed = {k for k in config.DATASETS_INFO if k != "overall"}
    assert e.metrics and set(e.metrics) <= allowed, f"unknown datasets: {set(e.metrics) - allowed}"
    assert all(0 < m.ndcg_at_10 <= 1 for m in e.metrics.values())
    assert set(e.contamination) <= allowed, f"unknown datasets in contamination: {e.contamination}"
    if config.OLR_KEY in e.metrics:
        m = e.metrics[config.OLR_KEY]
        assert m.subtasks and set(m.subtasks) == set(config.OLR_TASKS), "OpenLegalRetrieval-DE needs t1–t7"
        assert abs(sum(m.subtasks.values()) / 7 - m.ndcg_at_10) < 6e-4, "main score = mean of the seven subtasks"
    # file name matches the HF ID
    url = e.model_url or ""
    if url.startswith("https://huggingface.co/"):
        org, name = url.removeprefix("https://huggingface.co/").split("/")[:2]
        assert path.name == f"{org}__{name}.json", f"file name does not match {url}"


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_submission_complete(path: Path):
    e = BenchmarkEntry(**_load(path))
    if e.source != "submission":
        pytest.skip("not a submission")
    assert (e.model_url or "").startswith("https://huggingface.co/"), "a submission needs a public Hugging Face model"
    assert e.model_revision and re.fullmatch(r"[0-9a-f]{40}", e.model_revision), "model_revision = 40-character commit"
    assert e.protocol is not None, "protocol missing (written by benchmark/run_benchmark.py)"
    assert e.protocol.script == "benchmark/run_benchmark.py", "only measurements with the benchmark script"
    assert e.protocol.version == config.PROTOCOL_VERSION, f"protocol version {e.protocol.version} != {config.PROTOCOL_VERSION}"
    assert "contamination_declared" in e.protocol.settings, "training data declaration missing (--trained-on)"
    for ds, (nq, nd) in SIZES.items():
        if ds in e.metrics:
            run = e.protocol.tasks.get(ds)
            assert run and (run.n_queries, run.n_docs) == (nq, nd), f"{ds}: size differs from the protocol ({run})"
    if config.OLR_KEY in e.metrics:
        for tk, (nq, nd) in SIZES_OLR.items():
            run = e.protocol.tasks.get(f"{config.OLR_KEY}.{tk}")
            assert run and (run.n_queries, run.n_docs) == (nq, nd), f"OLR {tk}: size differs"


def test_ids_and_file_names_unique():
    ids = [_load(p)["id"] for p in FILES]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"duplicate IDs: {duplicates}"
    lower = [p.name.lower() for p in FILES]
    assert len(set(lower)) == len(lower), "file names must not differ only in case"


def test_example_file_valid_but_not_in_results():
    example = Path(config.BENCHMARK_DIR) / "example_result.json"
    assert example.exists()
    e = BenchmarkEntry(**_load(example))
    assert e.source == "submission" and e.protocol and e.protocol.script == "benchmark/run_benchmark.py"
    assert not (RESULTS / example.name).exists()
