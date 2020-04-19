from uuid import uuid4

import click
from flask.cli import FlaskGroup

from auth_api import config
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

    admin_username = "admin"
    measurement_tech_user = "measurement_tech_user"

    if len(User.query.filter(User.username.in_(admin_username, measurement_tech_user))) > 0:
        click.echo("users already been created")
        return

    click.echo("create users")
    user = User(username=admin_username, email="de1m0s242@gmail.com", password=config.ADMIN_USER_DEFAULT_PASSWORD,
                active=True,
                external_uuid=uuid4(),
                role="admin")
    db.session.add(user)
    measurement_user = User(username=measurement_tech_user, email="measurement.little_diary@de1mos.net",
                            password=config.MEASUREMENT_TECH_USER_DEFAULT_PASSWORD,
                            active=True,
                            external_uuid=uuid4(),
                            resources=["family_read"],
                            role="tech")
    db.session.add(measurement_user)
    db.session.commit()
    click.echo("users created")


if __name__ == "__main__":
    cli()
