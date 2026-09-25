"""Tải 45 file benchmark OR-Library (Set Covering) dùng cho Pha 1.

Chạy: python scripts/download_orlib.py
"""

import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

INSTANCE_NAMES = (
    [f"scp4{i}" for i in range(1, 11)]
    + [f"scp5{i}" for i in range(1, 11)]
    + [f"scp6{i}" for i in range(1, 6)]
    + [f"scpa{i}" for i in range(1, 6)]
    + [f"scpb{i}" for i in range(1, 6)]
    + [f"scpc{i}" for i in range(1, 6)]
    + [f"scpd{i}" for i in range(1, 6)]
)


def download_one(name: str) -> str:
    filename = f"{name}.txt"
    dest = OUTPUT_DIR / filename

    if dest.exists():
        print(f"[skip] {filename} đã có")
        return "skip"

    url = BASE_URL + filename
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[error] {filename}: {e}")
        return "error"

    dest.write_bytes(content)
    print(f"[ok] {filename}")
    return "ok"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = [download_one(name) for name in INSTANCE_NAMES]

    ok = results.count("ok")
    skip = results.count("skip")
    error = results.count("error")
    print(f"\nTổng kết: {ok} tải mới, {skip} đã có sẵn, {error} lỗi (trên {len(INSTANCE_NAMES)} file).")


if __name__ == "__main__":
    main()
