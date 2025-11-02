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

# Sensors that must be monotonically increasing and non-zero
MONOTONIC_SENSORS = {
    'volume_pulse_3',  # Горячая вода
    'volume_pulse_4',  # Холодная вода  
    'total_operating_hours',
    'energy',
    'volume'
}

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
        "name": "Горячая вода",
        "key": "volume_pulse_3",
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.WATER,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:water-thermometer",
    },
    "volume_pulse_4": {
        "name": "Холодная вода", 
        "key": "volume_pulse_4", 
        "unit": UnitOfVolume.CUBIC_METERS,
        "device_class": SensorDeviceClass.WATER,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:water",
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
        
        # Store previous valid values for monotonic sensors
        self._previous_value = None
        
        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = f"{device_info['name']} {sensor_config['name']}"
        self._attr_unique_id = f"{entry_id}_{sensor_type}"
        self._attr_device_info = device_info
        self._attr_icon = sensor_config.get("icon")
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")
        self._attr_native_unit_of_measurement = sensor_config["unit"]

    def _validate_monotonic_value(self, value: float) -> Optional[float]:
        """Validate that value is increasing and non-zero for monotonic sensors."""
        if self._sensor_type not in MONOTONIC_SENSORS:
            return value
            
        # Filter out zero values
        if value <= 0.001:
            _LOGGER.debug("Filtering out zero value for %s: %f", self._sensor_type, value)
            return self._previous_value
            
        # Check if value is increasing
        if self._previous_value is not None and value < self._previous_value:
            _LOGGER.warning(
                "Value decreased for %s: %f -> %f. Keeping previous value.",
                self._sensor_type, self._previous_value, value
            )
            return self._previous_value
            
        # Value is valid - update previous value
        self._previous_value = value
        return value

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        value = self.coordinator.data.get(SENSOR_TYPES[self._sensor_type]["key"])
        
        if value is not None:
            # Округляем значения для лучшего отображения
            if self._sensor_type in ["energy", "volume", "volume_pulse_1", "volume_pulse_2", "volume_pulse_3", "volume_pulse_4"]:
                value = round(value, 4)  # Объёмы и энергия
            elif self._sensor_type in ["supply_temperature", "return_temperature", "device_temperature", "temperature_difference"]:
                value = round(value, 2)  # Температуры
            elif self._sensor_type in ["flow", "power"]:
                value = round(value, 3)  # Расход и мощность
            elif self._sensor_type == "battery_voltage":
                value = round(value / 1000.0, 3)  # мВ -> В
            elif self._sensor_type in ["total_operating_hours", "normal_operating_hours", "error_operating_hours"]:
                value = int(value)  # Время работы в часах
            
            # Apply monotonic validation for specific sensors
            value = self._validate_monotonic_value(value)
        
        return value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get(SENSOR_TYPES[self._sensor_type]["key"]) is not None
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Initialize previous value from current state if available
        if self._sensor_type in MONOTONIC_SENSORS:
            current_state = self.hass.states.get(self.entity_id)
            if current_state and current_state.state not in ['unavailable', 'unknown', 'None', None]:
                try:
                    self._previous_value = float(current_state.state)
                    _LOGGER.debug("Initialized previous value for %s: %f", self._sensor_type, self._previous_value)
                except (ValueError, TypeError):
                    pass