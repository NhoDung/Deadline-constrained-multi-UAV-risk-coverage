"""Bản đồ rủi ro từ mask RescueNet (xem docs/phase2-rescuenet-thiet-ke.md mục 1b, 2, 3)."""

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# Chỉ số = nhãn 0..10 (Background, Water, Bld-No, Bld-Minor, Bld-Major,
# Bld-Total, Vehicle, Road-Clear, Road-Blocked, Tree, Pool).
SCORE_TABLES = {
    "default": [0, 1, 1, 2, 3, 3, 1, 1, 3, 0, 1],
    "tree1": [0, 1, 1, 2, 3, 3, 1, 1, 3, 1, 1],
    "convex": [0, 1, 1, 4, 9, 9, 1, 1, 9, 0, 1],
    "damage_only": [0, 0, 0, 2, 3, 3, 0, 0, 3, 0, 0],
}

DAMAGE_LABELS = (3, 4, 5, 8)


def load_mask(path) -> np.ndarray:
    return np.array(Image.open(path))


def cell_risk(mask: np.ndarray, grid: int, table: list) -> np.ndarray:
    """Điểm rủi ro trung bình của pixel trong mỗi ô lưới `grid` x `grid`.

    Phần pixel dư ở mép (khi kích thước ảnh không chia hết cho `grid`) bị cắt.
    """
    if mask.max() >= len(table):
        raise ValueError(f"mask có nhãn {int(mask.max())} nhưng bảng điểm chỉ có {len(table)} lớp")
    pixel_score = np.asarray(table, dtype=float)[mask]
    cell_h, cell_w = pixel_score.shape[0] // grid, pixel_score.shape[1] // grid
    cropped = pixel_score[: cell_h * grid, : cell_w * grid]
    return cropped.reshape(grid, cell_h, grid, cell_w).mean(axis=(1, 3))


def damage_fraction(mask: np.ndarray) -> float:
    """Tỉ lệ pixel thuộc nhãn hư hại (3, 4, 5, 8); dùng để chia tầng ảnh."""
    return float(np.isin(mask, DAMAGE_LABELS).mean())
