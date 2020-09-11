"""

from lifx_manager import LifxManager
manager = LifxManager()
manager.update_lights()
manager.lights
light = manager.get_light(location='Office', label='Office Lamp')
"""

from pprint import pprint
from typing import List, Set, FrozenSet, Optional, Any
import dataclasses
import logging
import threading
import time

# -----------------------------------------------------------------------------
# create logger
# -----------------------------------------------------------------------------
logger = logging.getLogger("lifx_manager")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
# -----------------------------------------------------------------------------


from lifxlan import LifxLAN, Light, Device
import lifxlan


@dataclasses.dataclass(eq=True, frozen=True)
class LifxLightWrapper:
    location: str = dataclasses.field(compare=True, hash=True)
    label: str = dataclasses.field(compare=True, hash=True)
    ip_address: str = dataclasses.field(compare=False, hash=False)
    mac_address: str = dataclasses.field(compare=False, hash=False)


class LifxManager:
    UPDATE_LIGHTS_ITERATIONS: int = 3
    UPDATE_LIGHTS_SLEEP_INTERVAL_SECONDS: float = 0.017
    BACKGROUND_LIGHTS_UPDATE_INTERVAL_SECONDS: float = 15 * 60

    _lan: LifxLAN
    _lights: List[LifxLightWrapper]
    _updater_thread: threading.Timer

    def __init__(self) -> None:
        logger.info("__init__ entry")
        self._lan = LifxLAN()
        self._lights = list()
        self.update_lights_in_thread()

    @property
    def lights(self) -> List[LifxLightWrapper]:
        return self._lights

    def get_light(self, location: str, label: str) -> Optional[LifxLightWrapper]:
        logger.info("get_light entry")
        for light in self._lights:
            if light.location == location and light.label == label:
                return light
        return None

    def update_lights_in_thread(self) -> None:
        self.update_lights()
        self._updater_thread = threading.Timer(
            self.BACKGROUND_LIGHTS_UPDATE_INTERVAL_SECONDS, self.update_lights_in_thread
        )
        self._updater_thread.start()

    def update_lights(self) -> None:
        logger.info("update_lights entry")
        self._lights = self.get_new_lights()

    def get_new_lights(self) -> List[LifxLightWrapper]:
        logger.info("get_new_lights entry")
        seen_mac_addresses: Set[str] = set()
        result: Set[LifxLightWrapper] = set()
        for i in range(self.UPDATE_LIGHTS_ITERATIONS):
            time.sleep(self.UPDATE_LIGHTS_SLEEP_INTERVAL_SECONDS)
            devices: List[Device] = self._lan.get_devices()
            current_lights: List[LifxLightWrapper] = []
            for device in devices:
                if device.get_mac_addr() in seen_mac_addresses:
                    continue
                try:
                    light: LifxLightWrapper = LifxLightWrapper(
                        location=device.get_location_label(),
                        label=device.get_label(),
                        ip_address=device.get_ip_addr(),
                        mac_address=device.get_mac_addr(),
                    )
                    current_lights.append(light)
                except lifxlan.errors.WorkflowException:
                    logger.exception("error while updating lights")
                    continue
                seen_mac_addresses.add(device.get_mac_addr())
            result.update(current_lights)
        return sorted(result, key=lambda x: (x.location, x.label))

    def close(self) -> None:
        logger.info("close entry")
        self._updater_thread.cancel()

