"""Support for the Remora devices."""
from .const import DOMAIN, DATA_REMORA_HOST

import logging
import voluptuous as vol

from homeassistant.const import (CONF_HOST, CONF_SENSORS)
import homeassistant.helpers.config_validation as cv
from datetime import timedelta
from homeassistant.util import Throttle


_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES_REMORA_SENSOR = timedelta(seconds=5)
MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE = timedelta(seconds=2)


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the Remora devices."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    
    # Store config to be used during entry setup
    # hass.data[DATA_REMORA_HOST] = conf[CONF_HOST]
    
    host = conf[CONF_HOST]
    remora = RemoraDevice(host)
    hass.data[DOMAIN] = remora
    # It doesn't really matter why we're not able to get the status, just that
    # we can't.
    try:
        remora.updateTeleInfo(no_throttle=True)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Failure while testing Remora TeleInfo retrieval.")
        return False
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
        
    @property
    def TeleInfo(self):
        """Get latest update if throttle allows. Return TeleInfo."""
        self.updateTeleInfo()
        return self._teleInfo

    def _get_TeleInfo(self):
        """Get the status from Remora TeleInfo and return it as a dict."""
        return self._remora.getTeleInfo()

    @Throttle(MIN_TIME_BETWEEN_UPDATES_REMORA_SENSOR)
    def updateTeleInfo(self, **kwargs):
        """Fetch the latest status from TeleInfo"""
        self._teleInfo = self._get_TeleInfo()

    @property
    def FilPiloteDic(self):
        """Get latest update if throttle allows. Return AllFilPilote."""
        self.updateAllFilPilote()
        return self._filPiloteDic

    def _set_FilPilote(self, num, fpMode):
        return self._remora.setFilPilote(num, fpMode)

    def _get_AllFilPilote(self):
        """Get the status from Remora FilPilote and
        return it as a dict."""
        return self._remora.getAllFilPilote()

    @Throttle(MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE)
    def updateAllFilPilote(self, **kwargs):
        """Fetch the latest status for FilPilote"""
        self._filPiloteDic = self._get_AllFilPilote()


    @property
    def RelaisDic(self):
        """Get latest update if throttle allows.
           Return the current Mode Relais"""
        self.updateRelais()
        return self._relais

    def _set_ModeRelais(self, rMode):
        return self._remora.setFnctRelais(rMode)
    
    def _set_EtatRelais(self, rEtat):
        return self._remora.setRelais(rEtat)

    def _get_Relais(self):
        """Get the status from Remora Relais"""
        return self._remora.getRelais()

    @Throttle(MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE)
    def updateRelais(self, **kwargs):
        """Fetch the latest status for Relais"""
        self._relais = self._get_Relais()