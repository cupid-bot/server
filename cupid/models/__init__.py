"""Database models and logic."""
from .app import App
from .database import db
from .relationship import Relationship, RelationshipKind    # noqa:F401
from .session import Session
from .user import Gender, User    # noqa:F401
from ..config import CONFIG


MODELS = [App, Relationship, Session, User]


def init_db():
    """Initialise the Peewee database model."""
    db.init(
        CONFIG.db_name,
        user=CONFIG.db_user,
        password=CONFIG.db_password,
        host=CONFIG.db_host,
        port=CONFIG.db_port,
    )
    db.create_tables(MODELS)
