from auth_api.models import User
from auth_api.models.roles_enum import Roles


def test_get_user(client, db, user, admin_headers, regular_user_headers, regular_user, tech_user):
    # test 404
    rep = client.get("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    # test 403
    rep = client.get("/api/v1/users/%d" % user.id, headers=regular_user_headers)
    assert rep.status_code == 403

    # test access from user himself
    rep = client.get("/api/v1/users/%d" % regular_user.id, headers=regular_user_headers)
    assert rep.status_code == 200

    # test access from admin user
    rep = client.get("/api/v1/users/%d" % user.id, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["active"] == user.active

    rep = client.get("/api/v1/users/%d" % tech_user.id, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["resources"] == tech_user.resources
    assert data["username"] == tech_user.username
    assert data["email"] == tech_user.email
    assert data["active"] == tech_user.active


def test_put_user(client, db, user, admin_headers, regular_user_headers):
    # test 404
    rep = client.put("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    data = {"username": "updated"}

    # test 403
    rep = client.put("/api/v1/users/%d" % user.id, json=data, headers=regular_user_headers)
    assert rep.status_code == 403

    # test update user
    rep = client.put("/api/v1/users/%d" % user.id, json=data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["username"] == "updated"
    assert data["email"] == user.email
    assert data["active"] == user.active


def test_delete_user(client, db, user, admin_headers, regular_user_headers):
    # test 404
    rep = client.delete("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    # test 403
    rep = client.delete("/api/v1/users/100000", headers=regular_user_headers)
    assert rep.status_code == 403

    # test get_user
    user_id = user.id
    rep = client.delete("/api/v1/users/%d" % user_id, headers=admin_headers)
    assert rep.status_code == 200
    assert db.session.query(User).filter_by(id=user_id).first() is None


def test_create_user(client, db, admin_headers, regular_user_headers):
    # test bad data
    data = {"username": "new user"}
    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 400

    data["password"] = "user_password"
    data["email"] = "create@mail.com"

    # test 403
    rep = client.post("/api/v1/users", json=data, headers=regular_user_headers)
    assert rep.status_code == 403

    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 201

    data = rep.get_json()
    user = db.session.query(User).filter_by(id=data["user"]["id"]).first()

    assert user.username == "new user"
    assert user.email == "create@mail.com"
    assert user.role == Roles.User


def test_create_tech_user(client, db, admin_headers):
    data = {"username": "new tech",
            "password": "tech_pass",
            "email": "create@mail.com",
            "role": Roles.Tech,
            "resources": ["resource_item"]}
    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 201

    data = rep.get_json()
    user = db.session.query(User).filter_by(id=data["user"]["id"]).first()

    assert user.username == "new tech"
    assert user.email == "create@mail.com"
    assert user.role == Roles.Tech
    assert user.resources == ["resource_item"]


def test_create_admin_user(client, db, admin_headers, regular_user_headers):
    data = {"username": "new admin",
            "password": "admin",
            "email": "admin@mail.com",
            "role": "admin"}

    # test 403
    rep = client.post("/api/v1/users", json=data, headers=regular_user_headers)
    assert rep.status_code == 403

    rep = client.post("/api/v1/users", json=data, headers=admin_headers)
    assert rep.status_code == 201

    data = rep.get_json()
    user = db.session.query(User).filter_by(id=data["user"]["id"]).first()

    assert user.username == "new admin"
    assert user.email == "admin@mail.com"
    assert user.role == Roles.Admin


def test_get_all_user(client, db, user_factory, admin_headers, regular_user_headers):
    users = user_factory.create_batch(30)

    db.session.add_all(users)
    db.session.commit()

    # test 403
    rep = client.get("/api/v1/users", headers=regular_user_headers)
    assert rep.status_code == 403

    rep = client.get("/api/v1/users", headers=admin_headers)
    assert rep.status_code == 200

    results = rep.get_json()
    for user in users:
        assert any(u["id"] == user.id for u in results["results"])


def test_change_password(client, db, regular_user, regular_user_headers, admin_headers, user):
    db.session.add(user)
    db.session.commit()

    old_password_hash = user.password
    resp = client.put(f"/api/v1/users/{user.id}/password",
                      json={"new_password": "Brand new password"},
                      headers=regular_user_headers)
    assert resp.status_code == 403

    assert user.password == old_password_hash

    old_password_hash = regular_user.password
    resp = client.put(f"/api/v1/users/{regular_user.id}/password",
                      json={"new_password": "Brand new password"},
                      headers=regular_user_headers)
    assert resp.status_code == 204

    assert regular_user.password != old_password_hash

    old_password_hash = regular_user.password
    resp = client.put(f"/api/v1/users/{regular_user.id}/password",
                      json={"new_password": "Brand new password 2"},
                      headers=admin_headers)
    assert resp.status_code == 204

    assert regular_user.password != old_password_hash


def test_get_public_user(client, db, user, admin_user, regular_user_headers):
    db.session.add(user)
    db.session.commit()

    # test 404
    rep = client.get(f"/api/v1/users/public?uuids=12345678-1234-5678-9012-123456789012&uuids={user.external_uuid}",
                     headers=regular_user_headers)
    assert rep.status_code == 404, rep.data

    rep = client.get("/api/v1/users/public?uuids=%s&uuids=%s&uuids=%s" % (user.external_uuid,
                                                                          admin_user.external_uuid,
                                                                          user.external_uuid),
                     headers=regular_user_headers)
    assert rep.status_code == 200

    data = rep.get_json()
    assert len(data) == 2
    values = {item['uuid']: item['username'] for item in data}
    assert set(values.keys()) == {str(user.external_uuid), str(admin_user.external_uuid)}
    assert values[str(user.external_uuid)] == user.username
    assert values[str(admin_user.external_uuid)] == admin_user.username
