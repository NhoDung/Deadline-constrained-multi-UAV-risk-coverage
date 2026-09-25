"""Chuyển đổi file raw OR-Library (chiều ô→gói, 1-indexed) thành input
cho thuật toán (chiều gói→ô, 0-indexed), lưu dưới dạng JSON.

Xem giải thích chi tiết ở docs/mo-hinh-du-lieu.md.

Chạy: python scripts/convert_to_input.py
"""

import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "OR-Library"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def parse_raw(text: str) -> dict:
    numbers = iter(int(tok) for tok in text.split())

    m = next(numbers)
    n = next(numbers)
    costs = [next(numbers) for _ in range(n)]

    sets = [[] for _ in range(n)]
    for cell in range(m):
        count = next(numbers)
        for _ in range(count):
            package_1indexed = next(numbers)
            sets[package_1indexed - 1].append(cell)

    return {"m": m, "n": n, "costs": costs, "sets": sets}


def validate(instance: dict, name: str) -> list:
    problems = []

    if len(instance["costs"]) != instance["n"]:
        problems.append(
            f"số chi phí ({len(instance['costs'])}) khác n ({instance['n']})"
        )

    covered = set()
    for cell_list in instance["sets"]:
        covered.update(cell_list)
    missing = set(range(instance["m"])) - covered
    if missing:
        problems.append(f"{len(missing)} ô không được gói nào phủ: {sorted(missing)[:5]}...")

    return problems


def convert_one(raw_path: Path) -> str:
    name = raw_path.stem
    dest = OUTPUT_DIR / f"{name}.json"

    if dest.exists():
        print(f"[skip] {name}.json đã có")
        return "skip"

    instance = parse_raw(raw_path.read_text())
    instance["instance"] = name

    problems = validate(instance, name)
    if problems:
        print(f"[warn] {name}: {'; '.join(problems)}")

    dest.write_text(json.dumps(instance))
    print(f"[ok] {name}.json")
    return "ok"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("*.txt"))
    results = [convert_one(f) for f in raw_files]

    ok = results.count("ok")
    skip = results.count("skip")
    print(f"\nTổng kết: {ok} chuyển đổi mới, {skip} đã có sẵn (trên {len(raw_files)} file raw).")


if __name__ == "__main__":
    main()
