import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.auto_exposure_controller import AutoExposureController


def _decision(**overrides):
    kwargs = {
        'smoothed_value': 255.0,
        'current_exposure': 6.7,
        'current_gain': 0.0,
        'exposure_min': 0.000032,
        'exposure_max': 14.0,
        'gain_min': 0.0,
        'gain_max': 300.0,
        'target': 95.0,
        'trend_count': 0,
        'is_day': True,
        'day_step_factor': 0.35,
        'day_min_step': 0.00025,
        'day_max_step': 0.005,
        'allow_gain_control': False,
    }
    kwargs.update(overrides)
    return AutoExposureController().decide(**kwargs)


def test_large_error_uses_aggressive_mode():
    decision = _decision(current_exposure=0.02, smoothed_value=60.0, target=95.0)

    assert decision.action == 'increase_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert decision.step_strategy == 'aggressive_bounded'
    assert decision.exposure_step > 0.005
    assert abs(decision.estimated_exposure - decision.proposed_exposure) < 0.000001
    assert decision.safety_limited is False


def test_saturated_day_exposure_uses_aggressive_halving():
    decision = _decision(current_exposure=6.7, smoothed_value=255.0, target=95.0)

    assert decision.action == 'decrease_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert decision.step_strategy == 'aggressive_bounded'
    assert decision.saturated is True
    assert abs(decision.estimated_exposure - (6.7 * (95.0 / 255.0))) < 0.000001
    assert abs(decision.proposed_exposure - 3.35) < 0.000001
    assert abs(decision.exposure_step - 3.35) < 0.000001
    assert decision.safety_limited is True


def test_normal_medium_day_error_keeps_day_bounded():
    decision = _decision(current_exposure=0.02, smoothed_value=110.0, target=95.0)

    assert decision.action == 'decrease_exposure'
    assert decision.convergence_mode == 'normal'
    assert decision.step_strategy == 'day_bounded'
    assert decision.saturated is False
    assert decision.safety_limited is False
    assert abs(decision.exposure_step - 0.005) < 0.000001
    assert abs(decision.proposed_exposure - 0.015) < 0.000001


def test_fine_convergence_after_persistent_small_error():
    decision = _decision(
        current_exposure=0.02,
        smoothed_value=91.0,
        target=95.0,
        trend_count=5,
    )

    assert decision.action == 'increase_exposure'
    assert decision.convergence_mode == 'fine'
    assert decision.fine_convergence is True
    assert decision.step_strategy == 'fine_convergence_bounded'
    assert decision.safety_limited is False
    assert abs(decision.exposure_step - 0.00125) < 0.000001


def test_target_reached_holds():
    decision = _decision(current_exposure=0.02, smoothed_value=94.0, target=95.0, trend_count=10)

    assert decision.action == 'hold'
    assert decision.reason == 'target_reached'
    assert decision.convergence_mode == 'target'
    assert decision.exposure_step == 0.0
    assert decision.safety_limited is False


def test_aggressive_decrease_below_100ms_uses_gentle_step():
    decision = _decision(
        current_exposure=0.05,
        exposure_min=0.000032,
        smoothed_value=255.0,
        target=95.0,
    )

    assert decision.action == 'decrease_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert decision.step_strategy == 'aggressive_bounded'
    assert abs(decision.proposed_exposure - 0.045) < 0.000001
    assert abs(decision.exposure_step - 0.005) < 0.000001
    assert decision.safety_limited is True


def test_aggressive_decrease_below_100ms_caps_to_85_percent():
    decision = _decision(
        current_exposure=0.01,
        exposure_min=0.000032,
        smoothed_value=255.0,
        target=95.0,
    )

    assert decision.action == 'decrease_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert decision.step_strategy == 'aggressive_bounded'
    assert abs(decision.proposed_exposure - 0.0085) < 0.000001
    assert abs(decision.exposure_step - 0.0015) < 0.000001
    assert decision.safety_limited is True


def test_aggressive_decrease_below_100ms_clamps_to_exposure_min():
    decision = _decision(
        current_exposure=0.00004,
        exposure_min=0.000038,
        smoothed_value=255.0,
        target=95.0,
    )

    assert decision.action == 'decrease_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert decision.step_strategy == 'aggressive_bounded'
    assert decision.proposed_exposure == 0.000038
    assert decision.exposure_step > 0.0


def test_aggressive_increase_clamps_to_exposure_max():
    decision = _decision(
        current_exposure=13.99,
        exposure_max=14.0,
        smoothed_value=50.0,
        target=95.0,
    )

    assert decision.action == 'increase_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert decision.proposed_exposure == 14.0
    assert abs(decision.exposure_step - 0.01) < 0.000001


def test_aggressive_increase_uses_estimate_when_inside_safety_limit():
    decision = _decision(
        current_exposure=0.02,
        smoothed_value=80.0,
        target=120.0,
    )

    assert decision.action == 'increase_exposure'
    assert decision.convergence_mode == 'aggressive'
    assert abs(decision.estimated_exposure - 0.03) < 0.000001
    assert abs(decision.proposed_exposure - 0.03) < 0.000001
    assert decision.safety_limited is False


if __name__ == '__main__':
    test_large_error_uses_aggressive_mode()
    test_saturated_day_exposure_uses_aggressive_halving()
    test_normal_medium_day_error_keeps_day_bounded()
    test_fine_convergence_after_persistent_small_error()
    test_target_reached_holds()
    test_aggressive_decrease_below_100ms_uses_gentle_step()
    test_aggressive_decrease_below_100ms_caps_to_85_percent()
    test_aggressive_decrease_below_100ms_clamps_to_exposure_min()
    test_aggressive_increase_clamps_to_exposure_max()
    test_aggressive_increase_uses_estimate_when_inside_safety_limit()
    print('auto exposure controller tests OK')
