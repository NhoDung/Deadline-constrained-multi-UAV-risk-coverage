from pipeline.rn.select import select_images


def make(i, damage, cells=100):
    return {"id": f"{i:05d}", "damage_frac": damage, "nonzero_cells": cells}


def test_filters_images_with_too_few_nonzero_cells():
    stats = [make(i, i / 100, 100 if i % 2 else 10) for i in range(30)]
    out = select_images(stats, n_per_tier=2, min_cells=60, seed=1)
    assert out and all(s["nonzero_cells"] >= 60 for s in out)


def test_stratifies_into_three_equal_tiers_ordered_by_damage():
    stats = [make(i, i / 100) for i in range(60)]
    out = select_images(stats, n_per_tier=5, min_cells=60, seed=1)
    by_tier = {t: [s["damage_frac"] for s in out if s["tier"] == t] for t in ("low", "mid", "high")}
    assert [len(v) for v in by_tier.values()] == [5, 5, 5]
    assert max(by_tier["low"]) < min(by_tier["mid"]) <= max(by_tier["mid"]) < min(by_tier["high"])


def test_same_seed_same_selection_different_seed_differs():
    stats = [make(i, i / 100) for i in range(60)]
    a = select_images(stats, 5, 60, seed=1)
    assert a == select_images(stats, 5, 60, seed=1)
    assert a != select_images(stats, 5, 60, seed=2)


def test_returns_fewer_when_tier_is_small():
    stats = [make(i, i / 100) for i in range(6)]
    out = select_images(stats, n_per_tier=10, min_cells=60, seed=1)
    assert len(out) == 6
