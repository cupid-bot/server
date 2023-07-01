"""Endpoints used while testing the API.

These should *always* be disabled in production.
"""
import functools
from typing import Any, Callable, Optional

import pydantic

from sanic.request import Request
from sanic.response import HTTPResponse, file, json

from .utils import app, parse_body
from .. import discord
from ..config import CONFIG
from ..models import App, MODELS
from ..testing import TESTING


class AppCreateForm(pydantic.BaseModel):
    """Form for creating a new app."""

    name: str


class DiscordUserRegisterForm(pydantic.BaseModel):
    """Form for registering a Discord access token."""

    token: str

    id: int
    name: str
    avatar_url: str
    discriminator: Optional[str]


def testing_only(handler: Callable) -> Callable:
    """Decorate a handler that only runs in testing mode."""
    @functools.wraps(handler)
    async def decorated(request: Request, *args: Any, **kwargs: Any) -> Any:
        """Make sure the server is in testing mode."""
        if CONFIG.testing:
            return await handler(request, *args, **kwargs)
        return json({    # pragma: no cover
            'description': 'Testing mode disabled.',
            'status': 403,
            'message': (
                'This endpoint may only be used when the server is in '
                'testing mode.'
            ),
        }, 403)
    return decorated


@app.get('/testing')
async def check_testing(request: Request) -> HTTPResponse:
    """Check if the server is in testing mode."""
    return json({'testing': CONFIG.testing})


@app.post('/testing/clear')
@testing_only
async def clear_database(request: Request) -> HTTPResponse:
    """Clear every table in the entire database."""
    for model in MODELS:
        model.delete().execute()
    return HTTPResponse(status=204)


@app.post('/testing/app')
@testing_only
@parse_body(AppCreateForm)
async def create_app(request: Request) -> HTTPResponse:
    """Create a new app."""
    return json(
        App.create(name=request.ctx.body.name).as_dict(with_token=True),
        201,
    )


@app.post('/testing/discord_user')
@testing_only
@parse_body(DiscordUserRegisterForm)
async def register_discord_user(request: Request) -> HTTPResponse:
    """Register a Discord user token for creating a user session."""
    user = discord.DiscordUser(
        id=request.ctx.body.id,
        name=request.ctx.body.name,
        discriminator=request.ctx.body.discriminator,
        avatar_url=request.ctx.body.avatar_url,
    )
    TESTING.discord_tokens[request.ctx.body.token] = user
    return HTTPResponse(status=201)


@app.get('/testing/coverage')
@testing_only
async def get_coverage(request: Request) -> HTTPResponse:
    """Get code coverage for since the server started up.

    Returns an Sqlite 3 file which can be rendered as a JSON or HTML coverage
    report by the Coverage.py library.
    """
    TESTING.coverage_measurer.save()
    return await file(    # pragma: no cover
        TESTING.coverage_file,
        mime_type='application/vnd.sqlite3',
        filename='coverage.sqlite',
    )
