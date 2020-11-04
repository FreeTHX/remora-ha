from datetime import timedelta

from homeassistant.util import Throttle

MIN_TIME_BETWEEN_UPDATES_REMORA_SENSOR = timedelta(seconds=5)
MIN_TIME_BETWEEN_UPDATES_REMORA_CLIMATE = timedelta(seconds=2)

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
