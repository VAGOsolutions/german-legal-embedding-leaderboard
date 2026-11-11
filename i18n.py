"""UI texts in German and English.

The language is chosen per page request via ?lang=de|en and passed to every component (no global state shared
between visitors). Every key has exactly two texts (de, en); tests/test_i18n.py checks completeness and that every
key used in the code exists.
"""
from typing import Any, Dict, Optional, Tuple
import config

LANGUAGES = ("de", "en")


def norm_lang(value: Any) -> str:
    return "en" if str(value or "").strip().lower().startswith("en") else "de"


TEXTS: Dict[str, Tuple[str, str]] = {
    # page / header
    "page.title": ("German Legal Embedding Benchmark | Rangliste", "German Legal Embedding Benchmark | Leaderboard"),
    "page.description": ("Rangliste von Embedding-Modellen auf deutschen juristischen Retrieval-Benchmarks (LegalQuAD, GerDaLIR Small, GerLayQA, GerLeRB, OpenLegalRetrieval-DE), nDCG@10.",
                         "Leaderboard of embedding models on German legal retrieval benchmarks (LegalQuAD, GerDaLIR Small, GerLayQA, GerLeRB, OpenLegalRetrieval-DE), nDCG@10."),
    "brand.by": ("by", "by"),
    "lang.aria": ("Sprache", "Language"),
    "lang.de": ("Deutsch", "German"),
    "lang.en": ("Englisch", "English"),
    "hero.subtitle": ("Faire, einheitliche Evaluation von Embedding-Modellen auf deutschen juristischen Retrieval-Benchmarks",
                      "Fair, uniform evaluation of embedding models on German legal retrieval benchmarks"),
    "hero.badge1": ("Deutsches Recht", "German law"),
    "hero.badge3": ("5 Benchmarks · 11 Aufgaben", "5 benchmarks · 11 tasks"),
    "view.aria": ("Ansicht", "View"),
    "view.table": ("Rangliste", "Leaderboard"),
    "view.tasks": ("Task-Performance", "Task performance"),
    "view.chart": ("Leistung nach Modellgröße", "Performance by model size"),
    "view.custom": ("Eigene Datensätze (NanoBEIR)", "Your own datasets (NanoBEIR)"),
    "about.title": ("Über den Benchmark", "About the benchmark"),
    "about.lead": ("Offene Plattform zur einheitlichen Evaluation von Embedding- und Retrieval-Modellen auf kuratierten deutschen juristischen Datensätzen.",
                   "Open platform for the uniform evaluation of embedding and retrieval models on curated German legal datasets."),
    "about.list_intro": ("Die Rangliste umfasst fünf Benchmarks aus Rechtsprechung, Gesetzgebung und juristischer Wissensabfrage:",
                         "The leaderboard covers five benchmarks from case law, legislation and legal knowledge retrieval:"),
    "about.footnote": ("Hauptmetrik ist nDCG@10; Overall = Mittel der fünf Benchmarks. Eigene Datensätze im NanoBEIR-Format (bis 50 Dokumente) lassen sich direkt im Dashboard evaluieren.",
                       "The main metric is nDCG@10; Overall = mean of the five benchmarks. Your own datasets in NanoBEIR format (up to 50 documents) can be evaluated directly in the dashboard."),
    "about.more": ("Mehr anzeigen …", "Show more …"),
    "about.less": ("Weniger anzeigen", "Show less"),
    "act.metrics": ("Metriken & Protokoll", "Metrics & protocol"),
    "act.submit": ("Ergebnis einreichen", "Submit results"),
    "act.custom": ("Eigenen Datensatz testen", "Evaluate your dataset"),
    "act.datasets": ("Datensätze & Papers", "Datasets & papers"),
    "act.sample": ("Beispiel-Ergebnisdatei", "Sample result file"),
    "olr.license": ("Lizenz ODbL 1.0", "Licence ODbL 1.0"),
    "olr.attribution": ("Enthält Informationen aus Open Legal Data (openlegaldata.io), bereitgestellt unter der ODbL 1.0.",
                        "Contains information from Open Legal Data (openlegaldata.io), made available under the ODbL 1.0."),
    # filters
    "filter.search": ("Modelle oder Organisationen suchen …", "Search models or organisations …"),
    "filter.all": ("Alle", "All"),
    "filter.type": ("Typus", "Type"),
    "filter.embedding": ("Embedding-Typ", "Embedding type"),
    "filter.count": ("{shown} von {total} Modellen", "{shown} of {total} models"),
    "size.label": ("Modellgröße", "Model size"),
    "size.min_open": ("≤ 1M", "≤ 1M"),
    "size.max_open": ("10B+", "10B+"),
    "size.unsized": ("Ohne Größenangabe (APIs, BM25)", "Without size (APIs, BM25)"),
    "size.unsized_hint": ("Modelle ohne bekannte Parameterzahl erscheinen nur, wenn der Regler den vollen Bereich abdeckt.",
                          "Models without a known parameter count only appear when the slider covers the full range."),
    # table
    "table.dataset_label": ("Benchmark-Datensatz", "Benchmark dataset"),
    "table.col_model": ("Modell", "Model"),
    "table.col_size": ("Größe", "Size"),
    "table.col_type": ("Typus", "Type"),
    "table.col_embedding": ("Embedding", "Embedding"),
    "table.details": ("Details anzeigen", "Show details"),
    "table.empty": ("Keine Modelle für diese Filter.", "No models match these filters."),
    "table.reset": ("Filter zurücksetzen", "Reset filters"),
    "table.model_license": ("Modelllizenz {lic}", "model licence {lic}"),
    "type.open": ("Offene Gewichte", "Open weights"),
    "type.prop": ("Proprietär", "Proprietary"),
    # task matrix
    "tasks.title": ("Task-Performance", "Task performance"),
    "tasks.lead": ("Jeder Einzelwert auf einen Blick: Overall, die fünf Benchmarks und die sieben Aufgaben von OpenLegalRetrieval-DE. Spaltenkopf anklicken zum Sortieren, Modellname für Details.",
                   "Every score at a glance: Overall, the five benchmarks and the seven OpenLegalRetrieval-DE tasks. Click a column header to sort, a model name for details."),
    "tasks.legend_low": ("niedrig", "low"),
    "tasks.legend_high": ("hoch (je Spalte)", "high (per column)"),
    "tasks.legend_best": ("= Bestwert der Spalte", "= best in column"),
    "tasks.legend_missing": ("= nicht gemessen", "= not measured"),
    "tasks.olr_explain": ("Was sind t1–t7? (OpenLegalRetrieval-DE)", "What are t1–t7? (OpenLegalRetrieval-DE)"),
    "tasks.lengths": ("Query {q} / Dokument {d} Token", "query {q} / document {d} tokens"),
    # chart
    "chart.title": ("Leistung nach Modellgröße", "Performance by model size"),
    "chart.lead": ("nDCG@10 gegen die Zahl der aktiven Parameter (logarithmisch). Blasengröße = Embedding-Dimension, Farbe = maximale Kontextlänge. Punkt anklicken für Details.",
                   "nDCG@10 versus number of active parameters (log scale). Bubble size = embedding dimension, colour = maximum context length. Click a point for details."),
    "chart.dataset": ("Datensatz", "Dataset"),
    "chart.x": ("X-Achse: Parameter (logarithmisch)", "x axis: parameters (log scale)"),
    "chart.y": ("Y-Achse: nDCG@10", "y axis: nDCG@10"),
    "chart.bubble": ("Blasengröße: Embedding-Dimension", "Bubble size: embedding dimension"),
    "chart.color": ("Farbe: max. Kontext (512 – 65k)", "Colour: max context (512 – 65k)"),
    "chart.own": ("Gelber Rand: SauerkrautLM (VAGO Solutions)", "Yellow outline: SauerkrautLM (VAGO Solutions)"),
    "chart.x_axis": ("Aktive Parameter (logarithmisch)", "Active parameters (log scale)"),
    "chart.y_axis": ("nDCG@10", "nDCG@10"),
    "chart.vm_high": ("max. Kontext 65k", "max context 65k"),
    "chart.tip_score": ("Score (nDCG@10)", "Score (nDCG@10)"),
    "chart.tip_params": ("Aktive Parameter", "Active parameters"),
    "chart.tip_dim": ("Dimension", "Dimension"),
    "chart.tip_ctx": ("Max. Kontext", "Max context"),
    "chart.tip_lexical": ("0 (lexikalisch)", "0 (lexical)"),
    "chart.tip_click": ("Klick öffnet die Modelldetails ↗", "Click to open model details ↗"),
    # detail dialog
    "detail.dimension": ("Dimension", "Dimension"),
    "detail.context": ("Max. Kontext (Token)", "Max context (tokens)"),
    "detail.params": ("Parameter", "Parameters"),
    "detail.notes": ("Modell & Messaufbau", "Model & evaluation setup"),
    "detail.per_dataset": ("Ergebnisse je Benchmark", "Results per benchmark"),
    "detail.dataset_link": ("Datensatz ↗", "Dataset ↗"),
    "detail.olr_breakdown": ("OpenLegalRetrieval-DE je Aufgabe", "OpenLegalRetrieval-DE per task"),
    "detail.model_link": ("Zum Modell", "Model page"),
    "detail.paper_link": ("Paper / Doku", "Paper / docs"),
    "common.close": ("Schließen", "Close"),
    "common.cancel": ("Abbrechen", "Cancel"),
    # metrics dialog
    "metrics.title": ("Metriken, Messprotokoll & Datensätze", "Metrics, protocol & datasets"),
    "metrics.primary": ("Hauptmetrik", "Primary metric"),
    "metrics.ndcg": ("nDCG@10 bewertet die Reihenfolge der zehn besten Treffer nach abgestufter Relevanz und Position: relevante Dokumente weiter oben zählen deutlich stärker.",
                     "nDCG@10 scores the ranking of the top ten results by graded relevance and position: relevant documents higher up count considerably more."),
    "metrics.recall": ("Anteil aller relevanten Dokumente unter den zehn besten Treffern.", "Share of all relevant documents among the top ten results."),
    "metrics.mrr": ("Kehrwert des Rangs des ersten relevanten Treffers (Mean Reciprocal Rank).", "Reciprocal rank of the first relevant result (mean reciprocal rank)."),
    "metrics.map": ("Mittlere Präzision über die relevanten Treffer (Mean Average Precision).", "Mean precision over the relevant results (mean average precision)."),
    "metrics.protocol_title": ("Messprotokoll", "Evaluation protocol"),
    "metrics.protocol": ("Alle Werte ohne Zusatz stammen aus eigenen Messungen von VAGO Solutions (November 2026) oder aus Einreichungen per Pull Request, gemessen mit dem öffentlichen Benchmark-Skript (benchmark/run_benchmark.py) im selben Protokoll: volle Testkorpora, Dokumente bis 8.192 Token (bzw. Modellmaximum), Query-Prompts und Instruktionen laut Modellkarte, nDCG@10 über alle Queries. OpenLegalRetrieval-DE: Makro-Mittel über t1–t7 mit festen Query-/Dokumentlängen je Aufgabe. Overall = Mittel der fünf Benchmarks, nur für Modelle mit allen fünf Werten. Einträge mit „(MTEB)“ sind öffentlich berichtete Werte ohne eigene Messung (nur LegalQuAD/GerDaLIR Small, nicht im Overall). ⚠ = laut MTEB-Metadaten mit GerDaLIR bzw. GerDaLIR Small trainiert; Werte dort sind zugunsten des Modells verzerrt.",
                         "All scores without a suffix were measured by VAGO Solutions (November 2026) or submitted via pull request, measured with the public benchmark script (benchmark/run_benchmark.py) under the same protocol: full test corpora, documents up to 8,192 tokens (or the model maximum), query prompts and instructions as in the model card, nDCG@10 over all queries. OpenLegalRetrieval-DE: macro mean over t1–t7 with fixed query/document lengths per task. Overall = mean of the five benchmarks, only for models with all five scores. Entries marked “(MTEB)” are publicly reported values we did not measure ourselves (LegalQuAD/GerDaLIR Small only, not in Overall). ⚠ = according to MTEB metadata trained on GerDaLIR or GerDaLIR Small; scores there are biased in the model's favour."),
    "metrics.datasets_title": ("Benchmarks", "Benchmarks"),
    "metrics.source": ("Quelle", "Source"),
    "metrics.gerdalir_full_title": ("GerDaLIR (vollständig) – derzeit nicht in der Rangliste", "GerDaLIR (full) – currently not ranked"),
    "metrics.gerdalir_full": ("Der vollständige GerDaLIR-Benchmark (lavis-nlp) ist bisher nur für die VAGO-Modelle gemessen; verglichen wird deshalb auf GerDaLIR Small.",
                              "The full GerDaLIR benchmark (lavis-nlp) has so far only been measured for the VAGO models, so comparisons use GerDaLIR Small."),
    "metrics.custom_title": ("Eigene Datensätze im NanoBEIR-Format (max. {n} Dokumente)", "Your own datasets in NanoBEIR format (max. {n} documents)"),
    "metrics.custom": ("Im Bereich „Eigene Datensätze (NanoBEIR)“ lassen sich eigene juristische Datensätze aus corpus, queries und qrels mit freigegebenen Modellen (ColBERT/Multi-Vector, Dense oder BM25) evaluieren; Hauptmetrik nDCG@10.",
                       "In “Your own datasets (NanoBEIR)” you can evaluate your own legal datasets (corpus, queries, qrels) with approved models (ColBERT/multi-vector, dense or BM25); main metric nDCG@10."),
    # licence of a model (display label; the data value stays machine-readable)
    "detail.license": ("Modelllizenz", "Model licence"),
    "license.cc-by-nc-4.0": ("CC BY-NC 4.0", "CC BY-NC 4.0"),
    "license.non-commercial": ("Non-Commercial", "Non-commercial"),
    "license.commercial-api": ("kommerziell (API)", "commercial (API)"),
    # provenance of an entry
    "detail.source": ("Herkunft", "Source"),
    "source.vago": ("Messung VAGO Solutions", "measured by VAGO Solutions"),
    "source.submission": ("Einreichung per Pull Request (Benchmark-Skript)", "submitted via pull request (benchmark script)"),
    "source.mteb": ("öffentlich berichteter MTEB-Wert", "publicly reported MTEB score"),
    "detail.protocol": ("Protokoll v{v}", "protocol v{v}"),
    "detail.revision": ("Revision {rev}", "revision {rev}"),
    "detail.contamination": ("mit Trainingsdaten von {ds} trainiert", "trained on training data of {ds}"),
    # submission (GitHub pull request, as in MTEB)
    "contrib.title": ("Ergebnisse einreichen", "Submit results"),
    "contrib.sub": ("Per Pull Request auf GitHub – nach dem Merge erscheint das Modell in der Rangliste.",
                    "Via pull request on GitHub – once merged, the model appears on the leaderboard."),
    "contrib.how": ("So geht's", "How it works"),
    "contrib.step1": ("{n}. Repository auf GitHub forken.", "{n}. Fork the repository on GitHub."),
    "contrib.step2": ("{n}. Das Benchmark-Skript (benchmark/run_benchmark.py) mit eurem Modell laufen lassen – es misst alle öffentlichen Benchmarks im festen Protokoll und schreibt die Ergebnisdatei.",
                      "{n}. Run the benchmark script (benchmark/run_benchmark.py) on your model – it measures all public benchmarks with the fixed protocol and writes the result file."),
    "contrib.step3": ("{n}. Die erzeugte Datei results/<organisation>__<modell>.json unverändert committen (Modell öffentlich auf Hugging Face, Revision angegeben).",
                      "{n}. Commit the generated file results/<organisation>__<model>.json unchanged (model public on Hugging Face, revision given)."),
    "contrib.step4": ("{n}. Pull Request öffnen. Die automatische Prüfung validiert die Datei; nach der Durchsicht durch die Maintainer wird gemergt.",
                      "{n}. Open a pull request. An automatic check validates the file; after review by the maintainers it is merged."),
    "contrib.cmd_title": ("Benchmark-Skript", "Benchmark script"),
    "contrib.cmd_hint": ("Prompts/Instruktionen laut Modellkarte über --query-prompt/--doc-prompt bzw. --prompt-format angeben. Alle Optionen: benchmark/README.md.",
                         "Pass prompts/instructions as in your model card via --query-prompt/--doc-prompt or --prompt-format. All options: benchmark/README.md."),
    "contrib.review_title": ("Was die Maintainer prüfen", "What maintainers check"),
    "contrib.review": ("Skript- und Protokollversion, öffentliches Modell mit fester Revision, Anzahl Queries/Dokumente je Benchmark, plausible Werte (Stichprobe wird nachgemessen) und die Angabe, ob Trainingsdaten der Benchmarks verwendet wurden.",
                       "Script and protocol version, a public model at a fixed revision, query/document counts per benchmark, plausible scores (spot checks are re-measured) and the declaration whether benchmark training data was used."),
    "contrib.olr": ("OpenLegalRetrieval-DE (Lizenz ODbL 1.0) lädt das Skript von Hugging Face. Ist der Datensatz nicht erreichbar, wird er übersprungen und VAGO Solutions misst den Wert für eingereichte Modelle nach.",
                    "The script loads OpenLegalRetrieval-DE (licence ODbL 1.0) from Hugging Face. If the dataset cannot be loaded, it is skipped and VAGO Solutions measures the score for submitted models."),
    "contrib.open_guide": ("Anleitung (CONTRIBUTING)", "Guide (CONTRIBUTING)"),
    "contrib.open_script": ("Benchmark-Skript", "Benchmark script"),
    # custom datasets
    "custom.title": ("Eigene Datensätze evaluieren (NanoBEIR)", "Evaluate your own datasets (NanoBEIR)"),
    "custom.lead": ("Eigene deutsche juristische Retrieval-Datensätze im NanoBEIR-Format (corpus, queries, qrels) mit nDCG@10 evaluieren – höchstens {n} Dokumente im Korpus.",
                    "Evaluate your own German legal retrieval datasets in NanoBEIR format (corpus, queries, qrels) with nDCG@10 – at most {n} documents in the corpus."),
    "custom.load_sample": ("NanoBEIR-Beispiel laden", "Load NanoBEIR sample"),
    "custom.download_sample": ("Beispiel-JSON herunterladen", "Download sample JSON"),
    "custom.badge_format": ("Format: NanoBEIR (corpus, queries, qrels)", "Format: NanoBEIR (corpus, queries, qrels)"),
    "custom.badge_metric": ("Hauptmetrik: nDCG@10", "Main metric: nDCG@10"),
    "custom.badge_limit": ("Korpus: max. {n} Dokumente", "Corpus: max. {n} documents"),
    "custom.engine": ("Engine: sentence-transformers v{v} ({mode} · {device})", "Engine: sentence-transformers v{v} ({mode} · {device})"),
    "custom.engine_mv": ("Multi-Vector & Dense aktiv", "multi-vector & dense active"),
    "custom.engine_dense": ("SentenceTransformer aktiv", "SentenceTransformer active"),
    "custom.engine_missing": ("Engine: sentence-transformers ≥ 6 (vorinstalliert) · nur freigegebene Modelle · feste Batchgröße",
                              "Engine: sentence-transformers ≥ 6 (preinstalled) · approved models only · fixed batch size"),
    "custom.step1": ("1. Modell & Evaluator", "1. Model & evaluator"),
    "custom.model_select": ("Modell (freigegebene Auswahl)", "Model (approved list)"),
    "custom.precision": ("Präzision", "Precision"),
    "custom.step2": ("2. NanoBEIR-Datensatz hochladen oder bearbeiten (max. {n} Dokumente)", "2. Upload or edit a NanoBEIR dataset (max. {n} documents)"),
    "custom.name_label": ("Name des Datensatzes", "Dataset name"),
    "custom.name_placeholder": ("z. B. Mein-BGH-Mietrecht-NanoBEIR", "e.g. My-BGH-Tenancy-NanoBEIR"),
    "custom.tab_combined": ("Kombinierte NanoBEIR-JSON", "Combined NanoBEIR JSON"),
    "custom.tab_split": ("Einzeldateien (corpus / queries / qrels)", "Separate files (corpus / queries / qrels)"),
    "custom.upload_combined": ("Kombinierte NanoBEIR-JSON hochladen (.json)", "Upload combined NanoBEIR JSON (.json)"),
    "custom.structure_html": ("<strong>Erwartete Struktur (NanoBEIR):</strong><br>• <code>corpus</code>: Liste aus <code>{{\"_id\", \"title\", \"text\"}}</code> (<strong>max. {n} Dokumente</strong>)<br>• <code>queries</code>: Liste aus <code>{{\"_id\", \"text\"}}</code><br>• <code>qrels</code>: Liste aus <code>{{\"query-id\", \"corpus-id\", \"score\"}}</code>",
                              "<strong>Expected structure (NanoBEIR):</strong><br>• <code>corpus</code>: list of <code>{{\"_id\", \"title\", \"text\"}}</code> (<strong>max. {n} documents</strong>)<br>• <code>queries</code>: list of <code>{{\"_id\", \"text\"}}</code><br>• <code>qrels</code>: list of <code>{{\"query-id\", \"corpus-id\", \"score\"}}</code>"),
    "custom.editor_label": ("NanoBEIR-JSON (corpus, queries, qrels)", "NanoBEIR JSON (corpus, queries, qrels)"),
    "custom.split_hint": ("Die drei Teile einzeln hochladen (.json, .jsonl, .csv oder .tsv) oder direkt einfügen:", "Upload the three parts separately (.json, .jsonl, .csv or .tsv) or paste them directly:"),
    "custom.upload_corpus": ("1. Corpus hochladen (max. {n} Dok.)", "1. Upload corpus (max. {n} docs)"),
    "custom.upload_queries": ("2. Queries hochladen", "2. Upload queries"),
    "custom.upload_qrels": ("3. Qrels hochladen", "3. Upload qrels"),
    "custom.split_error": ("Fehler beim Lesen der Einzeldateien: {err}", "Could not parse the separate files: {err}"),
    "custom.run": ("Evaluation starten (nDCG@10)", "Run evaluation (nDCG@10)"),
    "custom.valid": ("Gültiger NanoBEIR-Datensatz: {docs}/{max} Dokumente, {q} Queries, {rel} positive Qrels.", "Valid NanoBEIR dataset: {docs}/{max} documents, {q} queries, {rel} positive qrels."),
    "custom.stat_corpus": ("Korpus: {n} / {max} Dok.", "Corpus: {n} / {max} docs"),
    "custom.need_dataset": ("Bitte zuerst einen gültigen NanoBEIR-Datensatz (max. {n} Dokumente) eingeben.", "Please enter a valid NanoBEIR dataset (max. {n} documents) first."),
    "custom.done": ("Evaluation abgeschlossen: nDCG@10 = {v}", "Evaluation finished: nDCG@10 = {v}"),
    "custom.error": ("Fehler bei der Evaluation: {err}", "Evaluation failed: {err}"),
    "custom.result_title": ("Ergebnis: {name}", "Result: {name}"),
    "custom.result_meta": ("Modell: {model} · Modus: {enc} ({prec}) · Zeit: {s} s", "Model: {model} · mode: {enc} ({prec}) · time: {s} s"),
    "custom.kpi_ndcg": ("nDCG@10 (Hauptmetrik)", "nDCG@10 (main metric)"),
    "custom.kpi_scope": ("Umfang", "Scope"),
    "custom.per_query": ("Ergebnisse je Suchanfrage", "Results per query"),
    "custom.col_query": ("Query-Text", "Query text"),
    "custom.col_top1": ("Top-1-Treffer", "Top-1 hit"),
    # service messages
    "msg.json_invalid": ("Ungültiges JSON-Format: {err}", "Invalid JSON: {err}"),
    "msg.schema_invalid": ("Validierungsfehler im Schema: {err}", "Schema validation error: {err}"),
    "msg.root_object": ("Das JSON muss ein Objekt mit 'corpus', 'queries' und 'qrels' sein.", "The JSON must be an object with 'corpus', 'queries' and 'qrels'."),
    "msg.corpus_limit": ("Limit überschritten: {n} Dokumente, erlaubt sind höchstens {max} Dokumente.", "Limit exceeded: {n} documents, at most {max} documents are allowed."),
    "msg.corpus_max": ("Der Datensatz darf höchstens {max} Dokumente enthalten.", "The dataset may contain at most {max} documents."),
    "msg.nanobeir_invalid": ("Validierungsfehler im NanoBEIR-Schema: {err}", "NanoBEIR schema validation error: {err}"),
    "msg.dataset_valid": ("Datensatz gültig.", "Dataset valid."),
    "msg.qrels_none": ("Keine gültigen Qrels: jede Relevanzangabe muss auf eine vorhandene query-id und corpus-id mit score > 0 verweisen.",
                       "No valid qrels: every judgement must reference an existing query-id and corpus-id with score > 0."),
    "msg.model_not_allowed": ("Dieses Modell ist für die Live-Evaluation nicht freigegeben. Erlaubt sind: {models}", "This model is not approved for live evaluation. Allowed: {models}"),
    "msg.too_many_queries": ("Höchstens {max} Queries je Evaluation (aktuell: {n}).", "At most {max} queries per evaluation (currently: {n})."),
    "msg.text_too_long": ("Texte über {max} Zeichen: {ids}", "Texts longer than {max} characters: {ids}"),
    "msg.eval_busy": ("Gerade läuft eine andere Evaluation. Bitte in einigen Minuten erneut versuchen.", "Another evaluation is running. Please try again in a few minutes."),
    "msg.deps_missing": ("Für die Live-Evaluation müssen 'torch' und 'sentence-transformers>=6.0.0' installiert sein (requirements.txt bzw. Docker-Image). Details: {err}",
                         "Live evaluation needs 'torch' and 'sentence-transformers>=6.0.0' (requirements.txt or Docker image). Details: {err}"),
    "msg.mv_unsupported": ("Die installierte sentence-transformers-Version ({v}) unterstützt keinen MultiVectorEncoder (benötigt ≥ 6.0.0, siehe requirements.txt).",
                           "The installed sentence-transformers version ({v}) has no MultiVectorEncoder (needs ≥ 6.0.0, see requirements.txt)."),
    "msg.file_loaded": ("Datei „{name}“ geladen.", "File “{name}” loaded."),
    "msg.part_loaded": ("{what} „{name}“ geladen.", "{what} “{name}” loaded."),
    "msg.file_error": ("Fehler beim Lesen der Datei: {err}", "Could not read the file: {err}"),
    # footer
    "footer.about": ("Offenes Benchmark-System zur Leistungsanalyse von Embedding-Modellen für das deutsche Recht.",
                     "Open benchmark system for analysing embedding models on German law."),
    "footer.benchmarks": ("Benchmarks", "Benchmarks"),
    "footer.org": ("Organisation", "Organisation"),
    "footer.standard": ("Metrik: nDCG@10 (MTEB-Standard)", "Metric: nDCG@10 (MTEB standard)"),
    "footer.copyright": ("© 2026 German Legal Embedding Benchmark · VAGO Solutions", "© 2026 German Legal Embedding Benchmark · VAGO Solutions"),
    "footer.tagline": ("Für deutsche Gerichtsentscheidungen und Gesetze", "Built for German court decisions and statutes"),
}

