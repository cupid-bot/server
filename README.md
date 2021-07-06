<img src="docs/static/logo.png" alt="Cupid Logo" width="200"></img>

# Cupid API Server

This is the API server that powers the Cupid bot and website.

## Installation

Dependencies:

- [Python 3.9+](https://www.python.org/downloads/) (Python 3.x where x >= 9)
- [Pipenv](https://pypi.org/project/pipenv/) (`python3 -m pip install pipenv`)

Once you have these dependencies installed:

1. **Create a virtual environment:** `python3 -m pipenv shell`
2. **Install dependencies:** `pipenv install`
3. **Optionally, install development dependencies:** `pipenv install -d`

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

To see a list of available options, do `pipenv run cupid --help`.

## Commands

The following commands are available:

- **Run the server:** `pipenv run cupid`
- **Create an API app:** `pipenv run cupid create-app <name>`
- **Manage an API app:** `pipenv run cupid app <app>`
- **List API apps:** `pipenv run cupid list-apps`
- **Lint code (requires dev dependecies):** `pipenv run lint`

For more help on Cupid commands, add a `--help` to the end.

## API Docs

An [OpenAPI 3](https://swagger.io/specification) schema for the API is available at `docs/docs.yaml` in this repository.

Once the API server is running (and unless the `disable_docs` option has been enabled), interactive HTML docs will be served at `/docs.html`. The OpenAPI schema will also be available at `/docs.yaml`.
