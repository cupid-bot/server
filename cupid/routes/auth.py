"""Endpoints related to user authentication."""
import secrets

import pydantic

from sanic.exceptions import SanicException
from sanic.request import Request
from sanic.response import HTTPResponse, json

from .utils import app, authenticated, parse_body
from ..discord import DiscordAuthError, authenticate_user
from ..models import Session, User


class LoginForm(pydantic.BaseModel):
    """Form for creating an authentication session."""

    token: str


@app.post('/auth/login')
@parse_body(LoginForm)
async def discord_authenticate(request: Request) -> HTTPResponse:
    """Authenticate with a Discord OAuth2 bearer token."""
    try:
        user_data = await authenticate_user(request.ctx.body.token)
    except DiscordAuthError as error:
        raise SanicException(str(error), 422) from error
    user, created = User.from_object(user_data)
    return json(
        Session.create(user=user).as_dict(with_token=True),
        201 if created else 200,
    )


@app.get('/auth/me')
@authenticated
async def get_self(request: Request) -> HTTPResponse:
    """Get information on the authenticated user or app."""
    return json(request.ctx.requester.as_dict())


@app.delete('/auth/me')
@authenticated
async def delete_session(request: Request) -> HTTPResponse:
    """Delete the current authentication session or app."""
    request.ctx.requester.delete_instance()
    return HTTPResponse(status=204)


@app.patch('/auth/me')
@authenticated
async def refresh_token(request: Request) -> HTTPResponse:
    """Refresh the token of the authenticated app or session."""
    request.ctx.requester.secret = secrets.token_bytes()
    request.ctx.requester.save()
    return json(request.ctx.requester.as_dict(with_token=True))
