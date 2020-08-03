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

## License

`lifx-breathing` is distributed under the terms of the Apache License (Version 2.0). See [LICENSE](LICENSE) for
details.
