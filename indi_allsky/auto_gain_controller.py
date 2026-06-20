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
    cooldown_remaining: int
    step: float
    step_strategy: str
    auto_gain_raised: bool
    shadow: bool = True


class AutoGainController:
    """Shadow controller for future profile-aware auto gain decisions."""

    deadband = 10.0
    trend_frames = 3
    cooldown_frames = 2
    gain_step_fraction = 0.15
    gain_min_step = 0.01
    gain_max_step = None


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
        proposed_exposure = current_exposure
        proposed_gain = current_gain
        step = 0.0
        step_strategy = 'shadow_bounded'
        trend_active = trend_count >= trend_frames and trend_direction != 'none'

        if not enabled:
            reason = 'gain_auto_disabled'
        elif cooldown_remaining > 0:
            reason = 'cooldown'
        elif abs(error) <= deadband:
            reason = 'deadband'
        elif not trend_active:
            reason = 'waiting_for_persistent_trend'
        elif error > deadband:
            if current_exposure < exposure_max:
                action = 'hold'
                reason = 'exposure_first'
            elif current_gain < gain_max:
                step = self._gain_step(
                    current_gain,
                    gain_min,
                    gain_max,
                    gain_step_factor=gain_step_factor,
                    gain_min_step=gain_min_step,
                    gain_max_step=gain_max_step,
                )
                proposed_gain = self._clamp(current_gain + step, gain_min, gain_max)
                action = 'increase_gain' if proposed_gain > current_gain else 'hold'
                reason = 'exposure_at_max'
        elif error < (deadband * -1):
            if auto_gain_raised and current_gain > gain_min:
                step = self._gain_step(
                    current_gain,
                    gain_min,
                    gain_max,
                    gain_step_factor=gain_step_factor,
                    gain_min_step=gain_min_step,
                    gain_max_step=gain_max_step,
                )
                proposed_gain = self._clamp(current_gain - step, gain_min, gain_max)
                action = 'decrease_gain' if proposed_gain < current_gain else 'hold'
                reason = 'reduce_auto_gain_first'
            elif current_exposure > exposure_min:
                action = 'hold'
                reason = 'gain_not_auto_raised_exposure_control'

        if action == 'increase_gain':
            cooldown_remaining = cooldown_frames
            auto_gain_raised = True
        elif action == 'decrease_gain':
            cooldown_remaining = cooldown_frames
            if proposed_gain <= gain_min:
                auto_gain_raised = False

        state['trend_count'] = trend_count
        state['trend_direction'] = trend_direction
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
            cooldown_remaining=cooldown_remaining,
            step=abs(proposed_gain - current_gain),
            step_strategy=step_strategy,
            auto_gain_raised=auto_gain_raised,
            shadow=True,
        )


    def _clamp(self, value, minimum, maximum):
        if minimum > maximum:
            minimum, maximum = maximum, minimum

        return max(minimum, min(maximum, value))


    def _gain_step(self, current_gain, gain_min, gain_max, *, gain_step_factor, gain_min_step, gain_max_step):
        gain_range = max(0.0, gain_max - gain_min)
        if gain_range <= 0.0:
            return 0.0

        step = max(gain_min_step, max(abs(current_gain), 1.0) * gain_step_factor)
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
