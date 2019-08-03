import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (ClimateDevice,
                                              PLATFORM_SCHEMA)
from homeassistant.components.climate.const import (SUPPORT_PRESET_MODE,
                                                    HVAC_MODE_OFF,
                                                    HVAC_MODE_HEAT,
                                                    HVAC_MODE_HEAT_COOL,HVAC_MODE_COOL)

from .const import (FILPILOTE, FP, DOMAIN)
from homeassistant.const import (TEMP_CELSIUS, CONF_NAME)
import remora


_LOGGER = logging.getLogger(__name__)

REMORA_PRESET_MODES_TO_HVAC_MODE = {
    remora.FpMode.Arrêt.name: HVAC_MODE_OFF,
    remora.FpMode.HorsGel.name: HVAC_MODE_COOL,
    remora.FpMode.Eco.name: HVAC_MODE_HEAT_COOL,
    remora.FpMode.Confort.name: HVAC_MODE_HEAT
}

FP_CONFIG_SCHEMA = vol.Schema({
    vol.Required(FP): vol.All(vol.Coerce(int), vol.Range(min=0, max=7)),
    vol.Optional(CONF_NAME): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(FILPILOTE): vol.All(cv.ensure_list, [FP_CONFIG_SCHEMA])
})

CLIMATE_PREFIX = 'Remora.'

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Remora FilPilote platform."""
    entities = []
    for fp in config[FILPILOTE]:
        fpnum = fp[FP]
        if CONF_NAME in fp:
            fpname = fp[CONF_NAME]
        else:
            fpname = FP + str(fpnum)
        entities.append(RemoraFilPiloteClimate(hass.data[DOMAIN],
                                               fpnum,
                                               fpname))
    add_devices(entities, True)
 

class RemoraFilPiloteClimate(ClimateDevice):
    def __init__(self, remoraDevice, fpnum, fpname):
        self._remora = remoraDevice
        self._fpnum = fpnum
        self._fp = FP + str(fpnum)
        self._name = fpname
        self._preset_mode = self._remora.FilPiloteDic[self._fp].name

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device. Here just fpX"""
        return CLIMATE_PREFIX + self._name

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return REMORA_PRESET_MODES_TO_HVAC_MODE[self._preset_mode]

    @property
    def hvac_modes(self):
        """Return current operation ie. heat, cool, idle."""
        return list(REMORA_PRESET_MODES_TO_HVAC_MODE.values())

    @property
    def preset_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return the list of available operation modes."""
        return list(REMORA_PRESET_MODES_TO_HVAC_MODE.keys())

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_PRESET_MODE

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        fpmode = self.preset_modes[self.hvac_modes.index(hvac_mode)]
        self.set_preset_mode(fpmode)

    def set_preset_mode(self, preset_mode):
        self._remora._set_FilPilote(self._fpnum, remora.FpMode[preset_mode])
        self._preset_mode = preset_mode
        self.schedule_update_ha_state(True)
        
    def update(self):
        self._preset_mode = self._remora.FilPiloteDic[self._fp].name
