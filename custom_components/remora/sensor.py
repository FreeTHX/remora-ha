"""Support for Remora TeleInfo sensor."""
import asyncio
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (ATTR_SECONDS, CONF_RESOURCES,
                                 ENERGY_WATT_HOUR, POWER_WATT)
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_PREFIX = "Remora."
SENSOR_TYPES = {
    "_UPTIME": ["Uptime", ATTR_SECONDS, "mdi:history"],
    "ADCO": ["Adresse du compteur", "", "mdi:counter"],
    "OPTARIF": ["Option tarifaire choisie", "", "mdi:mdi-timer-sand"],
    "ISOUSC": ["Intensité souscrite", "A", "mdi:mdi-flash-outline"],
    "BASE": ["Index option Base", ENERGY_WATT_HOUR, "mdi:gauge"],
    "HCHC": ["Index option Heures Creuses", ENERGY_WATT_HOUR, "mdi:gauge"],
    "HCHP": ["Index option Heures Pleines", ENERGY_WATT_HOUR, "mdi:gauge"],
    "EJPHN": ["Index option Heures Normales", ENERGY_WATT_HOUR, "mdi:gauge"],
    "EJPHPM": ["Index option Heures de Pointe Mobile", ENERGY_WATT_HOUR, "mdi:gauge"],
    "BBRHCJB": [
        "Index option Heures Creuses Jours Bleus",
        ENERGY_WATT_HOUR,
        "mdi:gauge",
    ],
    "BBRHPJB": [
        "Index option Heures Pleines Jours Bleus",
        ENERGY_WATT_HOUR,
        "mdi:gauge",
    ],
    "BBRHCJW": [
        "Index option Heures Creuses Jours Blancs",
        ENERGY_WATT_HOUR,
        "mdi:gauge",
    ],
    "BBRHPJW": [
        "Index option Heures Pleines Jours Blancs",
        ENERGY_WATT_HOUR,
        "mdi:gauge",
    ],
    "BBRHCJR": [
        "Index option Heures Creuses Jours Rouges",
        ENERGY_WATT_HOUR,
        "mdi:gauge",
    ],
    "BBRHPJR": [
        "Index option Heures Pleines Jours Rouges",
        ENERGY_WATT_HOUR,
        "mdi:gauge",
    ],
    "PEJP": ["Préavis Début EJP (30 min)", "min", "mdi:counter"],
    "PTEC": ["Période Tarifaire en cours", "", "mdi:chart-timeline"],
    "DEMAIN": ["Couleur du lendemain ", "", "mdi:counter"],
    "IINST": ["Intensité instantanée", "A", "mdi:flash"],
    "ADPS": [
        "Avertissement de Dépassement De Puissance Souscrite",
        "A",
        "mdi:mdi-flash-red-eye",
    ],
    "IMAX": ["Intensité maximale", "A", "mdi:mdi-flash-red-eye"],
    "PAPP": ["Puissance apparente", "VA", "mdi:flash"],
    "HHPHC": ["Horaire Heures Pleines Heures Creuses", "A", "mdi:counter"],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RESOURCES, default=[]): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        )
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Remora TeleInfo sensors."""
    entities = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.upper()

        if sensor_type not in SENSOR_TYPES:
            _LOGGER.warning(
                "Sensor type: %s does not appear in TeleInfo output", sensor_type
            )
            return

        entities.append(RemoraTeleInfoSensor(hass.data[DOMAIN], sensor_type))

    async_add_entities(entities, True)


class RemoraTeleInfoSensor(Entity):
    """Representation of a Remora TeleInfo Sensor."""

    def __init__(self, remora, sensor_type):
        """Initialize the sensor."""
        self._remora = remora
        self.type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[sensor_type][0]
        self._unit = SENSOR_TYPES[sensor_type][1]
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the Remora TeleInfo sensor."""
        return self._name

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][2]

    @property
    def state(self) -> bool:
        """Return true if the Remora is online, else False."""
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity, if any."""
        if not self._unit:
            return ""
        return self._unit

    async def async_update(self) -> str:
        """Get the latest status and use it to update our sensor state."""
        await self._remora.async_updateTeleInfo()
        if self.type.upper() not in self._remora.TeleInfo:
            self._state = None
        else:
            self._state = self._remora.TeleInfo[self.type.upper()]
