import os
import os.path
import subprocess
from typing import Any, List, Optional

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

script_path: str = os.path.dirname(os.path.realpath(__file__))
lifx_path: str = os.path.join(script_path, "lifx.py")
process = None
command: List[str] = [
    "python",
    lifx_path,
    "--device-name",
    "Office Lamp",
    "--inhale-duration-ms",
    "5000",
    "--exhale-duration-ms",
    "5000",
]

from .lifx_manager import LifxManager, LifxLightWrapper

manager = LifxManager()
first_load: bool = True

from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)


class UpdateLightsForm(FlaskForm):
    pass


@app.route("/", methods=["GET"])
def index() -> Any:
    global first_load
    if first_load:
        manager.update_lights()
        first_load = False
    lights: List[LifxLightWrapper] = manager.lights
    update_lights_form = UpdateLightsForm()
    return render_template("index.html", lights=lights, update_lights_form=update_lights_form)


@app.route("/update_lights", methods=["POST"])
def update_lights() -> Any:
    manager.update_lights()
    return redirect(url_for("index"))


@app.route("/favicon.ico")
def favicon() -> Any:
    return app.send_static_file("favicon.ico")


@app.route("/icon.png")
def icon() -> Any:
    return app.send_static_file("icon.png")


@app.route("/start")
def hello_world() -> str:
    global process
    process = subprocess.Popen(command)
    return "Hello, World!"


@app.route("/stop")
def stop() -> str:
    global process
    if process is not None:
        process.terminate()
        process = None
    return "Hello, World!"
