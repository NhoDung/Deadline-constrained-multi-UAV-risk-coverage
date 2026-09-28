from scripts.opt_reference import OPT_REFERENCE


def test_scpa1_matches_known_opt_value():
    assert OPT_REFERENCE["scpa1"] == 253


def test_scp65_matches_known_opt_value():
    assert OPT_REFERENCE["scp65"] == 161


def test_unknown_instance_is_absent():
    assert "scpe1" not in OPT_REFERENCE
