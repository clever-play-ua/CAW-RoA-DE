"""
Same as CSW-RoA-PT/scripts/build_json_1_03.py, for deDE. See that file's
docstring for the full rationale (resolution order, why json+wts are
built from one shared per-key resolution pass).

deDE has no column in the VO CHARACTERS csv, so the speaker-name /
units table is built differently here: unit_id -> enUS name is scanned
out of all enUS per-mission/GLOBAL databases (every entry already
carries its own unit_id/unit_name), then paired by unit_id with
database/deDE/RoA_UNITS_deDE.json (flat unit_id -> deDE name table).
"""

import difflib
import hashlib
import json
import re
from pathlib import Path

TOOLKIT_ROOT = Path(r"C:\Users\UserM\Documents\GitHub\clever-play-ua.github.io\w3r-l10n-toolkit")
EN_WTS_DIR = Path(r"C:\Users\UserM\Documents\GitHub\CSW-RoA-PL\WTS_1_03\enUS")
WTS_OUT_DIR = Path(__file__).resolve().parent.parent / "WTS_1_03" / "deDE"
JSON_OUT_DIR = Path(__file__).resolve().parent.parent / "json_1_03"

BLOCK_RE = re.compile(r"(STRING (\d+)\s*\n(?://.*\n)?)\{\n([\s\S]*?)\n\}")
FUZZY_THRESHOLD = 0.90

CZ_UNITS_JSON = TOOLKIT_ROOT / "database" / "deDE" / "RoA_UNITS_deDE.json"
GLOBAL_EN_JSON = TOOLKIT_ROOT / "database" / "enUS" / "RoA_GLOBAL_EN.json"
GLOBAL_CZ_JSON = TOOLKIT_ROOT / "database" / "deDE" / "RoA_GLOBAL_deDE.json"
# Visible strings missing from the enUS database (map titles, factions,
# oil-system messages, credits headers): exact EN text -> deDE.
EXTRA = json.loads((TOOLKIT_ROOT / "database" / "deDE" / "RoA_EXTRA_deDE.json").read_text(encoding="utf-8"))

EN_JOB_FILES = [
    "RoA_A01_CNMC1_EN.json", "RoA_A01_M01_EN.json", "RoA_A01_M02_EN.json",
    "RoA_A01_M03_EN.json", "RoA_A01_M04_EN.json", "RoA_GLOBAL_EN.json",
]

JOBS = [
    ("CNMC1", "RoA_A01_CNMC1_EN.json", "RoA_A01_CNMC1_deDE.json", "RoA_A01_CNMC1_enUS_1_03.wts", True),
    ("M01", "RoA_A01_M01_EN.json", "RoA_A01_M01_deDE.json", "RoA_A01_M01_enUS_1_03.wts", True),
    ("M02", "RoA_A01_M02_EN.json", "RoA_A01_M02_deDE.json", "RoA_A01_M02_enUS_1_03.wts", True),
    ("M03", "RoA_A01_M03_EN.json", "RoA_A01_M03_deDE.json", "RoA_A01_M03_enUS_1_03.wts", True),
    ("M04", "RoA_A01_M04_EN.json", "RoA_A01_M04_deDE.json", "RoA_A01_M04_enUS_1_03.wts", True),
    ("GLOBAL", "RoA_GLOBAL_EN.json", "RoA_GLOBAL_deDE.json", "RoA_GLOBAL_enUS_1_03.wts", False),
]


def compute_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def load_wts_blocks(path):
    text = path.read_text(encoding="utf-8")
    return {m.group(2): m.group(3) for m in BLOCK_RE.finditer(text)}


def load_speaker_name_map():
    """unit_id -> enUS name, scanned from every enUS database file, paired
    by unit_id with the deDE name table."""
    en_names = {}
    for fname in EN_JOB_FILES:
        data = json.loads((TOOLKIT_ROOT / "database" / "enUS" / fname).read_text(encoding="utf-8"))["strings"]
        for entry in data.values():
            uid, name = entry.get("unit_id"), entry.get("unit_name")
            if uid and name:
                en_names.setdefault(uid, name)

    cz_units = json.loads(CZ_UNITS_JSON.read_text(encoding="utf-8"))

    out = {}
    for uid, cz_name in cz_units.items():
        en_name = en_names.get(uid)
        if en_name and cz_name and cz_name != en_name:
            out[en_name] = cz_name
    return out


def build_global_index():
    g_en = json.loads(GLOBAL_EN_JSON.read_text(encoding="utf-8"))["strings"]
    g_cz = json.loads(GLOBAL_CZ_JSON.read_text(encoding="utf-8"))
    by_hash = {}
    all_pairs = []
    for key, entry in g_en.items():
        cz = g_cz.get(key)
        if cz:
            by_hash.setdefault(compute_hash(entry["source"]), (entry["source"], cz))
            all_pairs.append((entry["source"], cz))
    return by_hash, all_pairs


