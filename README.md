<img src="docs/static/logo.png" alt="Cupid Logo" width="200"></img>

# Cupid API Server

This is the API server that powers the Cupid bot and website.

## Installation

Dependencies:

- [Python 3.9+](https://www.python.org/downloads/) (Python 3.x where x >= 9)
- [Poetry](https://python-poetry.org/docs/master/#installation)

  Click the link for installation instructions, or:

  **\*nix:**
  `curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -`

  **Windows Powershell:**
  `(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py -UseBasicParsing).Content | python -`

Once you have these dependencies installed:

1. **Create a virtual environment:** `python3 -m poetry shell`
2. **Install dependencies:** `poetry install --no-dev`
   (remove `--no-dev` for development dependencies)

## Configuration

There are three methods provided to configure the API server:

- Command line arguments (more details below).
- A configuration file (by default, `config.ini`).
- Environment variables.

When looking for a configuration option, the server will look for it in each of
these, in the above order, stopping as soon as it finds it.

These three options have different casing conventions. Command line arguments
should be `--kebab-case`, configuration file keys should be `snake_case`, and
environment variables should be `UPPER_SNAKE_CASE`. For example, the command
line argument `--db-name` is equivalent to the configuration file key `db_name`
and the environment variable `DB_NAME`.

To see a list of available options, do `poe cupid --help`.

## Commands

The following commands are available:

- **Run the server:** `poe cupid`
- **Create an API app:** `poe cupid create-app <name>`
- **Manage an API app:** `poe cupid app <app>`
- **List API apps:** `poe cupid list-apps`
- **Lint code (requires dev dependecies):** `poe lint`

For more help on Cupid commands, add a `--help` to the end.

Note that if to run outside of the Poetry shell (without running
`poetry shell`) you may have to replace `poe` with `poetry run poe` or even
`python3 -m poetry run poe`.

## API Docs

An [OpenAPI 3](https://swagger.io/specification) schema for the API is available at `docs/docs.yaml` in this repository.

Once the API server is running (and unless the `disable_docs` option has been enabled), interactive HTML docs will be served at `/docs.html`. The OpenAPI schema will also be available at `/docs.yaml`.
