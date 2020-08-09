from dataclasses import dataclass
from typing import Any, List, Tuple
import argparse
import logging
import signal
import sys
import time
import types

import lifxlan
from lifxlan import LifxLAN, Light, Device

global_light: Light = None
global_halt: bool = False

# -----------------------------------------------------------------------------
# create logger
# -----------------------------------------------------------------------------
logger = logging.getLogger("lifx_breathing")
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


class LifxDeviceNotFoundException(Exception):
    pass


def go_to_color(
    light: Light, destination_color: Tuple[int, int, int, int], duration_ms: int, flash_duration_ms: int,
) -> int:
    is_transient: int = 0
    cycles: float = 0.5
    duty_cycle: int = 0
    waveform: int = 3
    period_ms: int = duration_ms * 2 - flash_duration_ms

    start: float = time.perf_counter()
    light.set_waveform(is_transient, destination_color, period_ms, cycles, duty_cycle, waveform, rapid=False)
    while True:
        if global_halt:
            return 0
        time.sleep(1e-1)
        try:
            current_color: Tuple[int, int, int, int] = light.get_color()
        except lifxlan.errors.WorkflowException:
            logger.warning("exception while getting color")
            continue
        if current_color == destination_color:
            break
    light.set_power(False, rapid=False)
    time.sleep(flash_duration_ms / 1000.0)
    light.set_power(True, rapid=False)

    end: float = time.perf_counter()
    return int((end - start) * 1000)


def run_breathing_cycle(light: Light, inhale_duration_ms: int, exhale_duration_ms: int) -> None:
    # Colors are HSBK: [hue (0-65535), saturation (0-65535), brightness (0-65535), Kelvin (2500-9000)]
    red: Tuple[int, int, int, int] = (0, 65535, 65535, 3500)
    blue: Tuple[int, int, int, int] = (36044, 65535, 65535, 3500)

    target_inhale_duration_ms: int = inhale_duration_ms
    target_exhale_duration_ms: int = exhale_duration_ms
    flash_duration_ms: int = 200

    current_inhale_duration_ms: int = target_inhale_duration_ms
    current_exhale_duration_ms: int = target_exhale_duration_ms
    inhale_errors: List[int] = []
    exhale_errors: List[int] = []
    inhale_cumulative_error_ms: int = 0
    exhale_cumulative_error_ms: int = 0
    inhale_derivative_error_ms: int = 0
    exhale_derivative_error_ms: int = 0

    light.set_color(red, rapid=False)
    cnt: int = 0
    while True:
        actual_inhale_duration_ms: int = go_to_color(
            light, blue, current_inhale_duration_ms, flash_duration_ms
        )
        if global_halt:
            return
        actual_exhale_duration_ms: int = go_to_color(
            light, red, current_exhale_duration_ms, flash_duration_ms
        )
        if global_halt:
            return
        logger.info(
            f"actual_inhale_duration_ms: {actual_inhale_duration_ms}, actual_exhale_duration_ms: {actual_exhale_duration_ms}"
        )

        cnt += 1
        if cnt <= 1:
            logger.info("skip duration adjustment for first iteration")
            continue

        k_p: float = 1.0
        k_i: float = 0.05
        k_d: float = 0.03
        history_window_size: int = 10

        inhale_error_ms = target_inhale_duration_ms - actual_inhale_duration_ms
        inhale_errors = (inhale_errors + [inhale_error_ms])[-history_window_size:]
        inhale_cumulative_error_ms = sum(inhale_errors)
        if len(inhale_errors) <= 1:
            inhale_derivative_error_ms = 0
        else:
            inhale_derivative_error_ms = inhale_errors[-1] - inhale_errors[-2]
        inhale_correction_ms: int = int(k_p * inhale_error_ms) + int(k_i * inhale_cumulative_error_ms) + int(
            k_d * inhale_derivative_error_ms
        )
        logger.debug(
            f"inhale_error_ms: {inhale_error_ms}, inhale_cumulative_error_ms: {inhale_cumulative_error_ms}, inhale_derivative_error_ms: {inhale_derivative_error_ms}"
        )
        current_inhale_duration_ms += inhale_correction_ms

        exhale_error_ms = target_exhale_duration_ms - actual_exhale_duration_ms
        exhale_errors = (exhale_errors + [exhale_error_ms])[-history_window_size:]
        exhale_cumulative_error_ms = sum(exhale_errors)
        if len(exhale_errors) <= 1:
            exhale_derivative_error_ms = 0
        else:
            exhale_derivative_error_ms = exhale_errors[-1] - exhale_errors[-2]
        exhale_correction_ms: int = int(k_p * exhale_error_ms) + int(k_i * exhale_cumulative_error_ms) + int(
            k_d * exhale_derivative_error_ms
        )
        logger.debug(
            f"exhale_error_ms: {exhale_error_ms}, exhale_cumulative_error_ms: {exhale_cumulative_error_ms}, exhale_derivative_error_ms: {exhale_derivative_error_ms}"
        )
        current_exhale_duration_ms += exhale_correction_ms

        logger.info(
            f"current_inhale_duration_ms is now {current_inhale_duration_ms}, current_exhale_duration_ms is now {current_exhale_duration_ms}"
        )


def handler(signum: int, frame: types.FrameType) -> None:
    global global_light
    global global_halt

    logger.info("signal handler")
    if global_light is None:
        return
    logger.info("signal handler setting global halt flag")
    global_halt = True


@dataclass
class ProgramArguments:
    ip_address: str
    mac_address: str
    inhale_duration_ms: int
    exhale_duration_ms: int


def get_args() -> ProgramArguments:
    parser = argparse.ArgumentParser(description="Run LIFX breathing process.")
    parser.add_argument("--ip-address", help="IP address of LIFX device", required=True)
    parser.add_argument("--mac-address", help="MAC address of LIFX device", required=True)
    parser.add_argument("--inhale-duration-ms", type=int, help="Inhale duration milliseconds", required=True)
    parser.add_argument("--exhale-duration-ms", type=int, help="Exhale duration milliseconds", required=True)
    args: argparse.Namespace = parser.parse_args()
    return ProgramArguments(
        ip_address=args.ip_address,
        mac_address=args.mac_address,
        inhale_duration_ms=args.inhale_duration_ms,
        exhale_duration_ms=args.exhale_duration_ms,
    )


def main() -> None:
    args: ProgramArguments = get_args()
    logger.info(f"Getting light...")
    light: Light = Light(args.mac_address, args.ip_address)

    global global_light
    global_light = light
    signal.signal(signal.SIGTERM, handler)

    original_color: Tuple[int, int, int, int] = light.get_color()
    original_power: int = light.get_power()

    try:
        run_breathing_cycle(light, args.inhale_duration_ms, args.exhale_duration_ms)
    except:
        logger.exception("exception in main")
        raise
    finally:
        light.set_color(original_color, rapid=False)
        light.set_power(original_power, rapid=False)


if __name__ == "__main__":
    main()
