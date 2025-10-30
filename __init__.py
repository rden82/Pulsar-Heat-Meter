"""The Pulsar Heat Meter integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .pulsar_client import PulsarHeatMeterClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pulsar Heat Meter from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create client - исправлен доступ к данным
    client = PulsarHeatMeterClient(
        entry.data["host"],  # Правильный доступ
        entry.data.get("port", 4001),
        entry.data.get("device_address", "10264061")
    )
    
    # Create coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="pulsar_heat_meter",
        update_method=client.get_all_data,
        update_interval=timedelta(seconds=60),
    )
    
    # Create device info
    device_info = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": f"Pulsar Heat Meter {entry.data['host']}",
        "manufacturer": "Pulsar",
        "model": "Heat Meter",
    }
    
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "device_info": device_info,
    }
    
    # Start coordinator
    await coordinator.async_config_entry_first_refresh()
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok