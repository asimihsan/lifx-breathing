"""

### Development running

cd /Users/asimi/Dropbox/Private/Programming/lifx-breathing
FLASK_APP=lifx_breathing/flask_app.py FLASK_ENV=development FLASK_SECRET_KEY=secret_key flask run

### Production running


"""

import dataclasses
import os
import os.path
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional

# -----------------------------------------------------------------------------
# create logger
# -----------------------------------------------------------------------------
import logging

logger = logging.getLogger("flask_app")
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

from .lifx_manager import LifxManager, LifxLightWrapper

script_path: str = os.path.dirname(os.path.realpath(__file__))
lifx_path: str = os.path.join(script_path, "lifx.py")
processes: Dict[LifxLightWrapper, Any] = {}

manager = LifxManager()
first_load: bool = True

from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import HiddenField
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)


class UpdateLightsForm(FlaskForm):
    pass


class LightNotFoundError(Exception):
    pass


class StartLightForm(FlaskForm):
    location = HiddenField("location")
    label = HiddenField("label")


class StopLightForm(FlaskForm):
    location = HiddenField("location")
    label = HiddenField("label")


@dataclasses.dataclass(eq=True, frozen=True)
class LightAndForms:
    light: LifxLightWrapper
    start_form: StartLightForm
    stop_form: StopLightForm
    is_running: bool


@app.route("/", methods=["GET"])
def index() -> Any:
    global first_load
    if first_load:
        manager.update_lights()
        first_load = False
    trim_processes()
    lights: List[LifxLightWrapper] = manager.lights
    lights_and_forms = [
        LightAndForms(
            light=light,
            start_form=StartLightForm(location=light.location, label=light.label),
            stop_form=StopLightForm(location=light.location, label=light.label),
            is_running=light in processes,
        )
        for light in lights
    ]
    update_lights_form = UpdateLightsForm()
    return render_template(
        "index.html", lights_and_forms=lights_and_forms, update_lights_form=update_lights_form
    )


@app.route("/update_lights", methods=["POST"])
def update_lights() -> Any:
    manager.update_lights()
    return redirect(url_for("index"))


@app.route("/favicon.ico", methods=["GET"])
def favicon() -> Any:
    return app.send_static_file("favicon.ico")


@app.route("/icon.png", methods=["GET"])
def icon() -> Any:
    return app.send_static_file("icon.png")


@app.route("/start_light", methods=["POST"])
def start_light() -> Any:
    start_light_form = StartLightForm()
    data: Dict[str, str] = start_light_form.data
    location: str = data["location"]
    label: str = data["label"]
    light: Optional[LifxLightWrapper] = manager.get_light(location, label)
    if light is None:
        raise LightNotFoundError
    start_process(light)
    return redirect(url_for("index"))


@app.route("/stop_light", methods=["POST"])
def stop_light() -> Any:
    start_light_form = StartLightForm()
    data: Dict[str, str] = start_light_form.data
    location: str = data["location"]
    label: str = data["label"]
    light: Optional[LifxLightWrapper] = manager.get_light(location, label)
    if light is None:
        raise LightNotFoundError
    stop_process(light)
    return redirect(url_for("index"))


def start_process(light: LifxLightWrapper) -> None:
    global processes
    if light in processes:
        stop_process(light)

    command: List[str] = [
        "python",
        lifx_path,
        "--ip-address",
        light.ip_address,
        "--mac-address",
        light.mac_address,
        "--inhale-duration-ms",
        "5000",
        "--exhale-duration-ms",
        "5000",
    ]
    process = subprocess.Popen(command)
    processes[light] = process


def stop_process(light: LifxLightWrapper) -> None:
    global processes
    process: subprocess.Popen[Any] = processes[light]
    process.terminate()
    start: float = time.perf_counter()
    while process.poll() is None:
        time.sleep(0.1)
        if time.perf_counter() - start > 5.0:
            process.kill()
            break
    del processes[light]


def trim_processes() -> None:
    lights_to_stop: List[LifxLightWrapper] = [
        light for (light, process) in processes.items() if process.poll() is not None
    ]
    for light in lights_to_stop:
        logger.info(f"trim_processes is stopping light: {light}")
        stop_process(light)
