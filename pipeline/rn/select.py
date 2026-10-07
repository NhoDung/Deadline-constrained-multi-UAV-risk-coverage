"""Chọn ảnh RescueNet phân tầng theo mức hư hại (docs/phase2-rescuenet-thiet-ke.md mục 4)."""

import random

TIERS = ("low", "mid", "high")


def select_images(stats: list, n_per_tier: int, min_cells: int, seed: int) -> list:
    """Lọc ảnh đủ ô điểm > 0, chia 3 tầng theo tỉ lệ hư hại, bốc ngẫu nhiên có seed.

    Tầng chia theo tam phân vị của `damage_frac` trong số ảnh đủ điều kiện
    (tập validation không có nhãn phân loại ảnh 0/1/2 chính thức).
    """
    eligible = [s for s in stats if s["nonzero_cells"] >= min_cells]
    eligible.sort(key=lambda s: (s["damage_frac"], s["id"]))
    third = len(eligible) // 3
    tiers = [eligible[:third], eligible[third : 2 * third], eligible[2 * third :]]
    rng = random.Random(seed)
    chosen = []
    for name, tier in zip(TIERS, tiers):
        picked = rng.sample(tier, min(n_per_tier, len(tier)))
        chosen += [{**s, "tier": name} for s in sorted(picked, key=lambda s: s["id"])]
    return chosen
