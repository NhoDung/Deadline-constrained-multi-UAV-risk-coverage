import numpy as np

from pipeline.rn_prepare import build_from_mask


def test_build_from_mask_sets_reference_cost_and_is_deterministic():
    mask = np.zeros((40, 40), dtype=int)
    mask[:20, :20] = 5   # góc trên-trái: hư hại nặng
    mask[20:, 20:] = 3   # góc dưới-phải: hư hại vừa
    a = build_from_mask(mask, grid=4, table_name="default", k=2, routes_per_uav=60, max_cells=6, seed=1)
    b = build_from_mask(mask, grid=4, table_name="default", k=2, routes_per_uav=60, max_cells=6, seed=1)
    assert a == b
    assert a["m"] == 8  # 4 ô trái-trên + 4 ô phải-dưới có điểm > 0
    assert isinstance(a["reference_cost"], int) and a["reference_cost"] > 0


def test_shard_items_partitions_without_overlap_or_loss():
    from pipeline.rn_prepare import shard_items

    items = list(range(10))
    parts = [shard_items(items, k, 3) for k in range(3)]
    assert sorted(x for p in parts for x in p) == items
    assert all(len(set(a) & set(b)) == 0 for i, a in enumerate(parts) for b in parts[i + 1:])
    assert shard_items(items, 0, 1) == items
