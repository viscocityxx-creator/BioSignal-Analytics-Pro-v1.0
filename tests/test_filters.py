
import numpy as np
from src.preprocessing.filters import moving_average

def test_moving_average_preserves_length():
    x = np.arange(20, dtype=float)
    y = moving_average(x, window=5)
    assert len(x) == len(y)
