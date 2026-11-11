"""Bilingual UI: every key has de+en, every key used in the code exists, placeholders match."""
import re
import string
from pathlib import Path
import config
import i18n

ROOT = Path(config.BASE_DIR)


def test_every_key_has_both_languages():
    for k, v in i18n.TEXTS.items():
        assert isinstance(v, tuple) and len(v) == 2, k
        assert v[0].strip() and v[1].strip(), k


def test_placeholders_match():
    fmt = string.Formatter()
    for k, (de, en) in i18n.TEXTS.items():
        f_de = {f for _, f, _, _ in fmt.parse(de) if f}
        f_en = {f for _, f, _, _ in fmt.parse(en) if f}
        assert f_de == f_en, k


def test_all_used_keys_exist():
    pattern = re.compile(r"""\bt\(\s*(?:L|lang|self\.lang)\s*,\s*["']([a-z0-9_]+(?:\.[a-z0-9_]+)+)["']""")
    js = re.compile(r"""\bjs\(\s*["']([a-z0-9_.]+)["']""")
    loose = re.compile(r"""["']((?:view|chart|lang)\.[a-z_]+)["']""")
    found = set()
    for p in list((ROOT / "components").glob("*.py")) + list((ROOT / "services").glob("*.py")) + [ROOT / "main.py"]:
        src = p.read_text(encoding="utf-8")
        found |= set(pattern.findall(src)) | set(js.findall(src))
        found |= set(loose.findall(src))
    missing = sorted(k for k in found if k not in i18n.TEXTS)
    assert not missing, missing
    assert len(found) > 150


def test_dataset_texts_bilingual():
    for k, info in config.DATASETS_INFO.items():
        d = info["description"]
        assert isinstance(d, dict) and d["de"] and d["en"], k
    for k, info in config.OLR_TASKS.items():
        assert info["de"] and info["en"] and info["short"], k


def test_norm_lang_and_t():
    assert i18n.norm_lang("EN") == "en" and i18n.norm_lang("fr") == "de" and i18n.norm_lang(None) == "de"
    assert i18n.t("en", "filter.count", shown=1, total=2) == "1 of 2 models"
    assert i18n.model_type_label("en", "open") == "Open weights"
    assert i18n.model_type_label("de", "proprietary") == "Proprietär"
