"""Utilities common to the route handlers."""
import functools
from typing import Any, Callable, Type, Union

import pydantic

from sanic import Sanic
from sanic.exceptions import Forbidden, NotFound, SanicException
from sanic.request import Request
from sanic.response import HTTPResponse, json

from ..config import CONFIG
from ..graph import RelationshipForbidden
from ..models import Relationship, User
from ..tokens import Token, TokenParseError, TokenType


app = Sanic('cupid', configure_logging=False)


def run():
    """Run the app."""
    app.config.FALLBACK_ERROR_FORMAT = 'json'
    app.config.DEBUG = CONFIG.debug
    app.run(
        host=CONFIG.server_host,
        port=CONFIG.server_port,
        debug=CONFIG.debug,
        access_log=True,
    )


class AuthError(ValueError):
    """An error when parsing the authorisation header."""


@app.exception(pydantic.ValidationError)
async def handle_validation_error(
        request: Request, error: pydantic.ValidationError) -> HTTPResponse:
    """Handle a Pydantic validation error."""
    return json({
        'description': 'Badly formatted JSON body.',
        'status': 422,
        'message': 'JSON body did not conform to schema.',
        'errors': error.errors(),
    }, 422)


@app.exception(AuthError, TokenParseError)
async def handle_auth_error(
        request: Request,
        error: Union[AuthError, TokenParseError]) -> HTTPResponse:
    """Handle an authorisation or token error."""
    return json({
        'description': 'Invalid authorization header.',
        'status': 401,
        'message': str(error),
    }, 401)


@app.exception(RelationshipForbidden)
async def handle_forbidden_relationship(
        request: Request, error: RelationshipForbidden) -> HTTPResponse:
    """Handle a forbidden relationship proposal."""
    return json({
        'description': 'Forbidden relationship.',
        'status': 403,
        'message': str(error),
    }, 403)


def get_user_by_id(id: int) -> User:
    """Get a user by ID or raise a 404."""
    if user := User.get_or_none(User.id == id):
        return user
    raise NotFound(f'User not found by ID {id}.')


def get_relationship(id: int) -> Relationship:
    """Get a relationship by ID or raise a 404."""
    if rel := Relationship.get_or_none(Relationship.id == id):
        return rel
    raise NotFound(f'Relationship not found by ID {id}.')


def parse_body(
        model: Type[pydantic.BaseModel]) -> Callable[[Callable], Callable]:
    """Create a decorator to parse the request body as a Pydantic type."""
    def decorator(handler: Callable) -> Callable:
        """Decorate a handler to parse the request body as a Pydantic type."""
        @functools.wraps(handler)
        async def decorated(
                request: Request, *args: Any, **kwargs: Any) -> Any:
            """Parse the request body as a Pydantic type."""
            if not request.json:
                raise SanicException('JSON body missing.', 415)
            # We have a custom handler for Pydantic validation errors.
            request.ctx.body = model(**request.json)
            return await handler(request, *args, **kwargs)
        return decorated
    return decorator


def authenticate(request: Request):
    """Authenticate a request by checking the Authorization header."""
    if not (header := request.headers.get('authorization')):
        raise AuthError('Authorization header missing.')
    parts = header.split()
    if len(parts) != 2:
        raise AuthError('Authorization header badly formatted.')
    scheme, token = parts
    if scheme.lower() != 'bearer':
        raise AuthError('The "Bearer" authorisation scheme is required.')
    # We have a custom handler for token parse errors.
    request.ctx.token = Token.from_token(token)


def authenticated(handler: Callable) -> Callable:
    """Decorate a handler to make sure the client is authenticated."""
    @functools.wraps(handler)
    async def decorated(request: Request, *args: Any, **kwargs: Any) -> Any:
        """Make sure the client is authenticated."""
        authenticate(request)
        return await handler(request, *args, **kwargs)
    return decorated


def app_authenticated(handler: Callable) -> Callable:
    """Decorate a handler to make sure the client is an app."""
    @functools.wraps(handler)
    async def decorated(request: Request, *args: Any, **kwargs: Any) -> Any:
        """Make sure the client is authenticated as an app."""
        authenticate(request)
        if request.ctx.token.type != TokenType.APP:
            raise Forbidden('Endpoint requires app authorisation.')
        return await handler(request, *args, **kwargs)
    return decorated
