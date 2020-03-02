from auth_api.models import User
from auth_api.models.roles_enum import Roles


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


def test_get_all_user(client, db, user_factory, admin_headers):
    users = user_factory.create_batch(30)

    db.session.add_all(users)
    db.session.commit()

    rep = client.get("/api/v1/users", headers=admin_headers)
    assert rep.status_code == 200

    results = rep.get_json()
    for user in users:
        assert any(u["id"] == user.id for u in results["results"])


def test_change_password_by_user(client, db, regular_user, user_headers):
    old_password_hash = regular_user.password
    resp = client.put(f"/api/v1/users/{regular_user.id}/password",
                      json={"new_password": "Brand new password"},
                      headers=user_headers)
    assert resp.status_code == 204

    assert regular_user.password != old_password_hash


def test_change_password_by_admin(client, db, regular_user, admin_headers):
    old_password_hash = regular_user.password
    resp = client.put(f"/api/v1/users/{regular_user.id}/password",
                      json={"new_password": "Brand new password"},
                      headers=admin_headers)
    assert resp.status_code == 204

    assert regular_user.password != old_password_hash


def test_change_password_to_another_user(client, db, regular_user, user_headers, user_factory):
    another_user = user_factory()
    db.session.add(another_user)
    db.session.commit()

    old_password_hash = another_user.password
    resp = client.put(f"/api/v1/users/{another_user.id}/password",
                      json={"new_password": "Brand new password"},
                      headers=user_headers)
    assert resp.status_code == 403

    assert another_user.password == old_password_hash
