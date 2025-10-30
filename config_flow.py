"""Config flow for Pulsar Heat Meter."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import logging
import asyncio
import socket

DOMAIN = "pulsar_heat"
_LOGGER = logging.getLogger(__name__)

class PulsarHeatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pulsar Heat Meter."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                # Test basic TCP connection
                if await self._test_tcp_connection(user_input["host"], user_input.get("port", 4001)):
                    return self.async_create_entry(
                        title=f"Pulsar Heat Meter {user_input['host']}",
                        data=user_input
                    )
                else:
                    errors["base"] = "cannot_connect"
                    
            except Exception as e:
                _LOGGER.error(f"Connection test failed: {e}")
                errors["base"] = "cannot_connect"
        
        data_schema = vol.Schema({
            vol.Required("host", default="192.168.1.8"): str,
            vol.Optional("port", default=4001): cv.port,
            vol.Optional("device_address", default="10264061"): str,
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
    
    async def _test_tcp_connection(self, host: str, port: int) -> bool:
        """Test basic TCP connection to the device."""
        _LOGGER.info(f"Testing TCP connection to {host}:{port}")
        
        try:
            # Create socket and connect with timeout
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            # Connect to device
            await loop.run_in_executor(
                None, 
                lambda: sock.connect((host, port))
            )
            
            _LOGGER.info(f"Successfully established TCP connection to {host}:{port}")
            
            # Immediately close the connection gracefully
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            
            return True
            
        except socket.timeout:
            _LOGGER.error(f"Connection timeout to {host}:{port}")
            return False
        except ConnectionRefusedError:
            _LOGGER.error(f"Connection refused by {host}:{port}")
            return False
        except OSError as e:
            _LOGGER.error(f"Network error connecting to {host}:{port}: {e}")
            return False
        except Exception as e:
            _LOGGER.error(f"Unexpected error connecting to {host}:{port}: {e}")
            return False