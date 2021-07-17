"""Database and model base class for Peewee ORM."""
import peewee


db = peewee.PostgresqlDatabase(None, autorollback=True)


class BaseModel(peewee.Model):
    """Base model to set default settings."""

    class Meta:
        """Peewee settings config."""

        use_legacy_table_names = False
        database = db
