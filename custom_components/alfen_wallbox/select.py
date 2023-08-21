import logging
from typing import Final, Any

from dataclasses import dataclass

from homeassistant.helpers import entity_platform

from .const import ID, SERVICE_DISABLE_RFID_AUTHORIZATION_MODE, SERVICE_ENABLE_RFID_AUTHORIZATION_MODE, SERVICE_SET_CURRENT_PHASE, VALUE
from .entity import AlfenEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alfen import AlfenDevice

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)

from homeassistant.core import HomeAssistant, callback
from . import DOMAIN as ALFEN_DOMAIN

import voluptuous as vol


_LOGGER = logging.getLogger(__name__)


@dataclass
class AlfenSelectDescriptionMixin:
    """Define an entity description mixin for select entities."""

    api_param: str
    options_dict: dict[str, int]


@dataclass
class AlfenSelectDescription(SelectEntityDescription, AlfenSelectDescriptionMixin):
    """Class to describe an Alfen select entity."""


CHARGING_MODE_DICT: Final[dict[str, int]] = {
    "Disable": 0, "Comfort": 1, "Green": 2}

PHASE_ROTATION_DICT: Final[dict[str, str]] = {
    "L1": "L1",
    "L2": "L2",
    "L3": "L3",
    "L1,L2,L3": "L1L2L3",
    "L1,L3,L2": "L1L3L2",
    "L2,L1,L3": "L2L1L3",
    "L2,L3,L1": "L2L3L1",
    "L3,L1,L2": "L3L1L2",
    "L3,L2,L1": "L3L2L1",
}

AUTH_MODE_DICT: Final[dict[str, int]] = {
    "Plug and Charge": 0,
    "RFID": 2
}

LOAD_BALANCE_MODE_DICT: Final[dict[str, int]] = {
    "Modbus TCP/IP": 0,
    "DSMR4.x / SMR5.0 (P1)": 3
}

LOAD_BALANCE_DATA_SOURCE_DICT: Final[dict[str, int]] = {
    "Meter": 0,
    "Meter + EMS Monitoring": 1,
    "Energy Management System": 3
}

LOAD_BALANCE_RECEIVED_MEASUREMENTS_DICT: Final[dict[str, int]] = {
    "Exclude Charging Ev": 0,
    "Include Charging Ev": 1
}

DISPLAY_LANGUAGE_DICT: Final[dict[str, str]] = {
    "Czech": "cz_CZ",
    "Danish": "da_DK",
    "Dutch": "nl_NL",
    "English": "en_GB",
    "Finnish": "fi_FI",
    "French": "fr_FR",
    "German": "de_DE",
    "Hungarian": "hu_HU",
    "Icelandic": "is_IS",
    "Italian": "it_IT",
    "Norwegian": "no_NO",
    "Polish": "pl_PL",
    "Portuguese": "pt_PT",
    "Romanian": "ro_RO",
    "Spanish": "es_ES",
    "Swedish": "sv_SE",
}

ALLOWED_PHASE_DICT: Final[dict[str, int]] = {
    "1 Phase": 1,
    "3 Phases": 3,
}

PRIORITIES_DICT: Final[dict[str, int]] = {
    "Disable": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4
}

OPERATIVE_MODE_DICT: Final[dict[str, int]] = {
    "Operative": 0,
    "In-operative": 2,
}

GPRS_NETWORK_MODE_DICT: Final[dict[str, int]] = {
    "Automatic": 0,
    "Manual": 1
}

GPRS_TECHNOLOGY_DICT: Final[dict[str, int]] = {
    "2G (GPRS)": 0,
    "3G (UMTS)": 1,
    "4G (LTE)": 2,
}

DSMR_SMR_INTERFACE_DICT: Final[dict[str, int]] = {
    "Serial" : 0,
    "Telnet" : 1,
    "HomeWizard Wi-Fi P1": 2,
}

DIRECT_EXTERNAL_SUSPEND_SIGNAL: Final[dict[str, int]] = {
    "Not allowed": 0,
    "Allowed, suspend when closed": 1,
    "Allowed, suspend when open": 2
}

