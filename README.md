# Byter Bot
A simple bot made for the Créu Cat community! Made with <3 by rini and open to any contributions!

## Running
Below is simply how I run the bot myself on my system and within the VM instance, so it may be different on your system!

### Pre-requirements

* Python >= 3.8 (preferably 3.9)
* Latest version of [poetry](https://python-poetry.org/)
  * OR (Not recommended), Install the required packages manually through pip, `discord.py`, `psutil`, `fuzzywuzzy[speedup]` and `Pillow` (also `flake8` for linting)

### Setup

* Run `poetry install`
  * add `--no-dev` for production environments
* Set up a `TOKEN` file on the root dir, containing the bot's login token
* (Optional) Set up a `config.json` file and use it to override `config_defaults.json`

### Executing

Invoke the `bot` folder as a module
* With poetry, `poetry run python3 -m bot` (or whichever command python is defined in your system)
* Without it, drop the `poetry run` part

And you should be good to go! Feel free to open a pull request for any changes!
