"""Support for the Remora devices."""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_SENSORS
from homeassistant.util import Throttle

from .const import DOMAIN, SERVICE_RESET

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES_REMORA_SENSOR = timedelta(seconds=5)
MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE = timedelta(seconds=2)


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_HOST): cv.string})}, extra=vol.ALLOW_EXTRA
)

RESET_SCHEMA = vol.Schema({})


async def async_setup(hass, config):
    """Set up the Remora devices."""
    if DOMAIN not in config:
        return True

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
        _LOGGER.exception("Failure while testing Remora TeleInfo retrieval.")
        return False

    async def async_reset(service):
        await hass.data[DOMAIN].async_reset()

    hass.services.async_register(DOMAIN, SERVICE_RESET, async_reset, RESET_SCHEMA)

    return True


class RemoraDevice:
    """Stores the data retrieved from Remora.
    For each entity to use, acts as the single point responsible for fetching
    updates from the server.
    """

    def __init__(self, host):
        """Initialize the data object."""
        import remora

        self._host = host
        self._remora = remora.RemoraDevice(self._host)
        self._teleInfo = None
        self._filPiloteDic = None
        self._relais = None

    async def async_reset(self) -> bool:
        """Reset remora."""
        return await self._remora.reset()

    @property
    def TeleInfo(self) -> dict:
        """Return TeleInfo."""
        return self._teleInfo

    async def async_get_TeleInfo(self) -> dict:
        """Get the status from Remora TeleInfo and return it as a dict."""
        return (await self._remora.getTeleInfo())

    @Throttle(MIN_TIME_BETWEEN_UPDATES_REMORA_SENSOR)
    async def async_updateTeleInfo(self, **kwargs) -> None:
        """Fetch the latest status from TeleInfo"""
        self._teleInfo = await self.async_get_TeleInfo()

    @property
    def FilPiloteDic(self) -> dict:
        """Return AllFilPilote."""
        return self._filPiloteDic

    async def async_set_FilPilote(self, num, fpMode) -> bool:
        return (await self._remora.setFilPilote(num, fpMode))

    async def async_get_AllFilPilote(self) -> dict:
        """Get the status from Remora FilPilote and
        return it as a dict."""
        return (await self._remora.getAllFilPilote())

    @Throttle(MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE)
    async def async_updateAllFilPilote(self, **kwargs) -> None:
        """Fetch the latest status for FilPilote"""
        self._filPiloteDic = await self.async_get_AllFilPilote()

    @property
    def RelaisDic(self) -> dict:
        """Get latest update if throttle allows.
           Return the current Mode Relais"""
        return self._relais

    async def async_set_ModeRelais(self, rMode) -> bool:
        return (await self._remora.setFnctRelais(rMode))

    async def async_set_EtatRelais(self, rEtat) -> bool:
        return (await self._remora.setRelais(rEtat))

    async def async_get_Relais(self) -> dict:
        """Get the status from Remora Relais"""
        return (await self._remora.getRelais())

    @Throttle(MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE)
    async def async_updateRelais(self, **kwargs) -> None:
        """Fetch the latest status for Relais"""
        self._relais = await self.async_get_Relais()
