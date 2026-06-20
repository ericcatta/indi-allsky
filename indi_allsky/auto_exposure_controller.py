from dataclasses import dataclass


@dataclass(frozen=True)
class AutoExposureDecision:
    action: str
    reason: str
    blocker: str
    current_exposure: float
    proposed_exposure: float
    current_gain: float
    proposed_gain: float
    target: float
    error: float
    deadband: float
    trend_count: int
    trend_active: bool
    trend_direction: str
    trend_step: float
    step_strategy: str
    exposure_step: float
    shadow: bool = True


class AutoExposureController:
    """Shadow controller for future exposure-first, gain-second decisions."""

    deadband = 10.0
    inner_deadband = 5.0
    trend_frames = 5
    exposure_step_fraction = 0.25
    gain_step_fraction = 0.15
    day_step_factor = 0.35
    day_min_step = 0.00025
    day_max_step = 0.005

    def decide(
        self,
        *,
        smoothed_value,
        current_exposure,
        current_gain,
        exposure_min,
        exposure_max,
        gain_min,
        gain_max,
        target=75.0,
        trend_count=0,
        is_day=False,
        day_step_factor=None,
        day_min_step=None,
        day_max_step=None,
        allow_gain_control=True,
    ):
        smoothed_value = float(smoothed_value)
        current_exposure = float(current_exposure)
        current_gain = float(current_gain)
        exposure_min = float(exposure_min)
        exposure_max = float(exposure_max)
        gain_min = float(gain_min)
        gain_max = float(gain_max)
        target = float(target)
        is_day = bool(is_day)
        allow_gain_control = bool(allow_gain_control)
        day_step_factor = self._positive_float(day_step_factor, self.day_step_factor)
        day_min_step = self._positive_float(day_min_step, self.day_min_step)
        day_max_step = self._positive_float(day_max_step, self.day_max_step)

        current_exposure = self._clamp(current_exposure, exposure_min, exposure_max)
        current_gain = self._clamp(current_gain, gain_min, gain_max)
        proposed_exposure = current_exposure
        proposed_gain = current_gain
        error = target - smoothed_value
        action = 'hold'
        reason = 'inner_deadband_hold'
        blocker = 'inner_deadband_hold'
        trend_active = False
        trend_direction = 'none'
        trend_step = 0.0
        step_strategy = 'day_bounded' if is_day else 'legacy_fractional'
        exposure_step = 0.0

        if abs(error) <= self.inner_deadband:
            action = 'hold'
            reason = 'inner_deadband_hold'
            blocker = 'inner_deadband_hold'
        elif abs(error) <= self.deadband:
            if trend_count >= self.trend_frames:
                trend_active = True
                exposure_step = self._exposure_step(
                    current_exposure,
                    is_day=is_day,
                    day_step_factor=day_step_factor,
                    day_min_step=day_min_step,
                    day_max_step=day_max_step,
                )
                trend_step = exposure_step / 2.0
                if error > 0:
                    action = 'increase_exposure'
                    reason = 'trend_micro_increase_exposure'
                    blocker = 'none'
                    trend_direction = 'positive'
                    proposed_exposure = self._clamp(current_exposure + trend_step, exposure_min, exposure_max)
                else:
                    action = 'decrease_exposure'
                    reason = 'trend_micro_decrease_exposure'
                    blocker = 'none'
                    trend_direction = 'negative'
                    proposed_exposure = self._clamp(current_exposure - trend_step, exposure_min, exposure_max)
            else:
                reason = 'trend_not_confirmed'
                blocker = 'trend_not_confirmed'
        elif error > self.deadband:
            if current_exposure < exposure_max:
                action = 'increase_exposure'
                reason = 'increase_exposure_conditions_satisfied'
                blocker = 'none'
                exposure_step = self._exposure_step(
                    current_exposure,
                    is_day=is_day,
                    day_step_factor=day_step_factor,
                    day_min_step=day_min_step,
                    day_max_step=day_max_step,
                )
                proposed_exposure = self._clamp(current_exposure + exposure_step, exposure_min, exposure_max)
            elif allow_gain_control and current_gain < gain_max:
                action = 'increase_gain'
                reason = 'exposure_at_limit_increase_gain'
                blocker = 'none'
                gain_step = max(0.01, max(abs(current_gain), 1.0) * self.gain_step_fraction)
                proposed_gain = self._clamp(current_gain + gain_step, gain_min, gain_max)
            elif not allow_gain_control:
                reason = 'gain_control_disabled'
                blocker = 'gain_control_disabled'
            else:
                reason = 'exposure_and_gain_already_max'
                blocker = 'exposure_and_gain_already_max'
        elif error < (self.deadband * -1):
            if allow_gain_control and current_gain > gain_min:
                action = 'decrease_gain'
                reason = 'decrease_gain_before_exposure'
                blocker = 'none'
                gain_step = max(0.01, max(abs(current_gain), 1.0) * self.gain_step_fraction)
                proposed_gain = self._clamp(current_gain - gain_step, gain_min, gain_max)
            elif current_exposure > exposure_min:
                action = 'decrease_exposure'
                reason = 'decrease_exposure_conditions_satisfied'
                blocker = 'none'
                exposure_step = self._exposure_step(
                    current_exposure,
                    is_day=is_day,
                    day_step_factor=day_step_factor,
                    day_min_step=day_min_step,
                    day_max_step=day_max_step,
                )
                proposed_exposure = self._clamp(current_exposure - exposure_step, exposure_min, exposure_max)
            elif allow_gain_control:
                reason = 'exposure_and_gain_already_min'
                blocker = 'exposure_and_gain_already_min'
            else:
                reason = 'exposure_already_min'
                blocker = 'exposure_already_min'

        return AutoExposureDecision(
            action=action,
            reason=reason,
            blocker=blocker,
            current_exposure=current_exposure,
            proposed_exposure=proposed_exposure,
            current_gain=current_gain,
            proposed_gain=proposed_gain,
            target=target,
            error=error,
            deadband=self.deadband,
            trend_count=int(trend_count),
            trend_active=trend_active,
            trend_direction=trend_direction,
            trend_step=trend_step,
            step_strategy=step_strategy,
            exposure_step=exposure_step,
            shadow=True,
        )


    def _clamp(self, value, minimum, maximum):
        if minimum > maximum:
            minimum, maximum = maximum, minimum

        return max(minimum, min(maximum, value))


    def _positive_float(self, value, default):
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return float(default)

        if value_float <= 0.0:
            return float(default)

        return value_float


    def _exposure_step(self, current_exposure, *, is_day, day_step_factor, day_min_step, day_max_step):
        if not is_day:
            return max(0.05, current_exposure * self.exposure_step_fraction)

        step = max(day_min_step, current_exposure * day_step_factor)
        return min(day_max_step, step)
