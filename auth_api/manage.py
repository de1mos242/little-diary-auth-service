import click
from flask.cli import FlaskGroup

from auth_api import config
from auth_api.app import create_app
from auth_api.models.resources_enum import Resources
from auth_api.models.roles_enum import Roles
from auth_api.services.user_service import create_internal_user


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

    if User.query.filter(User.username.in_((admin_username, measurement_tech_user))).first():
        click.echo("users already been created")
        return

    click.echo("create users")
    create_internal_user(username=admin_username, email="admin@ld.de1mos.net",
                         password=config.ADMIN_USER_DEFAULT_PASSWORD, role=Roles.Admin)
    create_internal_user(username=measurement_tech_user, email="measurement-tech@ld.de1mos.net",
                         password=config.MEASUREMENT_TECH_USER_DEFAULT_PASSWORD, role=Roles.Tech,
                         resources=[Resources.FAMILY_READ.value])
    db.session.commit()
    click.echo("users were created")


if __name__ == "__main__":
    cli()
