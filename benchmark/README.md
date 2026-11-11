# Benchmark script (protocol 1.0)

`run_benchmark.py` evaluates an embedding model on all leaderboard benchmarks with the fixed protocol and writes the
result file `results/<organisation>__<model>.json` for your pull request (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

## Installation

```bash
pip install -r benchmark/requirements.txt     # torch, sentence-transformers 6.2.0, transformers 5.22.1, datasets
```
A GPU is recommended for GerLeRB (89,851 documents) and GerDaLIR Small (12,234 queries); on CPU it takes hours.

## Usage

```bash
# dense model, prompts from the Sentence Transformers config
python benchmark/run_benchmark.py --model <org>/<model> --revision <commit> \
    --model-type open --embedding-type dense --license apache-2.0 --trained-on none --out results/

# prompts as in the model card
python benchmark/run_benchmark.py --model intfloat/multilingual-e5-small --prompt-format e5 ...
python benchmark/run_benchmark.py --model Qwen/Qwen3-Embedding-0.6B --prompt-format qwen3inst ...
python benchmark/run_benchmark.py --model <org>/<model> --query-prompt "Query: " --doc-prompt "Document: " ...

# multi-vector models (ColBERT) via sentence-transformers 6 (MultiVectorEncoder)
python benchmark/run_benchmark.py --model <org>/<colbert> --type multivector --trust-remote-code \
    --model-type open --embedding-type late-interaction --trained-on none --out results/
```

| Option | Meaning |
|---|---|
| `--prompt-format` | `st` (default: prompts from the ST config), `none`, `e5` (`query: `/`passage: `), `e5inst`, `qwen3inst`, `gemma2inst` (instruct formats with a German task instruction per benchmark) |
| `--query-prompt`, `--doc-prompt` | custom prompts; `{instr}` is replaced by the task instruction |
| `--max-length` | maximum document length (protocol: 8192; the model maximum applies if smaller) |
| `--device`, `--dtype` | `cuda`, otherwise `cpu` (`mps` possible). Protocol dtype is `bf16`; `fp32` deviates by up to ~0.005 for small models and is for debugging only. |
| `--tasks` | subset, e.g. `legalquad,gerlayqa` (submissions need all) |
| `--trained-on` | mandatory: keys of benchmarks whose data was used in training, or `none` |
| `--license` | licence of the weights as an SPDX identifier |

## Protocol 1.0

| Benchmark | Source (fixed) | Queries | Documents |
|---|---|---:|---:|
| `legalquad` | HF `mteb/LegalQuAD` @ `37aa6cfb…` | 200 | 200 |
| `gerdalir_small` | HF `mteb/GerDaLIRSmall` @ `48327de6…` | 12,234 | 9,969 |
| `gerlayqa` | GitHub `trusthlt/eacl24-german-legal-questions` @ `cbc46594…` (`bgb_eval.json` against `bgb.json`, MD5-checked) | 2,152 | 2,377 |
| `gerlerb` | Zenodo 15745124 (`topics.txt`, `qrels.txt`, `corpus.trec.gz`, MD5-checked) | 367 | 89,851 |
| `openlegalretrieval_de` | HF `VAGOsolutions/openlegalretrieval-de`, 7 tasks (t1–t7) | per task | per task |

- All queries with at least one relevant document, full corpus, exact search (no ANN).
- Dense: normalised embeddings, cosine. Multi-vector: MaxSim as in the ST6 IR evaluator; public benchmarks use the query
  mode of the repo config and documents up to 8,192 tokens; OpenLegalRetrieval-DE uses fixed query/document lengths per task.
- Top 100 per query, nDCG@10 with graded relevance and linear gain (as in pytrec_eval/BEIR/MTEB).
- If a task's size deviates, the script aborts (`--no-check` is for debugging only; such results are not accepted).

## OpenLegalRetrieval-DE

Licence ODbL 1.0; contains information from Open Legal Data (openlegaldata.io), made available under the ODbL 1.0.
The script loads it from Hugging Face (`--olr-dataset`, `--olr-revision`) or from a local copy (`--olr-dir`). If the
dataset cannot be loaded, the benchmark is skipped and VAGO Solutions measures it for submitted models.

## Output

One JSON file in the `data/schema.py:BenchmarkEntry` schema with `source: "submission"`, `model_revision` and `protocol`
(script, version, date, settings, size per task). Submit it unchanged.
Example: [example_result.json](example_result.json), output for multilingual-e5-small (GerLayQA only, bf16 on CPU;
a submission contains all benchmarks).
