import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature
)
from homeassistant.const import CONF_NAME, TEMP_CELSIUS
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change

import remora

from .const import CONF_TEMP_SENSOR, DOMAIN, FILPILOTE, FNCT_RELAIS, FP, RELAIS

_LOGGER = logging.getLogger(__name__)

REMORA_FP_PRESET_MODES_TO_HVAC_MODE = {
    remora.FpMode.Arrêt.name: HVACMode.OFF,
    remora.FpMode.HorsGel.name: HVACMode.COOL,
    remora.FpMode.Eco.name: HVACMode.HEAT_COOL,
    remora.FpMode.Confort.name: HVACMode.HEAT,
}

REMORA_RELAIS_ETAT_TO_HVAC_MODE = {
    remora.RelaisEtat.Ouvert.name: HVACMode.OFF,
    remora.RelaisEtat.Fermé.name: HVACMode.HEAT,
}

FP_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(FP): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_TEMP_SENSOR): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(FILPILOTE): vol.All(cv.ensure_list, [FP_CONFIG_SCHEMA]),
        vol.Optional(RELAIS, default=True): cv.boolean,
    }
)

CLIMATE_PREFIX = "Remora."


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
            entities.append(
                RemoraFilPiloteClimate(hass.data[DOMAIN], fpnum, fpname, temp_sensor_id)
            )
    if config[RELAIS]:
        entities.append(RemoraRelaisClimate(hass.data[DOMAIN]))

    async_add_devices(entities, True)


class RemoraFilPiloteClimate(ClimateEntity):
    def __init__(self, remoraDevice, fpnum, fpname, temp_sensor_id):
        self._remora = remoraDevice
        self._fpnum = fpnum
        self._fp = FP + str(fpnum)
        self._name = fpname
        self._preset_mode = self._remora.FilPiloteDic[self._fp].name
        self._temp_sensor_id = temp_sensor_id
        self._cur_temp = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if self._temp_sensor_id is not None:
            # Set the current value of the temp_sensor
            current_temp_state = self.hass.states.get(self._temp_sensor_id)
            if current_temp_state is not None:
                self._async_update_temp(current_temp_state)
            # Record a State Changed Listener
            async_track_state_change(
                self.hass, self._temp_sensor_id, self._async_sensor_changed
            )

    async def _async_sensor_changed(self, entity_id, old_state, new_state) -> None:
        if new_state is None:
            return
        self._async_update_temp(new_state)
        # No modification on the heater
        await self.async_update_ha_state()

    @callback
    def _async_update_temp(self, state) -> None:
        """Update thermostat with latest state from sensor."""
        try:
            self._cur_temp = float(state.state)
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return True

    @property
    def name(self) -> str:
        """Return the name of the climate device. Here just fpX"""
        return CLIMATE_PREFIX + self._name

    @property
    def current_temperature(self) -> float:
        """Return the sensor temperature."""
        return self._cur_temp

    @property
    def hvac_mode(self) -> str:
        """Return current operation ie. heat, cool, idle."""
        return REMORA_FP_PRESET_MODES_TO_HVAC_MODE[self._preset_mode]

    @property
    def hvac_modes(self) -> list:
        """Return current operation ie. heat, cool, idle."""
        return list(REMORA_FP_PRESET_MODES_TO_HVAC_MODE.values())

    @property
    def preset_mode(self) -> str:
        """Return current operation ie. heat, cool, idle."""
        return self._preset_mode

    @property
    def preset_modes(self) -> list:
        """Return the list of available operation modes."""
        return list(REMORA_FP_PRESET_MODES_TO_HVAC_MODE.keys())

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return ClimateEntityFeature.PRESET_MODE

    async def async_set_hvac_mode(self, hvac_mode) -> None:
        """Set new target hvac mode."""
        fpmode = self.preset_modes[self.hvac_modes.index(hvac_mode)]
        await self.async_set_preset_mode(fpmode)

    async def async_set_preset_mode(self, preset_mode) -> None:
        await self._remora.async_set_FilPilote(self._fpnum, remora.FpMode[preset_mode])
        self._preset_mode = preset_mode
        self.async_schedule_update_ha_state()

    async def async_update(self) -> None:
        await self._remora.async_updateAllFilPilote()
        self._preset_mode = self._remora.FilPiloteDic[self._fp].name


class RemoraRelaisClimate(ClimateEntity):
    def __init__(self, remoraDevice):
        self._remora = remoraDevice
        self._relais_etat = self._remora.RelaisDic[RELAIS].name
        self._relais_mode = self._remora.RelaisDic[FNCT_RELAIS].name

    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return True

    @property
    def name(self) -> str:
        """Return the name of the climate device. Here just fpX"""
        return CLIMATE_PREFIX + RELAIS

    @property
    def hvac_mode(self) -> str:
        """Return current operation ie. heat, of."""
        return REMORA_RELAIS_ETAT_TO_HVAC_MODE[self._relais_etat]

    @property
    def hvac_modes(self) -> list:
        """Return current operation ie. heat, off."""
        return list(REMORA_RELAIS_ETAT_TO_HVAC_MODE.values())

    @property
    def preset_mode(self) -> str:
        """Return current operation ie. heat, off."""
        return self._relais_mode

    @property
    def preset_modes(self) -> list:
        """Return the list of available operation modes."""
        return list(
            [
                remora.RelaisMode.Arrêt.name,
                remora.RelaisMode.Automatique.name,
                remora.RelaisMode.MarcheForcée.name,
            ]
        )

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return ClimateEntityFeature.PRESET_MODE

    async def async_set_hvac_mode(self, hvac_mode) -> None:
        eMode = [
            key
            for (key, value) in REMORA_RELAIS_ETAT_TO_HVAC_MODE.items()
            if value == hvac_mode
        ][0]
        await self._remora.async_set_EtatRelais(remora.RelaisEtat[eMode])
        self._relais_etat = eMode
        self.async_schedule_update_ha_state()

    async def async_set_preset_mode(self, preset_mode) -> None:
        await self._remora.async_set_ModeRelais(remora.RelaisMode[preset_mode])
        self._preset_mode = preset_mode
        self.async_schedule_update_ha_state()

    async def async_update(self) -> None:
        await self._remora.async_updateRelais()
        self._relais_etat = self._remora.RelaisDic[RELAIS].name
        self._relais_mode = self._remora.RelaisDic[FNCT_RELAIS].name
