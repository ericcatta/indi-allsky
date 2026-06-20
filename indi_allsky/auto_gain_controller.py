from dataclasses import dataclass


@dataclass(frozen=True)
class AutoGainDecision:
    action: str
    reason: str
    mode: str
    enabled: bool
    current_exposure: float
    proposed_exposure: float
    exposure_min: float
    exposure_max: float
    current_gain: float
    proposed_gain: float
    gain_min: float
    gain_max: float
    target: float
    error: float
    deadband: float
    trend_count: int
    trend_direction: str
    trend_active: bool
    convergence_frames: int
    fine_convergence: bool
    convergence_mode: str
    cooldown_remaining: int
    step: float
    step_strategy: str
    auto_gain_raised: bool
    blocker: str
    shadow: bool = True


class AutoGainController:
    """Shadow controller for future profile-aware auto gain decisions."""

    deadband = 10.0
    trend_frames = 3
    cooldown_frames = 2
    gain_step_fraction = 0.15
    gain_min_step = 0.01
    gain_max_step = None
    aggressive_error_threshold = 20.0
    aggressive_step_multiplier = 2.0
    fine_convergence_error = 5.0
    fine_convergence_target = 1.5
    fine_convergence_frames = 5
    fine_step_multiplier = 0.25

    def should_apply(self, decision, *, apply_enabled):
        if not apply_enabled:
            return False, 'apply_disabled'

        if not decision.enabled:
            return False, 'mode_disabled'

        if decision.blocker != 'none':
            return False, decision.blocker

        if decision.action == 'hold':
            return False, 'hold'

        if decision.action not in ('increase_gain', 'decrease_gain'):
            return False, 'unsupported_action'

        if not decision.trend_active:
            return False, 'trend_not_confirmed'

        if decision.current_exposure < decision.exposure_max:
            return False, 'exposure_not_at_limit'

        if decision.proposed_gain > decision.gain_max:
            return False, 'gain_above_max'

        if decision.proposed_gain < decision.gain_min:
            return False, 'gain_below_min'

        if decision.proposed_gain == decision.current_gain:
            return False, 'gain_unchanged'

        return True, 'conditions_satisfied'


    def decide(
        self,
        *,
        smoothed_value,
        target,
        mode,
        enabled,
        current_exposure,
        exposure_min,
        exposure_max,
        current_gain,
        gain_min,
        gain_max,
        state,
        deadband=None,
        trend_frames=None,
        cooldown_frames=None,
        gain_step_factor=None,
        gain_min_step=None,
        gain_max_step=None,
    ):
        mode = str(mode or 'day')
        enabled = bool(enabled)
        smoothed_value = float(smoothed_value)
        target = float(target)
        current_exposure = self._clamp(float(current_exposure), float(exposure_min), float(exposure_max))
        exposure_min = float(exposure_min)
        exposure_max = float(exposure_max)
        current_gain = self._clamp(float(current_gain), float(gain_min), float(gain_max))
        gain_min = float(gain_min)
        gain_max = float(gain_max)
        deadband = self._positive_float(deadband, self.deadband)
        trend_frames = self._positive_int(trend_frames, self.trend_frames)
        cooldown_frames = self._positive_int(cooldown_frames, self.cooldown_frames)
        gain_step_factor = self._positive_float(gain_step_factor, self.gain_step_fraction)
        gain_min_step = self._positive_float(gain_min_step, self.gain_min_step)
        gain_max_step = self._optional_positive_float(gain_max_step)
        auto_gain_raised = bool(state.get('auto_gain_raised', False))

        error = target - smoothed_value
        abs_error = abs(error)
        convergence_direction = self._fine_error_direction(error)
        previous_convergence_direction = state.get('convergence_direction', 'none')
        convergence_previous = int(state.get('convergence_frames') or 0)
        if abs_error <= self.fine_convergence_target:
            convergence_frames = 0
            convergence_direction = 'none'
        elif abs_error < self.fine_convergence_error and convergence_direction == previous_convergence_direction:
            convergence_frames = convergence_previous + 1
        elif abs_error < self.fine_convergence_error:
            convergence_frames = 1
        else:
            convergence_frames = 0
            convergence_direction = 'none'

        fine_convergence = (
            abs_error > self.fine_convergence_target
            and abs_error < self.fine_convergence_error
            and convergence_direction != 'none'
            and convergence_frames >= self.fine_convergence_frames
        )
        trend_direction = self._error_direction(error, deadband)
        previous_direction = state.get('trend_direction', 'none')
        previous_count = int(state.get('trend_count') or 0)

        if abs(error) <= deadband:
            trend_count = 0
            trend_direction = 'none'
        elif previous_direction == trend_direction:
            trend_count = previous_count + 1
        else:
            trend_count = 1

        cooldown_remaining = max(0, int(state.get('cooldown_remaining') or 0))
        if cooldown_remaining > 0:
            cooldown_remaining -= 1

        action = 'hold'
        reason = 'deadband'
        blocker = 'deadband_hold'
        proposed_exposure = current_exposure
        proposed_gain = current_gain
        step = 0.0
        step_strategy = 'shadow_bounded'
        convergence_mode = 'normal'
        trend_active = trend_count >= trend_frames and trend_direction != 'none'
        if fine_convergence:
            convergence_mode = 'fine'
            trend_active = True
            if error > self.fine_convergence_target:
                trend_direction = 'positive'
            elif error < (self.fine_convergence_target * -1):
                trend_direction = 'negative'

        if not enabled:
            reason = 'mode_disabled'
            blocker = 'mode_disabled'
        elif cooldown_remaining > 0:
            reason = 'cooldown_active'
            blocker = 'cooldown_active'
        elif fine_convergence:
            step_strategy = 'fine_convergence_bounded'
            if error > self.fine_convergence_target:
                if current_exposure < exposure_max:
                    action = 'hold'
                    reason = 'exposure_not_at_limit'
                    blocker = 'exposure_not_at_limit'
                elif current_gain < gain_max:
                    step = self._gain_step(
                        current_gain,
                        gain_min,
                        gain_max,
                        gain_step_factor=gain_step_factor,
                        gain_min_step=gain_min_step,
                        gain_max_step=gain_max_step,
                        step_multiplier=self.fine_step_multiplier,
                    )
                    proposed_gain = self._clamp(current_gain + step, gain_min, gain_max)
                    action = 'increase_gain' if proposed_gain > current_gain else 'hold'
                    reason = 'fine_convergence_increase_gain' if action == 'increase_gain' else 'gain_already_max'
                    blocker = 'none' if action == 'increase_gain' else 'gain_already_max'
                else:
                    reason = 'gain_already_max'
                    blocker = 'gain_already_max'
            elif error < (self.fine_convergence_target * -1):
                if auto_gain_raised and current_gain > gain_min:
                    step = self._gain_step(
                        current_gain,
                        gain_min,
                        gain_max,
                        gain_step_factor=gain_step_factor,
                        gain_min_step=gain_min_step,
                        gain_max_step=gain_max_step,
                        step_multiplier=self.fine_step_multiplier,
                    )
                    proposed_gain = self._clamp(current_gain - step, gain_min, gain_max)
                    action = 'decrease_gain' if proposed_gain < current_gain else 'hold'
                    reason = 'fine_convergence_decrease_gain' if action == 'decrease_gain' else 'gain_already_min'
                    blocker = 'none' if action == 'decrease_gain' else 'gain_already_min'
                elif current_gain <= gain_min:
                    action = 'hold'
                    reason = 'gain_already_min'
                    blocker = 'gain_already_min'
                elif current_exposure > exposure_min:
                    action = 'hold'
                    reason = 'gain_not_auto_raised_exposure_control'
                    blocker = 'gain_not_auto_raised'
            else:
                reason = 'deadband_hold'
                blocker = 'deadband_hold'
        elif abs(error) <= deadband:
            reason = 'deadband_hold'
            blocker = 'deadband_hold'
        elif not trend_active:
            reason = 'trend_not_confirmed'
            blocker = 'trend_not_confirmed'
        elif error > deadband:
            step_multiplier = self.aggressive_step_multiplier if abs_error > self.aggressive_error_threshold else 1.0
            step_strategy = 'aggressive_bounded' if abs_error > self.aggressive_error_threshold else 'shadow_bounded'
            convergence_mode = 'aggressive' if abs_error > self.aggressive_error_threshold else 'normal'
            if current_exposure < exposure_max:
                action = 'hold'
                reason = 'exposure_not_at_limit'
                blocker = 'exposure_not_at_limit'
            elif current_gain < gain_max:
                step = self._gain_step(
                    current_gain,
                    gain_min,
                    gain_max,
                    gain_step_factor=gain_step_factor,
                    gain_min_step=gain_min_step,
                    gain_max_step=gain_max_step,
                    step_multiplier=step_multiplier,
                )
                proposed_gain = self._clamp(current_gain + step, gain_min, gain_max)
                action = 'increase_gain' if proposed_gain > current_gain else 'hold'
                reason = 'gain_increase_conditions_satisfied'
                blocker = 'none' if action == 'increase_gain' else 'gain_already_max'
            else:
                reason = 'gain_already_max'
                blocker = 'gain_already_max'
        elif error < (deadband * -1):
            step_multiplier = self.aggressive_step_multiplier if abs_error > self.aggressive_error_threshold else 1.0
            step_strategy = 'aggressive_bounded' if abs_error > self.aggressive_error_threshold else 'shadow_bounded'
            convergence_mode = 'aggressive' if abs_error > self.aggressive_error_threshold else 'normal'
            if auto_gain_raised and current_gain > gain_min:
                step = self._gain_step(
                    current_gain,
                    gain_min,
                    gain_max,
                    gain_step_factor=gain_step_factor,
                    gain_min_step=gain_min_step,
                    gain_max_step=gain_max_step,
                    step_multiplier=step_multiplier,
                )
                proposed_gain = self._clamp(current_gain - step, gain_min, gain_max)
                action = 'decrease_gain' if proposed_gain < current_gain else 'hold'
                reason = 'reduce_auto_gain_first' if action == 'decrease_gain' else 'gain_already_min'
                blocker = 'none' if action == 'decrease_gain' else 'gain_already_min'
            elif current_gain <= gain_min:
                action = 'hold'
                reason = 'gain_already_min'
                blocker = 'gain_already_min'
            elif current_exposure > exposure_min:
                action = 'hold'
                reason = 'gain_not_auto_raised_exposure_control'
                blocker = 'gain_not_auto_raised'

        if action == 'increase_gain':
            cooldown_remaining = cooldown_frames
            auto_gain_raised = True
        elif action == 'decrease_gain':
            cooldown_remaining = cooldown_frames
            if proposed_gain <= gain_min:
                auto_gain_raised = False

        state['trend_count'] = trend_count
        state['trend_direction'] = trend_direction
        state['convergence_frames'] = convergence_frames
        state['convergence_direction'] = convergence_direction
        state['cooldown_remaining'] = cooldown_remaining
        state['last_action'] = action
        state['auto_gain_raised'] = auto_gain_raised

        return AutoGainDecision(
            action=action,
            reason=reason,
            mode=mode,
            enabled=enabled,
            current_exposure=current_exposure,
            proposed_exposure=proposed_exposure,
            exposure_min=exposure_min,
            exposure_max=exposure_max,
            current_gain=current_gain,
            proposed_gain=proposed_gain,
            gain_min=gain_min,
            gain_max=gain_max,
            target=target,
            error=error,
            deadband=deadband,
            trend_count=trend_count,
            trend_direction=trend_direction,
            trend_active=trend_active,
            convergence_frames=convergence_frames,
            fine_convergence=fine_convergence,
            convergence_mode=convergence_mode,
            cooldown_remaining=cooldown_remaining,
            step=abs(proposed_gain - current_gain),
            step_strategy=step_strategy,
            auto_gain_raised=auto_gain_raised,
            blocker=blocker,
            shadow=True,
        )


    def _clamp(self, value, minimum, maximum):
        if minimum > maximum:
            minimum, maximum = maximum, minimum

        return max(minimum, min(maximum, value))


    def _gain_step(self, current_gain, gain_min, gain_max, *, gain_step_factor, gain_min_step, gain_max_step, step_multiplier=1.0):
        gain_range = max(0.0, gain_max - gain_min)
        if gain_range <= 0.0:
            return 0.0

        step = max(gain_min_step, max(abs(current_gain), 1.0) * gain_step_factor)
        step *= max(0.0, float(step_multiplier))
        if gain_max_step is not None:
            step = min(step, gain_max_step)

        return min(gain_range, step)


    def _positive_float(self, value, default):
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return float(default)

        if value_float <= 0.0:
            return float(default)

        return value_float


    def _optional_positive_float(self, value):
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return None

        if value_float <= 0.0:
            return None

        return value_float


    def _positive_int(self, value, default):
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return int(default)

        if value_int <= 0:
            return int(default)

        return value_int


    def _error_direction(self, error, deadband):
        if error > deadband:
            return 'positive'
        if error < (deadband * -1):
            return 'negative'

        return 'none'


    def _fine_error_direction(self, error):
        if error > self.fine_convergence_target:
            return 'positive'
        if error < (self.fine_convergence_target * -1):
            return 'negative'

        return 'none'
