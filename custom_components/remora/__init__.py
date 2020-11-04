"""Support for the Remora devices."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_SENSORS
from .remora import RemoraDevice
from .const import DOMAIN, SERVICE_RESET

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_HOST): cv.string})}, extra=vol.ALLOW_EXTRA
)

RESET_SCHEMA = vol.Schema({})


async def async_setup(hass, config) -> bool:
    """Set up the Remora devices."""
    if DOMAIN not in config:
        _LOGGER.error("Unable to find " + DOMAIN + " in configuration")
        return False

    conf = config[DOMAIN]

    host = conf[CONF_HOST]
    remora = RemoraDevice(host)
    hass.data[DOMAIN] = remora
    # It doesn't really matter why we're not able to get the status,
    # just that we can't.
    try:
        await remora.async_updateTeleInfo()
        await remora.async_updateAllFilPilote()
        await remora.async_updateRelais()
        # must add keyword param no_throttle=True
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Failure while testing Remora device.")
        return False

    async def async_reset(service):
        await hass.data[DOMAIN].async_reset()

    hass.services.async_register(DOMAIN, SERVICE_RESET, async_reset, RESET_SCHEMA)

    return True