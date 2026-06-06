#!/usr/bin/env python3
"""Extract weapon stats from MegaMek Java weapon class files into a CSV."""

import csv
import os
import re
import sys


WEAPONS_DIR = os.path.join(
    os.path.dirname(__file__),
    "megamek/src/megamek/common/weapons"
)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "megamek_weapons.csv")

FIELDS = [
    "className", "javaPackage", "category",
    "name", "internalName", "sortingName",
    "heat", "damage", "rackSize", "minimumRange",
    "shortRange", "mediumRange", "longRange", "extremeRange",
    "waterShortRange", "waterMediumRange", "waterLongRange", "waterExtremeRange",
    "tonnage", "criticalSlots", "bv", "cost",
    "shortAV", "medAV", "longAV", "extAV", "maxRange",
    "explosionDamage", "rulesRefs",
    "techBase", "techRating",
    "isIntroYear", "clanIntroYear",
]

RANGE_MAP = {
    "RANGE_SHORT": "Short",
    "RANGE_MED": "Medium",
    "RANGE_LONG": "Long",
    "RANGE_EXT": "Extreme",
    "RANGE_MAX": "Max",
}


def extract_string(pattern, text):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


def extract_num(field, text):
    m = re.search(rf'\b{field}\s*=\s*(-?[\d.]+)\s*;', text)
    return m.group(1) if m else ""


def extract_weapon(filepath):
    with open(filepath, encoding="utf-8", errors="replace") as f:
        src = f.read()

    # Only process files that set a weapon name
    if 'name = "' not in src:
        return None

    record = {k: "" for k in FIELDS}

    # Class and package info
    pkg_m = re.search(r'^package\s+([\w.]+)\s*;', src, re.MULTILINE)
    record["javaPackage"] = pkg_m.group(1) if pkg_m else ""

    cls_m = re.search(r'public\s+(?:(?:abstract|final)\s+)*class\s+(\w+)', src)
    record["className"] = cls_m.group(1) if cls_m else os.path.splitext(os.path.basename(filepath))[0]

    # Derive category from directory path relative to weapons/
    rel = os.path.relpath(filepath, WEAPONS_DIR)
    parts = rel.replace("\\", "/").split("/")
    record["category"] = parts[0] if len(parts) > 1 else ""

    # String fields
    record["name"] = extract_string(r'name\s*=\s*"([^"]+)"', src)
    record["internalName"] = extract_string(r'setInternalName\s*\(\s*"([^"]+)"', src)
    record["sortingName"] = extract_string(r'sortingName\s*=\s*"([^"]+)"', src)
    record["rulesRefs"] = extract_string(r'rulesRefs\s*=\s*"([^"]+)"', src)

    # Numeric fields
    for field in ["heat", "damage", "rackSize", "minimumRange",
                  "shortRange", "mediumRange", "longRange", "extremeRange",
                  "waterShortRange", "waterMediumRange", "waterLongRange", "waterExtremeRange",
                  "tonnage", "criticalSlots", "bv", "cost",
                  "shortAV", "medAV", "longAV", "extAV", "explosionDamage"]:
        record[field] = extract_num(field, src)

    # maxRange constant
    mr_m = re.search(r'maxRange\s*=\s*(RANGE_\w+)\s*;', src)
    if mr_m:
        record["maxRange"] = RANGE_MAP.get(mr_m.group(1), mr_m.group(1))

    # TechBase
    tb_m = re.search(r'\.setTechBase\s*\(\s*TechBase\.(\w+)\s*\)', src)
    record["techBase"] = tb_m.group(1) if tb_m else ""

    # TechRating
    tr_m = re.search(r'\.setTechRating\s*\(\s*TechRating\.(\w+)\s*\)', src)
    record["techRating"] = tr_m.group(1) if tr_m else ""

    # IS intro year (first arg of setISAdvancement)
    is_m = re.search(r'setISAdvancement\s*\(\s*(\d+)', src)
    record["isIntroYear"] = is_m.group(1) if is_m else ""

    # Clan intro year (first arg of setClanAdvancement)
    cl_m = re.search(r'setClanAdvancement\s*\(\s*(\d+)', src)
    record["clanIntroYear"] = cl_m.group(1) if cl_m else ""

    return record


def main():
    records = []
    for dirpath, _, filenames in os.walk(WEAPONS_DIR):
        for fname in filenames:
            if not fname.endswith(".java"):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                rec = extract_weapon(fpath)
                if rec:
                    records.append(rec)
            except Exception as e:
                print(f"Warning: skipped {fpath}: {e}", file=sys.stderr)

    records.sort(key=lambda r: (r["category"], r["name"]))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} weapons to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
