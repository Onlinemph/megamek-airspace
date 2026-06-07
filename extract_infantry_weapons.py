#!/usr/bin/env python3
"""Extract infantry-scale weapon stats from MegaMek Java weapon class files into a CSV."""

import csv
import os
import re
import sys


INFANTRY_DIR = os.path.join(
    os.path.dirname(__file__),
    "megamek/src/megamek/common/weapons/infantry"
)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "megamek_infantry_weapons.csv")

FIELDS = [
    "className", "subCategory",
    "name", "internalName",
    "infantryDamage", "infantryRange",
    "shots", "bursts", "crew", "ammoType",
    "tonnage", "bv", "cost",
    "rulesRefs", "techBase", "techRating", "isIntroYear", "clanIntroYear",
]


def extract_string(pattern, text):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


def extract_num(field, text):
    m = re.search(rf'\b{field}\s*=\s*(-?[\d.]+)\s*;', text)
    return m.group(1) if m else ""


def extract_weapon(filepath):
    with open(filepath, encoding="utf-8", errors="replace") as f:
        src = f.read()

    if 'name = "' not in src or "InfantryWeapon" not in src:
        return None

    record = {k: "" for k in FIELDS}

    cls_m = re.search(r'public\s+(?:(?:abstract|final)\s+)*class\s+(\w+)', src)
    record["className"] = cls_m.group(1) if cls_m else os.path.splitext(os.path.basename(filepath))[0]

    # sub-category from path under infantry/ (e.g. laser/rifle, smg, archaic ...)
    rel = os.path.relpath(filepath, INFANTRY_DIR)
    parts = rel.replace("\\", "/").split("/")
    record["subCategory"] = "/".join(parts[:-1]) if len(parts) > 1 else ""

    record["name"] = extract_string(r'name\s*=\s*"([^"]+)"', src)
    in_m = re.search(r'setInternalName\s*\(\s*"([^"]+)"', src)
    record["internalName"] = in_m.group(1) if in_m else record["name"]
    record["rulesRefs"] = extract_string(r'rulesRefs\s*=\s*"([^"]+)"', src)

    for field in ["infantryDamage", "infantryRange", "shots", "bursts", "crew",
                  "tonnage", "bv", "cost"]:
        record[field] = extract_num(field, src)

    am_m = re.search(r'ammoType\s*=\s*AmmoType\.AmmoTypeEnum\.(\w+)', src)
    record["ammoType"] = am_m.group(1) if am_m else ""

    tb_m = re.search(r'\.setTechBase\s*\(\s*TechBase\.(\w+)\s*\)', src)
    record["techBase"] = tb_m.group(1) if tb_m else ""

    tr_m = re.search(r'\.setTechRating\s*\(\s*TechRating\.(\w+)\s*\)', src)
    record["techRating"] = tr_m.group(1) if tr_m else ""

    is_m = re.search(r'setISAdvancement\s*\(\s*(\d+)', src)
    record["isIntroYear"] = is_m.group(1) if is_m else ""

    cl_m = re.search(r'setClanAdvancement\s*\(\s*(\d+)', src)
    record["clanIntroYear"] = cl_m.group(1) if cl_m else ""

    return record


def main():
    records = []
    for dirpath, _, filenames in os.walk(INFANTRY_DIR):
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

    records.sort(key=lambda r: (r["subCategory"], r["name"]))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} infantry weapons to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
