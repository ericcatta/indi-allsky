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


def make_params(**overrides):
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
    return params


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


def test_normal_error_keeps_shadow_bounded_step():
    _controller, decision = make_decision(smoothed_value=60.0)

    assert abs(decision.error) == 15.0
    assert decision.action == 'increase_gain'
    assert decision.step_strategy == 'shadow_bounded'
    assert decision.convergence_mode == 'normal'
    assert decision.step == 15.0


def test_large_error_uses_aggressive_bounded_step():
    _controller, normal_decision = make_decision(smoothed_value=60.0)
    _controller, aggressive_decision = make_decision(smoothed_value=50.0)

    assert abs(aggressive_decision.error) == 25.0
    assert aggressive_decision.action == 'increase_gain'
    assert aggressive_decision.step_strategy == 'aggressive_bounded'
    assert aggressive_decision.convergence_mode == 'aggressive'
    assert aggressive_decision.step == normal_decision.step * 2.0


def test_aggressive_gain_increase_clamps_to_max():
    _controller, decision = make_decision(
        smoothed_value=40.0,
        current_gain=210.0,
        gain_min=0.0,
        gain_max=220.0,
    )

    assert decision.step_strategy == 'aggressive_bounded'
    assert decision.proposed_gain == 220.0
    assert decision.proposed_gain <= decision.gain_max


def test_fine_convergence_activates_after_five_frames():
    controller = AutoGainController()
    state = {
        'trend_count': 0,
        'trend_direction': 'none',
        'convergence_frames': 0,
        'convergence_direction': 'none',
        'cooldown_remaining': 0,
        'auto_gain_raised': False,
    }
    params = make_params(
        smoothed_value=72.0,
        state=state,
    )
    decision = None
    for _frame in range(5):
        decision = controller.decide(**params)

    assert decision is not None
    assert decision.fine_convergence is True
    assert decision.convergence_frames == 5
    assert decision.convergence_mode == 'fine'
    assert decision.step_strategy == 'fine_convergence_bounded'
    assert decision.action == 'increase_gain'
    assert 0.0 < decision.step < 15.0


def test_fine_convergence_stops_inside_target_window():
    state = {
        'trend_count': 0,
        'trend_direction': 'none',
        'convergence_frames': 5,
        'convergence_direction': 'positive',
        'cooldown_remaining': 0,
        'auto_gain_raised': True,
    }
    _controller, decision = make_decision(
        smoothed_value=73.6,
        state=state,
    )

    assert abs(decision.error) <= 1.5
    assert decision.action == 'hold'
    assert decision.fine_convergence is False
    assert decision.convergence_mode == 'normal'
    assert decision.convergence_frames == 0


def test_fine_convergence_resets_on_error_sign_change():
    state = {
        'trend_count': 0,
        'trend_direction': 'none',
        'convergence_frames': 4,
        'convergence_direction': 'positive',
        'cooldown_remaining': 0,
        'auto_gain_raised': True,
    }
    _controller, decision = make_decision(
        smoothed_value=78.0,
        state=state,
    )

    assert decision.error < 0
    assert decision.action == 'hold'
    assert decision.fine_convergence is False
    assert decision.convergence_frames == 1
    assert state['convergence_direction'] == 'negative'


if __name__ == '__main__':
    test_apply_disabled_blocks_gain_write()
    test_mode_disabled_blocks_gain_write()
    test_exposure_below_max_blocks_gain_increase()
    test_exposure_at_max_trend_active_allows_gain_increase()
    test_gain_increase_clamps_to_max()
    test_normal_error_keeps_shadow_bounded_step()
    test_large_error_uses_aggressive_bounded_step()
    test_aggressive_gain_increase_clamps_to_max()
    test_fine_convergence_activates_after_five_frames()
    test_fine_convergence_stops_inside_target_window()
    test_fine_convergence_resets_on_error_sign_change()
    print('auto gain controller tests OK')
