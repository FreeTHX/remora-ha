"""Support for Remora TeleInfo sensor."""
import asyncio
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_SECONDS,
    CONF_RESOURCES,
    ENERGY_WATT_HOUR,
)
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_PREFIX = "Remora."
SENSOR_TYPES = {
    "_UPTIME": ["Uptime", "mdi:history", SensorDeviceClass.DURATION, None],
    "ADCO": ["Adresse du compteur", "mdi:counter", None, None],
    "OPTARIF": ["Option tarifaire choisie", "mdi:mdi-timer-sand", None, None],
    "ISOUSC": ["Intensité souscrite", "mdi:mdi-flash-outline", SensorDeviceClass.CURRENT, None],
    "BASE": ["Index option Base", "mdi:gauge", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL],
    "HCHC": ["Index option Heures Creuses", "mdi:gauge", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL],
    "HCHP": ["Index option Heures Pleines", "mdi:gauge", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL],
    "EJPHN": ["Index option Heures Normales", "mdi:gauge", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL],
    "EJPHPM": ["Index option Heures de Pointe Mobile", "mdi:gauge", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL],
    "BBRHCJB": [
        "Index option Heures Creuses Jours Bleus",
        "mdi:gauge",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL
    ],
    "BBRHPJB": [
        "Index option Heures Pleines Jours Bleus",
        "mdi:gauge",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL
    ],
    "BBRHCJW": [
        "Index option Heures Creuses Jours Blancs",
        "mdi:gauge",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL
    ],
    "BBRHPJW": [
        "Index option Heures Pleines Jours Blancs",
        "mdi:gauge",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL
    ],
    "BBRHCJR": [
        "Index option Heures Creuses Jours Rouges",
        "mdi:gauge",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL
    ],
    "BBRHPJR": [
        "Index option Heures Pleines Jours Rouges",
        "mdi:gauge",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL
    ],
    "PEJP": ["Préavis Début EJP (30 min)", "mdi:counter", SensorDeviceClass.DURATION, None],
    "PTEC": ["Période Tarifaire en cours", "mdi:chart-timeline", None, None],
    "DEMAIN": ["Couleur du lendemain ", "mdi:counter", None, None],
    "IINST": ["Intensité instantanée", "mdi:flash", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT],
    "ADPS": [
        "Avertissement de Dépassement De Puissance Souscrite",
        "mdi:mdi-flash-red-eye",
        SensorDeviceClass.CURRENT,
        None
    ],
    "IMAX": ["Intensité maximale", "mdi:mdi-flash-red-eye", SensorDeviceClass.CURRENT, None],
    "PAPP": ["Puissance apparente", "mdi:flash", SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT],
    "HHPHC": ["Horaire Heures Pleines Heures Creuses", "mdi:counter", None, None],
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


class RemoraTeleInfoSensor(SensorEntity):
    """Representation of a Remora TeleInfo Sensor."""

    def __init__(self, remora, sensor_type):
        """Initialize the sensor."""
        self._remora = remora
        self.type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[sensor_type][0]
    #    self._unit = SENSOR_TYPES[sensor_type][1]
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the Remora TeleInfo sensor."""
        return self._name

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][1]

    @property
    def state(self) -> bool:
        """Return true if the Remora is online, else False."""
        return self._state

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self.type][2]

    @property
    def state_class(self) -> str | None:
        return SENSOR_TYPES[self.type][3]

    #@property
    #def unit_of_measurement(self) -> str:
    #    """Return the unit of measurement of this entity, if any."""
    #    if not self._unit:
    #        return ""
    #    return self._unit

    async def async_update(self) -> str:
        """Get the latest status and use it to update our sensor state."""
        await self._remora.async_updateTeleInfo()
        if (
            self._remora.TeleInfo is None
            or self.type.upper() not in self._remora.TeleInfo
        ):
            self._state = None
        else:
            self._state = self._remora.TeleInfo[self.type.upper()]
