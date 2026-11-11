import gc
import json
import math
import re
import threading
import sys
import time
from typing import Dict, List, Any, Tuple, Optional, Set
import config
from i18n import t
from data.schema import CustomNanoBEIRDataset


class CustomEvalService:
    """
    Validates and evaluates custom datasets in NanoBEIR format (corpus, queries, qrels) with nDCG@10 as the
    primary metric and a hard limit of 50 corpus documents. Follows the NanoBEIR evaluation
    (MultiVectorEncoder / InformationRetrievalEvaluator).
    """

    MAX_CORPUS_DOCS = config.MAX_CUSTOM_CORPUS_DOCS  # 50
    _lock = threading.Lock()  # one evaluation at a time (resource protection on the public Space)

    @staticmethod
    def get_runtime_status() -> Dict[str, Any]:
        """Checks whether torch, sentence-transformers and MultiVectorEncoder are available."""
        try:
            import torch
            import sentence_transformers

            st_version = getattr(sentence_transformers, "__version__", "unknown")
            has_multivector = hasattr(sentence_transformers, "MultiVectorEncoder")
            if torch.cuda.is_available():
                device = "CUDA GPU"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "Apple MPS"
            else:
                device = "CPU"
            return {
                "ready": True,
                "st_version": st_version,
                "torch_version": getattr(torch, "__version__", "unknown"),
                "has_multivector": has_multivector,
                "device": device,
            }
        except ImportError:
            return {
                "ready": False,
                "st_version": None,
                "torch_version": None,
                "has_multivector": False,
                "device": "CPU",
            }

    @staticmethod
    def _validation_text(e: Exception, lang: str) -> str:
        """Short, readable Pydantic errors (field: message) instead of the raw dump with input values and doc links;
        known custom checks are shown in the UI language."""
        errors = getattr(e, "errors", None)
        if not callable(errors):
            return str(e)
        parts = []
        for err in errors()[:3]:
            msg = str(err.get("msg", ""))
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            if "No valid qrels" in msg:
                msg = t(lang, "msg.qrels_none")
            loc = ".".join(str(x) for x in err.get("loc", ()))
            parts.append(f"{loc}: {msg}" if loc else msg)
        rest = len(errors()) - 3
        return "; ".join(parts) + (f" (+{rest})" if rest > 0 else "")

    def parse_and_validate_dataset(self, raw_json_str: str, lang: str = "de") -> Tuple[bool, str, Optional[CustomNanoBEIRDataset]]:
        """Parses and validates a JSON string in NanoBEIR format, including the 50-document corpus limit."""
        try:
            raw_data = json.loads(raw_json_str)
        except Exception as e:
            return False, t(lang, "msg.json_invalid", err=str(e)), None

        if not isinstance(raw_data, dict):
            return False, t(lang, "msg.root_object"), None

        corpus_raw = raw_data.get("corpus")
        if isinstance(corpus_raw, list) and len(corpus_raw) > self.MAX_CORPUS_DOCS:
            return (
                False,
                t(lang, "msg.corpus_limit", n=len(corpus_raw), max=self.MAX_CORPUS_DOCS),
                None,
            )

        try:
            dataset = CustomNanoBEIRDataset(**raw_data)
        except Exception as e:
            return False, t(lang, "msg.nanobeir_invalid", err=self._validation_text(e, lang)), None

        return True, t(lang, "msg.dataset_valid"), dataset

    @staticmethod
    def convert_to_nanobeir_structures(
        dataset: CustomNanoBEIRDataset,
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Set[str]], Dict[str, Dict[str, float]]]:
        """
        Converts the validated dataset exactly like the NanoBEIR evaluation script:
        - corpus: Dict[cid, "title\\ntext" if title else "text"]
        - queries: Dict[qid, text]
        - relevant_docs: Dict[qid, Set[cid]] (score > 0)
        - qrels_graded: Dict[qid, Dict[cid, score]]
        """
        corpus: Dict[str, str] = {}
        for r in dataset.corpus:
            cid = str(r.id)
            title = (r.title or "").strip()
            text = (r.text or "").strip()
            corpus[cid] = f"{title}\n{text}".strip() if title else text

        queries: Dict[str, str] = {
            str(r.id): str(r.text).strip()
            for r in dataset.queries
        }

        relevant_docs: Dict[str, Set[str]] = {}
        qrels_graded: Dict[str, Dict[str, float]] = {}
        for r in dataset.qrels:
            score = float(r.score)
            if score > 0:
                qid = str(r.query_id)
                cid = str(r.corpus_id)
                if qid in queries and cid in corpus:
                    relevant_docs.setdefault(qid, set()).add(cid)
                    qrels_graded.setdefault(qid, {})[cid] = score

        return corpus, queries, relevant_docs, qrels_graded

    @staticmethod
    def compute_ir_metrics(
        queries: Dict[str, str],
        corpus: Dict[str, str],
        relevant_docs: Dict[str, Set[str]],
        similarity_matrix: Dict[str, Dict[str, float]],
        k: int = 10,
    ) -> Dict[str, Any]:
        """
        nDCG@10 (binary relevance, as in the Sentence Transformers InformationRetrievalEvaluator),
        Recall@10, MRR@10 and per-query results.
        """
        ndcg_scores: List[float] = []
        recall_scores: List[float] = []
        mrr_scores: List[float] = []
        query_details: List[Dict[str, Any]] = []

        for qid, qtext in queries.items():
            rel_set = relevant_docs.get(qid, set())
            if not rel_set:
                continue

            doc_scores = similarity_matrix.get(qid, {})
            ranked_cids = sorted(doc_scores.keys(), key=lambda c: doc_scores[c], reverse=True)
            top_k_cids = ranked_cids[:k]

            # DCG@k (binary relevance as in SentenceTransformers InformationRetrievalEvaluator / MultiVectorInformationRetrievalEvaluator)
            dcg = 0.0
            for rank_idx, cid in enumerate(top_k_cids):
                if cid in rel_set:
                    dcg += 1.0 / math.log2(rank_idx + 2)

            # IDCG@k
            ideal_hits = min(len(rel_set), k)
            idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
            ndcg = (dcg / idcg) if idcg > 0 else 0.0
            ndcg_scores.append(ndcg)

            # Recall@k
            hits_at_k = sum(1 for cid in top_k_cids if cid in rel_set)
            recall = (hits_at_k / len(rel_set)) if rel_set else 0.0
            recall_scores.append(recall)

            # MRR@k
            rr = 0.0
            for rank_idx, cid in enumerate(top_k_cids):
                if cid in rel_set:
                    rr = 1.0 / (rank_idx + 1)
                    break
            mrr_scores.append(rr)

            top_hit_cid = top_k_cids[0] if top_k_cids else None
            top_hit_preview = ""
            if top_hit_cid and top_hit_cid in corpus:
                raw_doc = corpus[top_hit_cid].replace("\n", " ")
                top_hit_preview = (raw_doc[:90] + "...") if len(raw_doc) > 90 else raw_doc

            query_details.append({
                "query_id": qid,
                "query_text": qtext,
                "ndcg_at_10": round(ndcg, 4),
                "recall_at_10": round(recall * 100.0, 2),
                "mrr_at_10": round(rr * 100.0, 2),
                "relevant_count": len(rel_set),
                "hits_at_10": hits_at_k,
                "top_doc_id": top_hit_cid or "-",
                "top_doc_is_relevant": (top_hit_cid in rel_set) if top_hit_cid else False,
                "top_doc_preview": top_hit_preview,
            })

        mean_ndcg = round(sum(ndcg_scores) / len(ndcg_scores), 4) if ndcg_scores else 0.0
        mean_recall = round((sum(recall_scores) / len(recall_scores)) * 100.0, 2) if recall_scores else 0.0
        mean_mrr = round((sum(mrr_scores) / len(mrr_scores)) * 100.0, 2) if mrr_scores else 0.0

        return {
            "ndcg_at_10": mean_ndcg,
            "recall_at_10": mean_recall,
            "mrr_at_10": mean_mrr,
            "evaluated_queries": len(ndcg_scores),
            "query_details": query_details,
        }

    @staticmethod
    def _tokenize_german_legal(text: str) -> List[str]:
        text_lower = text.lower()
        tokens = re.findall(r"[a-zäöüß0-9§]+", text_lower)
        return [t for t in tokens if len(t) > 1 or t == "§"]

    def _compute_bm25_similarity(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str],
        k1: float = 1.2,
        b: float = 0.75,
    ) -> Dict[str, Dict[str, float]]:
        """BM25 scores between queries and corpus (fast lexical baseline)."""
        tokenized_corpus: Dict[str, List[str]] = {
            cid: self._tokenize_german_legal(text) for cid, text in corpus.items()
        }
        num_docs = max(len(tokenized_corpus), 1)
        avgdl = sum(len(toks) for toks in tokenized_corpus.values()) / num_docs if num_docs else 1.0

        # Document frequencies
        df: Dict[str, int] = {}
        for toks in tokenized_corpus.values():
            for term in set(toks):
                df[term] = df.get(term, 0) + 1

        # IDF
        idf: Dict[str, float] = {}
        for term, freq in df.items():
            idf[term] = math.log(1.0 + (num_docs - freq + 0.5) / (freq + 0.5))

        sim_matrix: Dict[str, Dict[str, float]] = {}
        for qid, qtext in queries.items():
            q_tokens = self._tokenize_german_legal(qtext)
            sim_matrix[qid] = {}
            for cid, d_tokens in tokenized_corpus.items():
                dl = len(d_tokens)
                tf_map: Dict[str, int] = {}
                for t in d_tokens:
                    tf_map[t] = tf_map.get(t, 0) + 1

                score = 0.0
                for qt in q_tokens:
                    if qt not in tf_map:
                        continue
                    tf = tf_map[qt]
                    term_idf = idf.get(qt, 0.0)
                    denom = tf + k1 * (1.0 - b + b * (dl / max(avgdl, 1e-6)))
                    score += term_idf * ((tf * (k1 + 1.0)) / denom)
                sim_matrix[qid][cid] = score

        return sim_matrix

    def evaluate_dataset_sync(
        self,
        dataset: CustomNanoBEIRDataset,
        model_name: str = config.DEFAULT_EVAL_MODEL,
        encoder_mode: str = "auto",
        precision_label: str = "FP32",
        batch_size: int = 32,
        lang: str = "de",
    ) -> Dict[str, Any]:
        """Public entry point: checks the allow-list and limits, then runs one evaluation at a time."""
        spec = config.ALLOWED_EVAL_MODELS.get((model_name or "").strip())
        if spec is None:
            raise ValueError(t(lang, "msg.model_not_allowed", models=", ".join(config.ALLOWED_EVAL_MODELS)))
        if len(dataset.queries) > config.MAX_CUSTOM_QUERIES:
            raise ValueError(t(lang, "msg.too_many_queries", max=config.MAX_CUSTOM_QUERIES, n=len(dataset.queries)))
        too_long = [d.id for d in dataset.corpus if len((d.title or "") + d.text) > config.MAX_CUSTOM_TEXT_CHARS]
        too_long += [q.id for q in dataset.queries if len(q.text) > config.MAX_CUSTOM_TEXT_CHARS]
        if too_long:
            raise ValueError(t(lang, "msg.text_too_long", max=config.MAX_CUSTOM_TEXT_CHARS, ids=", ".join(too_long[:5])))
        if not self._lock.acquire(timeout=300):
            raise RuntimeError(t(lang, "msg.eval_busy"))
        try:
            # mode and batch size are fixed per model (not user-selectable) -> reproducible scores
            return self._evaluate_allowed(dataset, model_name.strip(), spec, precision_label, lang)
        finally:
            self._lock.release()

    def _evaluate_allowed(
        self,
        dataset: CustomNanoBEIRDataset,
        model_name: str,
        spec: Dict[str, Any],
        precision_label: str = "FP32",
        lang: str = "de",
    ) -> Dict[str, Any]:
        encoder_mode = spec["mode"]
        batch_size = config.EVAL_BATCH_SIZE
        return self._evaluate_dataset(dataset, model_name, encoder_mode, precision_label, batch_size, spec, lang)

    def _evaluate_dataset(
        self,
        dataset: CustomNanoBEIRDataset,
        model_name: str = config.DEFAULT_EVAL_MODEL,
        encoder_mode: str = "auto",
        precision_label: str = "FP32",
        batch_size: int = 32,
        spec: Optional[Dict[str, Any]] = None,
        lang: str = "de",
    ) -> Dict[str, Any]:
        """
        Runs the evaluation on a custom NanoBEIR dataset (max. 50 documents) with:
        - MultiVectorEncoder + MultiVectorInformationRetrievalEvaluator (late interaction / ColBERT, sentence-transformers >= 6.0.0)
        - SentenceTransformer + InformationRetrievalEvaluator (dense bi-encoders)
        - or the BM25 lexical baseline (instant, no GPU or download).
        """
        start_time = time.time()

        if len(dataset.corpus) > self.MAX_CORPUS_DOCS:
            raise ValueError(t(lang, "msg.corpus_max", max=self.MAX_CORPUS_DOCS))

        corpus, queries, relevant_docs, _ = self.convert_to_nanobeir_structures(dataset)

        # BM25 baseline
        if encoder_mode == "bm25" or model_name.strip().lower().startswith("bm25"):
            sim_matrix = self._compute_bm25_similarity(queries, corpus)
            metrics_res = self.compute_ir_metrics(queries, corpus, relevant_docs, sim_matrix, k=10)
            elapsed = round(time.time() - start_time, 2)
            return {
                "dataset_name": dataset.name,
                "model_name": model_name,
                "encoder_used": "BM25 (Lexical Baseline)",
                "precision": precision_label,
                "device": "cpu",
                "num_corpus": len(corpus),
                "num_queries": len(queries),
                "num_qrels": sum(len(s) for s in relevant_docs.values()),
                "ndcg_at_10": metrics_res["ndcg_at_10"],
                "recall_at_10": metrics_res["recall_at_10"],
                "mrr_at_10": metrics_res["mrr_at_10"],
                "query_details": metrics_res["query_details"],
                "elapsed_seconds": elapsed,
            }

        try:
            import torch
            import sentence_transformers
        except ImportError as import_err:
            # no package installation at runtime (security/reproducibility): dependencies come from requirements.txt
            raise RuntimeError(t(lang, "msg.deps_missing", err=str(import_err)))

        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        dtype_map = {
            "FP32": torch.float32,
            "FP16": torch.float16,
            "BF16": torch.bfloat16,
        }
        dtype = dtype_map.get(precision_label.upper(), torch.float32)

        is_multivector = (
            encoder_mode == "multivector"
            or (
                encoder_mode == "auto"
                and any(k in model_name.lower() for k in ["colbert", "multivector", "late-interaction", "moederncolbert"])
            )
        )

        ndcg_score = 0.0
        encoder_used_label = ""
        sim_matrix_for_details: Dict[str, Dict[str, float]] = {}

        if is_multivector:
            if not hasattr(sentence_transformers, "MultiVectorEncoder"):
                raise RuntimeError(t(lang, "msg.mv_unsupported", v=getattr(sentence_transformers, "__version__", "?")))

            from sentence_transformers import MultiVectorEncoder
            from sentence_transformers.multi_vector_encoder.evaluation import MultiVectorInformationRetrievalEvaluator

            encoder_used_label = "MultiVectorEncoder (MultiVectorInformationRetrievalEvaluator)"
            try:
                model = MultiVectorEncoder(
                    model_name,
                    model_kwargs={"torch_dtype": dtype},
                    device=device,
                    trust_remote_code=bool((spec or {}).get("trust_remote_code", False)),
                    revision=(spec or {}).get("revision"),
                )
            except TypeError:
                model = MultiVectorEncoder(
                    model_name,
                    model_kwargs={"dtype": dtype},
                    device=device,
                    trust_remote_code=bool((spec or {}).get("trust_remote_code", False)),
                    revision=(spec or {}).get("revision"),
                )

            evaluator = MultiVectorInformationRetrievalEvaluator(
                queries=queries,
                corpus=corpus,
                relevant_docs=relevant_docs,
                name=f"custom_{precision_label.lower()}",
                ndcg_at_k=[10],
                batch_size=batch_size,
                show_progress_bar=False,
            )

            eval_result = evaluator(model)
            metric_key = next((k for k in eval_result.keys() if k.endswith("ndcg@10")), None)
            ndcg_score = float(eval_result.get(metric_key, 0.0)) if metric_key else 0.0

            # similarity matrix for the per-query breakdown
            try:
                q_ids = list(queries.keys())
                c_ids = list(corpus.keys())
                q_texts = [queries[q] for q in q_ids]
                c_texts = [corpus[c] for c in c_ids]
                if hasattr(model, "encode_query") and hasattr(model, "encode_document"):
                    q_embs = model.encode_query(q_texts, batch_size=batch_size, show_progress_bar=False)
                    c_embs = model.encode_document(c_texts, batch_size=batch_size, show_progress_bar=False)
                else:
                    q_embs = model.encode(q_texts, batch_size=batch_size, show_progress_bar=False)
                    c_embs = model.encode(c_texts, batch_size=batch_size, show_progress_bar=False)
                scores_tensor = model.similarity(q_embs, c_embs)
                for qi, qid in enumerate(q_ids):
                    sim_matrix_for_details[qid] = {
                        cid: float(scores_tensor[qi][ci]) for ci, cid in enumerate(c_ids)
                    }
            except Exception:
                sim_matrix_for_details = self._compute_bm25_similarity(queries, corpus)

            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        else:
            from sentence_transformers import SentenceTransformer
            from sentence_transformers.evaluation import InformationRetrievalEvaluator

            encoder_used_label = "SentenceTransformer (InformationRetrievalEvaluator)"
            try:
                model = SentenceTransformer(
                    model_name,
                    model_kwargs={"torch_dtype": dtype},
                    device=device,
                    trust_remote_code=bool((spec or {}).get("trust_remote_code", False)),
                    revision=(spec or {}).get("revision"),
                )
            except TypeError:
                model = SentenceTransformer(
                    model_name,
                    model_kwargs={"dtype": dtype},
                    device=device,
                    trust_remote_code=bool((spec or {}).get("trust_remote_code", False)),
                    revision=(spec or {}).get("revision"),
                )

            evaluator = InformationRetrievalEvaluator(
                queries=queries,
                corpus=corpus,
                relevant_docs=relevant_docs,
                name=f"custom_{precision_label.lower()}",
                ndcg_at_k=[10],
                batch_size=batch_size,
                show_progress_bar=False,
            )

            eval_result = evaluator(model)
            metric_key = next((k for k in eval_result.keys() if k.endswith("ndcg@10")), None)
            ndcg_score = float(eval_result.get(metric_key, 0.0)) if metric_key else 0.0

            try:
                q_ids = list(queries.keys())
                c_ids = list(corpus.keys())
                q_texts = [queries[q] for q in q_ids]
                c_texts = [corpus[c] for c in c_ids]
                if hasattr(model, "encode_query") and hasattr(model, "encode_document"):
                    q_embs = model.encode_query(q_texts, batch_size=batch_size, show_progress_bar=False)
                    c_embs = model.encode_document(c_texts, batch_size=batch_size, show_progress_bar=False)
                else:
                    q_embs = model.encode(q_texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
                    c_embs = model.encode(c_texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
                scores_tensor = model.similarity(q_embs, c_embs)
                for qi, qid in enumerate(q_ids):
                    sim_matrix_for_details[qid] = {
                        cid: float(scores_tensor[qi][ci]) for ci, cid in enumerate(c_ids)
                    }
            except Exception:
                sim_matrix_for_details = self._compute_bm25_similarity(queries, corpus)

            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        details = self.compute_ir_metrics(queries, corpus, relevant_docs, sim_matrix_for_details, k=10)
        elapsed = round(time.time() - start_time, 2)

        return {
            "dataset_name": dataset.name,
            "model_name": model_name,
            "encoder_used": encoder_used_label,
            "precision": precision_label,
            "device": device,
            "num_corpus": len(corpus),
            "num_queries": len(queries),
            "num_qrels": sum(len(s) for s in relevant_docs.values()),
            "ndcg_at_10": round(ndcg_score, 4),
            "recall_at_10": details["recall_at_10"],
            "mrr_at_10": details["mrr_at_10"],
            "query_details": details["query_details"],
            "elapsed_seconds": elapsed,
        }


custom_eval_service = CustomEvalService()
