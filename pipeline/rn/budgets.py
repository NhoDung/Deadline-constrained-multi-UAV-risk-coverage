"""Chi phí tham chiếu R và ngân sách riêng từng UAV (docs/phase2-rescuenet-thiet-ke.md mục 5)."""

import math

import pulp


def reference_cost(instance: dict, time_limit: int = 120) -> int:
    """Chi phí nhỏ nhất để phủ mọi ô mà ít nhất một route phủ được (bỏ qua phân chia UAV)."""
    n, costs = instance["n"], instance["costs"]
    covering = {}
    for j, cells in enumerate(instance["sets"]):
        for i in cells:
            covering.setdefault(i, []).append(j)
    if not covering:
        return 0
    prob = pulp.LpProblem("reference_cover", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n)]
    prob += pulp.lpSum(costs[j] * x[j] for j in range(n))
    for i, routes in covering.items():
        prob += pulp.lpSum(x[j] for j in routes) >= 1, f"cover_{i}"
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    if pulp.LpStatus[prob.status] != "Optimal":
        raise RuntimeError(f"không giải tối ưu được chi phí tham chiếu (status={pulp.LpStatus[prob.status]})")
    return round(sum(costs[j] for j in range(n) if x[j].value() > 0.5))


def budgets_for_level(instance: dict, level: int) -> list:
    """B_u = floor(level% x R x share_u)."""
    r = instance["reference_cost"]
    return [math.floor(level * r * s / 100) for s in instance["uav_share"]]