# display labels for data values (the data stays unchanged, only the label is translated)
MODEL_TYPE = {"open": "type.open", "proprietary": "type.prop"}
EMBEDDING_TYPE = {"Dense": ("Dense", "Dense"), "Late-Interaction": ("Late-Interaction", "Late interaction"),
                  "Hybrid": ("Hybrid", "Hybrid"), "MoE": ("MoE", "MoE"), "BM25": ("BM25", "BM25")}
DS_ABBR = {"overall": "Overall", "legalquad": "LQuAD", "gerdalir_small": "GDS", "gerlayqa": "GLQ", "gerlerb": "GerLeRB",
           "openlegalretrieval_de": "OLR"}


def t(lang: str, key: str, **kw: Any) -> str:
    de, en = TEXTS[key]
    s = en if norm_lang(lang) == "en" else de
    return s.format(**kw) if kw else s


def ds_text(lang: str, key: str, field: str) -> str:
    """Dataset texts from config.DATASETS_INFO; description is bilingual."""
    info = config.DATASETS_INFO.get(key, {})
    if field == "short":
        return info.get("short_name", key)
    val = info.get(field, key)
    if isinstance(val, dict):
        return val.get(norm_lang(lang), val.get("de", ""))
    return str(val)


def ds_abbr(key: str) -> str:
    return DS_ABBR.get(key, key)


def model_type_label(lang: str, value: Optional[str]) -> str:
    k = MODEL_TYPE.get(value or "")
    return t(lang, k) if k else (value or "")


def embedding_type_label(lang: str, value: Optional[str]) -> str:
    pair = EMBEDDING_TYPE.get(value or "")
    return (pair[1] if norm_lang(lang) == "en" else pair[0]) if pair else (value or "")


def task_label(lang: str, key: str, long: bool = False) -> str:
    info = config.OLR_TASKS[key]
    text = info["en"] if norm_lang(lang) == "en" else info["de"]
    return f"{info['short']}: {text}" if long else info["short"]


def license_label(lang: str, value: Optional[str]) -> str:
    """Known licence values are translated, anything else (e.g. an SPDX identifier) is shown as is; unknown = '–'."""
    if not value:
        return "–"
    key = f"license.{value}"
    return t(lang, key) if key in TEXTS else value


def notes_for(item: Dict[str, Any]) -> Optional[str]:
    """Notes of a result entry (stored in English only)."""
    return item.get("notes")
