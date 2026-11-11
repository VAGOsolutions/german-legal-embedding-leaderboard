---
title: German Legal Embedding Benchmark Leaderboard
emoji: ⚖️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8080
pinned: false
---
# German Legal Embedding Benchmark Leaderboard

Leaderboard for embedding models on German legal retrieval benchmarks, ranked by nDCG@10.

## Benchmarks

- **LegalQuAD**: legal question → answer passage ([mteb/LegalQuAD](https://huggingface.co/datasets/mteb/LegalQuAD))
- **GerDaLIR Small**: court decision passage → cited decisions ([mteb/GerDaLIRSmall](https://huggingface.co/datasets/mteb/GerDaLIRSmall))
- **GerLayQA**: lay question → BGB sections ([trusthlt/eacl24-german-legal-questions](https://github.com/trusthlt/eacl24-german-legal-questions))
- **GerLeRB**: legal question → federal statute sections ([Zenodo 15745124](https://zenodo.org/records/15745124))
- **OpenLegalRetrieval-DE**: seven legal retrieval tasks (t1–t7) by VAGO Solutions

**Overall** is the mean of the five benchmarks and is only shown for models with all five scores.
The evaluation protocol is described in [benchmark/README.md](benchmark/README.md).

## Run locally

```bash
pip install -r requirements.txt
python main.py              # http://localhost:8080
```

With Docker: `docker compose up -d --build`. Tests: `pytest -q`.

## Submit a model

Run `benchmark/run_benchmark.py` and open a pull request with the generated result file. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licences

- **OpenLegalRetrieval-DE**: [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Contains information from Open Legal Data (openlegaldata.io), made available under the ODbL 1.0.
- **SauerkrautLM-MoEdernColBERT Legal models** (1.5M, 27M, 115M): CC BY-NC 4.0.
- **SauerkrautLM Legal API**: commercial, available via API only.
- All other benchmarks and models are subject to their own licences.