def resolve(entry, loc_data, global_hash_index, global_pairs, speaker_name_map):
    text = entry["source"]

    direct = loc_data.get(entry["_key"])
    if direct:
        return direct

    hit = global_hash_index.get(entry.get("hash") or compute_hash(text))
    if hit:
        return hit[1]
    best_hit, best_score = None, FUZZY_THRESHOLD
    for g_source, g_cz in global_pairs:
        score = difflib.SequenceMatcher(None, text, g_source).ratio()
        if score > best_score:
            best_score, best_hit = score, g_cz
    if best_hit:
        return best_hit

    cz_name = speaker_name_map.get(text.strip())
    if cz_name and cz_name != text.strip():
        return cz_name

    return None


def build_one(label, en_json_name, cz_json_name, en_wts_name, use_global_fallback,
               global_hash_index, global_pairs, speaker_name_map):
    en_data = json.loads((TOOLKIT_ROOT / "database" / "enUS" / en_json_name).read_text(encoding="utf-8"))["strings"]
    loc_data = json.loads((TOOLKIT_ROOT / "database" / "deDE" / cz_json_name).read_text(encoding="utf-8"))
    en_wts_path = EN_WTS_DIR / en_wts_name
    src_text = en_wts_path.read_text(encoding="utf-8")
    en_blocks = load_wts_blocks(en_wts_path)

    hash_index = {}
    for num, text in en_blocks.items():
        hash_index.setdefault(compute_hash(text), []).append(num)

    pairs_json = {}
    num_to_translation = {}
    for key, entry in en_data.items():
        entry = dict(entry, _key=key)
        text = entry["source"]
        cz = resolve(entry, loc_data,
                     global_hash_index if use_global_fallback else {},
                     global_pairs if use_global_fallback else [],
                     speaker_name_map)
        if not cz:
            continue

        pairs_json[key] = {
            "type": entry.get("type", ""),
            "unit_id": entry.get("unit_id", ""),
            "unit_name": entry.get("unit_name", ""),
            "enUS": text,
            "deDE": cz,
        }

        nums = hash_index.get(entry.get("hash") or compute_hash(text))
        if nums is None:
            best_num, best_score = None, FUZZY_THRESHOLD
            for n, block_text in en_blocks.items():
                score = difflib.SequenceMatcher(None, text, block_text).ratio()
                if score > best_score:
                    best_score, best_num = score, n
            nums = [best_num] if best_num is not None else []
        for num in nums:
            num_to_translation[num] = cz

    for num, text in en_blocks.items():
        if num in num_to_translation:
            continue
        if text in EXTRA:
            num_to_translation[num] = EXTRA[text]
            continue
        hit = global_hash_index.get(compute_hash(text)) if use_global_fallback else None
        if hit:
            num_to_translation[num] = hit[1]
            continue
        name = speaker_name_map.get(text.strip())
        if name and name != text.strip():
            num_to_translation[num] = name

    def replace(m):
        header, num, body = m.group(1), m.group(2), m.group(3)
        if num in num_to_translation:
            return f"{header}{{\n{num_to_translation[num]}\n}}"
        return m.group(0)

    out_wts_text = BLOCK_RE.sub(replace, src_text)
    wts_out_path = WTS_OUT_DIR / en_wts_name.replace("enUS", "deDE")
    wts_out_path.parent.mkdir(parents=True, exist_ok=True)
    wts_out_path.write_text(out_wts_text, encoding="utf-8")

    json_out_path = JSON_OUT_DIR / f"RoA_A01_{label}_1_03.json" if label != "GLOBAL" else JSON_OUT_DIR / "RoA_GLOBAL_1_03.json"
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = dict(sorted(pairs_json.items()))
    json_out_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total_blocks = len(en_blocks)
    translated_blocks = sum(1 for n in en_blocks if n in num_to_translation)
    print(f"[{label}] {len(pairs_json)} pairs -> {json_out_path.name} | "
          f"{translated_blocks}/{total_blocks} STRING blocks -> {wts_out_path.name}")


def build_units_json(speaker_name_map):
    cz_units = json.loads(CZ_UNITS_JSON.read_text(encoding="utf-8"))
    en_names = {}
    for fname in EN_JOB_FILES:
        data = json.loads((TOOLKIT_ROOT / "database" / "enUS" / fname).read_text(encoding="utf-8"))["strings"]
        for entry in data.values():
            uid, name = entry.get("unit_id"), entry.get("unit_name")
            if uid and name:
                en_names.setdefault(uid, name)

    out = {}
    for uid, cz_name in cz_units.items():
        en_name = en_names.get(uid)
        if en_name and cz_name:
            out[uid] = {"enUS": en_name, "deDE": cz_name}

    out_path = JSON_OUT_DIR / "RoA_UNITS_1_03.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[UNITS] {len(out)} pairs -> {out_path.name}")


def main():
    global_hash_index, global_pairs = build_global_index()
    speaker_name_map = load_speaker_name_map()

    for label, en_json, cz_json, en_wts, use_global_fallback in JOBS:
        build_one(label, en_json, cz_json, en_wts, use_global_fallback, global_hash_index, global_pairs, speaker_name_map)

    build_units_json(speaker_name_map)


if __name__ == "__main__":
    main()
