"""Tool for parsing and exporting config options."""
from __future__ import annotations

import configparser
import logging
import os
import pathlib
import sys
from datetime import timedelta
from typing import Any, Callable, Iterator, Optional, Union

import pydantic

from rich.logging import RichHandler


logger = logging.getLogger('cupid')


class LogLevel(int):
    """Pydantic validator for a logging level."""

    @classmethod
    def __get_validators__(cls) -> Iterator[Callable]:
        """Get the validator for a log level."""
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, int]) -> LogLevel:
        """Validate and convert a log level."""
        try:
            return LogLevel(value)    # Convert to an int.
        except ValueError:
            pass
        try:
            return {
                'critical': logging.CRITICAL,
                'error': logging.ERROR,
                'warning': logging.WARNING,
                'info': logging.INFO,
                'debug': logging.DEBUG,
                'notset': logging.NOTSET,
                'none': logging.NOTSET,
            }[value.lower()]
        except KeyError as e:
            raise ValueError(f'Invalid log level name "{value}".') from e

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]):
        """Update the schema to show this field."""
        field_schema.update(
            pattern='^([0-9]+|NONE|NOTSET|DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
            examples=[20, 'INFO', 'critical', 50, 'none'],
        )


class _Config(pydantic.BaseModel):
    """Config fields."""

    # Database connection information.
    db_name: str = 'cupid'
    db_user: str = 'cupid'
    db_password: str
    db_host: str = 'localhost'
    db_port: int = 5432

    # Discord-related configuration.
    discord_api_url: str = 'https://discord.com/api/v8'
    discord_cdn_url: str = 'https://cdn.discordapp.com'
    discord_guild_id: Optional[int] = None

    # Logging levels.
    log_level_peewee: LogLevel = logging.INFO    # SQL ORM logs.
    log_level_sanic: LogLevel = logging.INFO     # Internal Sanic logs.
    log_level_access: LogLevel = logging.INFO    # HTTP access logs.
    log_level_error: LogLevel = logging.INFO     # Handler error logs.
    log_level_cupid: LogLevel = logging.INFO     # Cupid's own logs.

    # Other miscellaneous configuration.
    server_host: str = '0.0.0.0'
    server_port: int = 80
    session_expiry: timedelta = timedelta(days=30)
    debug: bool = False


class Config:
    """Mutable interface to config so that it can be shared between modules."""

    def __getattr__(self, key: str) -> Any:
        """Get a value from the underlying config."""
        return getattr(_CONFIG, key)


BASE_PATH = pathlib.Path(__file__).parent.parent
_CONFIG: _Config = None
CONFIG: _Config = Config()


def _apply_log_levels():
    """Apply configured logging levels."""
    logs = {
        'peewee': (CONFIG.log_level_peewee, '{message}'),
        'sanic.root': (CONFIG.log_level_sanic, '{message}'),
        'sanic.access': (
            CONFIG.log_level_access, '{host}: {request} {message} {status}',
        ),
        'sanic.error': (CONFIG.log_level_error, '{message}'),
        'cupid': (CONFIG.log_level_cupid, '{message}'),
    }
    for log_name, (log_level, log_format) in logs.items():
        logger = logging.getLogger(log_name)
        logger.setLevel(log_level)
        handler = RichHandler()
        handler.setFormatter(logging.Formatter(log_format, style='{'))
        logger.addHandler(handler)


def normalise_options(data: dict[str, Any]) -> dict[str, Any]:
    """Normalise config option keys."""
    return {
        key.lower().lstrip('-').replace('-', '_'): value
        for key, value in data.items()
    }


def _get_config_data(arg_data: dict[str, Any]) -> dict[str, Any]:
    """Get and combine raw config data."""
    data = normalise_options(os.environ)
    parser = configparser.ConfigParser()
    if parser.read(arg_data['--config-file'] or BASE_PATH / 'config.ini'):
        data.update(normalise_options(parser['cupid']))
    for key, value in normalise_options(arg_data).items():
        if value is not None:
            data[key] = value
    return data


def load(arg_data: Optional[dict[str, Any]] = None):
    """Load config options."""
    global _CONFIG
    data = _get_config_data(arg_data or {})
    try:
        _CONFIG = _Config(**data)
    except pydantic.ValidationError as error:
        logger.critical(f'Error parsing config:\n{error}')
        sys.exit(1)
    _apply_log_levels()
