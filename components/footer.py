# pyrefly: ignore [missing-import]
from nicegui import ui
import config
from i18n import t


def render_footer(lang: str):
    """Footer: brand, benchmarks, organisation."""
    L = lang
    with ui.column().classes("w-full py-10 px-4 mt-16").style("background: #07030f; border-top: 1px solid rgba(255,255,255,0.08);"):
        with ui.column().classes("w-full max-w-7xl mx-auto gap-6"):
            ui.element("div").classes("ci-band")
            with ui.row().classes("w-full justify-between items-start flex-wrap gap-8"):
                with ui.column().classes("gap-3 max-w-sm"):
                    with ui.row().classes("brand-row items-center gap-3 flex-nowrap"):
                        ui.html('<img class="sk-logo" src="/static/sauerkrautlm-logo.svg" alt="SauerkrautLM" style="height:38px">')
                        ui.label(t(L, "brand.by")).classes("brand-by")
                        ui.html('<img class="vago-logo" src="/static/vago-solutions-white.svg" alt="VAGO Solutions" style="height:22px">')
                    ui.label("German Legal Embedding Benchmark").classes("font-bold")
                    ui.label(t(L, "footer.about")).classes("text-xs leading-relaxed ci-muted")

                with ui.column().classes("gap-1"):
                    ui.label(t(L, "footer.benchmarks")).classes("ci-kicker mb-1")
                    for k in ("legalquad", "gerdalir_small", "gerlayqa", "gerlerb"):
                        info = config.DATASETS_INFO[k]
                        ui.link(f"{info['short_name']} ↗", info["url"], new_tab=True).classes("text-xs ci-muted hover:text-white")
                    ui.label(f"OpenLegalRetrieval-DE · {t(L, 'olr.license')}").classes("text-xs ci-faint")

                with ui.column().classes("gap-1"):
                    ui.label(t(L, "footer.org")).classes("ci-kicker mb-1")
                    ui.link("VAGO Solutions ↗", "https://www.vago-solutions.ai", new_tab=True).classes("text-xs ci-muted hover:text-white")
                    ui.link("Hugging Face: VAGOsolutions ↗", "https://huggingface.co/VAGOsolutions", new_tab=True).classes("text-xs ci-muted hover:text-white")
                    ui.label(t(L, "footer.standard")).classes("text-xs ci-faint mt-1")

            with ui.row().classes("w-full justify-between items-center text-xs ci-faint flex-wrap gap-2"):
                ui.label(t(L, "footer.copyright"))
                ui.label(t(L, "footer.tagline"))
