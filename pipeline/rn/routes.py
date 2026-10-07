"""Sinh instance multi-UAV từ bản đồ rủi ro (docs/phase2-rescuenet-thiet-ke.md mục 1b, 5).

Route = đường đi tự tránh (không đi lại ô) liền mạch trên lưới 4 hướng, xuất
phát từ điểm của một UAV, ưu tiên bước vào ô có rủi ro cao. Route phủ các ô
có điểm > 0 nằm trên đường đi; ô điểm 0 chỉ là đường đi, không thuộc universe.
"""

import random

_MOVES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def start_cells(k: int, grid: int) -> list:
    """K điểm xuất phát cố định: 4 góc rồi 4 trung điểm cạnh."""
    last, mid = grid - 1, grid // 2
    pool = [(0, 0), (0, last), (last, 0), (last, last), (0, mid), (mid, 0), (last, mid), (mid, last)]
    if not 1 <= k <= len(pool):
        raise ValueError(f"k phải trong [1, {len(pool)}], nhận {k}")
    return pool[:k]


def random_route(start: tuple, risk, max_cells: int, rng: random.Random) -> list:
    """Đường đi tự tránh dài tối đa `max_cells` ô, lệch về ô rủi ro cao."""
    grid = risk.shape[0]
    path = [start]
    seen = {start}
    target = rng.randint(2, max_cells)
    while len(path) < target:
        r, c = path[-1]
        neighbours = [
            (r + dr, c + dc)
            for dr, dc in _MOVES
            if 0 <= r + dr < grid and 0 <= c + dc < grid and (r + dr, c + dc) not in seen
        ]
        if not neighbours:
            break
        weights = [float(risk[n]) + 0.1 for n in neighbours]
        nxt = rng.choices(neighbours, weights=weights)[0]
        path.append(nxt)
        seen.add(nxt)
    return path


def build_instance(risk, k: int, routes_per_uav: int, max_cells: int, seed: int,
                   takeoff_cost: int = 2, cell_cost: int = 1) -> dict:
    grid = risk.shape[0]
    cells = [(r, c) for r in range(grid) for c in range(grid) if risk[r, c] > 0]
    if not cells:
        raise ValueError("bản đồ rủi ro không có ô nào điểm > 0")
    index = {rc: i for i, rc in enumerate(cells)}
    starts = start_cells(k, grid)
    rng = random.Random(seed)

    costs, sets, owners, paths = [], [], [], []
    for u, start in enumerate(starts):
        best = {}  # tập ô phủ -> (chi phí, đường đi): giữ route rẻ nhất cho mỗi tập ô
        for _ in range(routes_per_uav):
            path = random_route(start, risk, max_cells, rng)
            covered = frozenset(index[p] for p in path if p in index)
            if not covered:
                continue
            cost = takeoff_cost + cell_cost * len(path)
            if covered not in best or cost < best[covered][0]:
                best[covered] = (cost, path)
        for covered, (cost, path) in sorted(best.items(), key=lambda kv: (kv[1][0], sorted(kv[0]))):
            costs.append(cost)
            sets.append(sorted(covered))
            owners.append(u)
            paths.append([list(p) for p in path])

    share_rng = random.Random(seed + 1)
    raw = [1 + share_rng.uniform(-0.2, 0.2) for _ in range(k)]
    return {
        "grid": grid,
        "m": len(cells),
        "n": len(costs),
        "costs": costs,
        "sets": sets,
        "weights": [float(risk[rc]) for rc in cells],
        "route_uav": owners,
        "paths": paths,
        "uav_starts": [list(s) for s in starts],
        "uav_share": [x / sum(raw) for x in raw],
        "cell_rc": [list(rc) for rc in cells],
        "reference_cost": None,
    }
