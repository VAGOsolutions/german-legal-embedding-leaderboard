from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
# One JSON file per model (results/<organisation>__<model>.json) is the only source of the leaderboard.
# New entries are added via GitHub pull request only (see CONTRIBUTING.md).
RESULTS_DIR = BASE_DIR / "results"
BENCHMARK_DIR = BASE_DIR / "benchmark"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Application Information
APP_TITLE = "German Legal Embedding Benchmark | Leaderboard"
APP_SUBTITLE = "EVALUATION OF EMBEDDING MODELS ON GERMAN LEGAL RETRIEVAL BENCHMARKS"
ORGANIZATION_NAME = "VAGO Solutions"

# Repository that receives result files via pull request
REPO_URL = os.getenv("LEADERBOARD_REPO_URL", "https://github.com/VAGOsolutions/german-legal-embedding-leaderboard").rstrip("/")
CONTRIBUTING_URL = f"{REPO_URL}/blob/main/CONTRIBUTING.md"
BENCHMARK_README_URL = f"{REPO_URL}/blob/main/benchmark/README.md"
# Provenance of an entry: measured by VAGO Solutions, submitted via PR (benchmark script), publicly reported MTEB score
RESULT_SOURCES = ("vago", "submission", "mteb")
# Protocol version of benchmark/run_benchmark.py; submissions must match it
PROTOCOL_VERSION = "1.0"

# Datasets (order = column order; descriptions are bilingual UI texts, shown via i18n.ds_text)
DATASETS_INFO = {
    "overall": {
        "name": "Overall (Legal-Aggregated)",
        "short_name": "Overall",
        "description": {
            "de": "Mittelwert der nDCG@10 über LegalQuAD, GerDaLIR Small, GerLayQA, GerLeRB und OpenLegalRetrieval-DE (nur Modelle mit allen fünf Werten).",
            "en": "Mean nDCG@10 over LegalQuAD, GerDaLIR Small, GerLayQA, GerLeRB and OpenLegalRetrieval-DE (only models with all five scores).",
        },
        "icon": "military_tech",
        "url": None,
        "citation": "Combined German Legal Benchmark Index",
    },
    "legalquad": {
        "name": "LegalQuAD",
        "short_name": "LegalQuAD",
        "description": {
            "de": "German Legal Question Answering Dataset (MTEB). Retrieval von Antwortpassagen zu juristischen Fachfragen.",
            "en": "German Legal Question Answering Dataset (MTEB). Retrieval of answer passages for legal questions.",
        },
        "icon": "contact_support",
        "url": "https://huggingface.co/datasets/mteb/LegalQuAD",
        "citation": "MTEB Benchmark / LegalQuAD",
    },
    "gerdalir_small": {
        "name": "GerDaLIR Small",
        "short_name": "GerDaLIR Small",
        "description": {
            "de": "German Dataset for Legal Information Retrieval, MTEB-Teilmenge. Case-Citation-Retrieval: zu einem Urteilsabschnitt die darin zitierten Entscheidungen finden (12.234 Queries, 9.969 Dokumente).",
            "en": "German Dataset for Legal Information Retrieval, MTEB subset. Case-citation retrieval: find the decisions cited in a court-decision passage (12,234 queries, 9,969 documents).",
        },
        "icon": "gavel",
        "url": "https://huggingface.co/datasets/mteb/GerDaLIRSmall",
        "citation": "MTEB Benchmark / GerDaLIR",
    },
    "gerlayqa": {
        "name": "GerLayQA (German Laymen Legal QA)",
        "short_name": "GerLayQA",
        "description": {
            "de": "Laienfragen zum deutschen Zivilrecht (EACL 2024): zu einer Frage aus Frag-einen-Anwalt.de die einschlägigen Rechtsnormen finden.",
            "en": "Lay questions on German civil law (EACL 2024): find the relevant statutes for a question from Frag-einen-Anwalt.de.",
        },
        "icon": "chat",
        "url": "https://github.com/trusthlt/eacl24-german-legal-questions",
        "citation": "Büttner & Habernal (EACL 2024)",
    },
    "gerlerb": {
        "name": "GerLeRB (German Legislative Retrieval)",
        "short_name": "GerLeRB",
        "description": {
            "de": "German Legislative Retrieval Benchmark: einschlägige Normen des Bundesrechts zu juristischen Fragen finden (367 Fragen, 89.851 Normabschnitte).",
            "en": "German Legislative Retrieval Benchmark: find the relevant federal statute sections for legal questions (367 questions, 89,851 statute sections).",
        },
        "icon": "account_balance",
        "url": "https://zenodo.org/records/15745124",
        "citation": "Zenodo Record 15745124",
    },
    "openlegalretrieval_de": {
        "name": "OpenLegalRetrieval-DE (7 Tasks)",
        "short_name": "OpenLegalRetrieval",
        "description": {
            "de": "Benchmark von VAGO Solutions aus sieben juristischen Retrieval-Aufgaben (Normen, Rechtsprechung, Zitate, Argumente, Tatbestandsmerkmale, Laienfragen, Fallbeschreibungen). Hauptwert: Makro-Mittel der nDCG@10 über t1–t7. Lizenz: ODbL 1.0 (enthält Informationen aus Open Legal Data).",
            "en": "VAGO Solutions benchmark of seven legal retrieval tasks (statutes, case law, citations, arguments, elements of an offence, lay questions, case descriptions). Main score: macro mean of nDCG@10 over t1–t7. Licence: ODbL 1.0 (contains information from Open Legal Data).",
        },
        "icon": "account_tree",
        "url": None,
        "citation": "VAGO Solutions (ODbL 1.0)",
    },
}

