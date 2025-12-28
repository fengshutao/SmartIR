"""Config flow for SmartIR integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_TYPES = [
    ("climate", "Climate"),
    ("fan", "Fan"),
    ("light", "Light"),
    ("media_player", "Media Player"),
]


class SmartIRConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartIR."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}
        self._device_type: str = ""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._device_type = user_input["device_type"]
            self._data = user_input
            return await self.async_step_device_config()

        # First step: select device type
        schema = vol.Schema({
            vol.Required("device_type", default="climate"): vol.In(dict(DEVICE_TYPES)),
            vol.Required("name"): str,
            vol.Optional("unique_id"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"device_type": ""},
        )

    async def async_step_device_config(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle device-specific configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Combine data from both steps
            full_data = {**self._data, **user_input}
            
            # Generate a unique ID if not provided
            if not full_data.get("unique_id"):
                full_data["unique_id"] = f"smartir_{full_data['device_code']}_{self._device_type}"
            
            return self.async_create_entry(
                title=full_data["name"],
                data={},
                options=full_data,
            )

        # Build schema based on device type
        fields = {
            vol.Required("device_code"): cv.positive_int,
            vol.Required("controller_data"): str,
            vol.Optional("delay", default=0.5): cv.positive_float,
            vol.Optional("power_sensor"): str,
        }

        # Add device-specific fields
        if self._device_type == "climate":
            fields[vol.Optional("temperature_sensor")] = str
            fields[vol.Optional("humidity_sensor")] = str
            fields[vol.Optional("power_sensor_restore_state", default=False)] = bool
        elif self._device_type == "media_player":
            fields[vol.Optional("device_class", default="tv")] = str
            fields[vol.Optional("source_names")] = str

        schema = vol.Schema(fields)

        return self.async_show_form(
            step_id="device_config",
            data_schema=schema,
            errors=errors,
            description_placeholders={"device_type": self._device_type},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SmartIROptionsFlow(config_entry)


class SmartIROptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for SmartIR."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # 修复：正确调用父类初始化，避免弃用警告
        super().__init__()
        self._config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        device_type = self._config_entry.options.get("device_type", "climate")
        
        # Common fields
        fields = {
            vol.Optional("name", default=self.options.get("name", "")): str,
            vol.Optional("device_code", default=self.options.get("device_code", 0)): cv.positive_int,
            vol.Optional("controller_data", default=self.options.get("controller_data", "")): str,
            vol.Optional("delay", default=self.options.get("delay", 0.5)): cv.positive_float,
            vol.Optional("power_sensor", default=self.options.get("power_sensor", "")): str,
        }
        
        # Device-specific fields
        if device_type == "climate":
            fields[vol.Optional("temperature_sensor", default=self.options.get("temperature_sensor", ""))] = str
            fields[vol.Optional("humidity_sensor", default=self.options.get("humidity_sensor", ""))] = str
            fields[vol.Optional("power_sensor_restore_state", default=self.options.get("power_sensor_restore_state", False))] = bool
        
        elif device_type == "media_player":
            fields[vol.Optional("device_class", default=self.options.get("device_class", "tv"))] = str
            fields[vol.Optional("source_names", default=self.options.get("source_names", ""))] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(fields)

        )
