import os.path
import subprocess
from typing import List

from flask import Flask

app = Flask(__name__)

script_path: str = os.path.dirname(os.path.realpath(__file__))
lifx_path: str = os.path.join(script_path, "lifx.py")
process: subprocess.Popen = None
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


@app.route("/")
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
