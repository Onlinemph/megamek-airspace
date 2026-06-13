#!/usr/bin/env python3
"""Extract warship-scale weapon stats (capital + sub-capital) from MegaMek Java files."""

import csv
import os
import re


WEAPONS_BASE = "/home/user/megamek-airspace/megamek/src/megamek/common/weapons"
DIRS = [
    os.path.join(WEAPONS_BASE, "capitalWeapons"),
    os.path.join(WEAPONS_BASE, "subCapitalWeapons"),
]
OUTPUT_FILE = "/home/user/megamek-airspace/megamek_warship_weapons.csv"

FIELDS = [
    "className", "category", "subCategory",
    "name", "internalName",
    "heat", "damage", "ammoType",
    "minimumRange", "shortRange", "mediumRange", "longRange", "extremeRange",
    "tonnage", "bv", "cost",
    "shortAV", "medAV", "longAV", "extAV", "maxRange",
    "rulesRefs", "techBase", "techRating", "isIntroYear", "clanIntroYear",
]

RANGE_MAP = {
    "RANGE_SHORT": "Short",
    "RANGE_MED": "Medium",
    "RANGE_LONG": "Long",
    "RANGE_EXT": "Extreme",
}


def extract_string(pattern, text):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


def extract_num(field, text):
    m = re.search(rf'\b{field}\s*=\s*(-?[\d.]+)\s*;', text)
    return m.group(1) if m else ""


def extract_weapon(filepath, base_dir):
    with open(filepath, encoding="utf-8", errors="replace") as f:
        src = f.read()

    if 'name = "' not in src and "this.name" not in src:
        return None

    record = {k: "" for k in FIELDS}

    cls_m = re.search(r'public\s+(?:(?:abstract|final)\s+)*class\s+(\w+)', src)
    record["className"] = cls_m.group(1) if cls_m else os.path.splitext(os.path.basename(filepath))[0]

    rel = os.path.relpath(filepath, WEAPONS_BASE)
    parts = rel.replace("\\", "/").split("/")
    record["category"] = parts[0]
    record["subCategory"] = "/".join(parts[1:-1]) if len(parts) > 2 else ""

    record["name"] = extract_string(r'(?:this\.)?name\s*=\s*"([^"]+)"', src)
    if not record["name"]:
        return None

    in_m = re.search(r'setInternalName\s*\(\s*(?:this\.name|"([^"]+)")', src)
    record["internalName"] = in_m.group(1) if (in_m and in_m.group(1)) else record["name"]

    record["rulesRefs"] = extract_string(r'rulesRefs\s*=\s*"([^"]+)"', src)

    for field in ["heat", "damage", "minimumRange", "shortRange", "mediumRange",
                  "longRange", "extremeRange", "tonnage", "bv", "cost",
                  "shortAV", "medAV", "longAV", "extAV"]:
        record[field] = extract_num(field, src)

    am_m = re.search(r'ammoType\s*=\s*AmmoType\.AmmoTypeEnum\.(\w+)', src)
    record["ammoType"] = am_m.group(1) if am_m else ""

    mr_m = re.search(r'maxRange\s*=\s*(RANGE_\w+)\s*;', src)
    record["maxRange"] = RANGE_MAP.get(mr_m.group(1), mr_m.group(1)) if mr_m else ""

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
    for base_dir in DIRS:
        for dirpath, _, filenames in os.walk(base_dir):
            for fname in filenames:
                if not fname.endswith(".java"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    rec = extract_weapon(fpath, base_dir)
                    if rec:
                        records.append(rec)
                except Exception as e:
                    print(f"Warning: skipped {fpath}: {e}")

    # Skip abstract base classes (no damage/AV values and name looks generic)
    records = [r for r in records if r["shortAV"] or r["medAV"] or r["longAV"] or r["heat"]]

    records.sort(key=lambda r: (r["category"], r["subCategory"], r["name"]))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} warship weapons to {OUTPUT_FILE}")
    for r in records:
        print(f"  {r['category']}/{r['subCategory']} | {r['name']} | heat={r['heat']} dmg={r['damage']} tons={r['tonnage']} bv={r['bv']} shortAV={r['shortAV']} medAV={r['medAV']} longAV={r['longAV']} extAV={r['extAV']}")


if __name__ == "__main__":
    main()
