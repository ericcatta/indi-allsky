# Captured from 3a57ee6d before off-grid gain recovery correction.
def recalculate_exposure(self, exposure, gain, adu, target_adu, target_adu_min, target_adu_max, exp_scale_factor):
        # There might be a race condition here if there is a day/night change but self.target_adu_found == True

        # Until we reach a good starting point, do not calculate a moving average
        if adu <= target_adu_max and adu >= target_adu_min:
            logger.warning('Found target value for exposure')
            self.current_adu_target = copy.copy(adu)
            self.target_adu_found = True
            self.hist_adu = []
            return


        if self._auto_gain_enabled():
            # moonmode settings are ignored with auto-gain

            if self.night_av[constants.NIGHT_NIGHT] == 1:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_NIGHT])
            else:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_DAY])

            gain_min, gain_max = self._auto_gain_limits()
        else:
            if self.night_av[constants.NIGHT_NIGHT] == 1:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_NIGHT])

                if self.night_av[constants.NIGHT_MOONMODE] == 1:
                    gain_min = float(self.gain_av[constants.GAIN_MIN_MOONMODE])
                    gain_max = float(self.gain_av[constants.GAIN_MAX_MOONMODE])
                else:
                    gain_min = float(self.gain_av[constants.GAIN_MIN_NIGHT])
                    gain_max = float(self.gain_av[constants.GAIN_MAX_NIGHT])

            else:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_DAY])

                gain_min = float(self.gain_av[constants.GAIN_MIN_DAY])
                gain_max = float(self.gain_av[constants.GAIN_MAX_DAY])


        # Scale the exposure up and down based on targets
        if adu > target_adu_max:
            next_exposure = exposure - ((exposure - (exposure * (target_adu / adu))) * exp_scale_factor)
        elif adu < target_adu_min:
            next_exposure = exposure - ((exposure - (exposure * (target_adu / adu))) * exp_scale_factor)
        else:
            next_exposure = exposure


        # Do not exceed the exposure limits
        if next_exposure < exposure_min:
            next_exposure = float(exposure_min)
        elif next_exposure > self.exposure_av[constants.EXPOSURE_MAX]:
            next_exposure = float(self.exposure_av[constants.EXPOSURE_MAX])


        if self._auto_gain_enabled():
            try:
                auto_gain_idx = self.auto_gain_step_list.index(gain)
            except ValueError:
                # fallback to min if gain does not match
                logger.error('Current gain not found in list, reset to minimum gain')
                auto_gain_idx = 0


            if next_exposure == exposure:
                # no change
                #logger.warning('Auto-Gain - no changes')
                next_gain = gain
                exposure_delta = 0.0
                gain_delta = 0.0
            elif next_exposure > exposure:
                # exposure/gain needs to increase
                if gain == self.auto_gain_step_list[-1]:
                    # already at max gain, increase exposure
                    next_gain = gain
                    exposure_delta = next_exposure - exposure
                    gain_delta = 0.0
                    logger.info('Auto-Gain increasing exposure to %0.6f (%+0.8f) [max gain]', next_exposure, exposure_delta)
                else:
                    if exposure < self.auto_gain_exposure_cutoff_high:
                        # maintain gain, increase exposure
                        next_gain = gain
                        next_exposure = min(next_exposure, self.auto_gain_exposure_cutoff_high)  # prevent hitting max exposure
                        exposure_delta = next_exposure - exposure
                        gain_delta = 0.0
                        logger.info('Auto-Gain increasing exposure to %0.6f (%+0.8f) [maintain gain]', next_exposure, exposure_delta)
                    else:
                        # increase gain, maintain exposure
                        next_gain = self.auto_gain_step_list[auto_gain_idx + 1]
                        next_exposure = min(exposure, self.auto_gain_exposure_cutoff_high)  # prevent hitting max exposure
                        exposure_delta = 0.0
                        gain_delta = next_gain - gain
                        logger.info('Auto-Gain increasing gain to %0.2f (%+0.2f) [maintain exposure]', next_gain, gain_delta)

            else:
                # exposure/gain needs to decrease
                if gain == self.auto_gain_step_list[0]:
                    # already at minimum gain, decrease exposure
                    next_gain = gain
                    exposure_delta = next_exposure - exposure
                    gain_delta = 0.0
                    logger.info('Auto-Gain decreasing exposure to %0.6f (%+0.8f) [minimum gain]', next_exposure, exposure_delta)
                else:
                    if exposure > self.auto_gain_exposure_cutoff_low:
                        # maintain gain, decrease exposure
                        next_gain = gain
                        next_exposure = max(next_exposure, self.auto_gain_exposure_cutoff_low)
                        exposure_delta = next_exposure - exposure
                        gain_delta = 0.0
                        logger.info('Auto-Gain decreasing exposure to %0.6f (%+0.8f) [maintain gain]', next_exposure, exposure_delta)
                    else:
                        # decrease gain, maintain exposure
                        next_gain = self.auto_gain_step_list[auto_gain_idx - 1]
                        #next_exposure = max(exposure, self.auto_gain_exposure_cutoff_low)
                        next_exposure = max(exposure, self.auto_gain_exposure_cutoff_mid)
                        exposure_delta = 0.0
                        gain_delta = next_gain - gain
                        logger.info('Auto-Gain decreasing gain to %0.2f (%+0.2f) [maintain exposure)', next_gain, gain_delta)

        else:
            # just set the gain to the max for the current mode
            next_gain = gain_max
            exposure_delta = next_exposure - exposure
            gain_delta = 0.0


        # Do not exceed the gain limits
        if next_gain > gain_max:
            next_gain = gain_max
        elif next_gain < gain_min:
            next_gain = gain_min


        # Binning
        if self.night_av[constants.NIGHT_NIGHT] == 1:
            if self.night_av[constants.NIGHT_MOONMODE] == 1:
                next_binning = self.binning_av[constants.BINNING_MOONMODE]
            else:
                next_binning = self.binning_av[constants.BINNING_NIGHT]
        else:
            next_binning = self.binning_av[constants.BINNING_DAY]


        ### Check for exposure flapping
        # Flapping is defined when the exposure increases then immediately decreases (or the opposite)
        # and cannot find a stable value.  The result is the image brightness will flash
        if self.exposure_av[constants.EXPOSURE_DELTA] > 0 and exposure_delta < 0:
            # exposure is decreasing
            exposure_offset = exposure_delta / 2
            next_exposure -= exposure_offset  # offset will be negative
            exposure_delta -= exposure_offset

            logger.warning('DETECTED EXPOSURE FLAPPING - Attempting to mitigate by adjusting exposure by %+0.8fs', exposure_offset * -1)
        elif self.exposure_av[constants.EXPOSURE_DELTA] < 0 and exposure_delta > 0:
            # exposure is increasing
            exposure_offset = exposure_delta / 2
            next_exposure -= exposure_offset
            exposure_delta -= exposure_offset

            logger.warning('DETECTED EXPOSURE FLAPPING - Attempting to mitigate by adjusting exposure by %+0.8fs', exposure_offset * -1)


        logger.warning('New calculated exposure: %0.6fs (%+0.8f) @ gain %0.2f (%+0.2f) bin %d', next_exposure, exposure_delta, next_gain, gain_delta, next_binning)
        old_gain_next = float(self.gain_av[constants.GAIN_NEXT])
        with self.exposure_av.get_lock():
            self.exposure_av[constants.EXPOSURE_NEXT] = float(next_exposure)
            self.exposure_av[constants.EXPOSURE_DELTA] = float(exposure_delta)

        with self.gain_av.get_lock():
            self.gain_av[constants.GAIN_NEXT] = float(next_gain)
            self.gain_av[constants.GAIN_DELTA] = float(gain_delta)

        if float(next_gain) != old_gain_next:
            self._save_auto_gain_runtime_state(
                self.profile_id,
                getattr(self, 'camera_id', None),
                self._auto_gain_mode(),
                next_gain,
                gain_min,
                gain_max,
                'runtime_next_changed',
            )

        with self.binning_av.get_lock():
            self.binning_av[constants.BINNING_NEXT] = int(next_binning)
