from dataclasses import dataclass


@dataclass(frozen=True)
class AutoExposureDecision:
    action: str
    current_exposure: float
    proposed_exposure: float
    current_gain: float
    proposed_gain: float
    target: float
    error: float
    deadband: float
    shadow: bool = True


class AutoExposureController:
    """Shadow controller for future exposure-first, gain-second decisions."""

    deadband = 10.0
    exposure_step_fraction = 0.25
    gain_step_fraction = 0.15

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
    ):
        smoothed_value = float(smoothed_value)
        current_exposure = float(current_exposure)
        current_gain = float(current_gain)
        exposure_min = float(exposure_min)
        exposure_max = float(exposure_max)
        gain_min = float(gain_min)
        gain_max = float(gain_max)
        target = float(target)

        current_exposure = self._clamp(current_exposure, exposure_min, exposure_max)
        current_gain = self._clamp(current_gain, gain_min, gain_max)
        proposed_exposure = current_exposure
        proposed_gain = current_gain
        error = target - smoothed_value
        action = 'hold'

        if abs(error) <= self.deadband:
            action = 'hold'
        elif error > self.deadband:
            if current_exposure < exposure_max:
                action = 'increase_exposure'
                exposure_step = max(0.05, current_exposure * self.exposure_step_fraction)
                proposed_exposure = self._clamp(current_exposure + exposure_step, exposure_min, exposure_max)
            elif current_gain < gain_max:
                action = 'increase_gain'
                gain_step = max(0.01, max(abs(current_gain), 1.0) * self.gain_step_fraction)
                proposed_gain = self._clamp(current_gain + gain_step, gain_min, gain_max)
        elif error < (self.deadband * -1):
            if current_gain > gain_min:
                action = 'decrease_gain'
                gain_step = max(0.01, max(abs(current_gain), 1.0) * self.gain_step_fraction)
                proposed_gain = self._clamp(current_gain - gain_step, gain_min, gain_max)
            elif current_exposure > exposure_min:
                action = 'decrease_exposure'
                exposure_step = max(0.05, current_exposure * self.exposure_step_fraction)
                proposed_exposure = self._clamp(current_exposure - exposure_step, exposure_min, exposure_max)

        return AutoExposureDecision(
            action=action,
            current_exposure=current_exposure,
            proposed_exposure=proposed_exposure,
            current_gain=current_gain,
            proposed_gain=proposed_gain,
            target=target,
            error=error,
            deadband=self.deadband,
            shadow=True,
        )


    def _clamp(self, value, minimum, maximum):
        if minimum > maximum:
            minimum, maximum = maximum, minimum

        return max(minimum, min(maximum, value))
