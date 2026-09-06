"""Manual GPIO planning and read-only observation of the supported RPi.GPIO pins."""


def configured_pins(config):
    settings = config.get('MANUAL_GPIO') or {}
    result = []
    for index in (1, 2, 3):
        name = str(settings.get('A_PIN_'+str(index)) or '')
        try:
            number = int(name)
            if not 0 <= number <= 27:
                raise ValueError()
        except ValueError:
            number = None
        result.append({'id': index, 'name': name, 'number': number, 'state': None})
    return result


def command_target(config, payload):
    if not isinstance(payload, dict):
        raise ValueError('A JSON object is required.')
    if config.get('MANUAL_GPIO', {}).get('A_CLASSNAME') != 'rpigpio_gpio_rpigpio':
        raise ValueError('Configure a supported manual GPIO interface first.')
    # Do not coerce strings such as "false" to a true output level.
    state = payload.get('NEW_PIN_STATE')
    if type(state) not in (int, bool) or state not in (0, 1):
        raise ValueError('Choose an explicit On or Off state.')
    try:
        if isinstance(payload.get('PIN_ID'), bool):
            raise ValueError()
        pin_id = int(payload['PIN_ID'])
        if str(payload['PIN_ID']) != str(pin_id):
            raise ValueError()
        pin = next(pin for pin in configured_pins(config) if pin['id'] == pin_id)
    except (KeyError, ValueError, TypeError, StopIteration):
        raise ValueError('Choose one of the three configured pins.') from None
    if pin['number'] is None:
        raise ValueError('The selected pin is not configured with a valid BCM number.')
    return pin, bool(state)


def observe_pins(config, gpio):
    pins = configured_pins(config)
    if config.get('MANUAL_GPIO', {}).get('A_CLASSNAME') != 'rpigpio_gpio_rpigpio':
        return pins
    # Selecting numbering is process-local; never call setup/output/cleanup on GET.
    if gpio.getmode() is None:
        gpio.setmode(gpio.BCM)
    if gpio.getmode() != gpio.BCM:
        raise ValueError('GPIO numbering mode is incompatible with BCM configuration.')
    for pin in pins:
        if pin['number'] is not None and gpio.gpio_function(pin['number']) == gpio.OUT:
            pin['state'] = int(bool(gpio.input(pin['number'])))
    return pins
