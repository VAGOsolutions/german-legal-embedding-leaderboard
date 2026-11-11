# Submitting results

New models are added via pull request only. Each model is one file `results/<organisation>__<model>.json`;
it appears on the leaderboard once the pull request is merged.

## Steps

1. Fork the repository and clone it.
2. Run the benchmark script (details: [benchmark/README.md](benchmark/README.md)):
   ```bash
   pip install -r benchmark/requirements.txt
   python benchmark/run_benchmark.py \
       --model <org>/<model> --revision <commit> \
       --prompt-format st \
       --model-type open --embedding-type dense \
       --license apache-2.0 --trained-on none \
       --out results/
   ```
   Set prompts as required by the model card: `--prompt-format` (`st`, `e5`, `e5inst`, `qwen3inst`, `gemma2inst`)
   or `--query-prompt`/`--doc-prompt`.
3. Commit only the generated file, unchanged.
4. Open a pull request. The `validate-results` check validates the file (`tests/test_results.py`). For pull requests
   from forks it also checks that only files with `"source": "submission"` are added or changed and that nothing is
   deleted (`tests/check_pr_sources.py`).

## Review criteria

- **Script and protocol:** `protocol.script` = `benchmark/run_benchmark.py`, `protocol.version` = `1.0`.
  Measurements with other tools or modified loaders are not accepted.
- **Model:** public on Hugging Face; `model_revision` is a 40-character commit, and the scores must be reproducible with it.
- **Scope:** query/document counts per benchmark exactly as in the protocol (LegalQuAD 200/200, GerDaLIR Small 12,234/9,969,
  GerLayQA 2,152/2,377, GerLeRB 367/89,851).
- **Prompts and precision:** prompts as required by the model card; `bf16` (protocol default). Both are recorded under `settings`.
- **Plausibility:** spot checks are re-measured; deviations above 0.005 nDCG@10 are discussed in the pull request.
- **Training data:** `--trained-on` is mandatory. List the keys of benchmarks whose training data was used (e.g. `gerdalir_small`);
  the entry is then marked with ⚠. Models trained on test data are not accepted.
- **Metadata:** model type, embedding type, licence (SPDX identifier), parameter count.

## OpenLegalRetrieval-DE

The script loads OpenLegalRetrieval-DE (key `openlegalretrieval_de`, licence ODbL 1.0) from Hugging Face. If the dataset
cannot be loaded, the benchmark is skipped and VAGO Solutions measures the score for the submitted model. Overall is shown
once all five scores are available.

## Other notes

- API models without public weights cannot be submitted (no verifiable revision).
- Corrections to existing entries: open a separate pull request with a reason and a new measurement.
