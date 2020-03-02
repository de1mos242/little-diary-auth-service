from uuid import uuid4

import factory
import pytest
from pytest_factoryboy import register

from auth_api.models import User
from auth_api.models.roles_enum import Roles


@register
class UserFactory(factory.Factory):
    username = factory.Sequence(lambda n: "user%d" % n)
    email = factory.Sequence(lambda n: "user%d@mail.com" % n)
    password = "mypwd"
    external_uuid = factory.LazyFunction(uuid4)

    class Meta:
        model = User


@pytest.mark.usefixtures("session")
def test_get_user(client, db, user, admin_headers):
    # test 404
    rep = client.get("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    # test get_user
    rep = client.get("/api/v1/users/%d" % user.id, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["active"] == user.active


@pytest.mark.usefixtures("session")
def test_put_user(client, db, user, admin_headers):
    # test 404
    rep = client.put("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    data = {"username": "updated"}

    # test update user
    rep = client.put("/api/v1/users/%d" % user.id, json=data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["username"] == "updated"
    assert data["email"] == user.email
    assert data["active"] == user.active


@pytest.mark.usefixtures("session")
def test_delete_user(client, db, user, admin_headers):
    # test 404
    rep = client.delete("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    # test get_user
    user_id = user.id
    rep = client.delete("/api/v1/users/%d" % user_id, headers=admin_headers)
    assert rep.status_code == 200
    assert db.session.query(User).filter_by(id=user_id).first() is None


@pytest.mark.usefixtures("session")
def test_create_user(client, db, admin_headers):
    # test bad data
    data = {"username": "new user"}
    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 400

    data["password"] = "user_password"
    data["email"] = "create@mail.com"

    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 201

    data = rep.get_json()
    user = db.session.query(User).filter_by(id=data["user"]["id"]).first()

    assert user.username == "new user"
    assert user.email == "create@mail.com"
    assert user.role == Roles.User


@pytest.mark.usefixtures("session")
def test_create_admin_user(client, db, admin_headers):
    data = {"username": "new admin",
            "password": "admin",
            "email": "admin@mail.com",
            "role": "admin"}

    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 201

    data = rep.get_json()
    user = db.session.query(User).filter_by(id=data["user"]["id"]).first()

    assert user.username == "new admin"
    assert user.email == "admin@mail.com"
    assert user.role == Roles.Admin


@pytest.mark.usefixtures("session")
def test_get_all_user(client, db, user_factory, admin_headers):
    users = user_factory.create_batch(30)

    db.session.add_all(users)
    db.session.commit()

    rep = client.get("/api/v1/users", headers=admin_headers)
    assert rep.status_code == 200

    results = rep.get_json()
    for user in users:
        assert any(u["id"] == user.id for u in results["results"])
