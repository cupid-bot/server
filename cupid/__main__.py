"""
Command line tool for running the Cupid server or managing API apps.

Server configuration options are read with the following priority (descending):
 - CLI arguments
 - INI file (config.ini by default)
 - Environment variables

Usage:
  cupid [options]
  cupid [options] create-app <name>
  cupid [options] app <name_or_id>
  cupid [options] list-apps

Database options:
  --db-name <name>            Name of the database to connect to ('cupid').
  --db-user <user>            DB user to authenticate as ('cupid').
  --db-password <password>    Password for the database.
  --db-host <host>            Database host ('localhost').
  --db-port <port>            Database port (5432).

Discord options:
  --discord-api-url <url>     Discord API URL ('https://discord.com/api/v8').
  --discord-cdn-url <url>     Discord CDN URL ('https://cdn.discordapp.com').
  --discord-guild-id <id>     Discord guild ID (None).

Logging options:
  --log-level-peewee <level>  Log level for SQL ('INFO').
  --log-level-sanic <level>   Log level for Sanic ('INFO').
  --log-level-access <level>  Log level for HTTP ('INFO').
  --log-level-error <level>   Log level for internal errors ('INFO').
  --log-level-cupid <level>   Log level for Cupid itself ('INFO').

Other server options:
  --server-host <host>        The host to bind to ('0.0.0.0').
  --server-port <port>        The port to bind to (80).
  --config-file <path>        INI file for config options ('config.ini').
  --session-expiry <time>     User session expiry time ('PD30').
  --debug                     Whether to run in debug mode (no).

App management options (only with "app" command):
  --rename <name>             Change the app's name.
  --refresh-token             Refresh the app's token.
  --delete                    Delete the app.
"""
import secrets
import sys
from typing import Any

from docopt import docopt

from rich import box
from rich.console import Console
from rich.table import Column, Table

from . import config, routes
from .models import App, init_db


console = Console()
stderr = Console(stderr=True)


def print_error(message: str):
    """Print an error message and exit."""
    stderr.print(message, style='red')
    sys.exit(1)


def print_app(app: App):
    """Display an app's information on stdout."""
    table = Table(
        Column(style='bold blue'),
        Column(style='green'),
        box=box.ROUNDED,
        show_header=False,
        show_lines=True,
        border_style='bold blue',
    )
    table.add_row('ID', str(app.id))
    table.add_row('Name', app.name)
    table.add_row('Token', app.token)
    console.print(table)


def get_app(name_or_id: str) -> App:
    """Get an app by ID/name/search."""
    try:
        id = int(name_or_id)
    except ValueError:
        pass
    else:
        app = App.get_or_none(App.id == id)
        if app:
            return app
    if app := App.get_or_none(App.name ** name_or_id):
        return app
    search = name_or_id.lower()
    matches = []
    for app in App.select():
        if search in app.name.lower():
            matches.append(app)
    if len(matches) == 1:
        return matches[0]
    print_error(
        f'No app found by name or ID [bold red]"{name_or_id}"[/bold red].',
    )


def create_app(args: dict[str, Any]):
    """Create a new app."""
    app = App.create(name=args['<name>'])
    print_app(app)


def manage_app(args: dict[str, Any]):
    """Manage an existing app."""
    app = get_app(args['<name_or_id>'])
    if args['--delete']:
        name, id = app.name, app.id
        app.delete_instance()
        console.print(f'[red]App [bold]{name} ({id})[/bold] deleted.[/red]')
        return
    if name := args['--rename']:
        app.name = name
    if args['--refresh-token']:
        app.secret = secrets.token_bytes()
    app.save()
    print_app(app)


def list_apps():
    """Display a list of current apps."""
    table = Table(
        Column('ID', style='green'),
        Column('Name', style='green'),
        box=box.ROUNDED,
        header_style='bold blue',
        border_style='bold blue',
    )
    for app in App.select().order_by(App.id):
        table.add_row(str(app.id), app.name)
    console.print(table)


if __name__ == '__main__':
    args = docopt(__doc__, version='Cupid 0.1.0')
    config.load(args)
    init_db()
    if args['create-app']:
        create_app(args)
    elif args['app']:
        manage_app(args)
    elif args['list-apps']:
        list_apps()
    else:
        routes.run()
