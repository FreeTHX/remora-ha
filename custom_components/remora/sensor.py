"""Support for Remora TeleInfo sensor."""
import asyncio
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_RESOURCES,
    TIME_SECONDS,
    TIME_MINUTES,
    #UnitOfTime,
    ELECTRIC_CURRENT_AMPERE,
    #UnitOfElectricCurrent,
    ENERGY_WATT_HOUR,
    #UnitOfEnergy,
    POWER_VOLT_AMPERE,
    #UnitOfApparentPower,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_PREFIX = "Remora."


DEVICE_CLASS = "device_class"
STATE_CLASS = "state_class"
DESCRIPTION = "description"
ICON = "icon"
UNIT = "unit"
SENSOR_TYPES: dict[str, dict[str, str]] = {
    "ADCO": {
        DESCRIPTION: "Adresse du compteur",
        ICON: "mdi:counter"
    },
    "OPTARIF": {        
        DESCRIPTION: "Option tarifaire choisie",
        ICON: "mdi:mdi-timer-sand",
    },
    "ISOUSC": {        
        DESCRIPTION: "Intensité souscrite",
        ICON: "mdi:mdi-flash-outline",
        DEVICE_CLASS: SensorDeviceClass.CURRENT,
        #UNIT: UnitOfElectricCurrent.AMPERE
        UNIT: ELECTRIC_CURRENT_AMPERE
    },
    "BASE": {        
        DESCRIPTION: "Index option Base",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "HCHC": {        
        DESCRIPTION: "Index option Heures Creuses",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "HCHP": {        
        DESCRIPTION: "Index option Heures Pleines",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "EJPHN": {        
        DESCRIPTION: "Index option Heures Normales",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "EJPHPM": {        
        DESCRIPTION: "Index option Heures de Pointe Mobile",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "BBRHCJB": {        
        DESCRIPTION: "Index option Heures Creuses Jours Bleus",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "BBRHPJB": {        
        DESCRIPTION: "Index option Heures Pleines Jours Bleus",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "BBRHCJW": {        
        DESCRIPTION: "Index option Heures Creuses Jours Blancs",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "BBRHPJW": {        
        DESCRIPTION: "Index option Heures Pleines Jours Blancs",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "BBRHCJR": {        
        DESCRIPTION: "Index option Heures Creuses Jours Rouges",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "BBRHPJR": {        
        DESCRIPTION: "Index option Heures Pleines Jours Rouges",
        ICON: "mdi:gauge",
        DEVICE_CLASS: SensorDeviceClass.ENERGY,
        STATE_CLASS: SensorStateClass.TOTAL,
        #UNIT: UnitOfEnergy.WATT_HOUR
        UNIT: ENERGY_WATT_HOUR
    },
    "PEJP": {        
        DESCRIPTION: "Préavis Début EJP (30 min)",
        ICON: "mdi:counter",
        DEVICE_CLASS: SensorDeviceClass.DURATION,
        #UNIT: UnitOfTime.MINUTES
        UNIT: TIME_MINUTES
    },
    "PTEC": {        
        DESCRIPTION: "Période Tarifaire en cours",
        ICON: "mdi:chart-timeline"
    },
    "DEMAIN": {        
        DESCRIPTION: "Couleur du lendemain",
        ICON: "mdi:counter"
    },
    "IINST": {        
        DESCRIPTION: "Intensité instantanée",
        ICON: "mdi:flash",
        DEVICE_CLASS: SensorDeviceClass.CURRENT,
        STATE_CLASS: SensorStateClass.MEASUREMENT,
        #UNIT: UnitOfElectricCurrent.AMPERE
        UNIT: ELECTRIC_CURRENT_AMPERE
    },
    "ADPS": {        
        DESCRIPTION: "Avertissement de Dépassement De Puissance Souscrite",
        ICON: "mdi:mdi-flash-red-eye",
        DEVICE_CLASS: SensorDeviceClass.CURRENT,
        #UNIT: UnitOfElectricCurrent.AMPERE
        UNIT: ELECTRIC_CURRENT_AMPERE
    },
    "IMAX": {        
        DESCRIPTION: "Intensité maximale",
        ICON: "mdi:mdi-flash-red-eye",
        DEVICE_CLASS: SensorDeviceClass.CURRENT,
        #UNIT: UnitOfElectricCurrent.AMPERE
        UNIT: ELECTRIC_CURRENT_AMPERE
    },
    "PAPP": {        
        DESCRIPTION: "Puissance apparente",
        ICON: "mdi:flash",
        DEVICE_CLASS: SensorDeviceClass.APPARENT_POWER,
        STATE_CLASS: SensorStateClass.MEASUREMENT,
        #UNIT: UnitOfApparentPower.VOLT_AMPERE
        UNIT: POWER_VOLT_AMPERE
    },
    "HHPHC": {        
        DESCRIPTION: "Horaire Heures Pleines Heures Creuses",
        ICON: "mdi:counter"
    }
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
        self._name = SENSOR_PREFIX + SENSOR_TYPES.get( self.type , {}).get(DESCRIPTION)
        self._icon = SENSOR_TYPES.get( self.type, {}).get(ICON)
        self._device_class = SENSOR_TYPES.get( self.type, {}).get(DEVICE_CLASS)
        self._state_class = SENSOR_TYPES.get( self.type, {}).get(STATE_CLASS)
        self._unit = SENSOR_TYPES.get( self.type, {}).get(UNIT)
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the Remora TeleInfo sensor."""
        return self._name

    @property
    def icon(self) -> str | None:
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def state_class(self) -> str | None:
        return self._state_class
        
    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @property
    def suggested_unit_of_measurement(self) -> str | None:
        return self._unit
        
    async def async_update(self) -> None:
        """Get the latest status and use it to update our sensor state."""
        await self._remora.async_updateTeleInfo()
        if (
            self._remora.TeleInfo is None
            or self.type.upper() not in self._remora.TeleInfo
        ):
            self._state = None
        else:
            self._state = self._remora.TeleInfo[self.type.upper()]
