"""Tool for interacting with the Discord API for user authentication."""
import dataclasses
from typing import Any

import aiohttp

from .config import CONFIG


AVATAR_URL = '{cdn}/avatars/{id}/{hash}.png'
NO_AVATAR_URL = '{cdn}/avatars/embed/avatars/{discrim}.png'

session: aiohttp.ClientSession = None


def get_required_scopes() -> set[str]:
    """Get the scopes a bearer token must have."""
    if CONFIG.discord_guild_id:
        return {'identify', 'guilds'}
    else:
        return {'identify'}


async def get_session() -> session:
    """Get or create the aiohttp session."""
    global session
    if (not session) or session.closed:
        session = aiohttp.ClientSession()
    return session


@dataclasses.dataclass
class DiscordUser:
    """Data on a Discord user from the Discord API."""

    id: str
    name: str
    discriminator: str
    avatar_url: str


class DiscordAuthError(ValueError):
    """An issue with the provided Discord token."""


def get_avatar_url(data: dict[str, Any]) -> str:
    """Form the avatar URL of a user object."""
    if av_hash := data['avatar']:
        return AVATAR_URL.format(
            cdn=CONFIG.discord_cdn_url, id=data['id'], hash=av_hash,
        )
    return NO_AVATAR_URL.format(
        cdn=CONFIG.discord_cdn_url, discrim=int(data['discriminator']) % 5,
    )


async def make_discord_request(endpoint: str, token: str) -> dict[str, Any]:
    """Make a parameter-less GET request to the Discord API."""
    session = await get_session()
    headers = {'Authorization': 'Bearer ' + token}
    endpoint = CONFIG.discord_api_url + endpoint
    async with session.get(endpoint, headers=headers) as response:
        try:
            return await response.json()
        except ValueError as e:
            raise DiscordAuthError('Unexpected Discord API response.') from e


async def get_user(token: str) -> DiscordUser:
    """Get a Discord user using a bearer token."""
    data = await make_discord_request('/oauth2/@me', token)
    if not (scopes := data['scopes']):
        raise ValueError('Invalid Discord access token.')
    if (required := get_required_scopes()) - set(scopes):
        raise DiscordAuthError(
            'The following scopes are required: ' + ', '.join(required),
        )
    user = data['user']
    return DiscordUser(
        id=int(user['id']),
        name=user['username'],
        avatar_url=get_avatar_url(user),
        discriminator=user['discriminator'],
    )


async def check_guilds(token: str):
    """Make sure the user is in the required guild, if specified."""
    if not CONFIG.discord_guild_id:
        return
    data = await make_discord_request('/users/@me/guilds', token)
    for guild in data:
        if guild['id'] == str(CONFIG.discord_guild_id):
            return
    raise DiscordAuthError('You are not in the required Discord server.')


async def authenticate_user(token: str) -> DiscordUser:
    """Get data on a user from an user token."""
    user = get_user(token)
    check_guilds(token)
    return user
