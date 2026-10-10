import numpy as np
import pytest
from PIL import Image

from pipeline.rn.risk import SCORE_TABLES, cell_risk, damage_fraction, load_mask

TABLE = SCORE_TABLES["default"]


def test_cell_risk_averages_pixel_scores_per_cell():
    mask = np.array([[5, 0, 0, 0], [5, 0, 0, 0], [0, 0, 4, 4], [0, 0, 4, 4]])
    out = cell_risk(mask, grid=2, table=TABLE)
    assert out.tolist() == [[1.5, 0.0], [0.0, 3.0]]


def test_cell_risk_crops_remainder_pixels():
    # Ảnh 5x5 không chia hết cho lưới 2x2: phải cắt phần dư thay vì báo lỗi.
    out = cell_risk(np.zeros((5, 5), dtype=int), grid=2, table=TABLE)
    assert out.shape == (2, 2)


def test_cell_risk_rejects_labels_outside_table():
    with pytest.raises(ValueError):
        cell_risk(np.array([[11]]), grid=1, table=TABLE)


def test_tree_scores_zero_in_default_and_one_in_tree1():
    mask = np.full((2, 2), 9)
    assert cell_risk(mask, 1, SCORE_TABLES["default"]).item() == 0.0
    assert cell_risk(mask, 1, SCORE_TABLES["tree1"]).item() == 1.0


def test_damage_fraction_counts_labels_3_4_5_8():
    assert damage_fraction(np.array([[3, 4], [0, 9]])) == 0.5


def test_load_mask_reads_grayscale_png(tmp_path):
    path = tmp_path / "x_lab.png"
    Image.fromarray(np.array([[0, 5], [8, 10]], dtype=np.uint8)).save(path)
    assert load_mask(path).tolist() == [[0, 5], [8, 10]]
