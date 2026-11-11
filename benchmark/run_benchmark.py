#!/usr/bin/env python3
"""German Legal Embedding Benchmark – evaluation script (protocol 1.0).

Evaluates an embedding model on the leaderboard benchmarks with the fixed protocol and writes the result file
results/<organisation>__<model>.json for a pull request (see CONTRIBUTING.md).

Benchmarks (data is loaded at a fixed revision or checksum):
  legalquad       mteb/LegalQuAD (rev. 37aa6cf…), 200 queries / 200 documents
  gerdalir_small  mteb/GerDaLIRSmall (rev. 48327de…), 12,234 queries / 9,969 documents
  gerlayqa        GerLayQA test (trusthlt/eacl24-german-legal-questions @ cbc4659…, bgb_eval.json against bgb.json), 2,152 / 2,377
  gerlerb         GerLeRB (Zenodo 15745124, CC-BY-4.0), 367 / 89,851
  openlegalretrieval_de  OpenLegalRetrieval-DE (ODbL 1.0), 7 tasks t1–t7, macro mean; loaded from Hugging Face
                  (--olr-dataset, or a local copy via --olr-dir). If it cannot be loaded, it is skipped.

Protocol: all queries, full corpora, documents up to 8,192 tokens (or the model maximum), prompts/instructions as in the
model card, exact search (dense: cosine on normalised embeddings; multi-vector: MaxSim), top 100, nDCG@10 with graded
relevance and linear gain (as in pytrec_eval/BEIR/MTEB). The loaders are identical to those of the reference measurements.

Examples:
  python benchmark/run_benchmark.py --model intfloat/multilingual-e5-small --prompt-format e5 \\
      --model-type open --embedding-type dense --trained-on none --out results/
  python benchmark/run_benchmark.py --model <org>/<colbert-model> --type multivector --trust-remote-code \\
      --model-type open --embedding-type late-interaction --trained-on none --out results/
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

PROTOCOL_VERSION = "1.0"
SCRIPT = "benchmark/run_benchmark.py"
OLR = "openlegalretrieval_de"
PUBLIC = ("legalquad", "gerdalir_small", "gerlayqa", "gerlerb")
ALL_TASKS = PUBLIC + (OLR,)

MTEB = {"legalquad": ("mteb/LegalQuAD", "37aa6cfb01d48960b0f8e3f17d6e3d99bf1ebc3e"),
        "gerdalir_small": ("mteb/GerDaLIRSmall", "48327de6ee192e9610f3069789719788957c7abd")}
GLQ_REPO = "https://raw.githubusercontent.com/trusthlt/eacl24-german-legal-questions/cbc465942f0c1eab25ec8864bc358466e4d88e0e/data"
GLQ_MD5 = {"bgb.json": "d619608e9451b2cff95c3805fb57b4ac", "bgb_eval.json": "8d4d4c9509c84f4f546c86489c2012ce",
           "bgb_dev.json": "25295db4c45c5ead1b9036d4923aa490"}
LERB_URL = "https://zenodo.org/api/records/15745124/files/{f}/content"
LERB_MD5 = {"topics.txt": "a9b7d2201367691ea4c3e66bd8144844", "qrels.txt": "646e02380336544a5baaa8cdcefac97b",
            "corpus.trec.gz": "5a0cabd33eb10ad9eff18344872304ed"}
OLR_DEFAULT = "VAGOsolutions/openlegalretrieval-de"
OLR_TD = {"t1": "t1_statute", "t2": "t2_case", "t3": "t3_citation", "t4": "t4_argument", "t5": "t5_merkmal_v2"}
# query/document length per OLR task (multi-vector models with their own length control only, as in the model cards)
OLR_LENGTHS = {"t1": (128, 2048), "t2": (2048, 2048), "t3": (2048, 2048), "t4": (256, 2048), "t5": (128, 2048),
               "t6": (512, 2048), "t7": (512, 4096)}
EXPECTED_SIZE = {"legalquad": (200, 200), "gerdalir_small": (12234, 9969), "gerlayqa": (2152, 2377), "gerlerb": (367, 89851),
          "t1": (1178, 111555), "t2": (555, 52543), "t3": (819, 111555), "t4": (310, 111555), "t5": (6373, 111555),
          "t6": (2151, 2377), "t7": (12234, 9969)}

# German task instructions (instruct formats only; part of the protocol, identical to the reference measurements)
INSTR = {
    "t1": "Gegeben eine natürlichsprachige juristische Frage, finde die einschlägige deutsche Rechtsnorm.",
    "t2": "Gegeben den Sachverhalt bzw. die Begründung einer Gerichtsentscheidung, finde die darin zitierten Präzedenzentscheidungen.",
    "t3": "Gegeben eine Gerichtsentscheidung, finde die darin angewandte deutsche Rechtsnorm.",
    "t4": "Gegeben ein juristisches Argument aus einer Entscheidung, finde die zugrundeliegende Rechtsgrundlage.",
    "t5": "Gegeben ein Tatbestandsmerkmal, finde die Rechtsnorm, die es regelt.",
    "t6": "Gegeben eine alltagssprachliche juristische Frage eines Laien, finde den einschlägigen BGB-Paragraphen.",
    "t7": "Gegeben die Beschreibung eines Rechtsfalls, finde relevante frühere Gerichtsentscheidungen.",
    "legalquad": "Gegeben eine juristische Frage, finde die Textstelle, die sie beantwortet.",
    "gerlerb": "Gegeben eine juristische Frage, finde die einschlägige deutsche Rechtsnorm.",
}
INSTR["gerlayqa"] = INSTR["t6"]
INSTR["gerdalir_small"] = INSTR["t7"]
# prompt formats as in the model cards; {instr} = task instruction
PROMPT_FORMATS = {
    "st": (None, None),                                   # prompts from the model's Sentence Transformers config
    "none": ("", ""),
    "e5": ("query: ", "passage: "),                       # multilingual-e5-small/-base
    "e5inst": ("Instruct: {instr}\nQuery: ", ""),          # multilingual-e5-large-instruct
    "qwen3inst": ("Instruct: {instr}\nQuery:", ""),        # Qwen3-Embedding
    "gemma2inst": ("<instruct>{instr}\n<query>", ""),      # bge-multilingual-gemma2
}


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- data
def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _fetch(url: str, target: Path, md5: str) -> Path:
    if not (target.exists() and _md5(target) == md5):
        target.parent.mkdir(parents=True, exist_ok=True)
        log(f"  downloading {url}")
        urllib.request.urlretrieve(url, target)
    got = _md5(target)
    if got != md5:
        raise SystemExit(f"checksum mismatch for {target.name}: {got} != {md5}")
    return target


def _rels_filter(queries, rels):
    return {k: v for k, v in queries.items() if k in rels}


def load_mteb(key):
    from datasets import load_dataset
    path, rev = MTEB[key]
    c = load_dataset(path, "corpus", revision=rev)["corpus"]
    q = load_dataset(path, "queries", revision=rev)["queries"]
    qr = load_dataset(path, "default", revision=rev)["test"]
    rels = {}
    for qi, ci, s in zip(qr["query-id"], qr["corpus-id"], qr["score"]):
        if int(s) > 0:
            rels.setdefault(str(qi), {})[str(ci)] = int(s)
    titles = c["title"] if "title" in c.column_names else [""] * len(c)
    corpus = {str(i): (f"{ti} {tx}".strip() if ti else (tx or "")) for i, ti, tx in zip(c["_id"], titles, c["text"])}
    queries = {str(i): t for i, t in zip(q["_id"], q["text"])}
    return _rels_filter(queries, rels), corpus, rels


def _bgb(data_dir: Path):
    nid = lambda s: s.strip().replace(" ", "")
    bgb = json.load(open(_fetch(f"{GLQ_REPO}/bgb.json", data_dir / "gerlayqa" / "bgb.json", GLQ_MD5["bgb.json"])))
    return nid, {nid(r["id"]): r["content"] for r in bgb}


def load_gerlayqa(data_dir: Path, filename="bgb_eval.json", prefix="glqtest"):
    nid, corpus = _bgb(data_dir)
    items = json.load(open(_fetch(f"{GLQ_REPO}/{filename}", data_dir / "gerlayqa" / filename, GLQ_MD5[filename])))
    queries, rels = {}, {}
    for i, it in enumerate(items):
        golds = [nid(g) for g in (it.get("Paragraphs") or []) if nid(g) in corpus]
        if golds:
            queries[f"{prefix}{i}"] = it["Question_text"].strip()
            rels[f"{prefix}{i}"] = {g: 1 for g in golds}
    return queries, corpus, rels


def load_gerlerb(data_dir: Path):
    d = data_dir / "gerlerb"
    p = {f: _fetch(LERB_URL.format(f=f), d / f, m) for f, m in LERB_MD5.items()}
    queries = dict(l.rstrip("\n").split("\t", 1) for l in open(p["topics.txt"], encoding="utf-8").readlines()[1:])
    rels = {}
    for l in open(p["qrels.txt"], encoding="utf-8").readlines()[1:]:
        qi, _, ci, s = l.split()
        if int(s) > 0:
            rels.setdefault(qi, {})[ci] = int(s)
    txt = gzip.open(p["corpus.trec.gz"], "rt", encoding="utf-8").read()
    corpus = dict(re.findall(r"<DOCNO>(.*?)</DOCNO>\s*<TEXT>(.*?)</TEXT>", txt, re.S))
    return _rels_filter(queries, rels), corpus, rels


def olr_source(a) -> tuple[Path | None, str]:
    """Folder with t1_statute/ … t5_merkmal_v2/, or (None, reason)."""
    if a.olr_dir:
        d = Path(a.olr_dir)
        return (d, f"local:{d}") if all((d / v / "corpus.jsonl").exists() for v in OLR_TD.values()) else (None, f"{d} incomplete")
    try:
        from huggingface_hub import snapshot_download
        pat = [f"{v}/{f}" for v in OLR_TD.values() for f in ("corpus.jsonl", "queries.clean.jsonl", "qrels.clean.txt")]
        d = snapshot_download(a.olr_dataset, repo_type="dataset", revision=a.olr_revision, allow_patterns=pat,
                              token=os.environ.get("HF_TOKEN") or None, cache_dir=str(Path(a.data_dir) / "hf"))
        return Path(d), f"hf:{a.olr_dataset}@{a.olr_revision or 'main'}"
    except Exception as e:  # no access or offline
        return None, f"cannot load {a.olr_dataset} ({type(e).__name__})"


def _doc_text(r: dict) -> str:
    h = " ".join(str(r.get(k) or "") for k in ("book_code", "section", "title")).strip()
    body = r.get("text") or ""
    return (h + "\n" + body).strip() if h else body


def load_olr_task(tk: str, olr_dir: Path, data_dir: Path):
    if tk in OLR_TD:
        d = olr_dir / OLR_TD[tk]
        queries = {}
        for line in open(d / "queries.clean.jsonl", encoding="utf-8"):
            r = json.loads(line); queries[r["id"]] = r["text"]
        corpus = {}
        for line in open(d / "corpus.jsonl", encoding="utf-8"):
            r = json.loads(line); corpus[r["id"]] = _doc_text(r)
        rels = {}
        for line in open(d / "qrels.clean.txt", encoding="utf-8"):
            p = line.split()
            if len(p) >= 4 and p[3] != "0":
                rels.setdefault(p[0], {})[p[2]] = int(p[3])
        rels = {q: {x: g for x, g in ds.items() if x in corpus} for q, ds in rels.items()}
        rels = {q: ds for q, ds in rels.items() if ds and q in queries}
        return {q: queries[q] for q in rels}, corpus, rels
    if tk == "t6":                                   # GerLayQA dev questions against all BGB sections
        return load_gerlayqa(data_dir, "bgb_dev.json", "glqdev")
    if tk == "t7":                                   # GerDaLIR Small (empty titles -> same loader as legalquad)
        return load_mteb("gerdalir_small")
    raise KeyError(tk)


# ---------------------------------------------------------------- scoring
def ndcg_at(ranking, rq, k=10):
    dcg = sum(rq.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranking[:k]))
    ideal = sorted(rq.values(), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def ndcg10(run, rels, qids):
    return sum(ndcg_at([d for d, _ in sorted(run[q].items(), key=lambda x: -x[1])], rels[q], 10) for q in qids) / len(qids)


# ---------------------------------------------------------------- models
class Dense:
    def __init__(self, a, torch):
        from sentence_transformers import SentenceTransformer
        self.torch = torch
        kw = {"dtype": {"fp32": torch.float32, "bf16": torch.bfloat16, "fp16": torch.float16}[a.dtype]}
        self.m = SentenceTransformer(a.model, revision=a.revision, device=a.device, trust_remote_code=a.trust_remote_code, model_kwargs=kw)
        self.m.max_seq_length = min(a.max_length, self.m.max_seq_length or a.max_length)
        self.prompts = dict(getattr(self.m, "prompts", {}) or {})
        self.a = a

    def q_prompt(self, task):
        q, _ = PROMPT_FORMATS[self.a.prompt_format]
        if self.a.query_prompt is not None:
            q = self.a.query_prompt
        if q is None:
            q = self.prompts.get("query", "")
        return q.format(instr=INSTR.get(task, ""))

    def d_prompt(self, task):
        _, d = PROMPT_FORMATS[self.a.prompt_format]
        if self.a.doc_prompt is not None:
            d = self.a.doc_prompt
        if d is None:
            d = self.prompts.get("document") or self.prompts.get("passage", "")
        return d.format(instr=INSTR.get(task, ""))

    def _enc(self, texts, prompt):
        import numpy as np
        E = self.m.encode(texts, prompt=prompt or None, batch_size=self.a.batch_size, normalize_embeddings=True,
                          convert_to_numpy=True, show_progress_bar=self.a.progress).astype(np.float32)
        return self.torch.from_numpy(E)

    def queries(self, texts, task, olr_task=None):
        return self._enc(texts, self.q_prompt(olr_task or task))

    def docs(self, texts, task, olr_task=None):
        return self._enc(texts, self.d_prompt(olr_task or task))

    def score(self, Q, D):
        return Q @ D.T

    def info(self):
        dim_fn = getattr(self.m, "get_embedding_dimension", None) or self.m.get_sentence_embedding_dimension
        return {"dimension": int(dim_fn() or 0) or None, "max_tokens": int(self.m.max_seq_length),
                "parameters": sum(p.numel() for p in self.m.parameters())}


class MultiVector:
    """ColBERT/MoEdernColBERT via sentence-transformers >= 6 (MultiVectorEncoder), MaxSim as in the ST6 IR evaluator."""
    def __init__(self, a, torch):
        from sentence_transformers.multi_vector_encoder import MultiVectorEncoder, maxsim
        self.torch, self.maxsim, self.a = torch, maxsim, a
        self.m = MultiVectorEncoder(a.model, revision=a.revision, device=a.device, trust_remote_code=a.trust_remote_code)
        self.m.eval()
        self.ql0, self.dl0 = self.m[0].query_length, self.m[0].document_length
        self.qe0 = dict(self.m[0].query_expansion or {})

    def _set_lengths(self, olr_task):
        if olr_task:                                   # OLR: fixed lengths per task, queries padded to the task length
            ql, dl = OLR_LENGTHS[olr_task]
            self.m[0].query_expansion = {"strategy": "fixed", "attend": self.qe0.get("attend", False), "length": ql}
        else:                                          # public benchmarks: query mode from the repo config, documents 8,192
            ql, dl = self.ql0, self.a.max_length
            self.m[0].query_expansion = dict(self.qe0)
        self.m[0].query_length, self.m[0].document_length = ql, dl

    def _ac(self):
        """As in the model cards: fp32 weights with bf16 autocast (--dtype fp32 disables it)."""
        import contextlib
        if self.a.dtype != "bf16":
            return contextlib.nullcontext()
        dev = "cuda" if str(self.a.device).startswith("cuda") else "cpu"
        return self.torch.autocast(dev, dtype=self.torch.bfloat16)

    def queries(self, texts, task, olr_task=None):
        self._set_lengths(olr_task)
        with self._ac():
            E = self.m.encode_query(texts, batch_size=self.a.batch_size, show_progress_bar=self.a.progress)
        return self.torch.nn.utils.rnn.pad_sequence([e.float().cpu() for e in E], batch_first=True)

    def docs(self, texts, task, olr_task=None):
        self._set_lengths(olr_task)
        with self._ac():
            E = self.m.encode_document(texts, batch_size=self.a.batch_size, show_progress_bar=self.a.progress)
        return [e.float().cpu() for e in E]

    def score(self, Q, D):
        return self.maxsim(Q, D)

    def info(self):
        dim = None
        try:
            dim = int(self.m.encode_document(["Test"])[0].shape[-1])
        except Exception:
            pass
        return {"dimension": dim, "max_tokens": int(self.a.max_length), "parameters": sum(p.numel() for p in self.m.parameters())}


def search(enc, task, queries, corpus, rels, olr_task=None, k=100, doc_block=2000):
    """Exact search over the full corpus, documents in blocks (memory), top k per query."""
    torch = enc.torch
    qids, dids = list(queries), list(corpus)
    Q = enc.queries([queries[q] for q in qids], task, olr_task)
    best_s = torch.full((len(qids), 0), float("-inf")); best_i = torch.zeros((len(qids), 0), dtype=torch.long)
    for s in range(0, len(dids), doc_block):
        D = enc.docs([corpus[d] for d in dids[s:s + doc_block]], task, olr_task)
        S = torch.cat([enc.score(Q[i:i + 256], D).float() for i in range(0, len(qids), 256)])
        cat_s = torch.cat([best_s, S], 1)
        cat_i = torch.cat([best_i, torch.arange(s, s + S.shape[1]).expand(len(qids), -1)], 1)
        top = cat_s.topk(min(k, cat_s.shape[1]), 1)
        best_s, best_i = top.values, torch.gather(cat_i, 1, top.indices)
        log(f"    {task}{'/' + olr_task if olr_task else ''}: {min(s + doc_block, len(dids))}/{len(dids)} documents")
    run = {q: {dids[int(i)]: float(v) for v, i in zip(best_s[j].tolist(), best_i[j].tolist())} for j, q in enumerate(qids)}
    return ndcg10(run, rels, qids), len(qids), len(dids)


# ---------------------------------------------------------------- result file
MODEL_TYPES = ("open", "proprietary")
EMB = {"dense": "Dense", "late-interaction": "Late-Interaction", "hybrid": "Hybrid", "moe": "MoE"}


def result_filename(org: str, name: str) -> str:
    clean = lambda x: "".join(c if c.isalnum() or c in "._-" else "-" for c in x).strip("-")
    return f"{clean(org)}__{clean(name)}.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_argument_group("model")
    g.add_argument("--model", required=True, help="Hugging Face ID (public) or local path")
    g.add_argument("--revision", default=None, help="model commit (default: latest; resolved and stored)")
    g.add_argument("--type", choices=["dense", "multivector"], default="dense")
    g.add_argument("--prompt-format", choices=list(PROMPT_FORMATS), default="st",
                   help="st = prompts from the ST config; e5/e5inst/qwen3inst/gemma2inst = formats as in the model card")
    g.add_argument("--query-prompt", default=None, help="custom query prompt (overrides the format; {instr} = task instruction)")
    g.add_argument("--doc-prompt", default=None, help="custom document prompt")
    g.add_argument("--trust-remote-code", action="store_true")
    r = ap.add_argument_group("compute")
    r.add_argument("--max-length", type=int, default=8192, help="max document length in tokens (protocol: 8192)")
    r.add_argument("--batch-size", type=int, default=16)
    r.add_argument("--device", default=None, help="cuda | mps | cpu (default: cuda if available, else cpu)")
    r.add_argument("--dtype", choices=["fp32", "bf16", "fp16"], default="bf16",
                   help="protocol: bf16 (as in the reference measurements; fp32 deviates by up to ~0.005 for small models)")
    r.add_argument("--threads", type=int, default=0, help="CPU threads (0 = torch default)")
    r.add_argument("--doc-block", type=int, default=2000, help="documents per block (memory)")
    r.add_argument("--progress", action="store_true")
    d = ap.add_argument_group("tasks and data")
    d.add_argument("--tasks", default=",".join(ALL_TASKS), help=f"comma-separated list of {', '.join(ALL_TASKS)}")
    d.add_argument("--data-dir", default=str(Path.home() / ".cache" / "german-legal-benchmark"))
    d.add_argument("--olr-dataset", default=OLR_DEFAULT, help="Hugging Face dataset of OpenLegalRetrieval-DE (token via HF_TOKEN)")
    d.add_argument("--olr-revision", default=None)
    d.add_argument("--olr-dir", default=None, help="local folder with t1_statute/ … t5_merkmal_v2/")
    m = ap.add_argument_group("result file metadata")
    m.add_argument("--model-name", default=None, help="display name (default: name from the HF ID)")
    m.add_argument("--organization", default=None, help="default: organisation from the HF ID")
    m.add_argument("--model-type", choices=MODEL_TYPES, required=True)
    m.add_argument("--embedding-type", choices=list(EMB), required=True)
    m.add_argument("--parameters", default=None, help="parameter count (e.g. 118M); default: counted")
    m.add_argument("--license", default=None, help="licence of the weights as an SPDX identifier (e.g. apache-2.0, mit, cc-by-nc-4.0)")
    m.add_argument("--trained-on", required=True,
                   help="benchmarks whose training/test data was used in training (comma-separated keys) or 'none'")
    m.add_argument("--notes", default=None)
    m.add_argument("--out", default="results/", help="folder (file name is generated) or .json path")
    m.add_argument("--no-check", action="store_true", help="disable the size check (debugging only; such results are not accepted)")
    a = ap.parse_args()

    import torch
    if a.threads:
        torch.set_num_threads(a.threads)
    a.device = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tasks = [t.strip() for t in a.tasks.split(",") if t.strip()]
    unknown = set(tasks) - set(ALL_TASKS)
    if unknown:
        raise SystemExit(f"unknown tasks: {unknown}")
    trained_on = [] if a.trained_on.strip().lower() == "none" else [x.strip() for x in a.trained_on.split(",") if x.strip()]
    if set(trained_on) - set(ALL_TASKS):
        raise SystemExit(f"--trained-on: unknown keys {set(trained_on) - set(ALL_TASKS)}")
    data_dir = Path(a.data_dir); data_dir.mkdir(parents=True, exist_ok=True)

    # public model? resolve the revision
    hf_id, private = None, None
    if not Path(a.model).exists():
        from huggingface_hub import HfApi
        info = HfApi().model_info(a.model, revision=a.revision)
        hf_id, private, a.revision = a.model, bool(getattr(info, "private", False)), info.sha
        log(f"[model] {hf_id} @ {a.revision} ({'PRIVATE' if private else 'public'})")

    t0 = time.time()
    enc = (MultiVector if a.type == "multivector" else Dense)(a, torch)
    minfo = enc.info()
    settings = {"type": a.type, "prompt_format": a.prompt_format, "query_prompt": a.query_prompt, "doc_prompt": a.doc_prompt,
                "max_length": a.max_length, "batch_size": a.batch_size, "dtype": a.dtype, "device": a.device,
                "torch": torch.__version__, "contamination_declared": True}
    if a.type == "dense":
        settings["query_prompt_resolved"] = {t: enc.q_prompt(t) for t in PUBLIC}
        settings["doc_prompt_resolved"] = enc.d_prompt("legalquad")
        settings["max_seq_length"] = enc.m.max_seq_length
    else:
        settings.update({"query_length": enc.ql0, "document_length": a.max_length, "query_expansion": enc.qe0,
                         "olr_lengths": OLR_LENGTHS})
    import sentence_transformers, transformers
    settings.update({"sentence_transformers": sentence_transformers.__version__, "transformers": transformers.__version__})

    metrics, tasks_run = {}, {}
    loaders = {"legalquad": lambda: load_mteb("legalquad"), "gerdalir_small": lambda: load_mteb("gerdalir_small"),
               "gerlayqa": lambda: load_gerlayqa(data_dir), "gerlerb": lambda: load_gerlerb(data_dir)}
    for t in [x for x in tasks if x in PUBLIC]:
        q, c, rels = loaders[t]()
        if not a.no_check and (len(q), len(c)) != EXPECTED_SIZE[t]:
            raise SystemExit(f"{t}: size {len(q)}/{len(c)} != protocol {EXPECTED_SIZE[t]}")
        ts = time.time()
        nd, nq, ndoc = search(enc, t, q, c, rels, doc_block=a.doc_block)
        metrics[t] = {"ndcg_at_10": round(nd, 4)}; tasks_run[t] = {"n_queries": nq, "n_docs": ndoc}
        log(f"RESULT {t} nDCG@10 {nd:.4f}  ({nq} queries, {ndoc} documents, {time.time() - ts:.0f} s)")

    if OLR in tasks:
        olr_dir, source = olr_source(a)
        settings["olr_source"] = source
        if olr_dir is None:
            log(f"[olr] skipped: {source}. VAGO Solutions measures OpenLegalRetrieval-DE for submitted models.")
        else:
            sub = {}
            for tk in OLR_LENGTHS:
                q, c, rels = load_olr_task(tk, olr_dir, data_dir)
                if not a.no_check and (len(q), len(c)) != EXPECTED_SIZE[tk]:
                    raise SystemExit(f"OLR {tk}: size {len(q)}/{len(c)} != protocol {EXPECTED_SIZE[tk]}")
                nd, nq, ndoc = search(enc, OLR, q, c, rels, olr_task=tk, doc_block=a.doc_block)
                sub[tk] = round(nd, 4); tasks_run[f"{OLR}.{tk}"] = {"n_queries": nq, "n_docs": ndoc}
                log(f"RESULT {OLR}/{tk} nDCG@10 {nd:.4f}")
            metrics[OLR] = {"ndcg_at_10": round(sum(sub.values()) / 7, 4), "subtasks": sub}

    org = a.organization or (hf_id.split("/")[0] if hf_id and "/" in hf_id else "unknown")
    name = a.model_name or (hf_id.split("/")[-1] if hf_id else Path(a.model).name)
    entry = {
        "id": f"{org}-{name}".lower().replace("/", "-").replace(" ", "-"),
        "model_name": name, "organization": org,
        "model_type": a.model_type, "embedding_type": EMB[a.embedding_type],
        "dimension": minfo["dimension"], "max_tokens": minfo["max_tokens"],
        "parameters": a.parameters or minfo["parameters"],
        "model_url": f"https://huggingface.co/{hf_id}" if hf_id else None, "paper_url": None,
        "license": a.license,
        "metrics": metrics,
        "notes": a.notes or f"Measured with {SCRIPT} (protocol {PROTOCOL_VERSION}).",
        "source": "submission", "model_revision": a.revision,
        "protocol": {"script": SCRIPT, "version": PROTOCOL_VERSION, "date": _dt.date.today().isoformat(),
                     "settings": settings, "tasks": tasks_run},
        "contamination": list(trained_on),
    }
    if private:
        log("WARNING: the model is private; submissions require a public model.")
    out = Path(a.out)
    if out.suffix != ".json":
        out.mkdir(parents=True, exist_ok=True)
        out = out / result_filename(org, name)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False); f.write("\n")
    log(f"written: {out}  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    sys.exit(main())
