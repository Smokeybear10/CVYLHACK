import numpy as np
from pipeline.crop import crop_xy


def test_crop_xy_keeps_only_inside():
    pts = np.array([[0, 0, 1], [5, 5, 1], [50, 50, 1]], dtype=float)
    out = crop_xy(pts, (-1, -1, 10, 10))
    assert out.shape[0] == 2
    assert (out[:, 0] <= 10).all()