# OpenLegalRetrieval-DE: the seven subtasks (query/document length in tokens, as in the evaluation protocol)
OLR_KEY = "openlegalretrieval_de"
OLR_TASKS = {
    "t1": {"short": "Statute", "de": "Rechtsfrage → Rechtsnorm", "en": "legal question → statute", "q": 128, "d": 2048},
    "t2": {"short": "Case", "de": "Entscheidung → zitierte Präzedenzfälle", "en": "decision → cited precedents", "q": 2048, "d": 2048},
    "t3": {"short": "Citation", "de": "Urteil → angewandte Rechtsnorm", "en": "judgment → applied statute", "q": 2048, "d": 2048},
    "t4": {"short": "Argument", "de": "juristisches Argument → Rechtsgrundlage", "en": "legal argument → legal basis", "q": 256, "d": 2048},
    "t5": {"short": "Merkmal", "de": "Tatbestandsmerkmal → Norm", "en": "element of an offence → statute", "q": 128, "d": 2048},
    "t6": {"short": "GerLayQA", "de": "Laienfrage → BGB-Paragraph (GerLayQA-Variante)", "en": "lay question → BGB section (GerLayQA variant)", "q": 512, "d": 2048},
    "t7": {"short": "GerDaLIR", "de": "Fallbeschreibung → frühere Entscheidungen (GerDaLIR-Variante)", "en": "case description → earlier decisions (GerDaLIR variant)", "q": 512, "d": 4096},
}

# Size filter (log10 of the parameter count): 1M … 10B; the slider ends mean "no limit"
SIZE_LOG_MIN = 6.0
SIZE_LOG_MAX = 10.0

# Custom NanoBEIR Evaluation Settings
MAX_CUSTOM_CORPUS_DOCS = 50
DEFAULT_EVAL_MODEL = "VAGOsolutions/SauerkrautLM-MoEdernColBERT-27M"
# Security (public Space): live evaluation only with approved models at pinned revisions.
# - no free-form model name (otherwise visitors could load arbitrary repos)
# - trust_remote_code only for VAGO Solutions models pinned to a commit
# - no package installation at runtime, fixed batch size, limits on queries and text length, one evaluation at a time
ALLOWED_EVAL_MODELS = {
    "VAGOsolutions/SauerkrautLM-MoEdernColBERT-27M": {"label": "SauerkrautLM-MoEdernColBERT-27M (ColBERT, MoE)", "mode": "multivector",
        "revision": "d2b7b1feaaac1bf87510ca9525208c3daeabcc5a", "trust_remote_code": True},
    "VAGOsolutions/SauerkrautLM-MoEdernColBERT-1.5M": {"label": "SauerkrautLM-MoEdernColBERT-1.5M (ColBERT, MoE)", "mode": "multivector",
        "revision": "9d360b8b88ae11bea5784bf9012ff509fdd5c2da", "trust_remote_code": True},
    "VAGOsolutions/SauerkrautLM-MoEdernColBERT-115M": {"label": "SauerkrautLM-MoEdernColBERT-115M (ColBERT, MoE)", "mode": "multivector",
        "revision": "66380d2ade3b5027bba83bdcdba052d0bb86dcdb", "trust_remote_code": True},
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {"label": "paraphrase-multilingual-MiniLM-L12-v2 (Dense)", "mode": "dense",
        "revision": "e8f8c211226b894fcb81acc59f3b34ba3efd5f42", "trust_remote_code": False},
    "intfloat/multilingual-e5-small": {"label": "multilingual-e5-small (Dense)", "mode": "dense",
        "revision": "614241f622f53c4eeff9890bdc4f31cfecc418b3", "trust_remote_code": False},
    "intfloat/multilingual-e5-base": {"label": "multilingual-e5-base (Dense)", "mode": "dense",
        "revision": "d128750597153bb5987e10b1c3493a34e5a4502a", "trust_remote_code": False},
    "BAAI/bge-m3": {"label": "BAAI/bge-m3 (Dense)", "mode": "dense",
        "revision": "5617a9f61b028005a4858fdac845db406aefb181", "trust_remote_code": False},
    "Qwen/Qwen3-Embedding-0.6B": {"label": "Qwen3-Embedding-0.6B (Dense)", "mode": "dense",
        "revision": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3", "trust_remote_code": False},
    "BM25-Baseline": {"label": "BM25 (lexical baseline, instant)", "label_de": "BM25 (lexikalische Baseline, sofort)", "mode": "bm25", "revision": None, "trust_remote_code": False},
}
SUGGESTED_EVAL_MODELS = list(ALLOWED_EVAL_MODELS)
MAX_CUSTOM_QUERIES = 200          # max queries per live evaluation
MAX_CUSTOM_TEXT_CHARS = 20000     # max characters per document/query
EVAL_BATCH_SIZE = 16              # fixed: MoEdernColBERT scores depend on the batch size (attention window follows the padded length)

# Brand colours: VAGO Solutions + SauerkrautLM (font: Inter)
BRAND_VAGO_BG = "#05010d"
BRAND_VAGO_ACCENT = "#8054ff"
BRAND_VAGO_GRADIENT = "linear-gradient(90deg, #ff9898 0%, #8054ff 100%)"
BRAND_SK_YELLOW = "#F8D84A"
BRAND_SK_GRADIENT = "linear-gradient(100deg, #CC01FE 0%, #9301FF 42%, #3E96F7 100%)"
