"""Database and model base class for Peewee ORM."""
from typing import Any

import peewee


db = peewee.PostgresqlDatabase(None, autorollback=False)


class BaseModel(peewee.Model):
    """Base model to set default settings."""

    class Meta:
        """Peewee settings config."""

        use_legacy_table_names = False
        database = db


class BytesField(peewee.BlobField):
    """A field storing plain binary data."""

    def coerce(self, value: Any) -> bytes:
        """Coerce data to bytes."""
        return bytes(value)
