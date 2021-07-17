"""Utilities for testing the server."""
import dataclasses
import tempfile
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import coverage

    from .discord import DiscordUser


@dataclasses.dataclass
class TestingData:
    """Data stored when in testing mode."""

    enabled: bool = False
    coverage_measurer: Optional['coverage.Coverage'] = None
    coverage_file: Optional[str] = None
    discord_tokens: dict[str, 'DiscordUser'] = dataclasses.field(
        default_factory=dict,
    )


TESTING = TestingData()


def enable():
    """Enable testing mode."""
    # Don't import at top-level because it is an optional dependency.
    import coverage
    TESTING.enabled = True
    TESTING.coverage_file = tempfile.mkstemp()[1]
    TESTING.coverage_measurer = coverage.Coverage(
        data_file=TESTING.coverage_file,
        source_pkgs=(
            'cupid.graph',
            'cupid.tokens',
            'cupid.models',
            'cupid.models.app',
            'cupid.models.database',
            'cupid.models.enums',
            'cupid.models.relationship',
            'cupid.models.session',
            'cupid.models.user',
            'cupid.routes',
            'cupid.routes.auth',
            'cupid.routes.relationships',
            'cupid.routes.users',
            'cupid.routes.utils',
        ),
        branch=True,
    )
    TESTING.coverage_measurer.start()
