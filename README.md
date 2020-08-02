## Introduction

## How to install

Install pyenv and pyenv-virtualhelper and put them into your shell RC

```
brew install pyenv pyenv-virtualenv
```

Install miniconda3 and a virtualenv:

```
pyenv install miniconda3-latest
pyenv virtualenv miniconda3-latest lifx-env
```

Change directory into Git clone, then first install poetry and lifxlan (not sure why but poetry can't install lifxlan)

```
pip install -r requirements.txt
```

Then use poetry to install dependencies:

```
poetry install
```

## License

`lifx-breathing` is distributed under the terms of the Apache License (Version 2.0). See [LICENSE](LICENSE) for
details.
