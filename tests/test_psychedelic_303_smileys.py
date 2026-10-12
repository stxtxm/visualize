import numpy as np

from effects.psychedelic_303 import (
    Psychedelic303Effect,
    SMILEY_DARK,
    SMILEY_YELLOW,
)


def test_numpy_smiley_has_face_eyes_and_curved_grin():
    effect = Psychedelic303Effect(100, 100)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    effect._draw_smiley_numpy(frame, 50, 50, 30, 0.0, 1)

    assert tuple(frame[50, 50]) == SMILEY_YELLOW
    assert tuple(frame[44, 41]) == SMILEY_DARK
    assert tuple(frame[44, 59]) == SMILEY_DARK
    assert tuple(frame[65, 50]) == SMILEY_DARK


def test_numpy_smiley_includes_a_wink_expression():
    effect = Psychedelic303Effect(100, 100)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    effect._draw_smiley_numpy(frame, 50, 50, 30, 0.0, 0)

    assert tuple(frame[45, 41]) == SMILEY_DARK
    assert tuple(frame[44, 59]) == SMILEY_DARK
