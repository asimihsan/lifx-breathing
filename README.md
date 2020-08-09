## Introduction

## How to install

Install pyenv and pyenv-virtualhelper and put them into your shell RC

```
brew install pyenv pyenv-virtualenv
```

Install the latest version of Python 3 and a virtualenv:

```
pyenv install 3.8.5
pyenv virtualenv 3.8.5 lifx-env
```

Change directory into Git clone, this should automatically switch virtualenv to `lifx-env`.

Then first install prerequisites and poetry.

```
pip install --upgrade pip wheel
pip install -r requirements.txt
```

Then use poetry to install dependencies:

```
poetry install
```

Since there will be new executables present make them available:

```
pyenv rehash
```

### Development running

```
FLASK_APP=lifx_breathing/flask_app.py FLASK_ENV=development FLASK_SECRET_KEY=secret_key flask run
```

### Production running with supervisord

```
mkdir -p /tmp/lifx_breathing_logs/
FLASK_SECRET_KEY=secret_key supervisord --configuration supervisord.conf
```

or skip `--nodaemon` if you want to run this in the background.

### Setting up systemd service

```
mkdir -p /tmp/lifx_breathing_logs/
mkdir -p ~/.config/systemd/user/
cp lifx-breathing.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user status lifx-breathing.service
systemctl --user start lifx-breathing.service
systemctl --user enable lifx-breathing.service
```

## License

`lifx-breathing` is distributed under the terms of the Apache License (Version 2.0). See [LICENSE](LICENSE) for
details.
