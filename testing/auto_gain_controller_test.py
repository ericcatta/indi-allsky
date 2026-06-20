from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.auto_gain_controller import AutoGainController


def make_decision(**overrides):
    controller = AutoGainController()
    params = {
        'smoothed_value': 50.0,
        'target': 75.0,
        'mode': 'night',
        'enabled': True,
        'current_exposure': 14.0,
        'exposure_min': 0.0,
        'exposure_max': 14.0,
        'current_gain': 100.0,
        'gain_min': 0.0,
        'gain_max': 220.0,
        'state': {
            'trend_count': 0,
            'trend_direction': 'none',
            'cooldown_remaining': 0,
            'auto_gain_raised': False,
        },
        'deadband': 10.0,
        'trend_frames': 1,
        'cooldown_frames': 2,
        'gain_step_factor': 0.15,
        'gain_min_step': 0.01,
        'gain_max_step': 0.0,
    }
    params.update(overrides)
    return controller, controller.decide(**params)


def test_apply_disabled_blocks_gain_write():
    controller, decision = make_decision()

    should_apply, reason = controller.should_apply(decision, apply_enabled=False)

    assert should_apply is False
    assert reason == 'apply_disabled'


def test_mode_disabled_blocks_gain_write():
    controller, decision = make_decision(enabled=False)

    should_apply, reason = controller.should_apply(decision, apply_enabled=True)

    assert decision.action == 'hold'
    assert should_apply is False
    assert reason == 'mode_disabled'


def test_exposure_below_max_blocks_gain_increase():
    controller, decision = make_decision(current_exposure=10.0)

    should_apply, reason = controller.should_apply(decision, apply_enabled=True)

    assert decision.action == 'hold'
    assert decision.blocker == 'exposure_not_at_limit'
    assert should_apply is False
    assert reason == 'exposure_not_at_limit'


def test_exposure_at_max_trend_active_allows_gain_increase():
    controller, decision = make_decision()

    should_apply, reason = controller.should_apply(decision, apply_enabled=True)

    assert decision.action == 'increase_gain'
    assert decision.trend_active is True
    assert decision.blocker == 'none'
    assert should_apply is True
    assert reason == 'conditions_satisfied'
    assert decision.proposed_gain > decision.current_gain


def test_gain_increase_clamps_to_max():
    _controller, decision = make_decision(
        current_gain=218.0,
        gain_min=0.0,
        gain_max=220.0,
    )

    assert decision.action == 'increase_gain'
    assert decision.proposed_gain == 220.0
    assert decision.proposed_gain <= decision.gain_max


if __name__ == '__main__':
    test_apply_disabled_blocks_gain_write()
    test_mode_disabled_blocks_gain_write()
    test_exposure_below_max_blocks_gain_increase()
    test_exposure_at_max_trend_active_allows_gain_increase()
    test_gain_increase_clamps_to_max()
    print('auto gain controller tests OK')
