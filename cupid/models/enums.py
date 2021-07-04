"""Tool for handling enums in database fields."""
from __future__ import annotations

import enum
from typing import Any, Optional, Type

import peewee


class EnumField(peewee.SmallIntegerField):
    """A field where each value is an integer representing an option."""

    def __init__(
            self, options: Type[enum.Enum], **kwargs: Any):
        """Create a new enum field."""
        self.options = options
        super().__init__(**kwargs)

    def python_value(self, raw: int) -> Optional[enum.Enum]:
        """Convert a raw number to an enum value."""
        if raw is None:
            return None
        number = super().python_value(raw)
        return self.options(number)

    def db_value(self, instance: enum.Enum) -> Optional[int]:
        """Convert an enum value to a raw number."""
        if instance is None:
            return super().db_value(None)
        if not isinstance(instance, self.options):
            raise TypeError(f'Instance is not of enum class {self.options}.')
        number = instance.value
        return super().db_value(number)
