from enum import Enum
from typing import Dict, List, Optional, Any, Literal
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator, model_validator

class ModelType(str, Enum):
    OPEN_WEIGHTS = "open"
    PROPRIETARY = "proprietary"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_lower = value.strip().lower()
            if val_lower in ["open", "open weights", "open-weights", "open_weights", "open source", "opensource"]:
                return cls.OPEN_WEIGHTS
            if val_lower in ["proprietary", "closed", "commercial"]:
                return cls.PROPRIETARY
        return None

class EmbeddingType(str, Enum):
    DENSE = "Dense"
    LATE_INTERACTION = "Late-Interaction"
    HYBRID = "Hybrid"
    MOE = "MoE"
    BM25 = "BM25"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_lower = value.strip().lower()
            if "moe" in val_lower or "mixture of experts" in val_lower or "mixture-of-experts" in val_lower or "expert" in val_lower:
                return cls.MOE
            if "late" in val_lower or "colbert" in val_lower:
                return cls.LATE_INTERACTION
            if "hybrid" in val_lower:
                return cls.HYBRID
            if "bm25" in val_lower or "sparse" in val_lower or "lexical" in val_lower:
                return cls.BM25
            if "dense" in val_lower:
                return cls.DENSE
        return None

class DatasetMetrics(BaseModel):
    ndcg_at_10: float = Field(..., ge=0.0, le=1.0, description="nDCG@10 as a fraction (e.g. 0.8874)")
    recall_at_10: Optional[float] = Field(None, ge=0.0, le=100.0, description="Recall@10 in percent")
    mrr_at_10: Optional[float] = Field(None, ge=0.0, le=100.0, description="MRR@10 in percent")
    map_at_10: Optional[float] = Field(None, ge=0.0, le=100.0, description="MAP@10 in percent")
    subtasks: Optional[Dict[str, float]] = Field(
        None, description="Subtasks of a multi-task benchmark (e.g. OpenLegalRetrieval-DE t1–t7), nDCG@10 each as a fraction"
    )

    @field_validator("subtasks")
    @classmethod
    def check_subtasks(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return None
        for k, x in v.items():
            if not isinstance(x, (int, float)) or not 0.0 <= float(x) <= 1.0:
                raise ValueError(f"subtask score {k} must be between 0 and 1")
        return {k: round(float(x), 4) for k, x in v.items()}

    @field_validator("ndcg_at_10", mode="before")
    @classmethod
    def normalize_ndcg(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            # If provided as percentage > 1.0, convert to decimal fraction (0.0 - 1.0)
            if v > 1.0:
                return round(float(v) / 100.0, 4)
            return round(float(v), 4)
        if isinstance(v, str):
            clean_v = v.replace("%", "").strip()
            num = float(clean_v)
            if num > 1.0:
                return round(num / 100.0, 4)
            return round(num, 4)
        return v

    @field_validator("recall_at_10", "mrr_at_10", "map_at_10", mode="before")
    @classmethod
    def normalize_percentages(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            if 0.0 <= v <= 1.0 and v != 0.0 and v != 1.0:
                return round(float(v) * 100.0, 2)
            return round(float(v), 2)
        if isinstance(v, str):
            clean_v = v.replace("%", "").strip()
            num = float(clean_v)
            if 0.0 <= num <= 1.0 and num != 0.0 and num != 1.0:
                return round(num * 100.0, 2)
            return round(num, 2)
        return v

class TaskRun(BaseModel):
    """Size of a task as measured by the benchmark script (cross-check for maintainers)."""
    n_queries: int = Field(..., ge=1)
    n_docs: int = Field(..., ge=1)


class ProtocolInfo(BaseModel):
    """Evaluation protocol of an entry. For submissions, benchmark/run_benchmark.py writes this block."""
    script: str = Field(..., description="Tool used for the measurement (e.g. benchmark/run_benchmark.py)")
    version: str = Field(..., description="Protocol/script version (see config.PROTOCOL_VERSION)")
    date: Optional[str] = Field(None, description="Measurement date (ISO 8601)")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Prompts, lengths, dtype, device, batch size …")
    tasks: Dict[str, TaskRun] = Field(default_factory=dict, description="Per dataset: number of queries and documents")


class BenchmarkEntry(BaseModel):
    id: str = Field(..., description="Unique model ID (e.g. bge-m3)")
    model_name: str = Field(..., description="Display name of the embedding model")
    organization: str = Field(..., description="Organisation / developer")
    model_type: ModelType = Field(..., description="open (public weights) or proprietary")
    embedding_type: EmbeddingType = Field(..., description="Dense, Late-Interaction, Hybrid, MoE or BM25")
    dimension: Optional[int] = Field(None, description="Embedding dimension (e.g. 1024)")
    max_tokens: Optional[int] = Field(None, description="Maximum context in tokens (e.g. 8192)")
    parameters: Optional[int] = Field(None, description="Number of active parameters (e.g. 567000000 for 567M, 1 for BM25)")
    model_url: Optional[str] = Field(None, description="Link to Hugging Face or documentation")
    paper_url: Optional[str] = Field(None, description="Link to the paper")
    metrics: Dict[str, DatasetMetrics] = Field(
        ...,
        description="Dataset key (see config.DATASETS_INFO) -> metrics"
    )
    notes: Optional[str] = Field(None, description="Additional notes / evaluation setup")
    # Provenance (results/<organisation>__<model>.json, added via pull request)
    source: Literal["vago", "submission", "mteb"] = Field(
        "vago", description="vago = measured by VAGO Solutions, submission = submitted via PR (benchmark script), mteb = publicly reported MTEB score")
    model_revision: Optional[str] = Field(None, description="Hugging Face commit of the measured model")
    license: Optional[str] = Field(None, description="Licence or terms of use of the model, e.g. 'commercial-api' or an SPDX identifier such as 'apache-2.0'")
    protocol: Optional[ProtocolInfo] = Field(None, description="Evaluation protocol (required for submissions)")
    contamination: List[str] = Field(default_factory=list,
        description="Dataset keys whose training/test data was used to train the model (self-declared or from MTEB metadata)")

    @field_validator("parameters", mode="before")
    @classmethod
    def normalize_parameters(cls, v: Any) -> Optional[int]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str):
            val_clean = v.strip().upper().replace(",", "")
            if val_clean.endswith("B"):
                return int(float(val_clean[:-1]) * 1_000_000_000)
            if val_clean.endswith("M"):
                return int(float(val_clean[:-1]) * 1_000_000)
            if val_clean.endswith("K"):
                return int(float(val_clean[:-1]) * 1_000)
            return int(float(val_clean))
        return v

class NanoBEIRCorpusDoc(BaseModel):
    id: str = Field(..., description="Document ID (_id or id)")
    title: Optional[str] = Field("", description="Optional document title")
    text: str = Field(..., min_length=1, description="Full document text")

    @model_validator(mode="before")
    @classmethod
    def extract_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            doc_id = data.get("_id", data.get("id"))
            if doc_id is not None:
                data = dict(data)
                data["id"] = str(doc_id).strip()
        return data


class NanoBEIRQuery(BaseModel):
    id: str = Field(..., description="Query ID (_id or id)")
    text: str = Field(..., min_length=1, description="Query text")

    @model_validator(mode="before")
    @classmethod
    def extract_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            q_id = data.get("_id", data.get("id"))
            if q_id is not None:
                data = dict(data)
                data["id"] = str(q_id).strip()
        return data


class NanoBEIRQrel(BaseModel):
    query_id: str = Field(..., description="Referenced query ID (query-id or query_id)")
    corpus_id: str = Field(..., description="Referenced document ID (corpus-id or corpus_id)")
    score: float = Field(1.0, description="Relevance score (> 0 for relevant documents)")

    @model_validator(mode="before")
    @classmethod
    def extract_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            q_id = data.get("query-id", data.get("query_id"))
            c_id = data.get("corpus-id", data.get("corpus_id"))
            if q_id is not None:
                data["query_id"] = str(q_id).strip()
            if c_id is not None:
                data["corpus_id"] = str(c_id).strip()
            if "score" not in data or data["score"] is None:
                data["score"] = 1.0
        return data


class CustomNanoBEIRDataset(BaseModel):
    name: str = Field("Custom Legal NanoBEIR", description="Name of the custom evaluation dataset")
    corpus: List[NanoBEIRCorpusDoc] = Field(..., min_length=1, max_length=50, description="Corpus with at most 50 documents")
    queries: List[NanoBEIRQuery] = Field(..., min_length=1, description="Queries")
    qrels: List[NanoBEIRQrel] = Field(..., min_length=1, description="Relevance judgements (qrels)")

    @field_validator("corpus")
    @classmethod
    def check_max_corpus_size(cls, v: List[NanoBEIRCorpusDoc]) -> List[NanoBEIRCorpusDoc]:
        if len(v) > 50:
            raise ValueError(f"The corpus may contain at most 50 documents (currently: {len(v)}).")
        if len(v) == 0:
            raise ValueError("The corpus must not be empty.")
        return v

    # Instance method instead of classmethod: the classmethod variant is deprecated since Pydantic 2.12.
    @model_validator(mode="after")
    def validate_references(self) -> "CustomNanoBEIRDataset":
        corpus_ids = {d.id for d in self.corpus}
        query_ids = {q.id for q in self.queries}
        valid_qrels = [r for r in self.qrels if r.score > 0 and r.query_id in query_ids and r.corpus_id in corpus_ids]
        if not valid_qrels:
            raise ValueError(
                "No valid qrels: every judgement must reference an existing query-id and corpus-id with score > 0."
            )
        return self
