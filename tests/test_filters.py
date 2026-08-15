import numpy as np
from src.preprocessing.filters import moving_average, adaptive_smoothing_window


def test_moving_average_preserves_length():
    x = np.arange(20, dtype=float)
    y = moving_average(x, window=5)
    assert len(x) == len(y)


def test_smoothing_window_scales_with_sampling_rate():
    assert adaptive_smoothing_window(250) == 5
    assert adaptive_smoothing_window(500) == 10
