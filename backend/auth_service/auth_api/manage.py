import click
from flask.cli import FlaskGroup

from auth_api.app import create_app


def create_auth_api(info):
    return create_app(cli=True)


@click.group(cls=FlaskGroup, create_app=create_auth_api)
def cli():
    """Main entry point"""


@cli.command("init")
def init():
    """Create a new admin user
    """
    from auth_api.extensions import db
    from auth_api.models import User

    click.echo("create user")
    user = User(username="admin", email="de1m0s242@gmail.com", password="qwerty", active=True)
    db.session.add(user)
    db.session.commit()
    click.echo("created user admin")


if __name__ == "__main__":
    cli()
