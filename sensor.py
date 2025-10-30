"""Sensor platform for Pulsar Heat Meter."""
import logging
from typing import Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import (
    UnitOfVolume,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    # Энергии
    "energy": {
        "name": "Энергия",
        "key": "energy",
        "unit": "Gcal",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:fire",
    },
    # Объёмы
    "volume": {
        "name": "Объём прямой",
        "key": "volume",
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:water",
    },
    # Расход
    "flow": {
        "name": "Расход",
        "key": "flow",
        "unit": f"{UnitOfVolume.CUBIC_METERS}/h",
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-pump",
    },
    # Мощность
    "power": {
        "name": "Мощность",
        "key": "power",
        "unit": "Gcal/h",
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    # Температуры
    "supply_temperature": {
        "name": "Температура подачи",
        "key": "supply_temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "return_temperature": {
        "name": "Температура обратки",
        "key": "return_temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "device_temperature": {
        "name": "Температура прибора",
        "key": "device_temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "temperature_difference": {
        "name": "Перепад температур",
        "key": "temperature_difference",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-lines",
    },
    # Счётчики часов
    "total_operating_hours": {
        "name": "Общее время работы",
        "key": "total_operating_hours",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    "normal_operating_hours": {
        "name": "Время нормальной работы",
        "key": "normal_operating_hours",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer-check",
    },
    "error_operating_hours": {
        "name": "Время работы с ошибками",
        "key": "error_operating_hours",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer-alert",
    },
    # Прибор
    "battery_voltage": {
        "name": "Напряжение батареи",
        "key": "battery_voltage",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    # Импульсные входы
    "volume_pulse_1": {
        "name": "Объём импульсный 1",
        "key": "volume_pulse_1",
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:counter",
    },
    "volume_pulse_2": {
        "name": "Объём импульсный 2", 
        "key": "volume_pulse_2",
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:counter",
    },
    "volume_pulse_3": {
        "name": "Горячая вода",  # ← Изменено название
        "key": "volume_pulse_3",
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:water-thermometer",  # Специальная иконка для горячей воды
    },
    "volume_pulse_4": {
        "name": "Холодная вода",  # ← Изменено название
        "key": "volume_pulse_4", 
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:water",  # Иконка для холодной воды
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pulsar Heat Meter sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][entry.entry_id]["device_info"]

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(PulsarHeatMeterSensor(coordinator, sensor_type, device_info, entry.entry_id))

    async_add_entities(sensors)


class PulsarHeatMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pulsar Heat Meter sensor."""

    def __init__(self, coordinator, sensor_type, device_info, entry_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._device_info = device_info
        self._entry_id = entry_id
        
        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = f"{device_info['name']} {sensor_config['name']}"
        self._attr_unique_id = f"{entry_id}_{sensor_type}"
        self._attr_device_info = device_info
        self._attr_icon = sensor_config.get("icon")
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")
        self._attr_native_unit_of_measurement = sensor_config["unit"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        value = self.coordinator.data.get(SENSOR_TYPES[self._sensor_type]["key"])
        
        if value is not None:
            # Округляем значения для лучшего отображения
            if self._sensor_type in ["energy", "volume", "volume_pulse_1", "volume_pulse_2", "volume_pulse_3", "volume_pulse_4"]:
                return round(value, 4)  # Объёмы и энергия
            elif self._sensor_type in ["supply_temperature", "return_temperature", "device_temperature", "temperature_difference"]:
                return round(value, 2)  # Температуры
            elif self._sensor_type in ["flow", "power"]:
                return round(value, 3)  # Расход и мощность
            elif self._sensor_type == "battery_voltage":
                return round(value / 1000.0, 3)  # мВ -> В
            elif self._sensor_type in ["total_operating_hours", "normal_operating_hours", "error_operating_hours"]:
                return int(value)  # Время работы в часах
        
        return value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get(SENSOR_TYPES[self._sensor_type]["key"]) is not None
        )