import logging
import voluptuous as vol
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change
from homeassistant.components.climate import (ClimateDevice,
                                              PLATFORM_SCHEMA)
from homeassistant.components.climate.const import (SUPPORT_PRESET_MODE,
                                                    HVAC_MODE_OFF,
                                                    HVAC_MODE_HEAT,
                                                    HVAC_MODE_HEAT_COOL,HVAC_MODE_COOL)

from .const import (FILPILOTE,
                    FP,
                    RELAIS,
                    FNCT_RELAIS,
                    DOMAIN,
                    CONF_TEMP_SENSOR)
from homeassistant.const import (TEMP_CELSIUS, CONF_NAME)
import remora


_LOGGER = logging.getLogger(__name__)

REMORA_FP_PRESET_MODES_TO_HVAC_MODE = {
    remora.FpMode.Arrêt.name: HVAC_MODE_OFF,
    remora.FpMode.HorsGel.name: HVAC_MODE_COOL,
    remora.FpMode.Eco.name: HVAC_MODE_HEAT_COOL,
    remora.FpMode.Confort.name: HVAC_MODE_HEAT
}

REMORA_RELAIS_ETAT_TO_HVAC_MODE = {
    remora.RelaisEtat.Ouvert.name: HVAC_MODE_OFF,
    remora.RelaisEtat.Fermé.name: HVAC_MODE_HEAT,
}

FP_CONFIG_SCHEMA = vol.Schema({
    vol.Required(FP): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_TEMP_SENSOR): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(FILPILOTE): vol.All(cv.ensure_list, [FP_CONFIG_SCHEMA]),
    vol.Optional(RELAIS, default=True): cv.boolean
})

CLIMATE_PREFIX = 'Remora.'

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the Remora FilPilote and Relais platform."""
    entities = []
    if FILPILOTE in config:
        for fp in config[FILPILOTE]:
            fpnum = fp[FP]
            if CONF_NAME in fp:
                fpname = fp[CONF_NAME]
            else:
                fpname = FP + str(fpnum)
            if CONF_TEMP_SENSOR in fp:
                temp_sensor_id = fp[CONF_TEMP_SENSOR]
            else:
                temp_sensor_id = None
            entities.append(RemoraFilPiloteClimate(hass.data[DOMAIN],
                                                   fpnum,
                                                   fpname,
                                                   temp_sensor_id))
    if config[RELAIS]:
        entities.append(RemoraRelaisClimate(hass.data[DOMAIN]))

    async_add_devices(entities, True)
 

class RemoraFilPiloteClimate(ClimateDevice):
    def __init__(self, remoraDevice, fpnum, fpname, temp_sensor_id):
        self._remora = remoraDevice
        self._fpnum = fpnum
        self._fp = FP + str(fpnum)
        self._name = fpname
        self._preset_mode = self._remora.FilPiloteDic[self._fp].name
        self._temp_sensor_id = temp_sensor_id
        self._cur_temp = None

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        # Add listener if  is set
        if self._temp_sensor_id is not None:
            async_track_state_change(
                self.hass, self._temp_sensor_id, self._async_sensor_changed
            )


    async def _async_sensor_changed(self, entity_id, old_state, new_state):
        """Handle temperature changes."""
        if new_state is None:
            return

        self._async_update_temp(new_state)
        # No modification on the heater
        await self.async_update_ha_state()

    @callback
    def _async_update_temp(self, state):
        """Update thermostat with latest state from sensor."""
        try:
            self._cur_temp = float(state.state)
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device. Here just fpX"""
        return CLIMATE_PREFIX + self._name

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._cur_temp

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return REMORA_FP_PRESET_MODES_TO_HVAC_MODE[self._preset_mode]

    @property
    def hvac_modes(self):
        """Return current operation ie. heat, cool, idle."""
        return list(REMORA_FP_PRESET_MODES_TO_HVAC_MODE.values())

    @property
    def preset_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return the list of available operation modes."""
        return list(REMORA_FP_PRESET_MODES_TO_HVAC_MODE.keys())

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_PRESET_MODE

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        fpmode = self.preset_modes[self.hvac_modes.index(hvac_mode)]
        await self.async_set_preset_mode(fpmode)

    async def async_set_preset_mode(self, preset_mode):
        await self.hass.async_add_executor_job( self._remora._set_FilPilote, self._fpnum, remora.FpMode[preset_mode])    
        #self._remora._set_FilPilote(self._fpnum, remora.FpMode[preset_mode])
        self._preset_mode = preset_mode
        self.async_schedule_update_ha_state(True)
        
    async def async_update(self):
        self._preset_mode = self._remora.FilPiloteDic[self._fp].name


class RemoraRelaisClimate(ClimateDevice):
    def __init__(self, remoraDevice):
        self._remora = remoraDevice
        self._relais_etat = self._remora.RelaisDic[RELAIS].name
        self._relais_mode = self._remora.RelaisDic[FNCT_RELAIS].name
        
    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device. Here just fpX"""
        return CLIMATE_PREFIX + RELAIS

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, of."""
        return REMORA_RELAIS_ETAT_TO_HVAC_MODE[self._relais_etat]

    @property
    def hvac_modes(self):
        """Return current operation ie. heat, off."""
        return list(REMORA_RELAIS_ETAT_TO_HVAC_MODE.values())

    @property
    def preset_mode(self):
        """Return current operation ie. heat, off."""
        return self._relais_mode

    @property
    def preset_modes(self):
        """Return the list of available operation modes."""
        return list([remora.RelaisMode.Arrêt.name,
                     remora.RelaisMode.Automatique.name,
                     remora.RelaisMode.MarcheForcée.name])

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_PRESET_MODE

    async def async_set_hvac_mode(self, hvac_mode):
        eMode = [key for (key, value) in REMORA_RELAIS_ETAT_TO_HVAC_MODE.items()             if value == hvac_mode][0]
        await self.hass.async_add_executor_job( self._remora._set_EtatRelais, remora.RelaisEtat[eMode])
        #self._remora._set_EtatRelais(remora.RelaisEtat[eMode])
        self._relais_etat = eMode
        self.async_schedule_update_ha_state(True)

    async def async_set_preset_mode(self, preset_mode):
        await self.hass.async_add_executor_job( self._remora._set_ModeRelais, remora.RelaisMode[preset_mode])
        #self._remora._set_ModeRelais(remora.RelaisMode[preset_mode])
        self._preset_mode = preset_mode
        self.async_schedule_update_ha_state(True)
        
    async def async_update(self):
        self._relais_etat = self._remora.RelaisDic[RELAIS].name
        self._relais_mode = self._remora.RelaisDic[FNCT_RELAIS].name