from typing import Tuple
import time

from lifxlan import LifxLAN, Light, Device


def go_to_color(
    light: Light,
    destination_color: Tuple[int, int, int, int],
    duration: int,
    flash_color: Tuple[int, int, int, int],
    flash_duration: float,
) -> None:
    is_transient: int = 0
    cycles: float = 0.5
    duty_cycle: int = 0
    waveform: int = 3
    light.set_waveform(
        is_transient,
        destination_color,
        duration,
        cycles,
        duty_cycle,
        waveform,
        rapid=True,
    )
    while True:
        current_color: Tuple[int, int, int, int] = light.get_color()
        if current_color == destination_color:
            break
        time.sleep(5e-2)
    light.set_color(flash_color, rapid=True)
    time.sleep(flash_duration)
    light.set_color(destination_color, rapid=True)


def main() -> None:
    print("Getting light by name...")
    lan = LifxLAN()
    device: Device = lan.get_device_by_name("Office Lamp")
    mac_address: str = device.get_mac_addr()
    ip_address: str = device.get_ip_addr()
    light = Light(mac_address, ip_address)

    # print("Getting light directly...")
    # mac_address: str = "D0:73:D5:5B:10:0D"
    # ip_address: str = "192.168.1.59"
    # light = Light(mac_address, ip_address)

    # Colors are HSBK: [hue (0-65535), saturation (0-65535), brightness (0-65535), Kelvin (2500-9000)]
    red: Tuple[int, int, int, int] = (0, 65535, 65535, 3500)
    blue: Tuple[int, int, int, int] = (36044, 65535, 65535, 3500)
    green: Tuple[int, int, int, int] = (22937, 65535, 65535, 3500)

    flash_duration: float = 1e-1
    desired_breath: int = 5000
    duration: int = desired_breath * 2 - int(flash_duration * 1000)
    print(f"duration starts at {duration}")

    for i in range(10):
        start: float = time.perf_counter()
        go_to_color(light, blue, duration, green, flash_duration)
        first: float = time.perf_counter()
        go_to_color(light, red, duration, green, flash_duration)
        second: float = time.perf_counter()
        delta1: float = first - start
        delta2: float = second - first
        print(f"delta1: {delta1:.2f}, delta2: {delta2:.2f}")

        delta_avg: int = int(sum([delta1 * 1000, delta2 * 1000]) / 2.0)
        if delta_avg > desired_breath:
            duration -= 100
        elif delta_avg < desired_breath:
            duration += 100
        print(f"duration is now {duration}")

    import ipdb

    ipdb.set_trace()
    pass


if __name__ == "__main__":
    main()
