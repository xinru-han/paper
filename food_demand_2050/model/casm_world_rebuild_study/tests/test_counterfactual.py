from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest


STUDY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY_DIR))

from run_counterfactuals import combine_food_and_nonfood_shifters


def test_unit_preference_preserves_macro_shifter_and_food_share():
    macro = np.array([[1.2, 0.9], [1.1, 1.3]])
    share = np.array([[0.8, 0.0], [1.0, 0.35]])
    total, realized = combine_food_and_nonfood_shifters(
        macro, share, np.ones_like(share)
    )
    assert np.array_equal(total, macro)
    assert np.array_equal(realized, share)


def test_food_only_multiplier_leaves_nonfood_anchor_unchanged():
    macro = np.ones((1, 2))
    share = np.array([[0.25, 1.0]])
    preference = np.array([[2.0, 0.5]])
    total, realized = combine_food_and_nonfood_shifters(macro, share, preference)
    assert total[0, 0] == pytest.approx(1.25)
    assert realized[0, 0] == pytest.approx(0.4)
    assert total[0, 1] == pytest.approx(0.5)
    assert realized[0, 1] == pytest.approx(1.0)
    base = np.array([[100.0, 50.0]])
    final = base * total
    food = final * realized
    nonfood = final - food
    assert food[0, 0] == pytest.approx(50.0)
    assert nonfood[0, 0] == pytest.approx(75.0)


def test_invalid_preference_is_rejected():
    with pytest.raises(ValueError):
        combine_food_and_nonfood_shifters(
            np.ones((1, 1)), np.array([[0.5]]), np.array([[0.0]])
        )

