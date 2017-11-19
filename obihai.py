"""
Support for Obihai Sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.obihai/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import STATE_UNKNOWN
from homeassistant.const import (
    CONF_PATH, CONF_HOST, CONF_PASSWORD, CONF_USERNAME)

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
import requests
import xml.etree.ElementTree
import re
from urllib.parse import urljoin


_LOGGER = logging.getLogger(__name__)

#DEPENDENCIES = ['obihai']

DEFAULT_PATH = 'DI_S_.xml'
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST):
        cv.string,
    vol.Optional(CONF_PATH, default=DEFAULT_PATH):
        cv.string,
    vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME):
        cv.string,
    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD):
        cv.string,
})


def get_state(url, username, password) :

    resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(username,password))
    root = xml.etree.ElementTree.fromstring(resp.text)

    services = dict()
    for o in root.findall("object") :
      name = o.attrib.get('name') 
      if 'Service Status' in name :
        for e in o.findall("./parameter[@name='Status']/value") :
          state = e.attrib.get('current').split()[0] # take the first word
          services[name] = state
    return services

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Obihai sensor platform."""

    server_origin = '{}://{}'.format('http', config[CONF_HOST])
    url = urljoin(server_origin, config[CONF_PATH])

    username = config.get(CONF_USERNAME, None)
    password = config.get(CONF_PASSWORD, None)

    sensors = []

    services = get_state(url,username,password)
    for key, value in services.items():
        sensors.append(
	    ObihaiServiceSensors(url, username, password, key, )
        )

    add_devices(sensors)


class ObihaiServiceSensors(Entity):
    """Get the status of each Obihai Lines."""

    def __init__(self, url, username, password, service_name):
        """Initialize monitor sensor."""
        self._url = url
        self._username = username
        self._password = password
        self._service_name = service_name
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{}'.format(self._service_name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Update the sensor."""
        services = get_state(self._url, self._username, self._password)
     
        if services[self._service_name] is None:
            self._state = STATE_UNKNOWN
        else:
            self._state = services[self._service_name]
