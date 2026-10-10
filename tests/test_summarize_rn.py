from pipeline.summarize_rn import paired_wilcoxon, ratios_to_ilp


def rec(instance, algorithm, level, objective):
    return {"instance": instance, "algorithm": algorithm, "budget_level": level, "objective": objective}


def test_ratios_to_ilp_pairs_by_instance_and_skips_missing_ilp():
    records = [rec("a", "ilp_uav", 50, 10.0), rec("b", "ilp_uav", 50, 20.0),
               rec("a", "proposed", 50, 9.0), rec("b", "proposed", 50, 20.0),
               rec("c", "proposed", 50, 5.0)]
    assert ratios_to_ilp(records)[("proposed", 50)] == [0.9, 1.0]


def test_ratios_skip_zero_optimum():
    records = [rec("a", "ilp_uav", 25, 0.0), rec("a", "proposed", 25, 0.0)]
    assert ratios_to_ilp(records).get(("proposed", 25), []) == []


def test_wilcoxon_identical_samples_gives_p_one():
    assert paired_wilcoxon([0.9, 0.8, 1.0], [0.9, 0.8, 1.0]) == 1.0


def test_wilcoxon_consistent_improvement_gives_small_p():
    a = [0.99 - 0.001 * i for i in range(12)]
    b = [x - 0.05 - 0.001 * i for i, x in enumerate(a)]
    assert paired_wilcoxon(a, b) < 0.01


def test_ratios_can_be_filtered_by_ilp_status():
    ilp_opt = {**rec("a", "ilp_uav", 50, 10.0), "status": "optimal"}
    ilp_bk = {**rec("b", "ilp_uav", 50, 20.0), "status": "best-known"}
    records = [ilp_opt, ilp_bk, rec("a", "proposed", 50, 9.0), rec("b", "proposed", 50, 20.0)]
    assert ratios_to_ilp(records, ilp_status="optimal")[("proposed", 50)] == [0.9]
    assert ratios_to_ilp(records, ilp_status="best-known")[("proposed", 50)] == [1.0]


def test_win_tie_loss_counts_pairs_with_tolerance():
    from pipeline.summarize_rn import win_tie_loss

    assert win_tie_loss([1.0, 0.9, 0.8, 0.5], [0.9, 0.9, 0.9, 0.5 + 1e-12]) == (1, 2, 1)
