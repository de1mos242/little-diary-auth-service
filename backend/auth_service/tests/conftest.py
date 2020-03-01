import json
from uuid import uuid4

import pytest

from auth_api.app import create_app
from auth_api.extensions import db as _db
from auth_api.models import User


@pytest.fixture(scope='session')
def app():
    app = create_app(testing=True)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='session')
def db(app):
    exclude_tables = ["alembic_version"]

    meta = _db.metadata
    for table in reversed(meta.sorted_tables):
        if table.name not in exclude_tables:
            _db.session.execute(table.delete())

    _db.session.commit()
    return _db


@pytest.fixture(scope='function')
def session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def admin_user(session):
    user = User(
        username='admin',
        email='admin@admin.com',
        password='admin',
        external_uuid=uuid4()
    )

    session.add(user)
    session.commit()

    return user


@pytest.fixture
def admin_headers(admin_user, client):
    data = {
        'username': admin_user.username,
        'password': 'admin'
    }
    rep = client.post(
        '/auth/login',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )

    tokens = json.loads(rep.get_data(as_text=True))
    return {
        'content-type': 'application/json',
        'authorization': 'Bearer %s' % tokens['access_token']
    }


@pytest.fixture
def admin_refresh_headers(admin_user, client):
    data = {
        'username': admin_user.username,
        'password': 'admin'
    }
    rep = client.post(
        '/auth/login',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )

    tokens = json.loads(rep.get_data(as_text=True))
    return {
        'content-type': 'application/json',
        'authorization': 'Bearer %s' % tokens['refresh_token']
    }