ALFEN_SELECT_TYPES: Final[tuple[AlfenSelectDescription, ...]] = (
    AlfenSelectDescription(
        key="lb_solar_charging_mode",
        name="Solar Charging Mode",
        icon="mdi:solar-power",
        options=list(CHARGING_MODE_DICT),
        options_dict=CHARGING_MODE_DICT,
        api_param="3280_1",
    ),

    AlfenSelectDescription(
        key="lb_phase_connection",
        name="Load Balancing Phase Connection",
        icon=None,
        options=list(PHASE_ROTATION_DICT),
        options_dict=PHASE_ROTATION_DICT,
        api_param="2069_0",
    ),
    AlfenSelectDescription(
        key="auth_mode",
        name="Auth. Mode",
        icon="mdi:key",
        options=list(AUTH_MODE_DICT),
        options_dict=AUTH_MODE_DICT,
        api_param="2126_0",
    ),

    AlfenSelectDescription(
        key="load_balancing_mode",
        name="Load Balancing Mode",
        icon="mdi:scale-balance",
        options=list(LOAD_BALANCE_MODE_DICT),
        options_dict=LOAD_BALANCE_MODE_DICT,
        api_param="2064_0",
    ),
    AlfenSelectDescription(
        key="lb_active_balancing_received_measurements",
        name="Load Balancing Received Measurements",
        icon="mdi:scale-balance",
        options=list(LOAD_BALANCE_RECEIVED_MEASUREMENTS_DICT),
        options_dict=LOAD_BALANCE_RECEIVED_MEASUREMENTS_DICT,
        api_param="206F_0",
    ),
    AlfenSelectDescription(
        key="display_language",
        name="Display Language",
        icon="mdi:translate",
        options=list(DISPLAY_LANGUAGE_DICT),
        options_dict=DISPLAY_LANGUAGE_DICT,
        api_param="205D_0",
    ),
    AlfenSelectDescription(
        key="bo_network_1_connection_priority",
        name="Backoffice Network 1 Connection Priority (Ethernet)",
        icon="mdi:ethernet-cable",
        options=list(PRIORITIES_DICT),
        options_dict=PRIORITIES_DICT,
        api_param="20F0_E",
    ),
    AlfenSelectDescription(
        key="bo_network_2_connection_priority",
        name="Backoffice Network 2 Connection Priority (GPRS)",
        icon="mdi:antenna",
        options=list(PRIORITIES_DICT),
        options_dict=PRIORITIES_DICT,
        api_param="20F1_E",
    ),
    AlfenSelectDescription(
        key="socket_1_operation_mode",
        name="Socket 1 Operation Mode",
        icon="mdi:power-socket-eu",
        options=list(OPERATIVE_MODE_DICT),
        options_dict=OPERATIVE_MODE_DICT,
        api_param="205F_0",
    ),
    AlfenSelectDescription(
        key="gprs_network_mode",
        name="GPRS Network Mode",
        icon="mdi:antenna",
        options=list(GPRS_NETWORK_MODE_DICT),
        options_dict=GPRS_NETWORK_MODE_DICT,
        api_param="2113_0",
    ),
    AlfenSelectDescription(
        key="gprs_technology",
        name="GPRS Technology",
        icon="mdi:antenna",
        options=list(GPRS_TECHNOLOGY_DICT),
        options_dict=GPRS_TECHNOLOGY_DICT,
        api_param="2114_0",
    ),
     AlfenSelectDescription(
        key="lb_dsmr_smr_interface",
        name="Load Balancing DSMR/SMR Interface",
        icon="mdi:scale-balance",
        options=list(DSMR_SMR_INTERFACE_DICT),
        options_dict=DSMR_SMR_INTERFACE_DICT,
        api_param="2191_1",
    ),
    AlfenSelectDescription(
        key="lb_data_source",
        name="Load Balancing Data Source",
        icon="mdi:scale-balance",
        options=list(LOAD_BALANCE_DATA_SOURCE_DICT),
        options_dict=LOAD_BALANCE_DATA_SOURCE_DICT,
        api_param="2530_1",
    ),
    AlfenSelectDescription(
        key="ps_installation_max_allowed_phase",
        name="Installation Max. Allowed Phases",
        icon="mdi:scale-balance",
        options=list(ALLOWED_PHASE_DICT),
        options_dict=ALLOWED_PHASE_DICT,
        api_param="2189_0",
    ),
    AlfenSelectDescription(
        key="ps_installation_direct_external_suspend_signal",
        name="Installation Direct External Suspend Signal",
        icon="mdi:scale-balance",
        options=list(DIRECT_EXTERNAL_SUSPEND_SIGNAL),
        options_dict=DIRECT_EXTERNAL_SUSPEND_SIGNAL,
        api_param="216C_0",
    ),

)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Alfen Select from a config_entry"""

    device = hass.data[ALFEN_DOMAIN][entry.entry_id]
    selects = [AlfenSelect(device, description)
               for description in ALFEN_SELECT_TYPES]

    async_add_entities(selects)

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_SET_CURRENT_PHASE,
        {
            vol.Required("phase"): str,
        },
        "async_set_current_phase",
    )

    platform.async_register_entity_service(
        SERVICE_ENABLE_RFID_AUTHORIZATION_MODE,
        {},
        "async_enable_rfid_auth_mode",
    )

    platform.async_register_entity_service(
        SERVICE_DISABLE_RFID_AUTHORIZATION_MODE,
        {},
        "async_disable_rfid_auth_mode",
    )

class AlfenSelect(AlfenEntity, SelectEntity):
    """Define Alfen select."""

    values_dict: dict[int, str]

    def __init__(
        self, device: AlfenDevice, description: AlfenSelectDescription
    ) -> None:
        """Initialize."""
        super().__init__(device)
        self._device = device
        self._attr_name = f"{device.name} {description.name}"

        self._attr_unique_id = f"{self._device.id}_{description.key}"
        self._attr_options = description.options
        self.entity_description = description
        self.values_dict = {v: k for k, v in description.options_dict.items()}
        self._async_update_attrs()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value = {v: k for k, v in self.values_dict.items()}[option]
        await self.update_state(self.entity_description.api_param, value)
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        value = self._get_current_option()
        return self.values_dict.get(value)

    def _get_current_option(self) -> str | None:
        """Return the current option."""
        for prop in self._device.properties:
            if prop[ID] == self.entity_description.api_param:
                return prop[VALUE]
        return None

    async def async_update(self):
        """Update the entity."""
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Update select attributes."""
        self._attr_current_option = self._get_current_option()

    async def async_set_current_phase(self, phase):
        """Set the current phase."""
        await self._device.set_current_phase(phase)
        await self.async_select_option(phase)

    async def async_enable_rfid_auth_mode(self):
        """Enable RFID authorization mode."""
        await self._device.set_rfid_auth_mode(True)
        await self.update_state(self.entity_description.api_param, 2)
        self.async_write_ha_state()

    async def async_disable_rfid_auth_mode(self):
        """Disable RFID authorization mode."""
        await self._device.set_rfid_auth_mode(False)
        await self.update_state(self.entity_description.api_param, 0)
        self.async_write_ha_state()