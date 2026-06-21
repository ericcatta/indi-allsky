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
    convergence_mode: str = 'normal'
    convergence_frames: int = 0
    fine_convergence: bool = False
    saturated: bool = False
    estimated_exposure: float = 0.0
    correction_ratio: float = 1.0
    safety_limited: bool = False
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
        abs_error = abs(error)
        convergence_mode = 'normal'
        convergence_frames = int(trend_count)
        fine_convergence = False
        saturated = bool(smoothed_value >= 245.0)
        correction_ratio = target / max(smoothed_value, 1.0)
        estimated_exposure = self._clamp(current_exposure * correction_ratio, exposure_min, exposure_max)
        safety_limited = False

        if abs_error <= 1.5:
            action = 'hold'
            reason = 'target_reached'
            blocker = 'target_reached'
            convergence_mode = 'target'

        elif abs_error > 20.0:
            convergence_mode = 'aggressive'
            step_strategy = 'aggressive_bounded'
            if error > 0:
                if current_exposure < exposure_max:
                    action = 'increase_exposure'
                    reason = 'aggressive_increase_exposure'
                    blocker = 'none'
                    exposure_step = self._aggressive_exposure_step(
                        current_exposure,
                        is_day=is_day,
                        day_step_factor=day_step_factor,
                        day_min_step=day_min_step,
                        day_max_step=day_max_step,
                    )
                    safety_limit = current_exposure + exposure_step
                    proposed_exposure = min(estimated_exposure, safety_limit)
                    proposed_exposure = self._clamp(proposed_exposure, exposure_min, exposure_max)
                    safety_limited = proposed_exposure < estimated_exposure
                    exposure_step = max(0.0, proposed_exposure - current_exposure)
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
            else:
                if allow_gain_control and current_gain > gain_min:
                    action = 'decrease_gain'
                    reason = 'decrease_gain_before_exposure'
                    blocker = 'none'
                    gain_step = max(0.01, max(abs(current_gain), 1.0) * self.gain_step_fraction)
                    proposed_gain = self._clamp(current_gain - gain_step, gain_min, gain_max)
                elif current_exposure > exposure_min:
                    action = 'decrease_exposure'
                    reason = 'aggressive_decrease_exposure'
                    blocker = 'none'
                    if current_exposure > 1.0:
                        safety_limit = current_exposure * 0.5
                    elif current_exposure > 0.1:
                        safety_limit = current_exposure * 0.7
                    else:
                        exposure_step = self._exposure_step(
                            current_exposure,
                            is_day=is_day,
                            day_step_factor=day_step_factor,
                            day_min_step=day_min_step,
                            day_max_step=day_max_step,
                        )
                        safety_limit = max(current_exposure - exposure_step, current_exposure * 0.85)

                    proposed_exposure = max(estimated_exposure, safety_limit)
                    proposed_exposure = self._clamp(proposed_exposure, exposure_min, exposure_max)
                    safety_limited = proposed_exposure > estimated_exposure
                    exposure_step = max(0.0, current_exposure - proposed_exposure)
                elif allow_gain_control:
                    reason = 'exposure_and_gain_already_min'
                    blocker = 'exposure_and_gain_already_min'
                else:
                    reason = 'exposure_already_min'
                    blocker = 'exposure_already_min'

        elif abs_error < self.inner_deadband:
            convergence_mode = 'fine'
            if trend_count >= self.trend_frames:
                fine_convergence = True
                trend_active = True
                exposure_step = self._exposure_step(
                    current_exposure,
                    is_day=is_day,
                    day_step_factor=day_step_factor,
                    day_min_step=day_min_step,
                    day_max_step=day_max_step,
                ) / 4.0
                trend_step = exposure_step
                step_strategy = 'fine_convergence_bounded'
                if error > 0:
                    action = 'increase_exposure'
                    reason = 'fine_increase_exposure'
                    blocker = 'none'
                    trend_direction = 'positive'
                    proposed_exposure = self._clamp(current_exposure + trend_step, exposure_min, exposure_max)
                    exposure_step = max(0.0, proposed_exposure - current_exposure)
                else:
                    action = 'decrease_exposure'
                    reason = 'fine_decrease_exposure'
                    blocker = 'none'
                    trend_direction = 'negative'
                    proposed_exposure = self._clamp(current_exposure - trend_step, exposure_min, exposure_max)
                    exposure_step = max(0.0, current_exposure - proposed_exposure)
            else:
                reason = 'fine_trend_not_confirmed'
                blocker = 'trend_not_confirmed'

        elif abs_error <= self.deadband:
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
            convergence_mode=convergence_mode,
            convergence_frames=convergence_frames,
            fine_convergence=fine_convergence,
            saturated=saturated,
            estimated_exposure=estimated_exposure,
            correction_ratio=correction_ratio,
            safety_limited=safety_limited,
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


    def _aggressive_exposure_step(self, current_exposure, *, is_day, day_step_factor, day_min_step, day_max_step):
        if not is_day:
            return max(0.1, current_exposure * (self.exposure_step_fraction * 2.0))

        normal_step = self._exposure_step(
            current_exposure,
            is_day=is_day,
            day_step_factor=day_step_factor,
            day_min_step=day_min_step,
            day_max_step=day_max_step,
        )
        aggressive_step = max(day_min_step, current_exposure * day_step_factor * 2.0)
        return max(normal_step, aggressive_step)
