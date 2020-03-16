from uuid import uuid4

from auth_api.models import User
from auth_api.models.roles_enum import Roles


def test_get_user(client, db, user, admin_headers, regular_user_headers, regular_user, tech_user):
    # test 404
    rep = client.get("/api/v1/users/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    # test 403
    rep = client.get("/api/v1/users/%s" % user.external_uuid, headers=regular_user_headers)
    assert rep.status_code == 403

    # test access from user himself
    rep = client.get("/api/v1/users/%s" % regular_user.external_uuid, headers=regular_user_headers)
    assert rep.status_code == 200

    # test access from admin user
    rep = client.get("/api/v1/users/%s" % user.external_uuid, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["active"] == user.active

    rep = client.get("/api/v1/users/%s" % tech_user.external_uuid, headers=admin_headers)
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
    rep = client.put("/api/v1/users/%s" % user.external_uuid, json=data, headers=regular_user_headers)
    assert rep.status_code == 403

    # test update user
    rep = client.put("/api/v1/users/%s" % user.external_uuid, json=data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()["user"]
    assert data["username"] == "updated"
    assert data["email"] == user.email
    assert data["active"] == user.active


def test_delete_user(client, db, user, admin_headers, regular_user_headers):
    # test 404
    rep = client.delete("/api/v1/users/%s" % str(uuid4()), headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(user)
    db.session.commit()

    # test 403
    rep = client.delete("/api/v1/users/%s" % str(uuid4()), headers=regular_user_headers)
    assert rep.status_code == 403

    # test get_user
    user_id = user.id
    rep = client.delete("/api/v1/users/%s" % user.external_uuid, headers=admin_headers)
    assert rep.status_code == 200
    assert db.session.query(User).filter_by(id=user_id).first() is None


def test_create_user(client, db, admin_headers, regular_user_headers):
    # test bad data
    created_uuid = uuid4()
    data = {"username": "new user"}
    rep = client.put(f"/api/v1/users/{created_uuid}", json=data, headers=admin_headers)
    assert rep.status_code == 400

    data["password"] = "user_password"
    data["email"] = "create@mail.com"

    # test 403
    rep = client.put(f"/api/v1/users/{created_uuid}", json=data, headers=regular_user_headers)
    assert rep.status_code == 403, rep.data

    rep = client.put(f"/api/v1/users/{created_uuid}", json=data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()
    user = db.session.query(User).filter_by(external_uuid=data["user"]["uuid"]).first()

    assert user.username == "new user"
    assert user.email == "create@mail.com"
    assert user.role == Roles.User
    assert user.external_uuid == created_uuid


def test_create_tech_user(client, db, admin_headers):
    created_uuid = uuid4()
    data = {"username": "new tech",
            "password": "tech_pass",
            "email": "create@mail.com",
            "role": Roles.Tech,
            "resources": ["resource_item"]}
    rep = client.put(f"/api/v1/users/{created_uuid}", json=data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()
    user = db.session.query(User).filter_by(external_uuid=data["user"]["uuid"]).first()

    assert user.username == "new tech"
    assert user.email == "create@mail.com"
    assert user.role == Roles.Tech
    assert user.resources == ["resource_item"]
    assert user.external_uuid == created_uuid


def test_create_admin_user(client, db, admin_headers, regular_user_headers):
    created_uuid = uuid4()
    data = {"username": "new admin",
            "password": "admin",
            "email": "admin@mail.com",
            "role": "admin"}

    # test 403
    rep = client.put(f"/api/v1/users/{created_uuid}", json=data, headers=regular_user_headers)
    assert rep.status_code == 403

    rep = client.put(f"/api/v1/users/{created_uuid}", json=data, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()
    user = db.session.query(User).filter_by(external_uuid=data["user"]["uuid"]).first()

    assert user.username == "new admin"
    assert user.email == "admin@mail.com"
    assert user.role == Roles.Admin
    assert user.external_uuid == created_uuid


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
        assert any(u["uuid"] == str(user.external_uuid) for u in results["results"])


def test_change_password(client, db, regular_user, regular_user_headers, admin_headers, user):
    db.session.add(user)
    db.session.commit()

    old_password_hash = user.password
    resp = client.put(f"/api/v1/users/{user.external_uuid}/password",
                      json={"new_password": "Brand new password"},
                      headers=regular_user_headers)
    assert resp.status_code == 403

    assert user.password == old_password_hash

    old_password_hash = regular_user.password
    resp = client.put(f"/api/v1/users/{regular_user.external_uuid}/password",
                      json={"new_password": "Brand new password"},
                      headers=regular_user_headers)
    assert resp.status_code == 204

    assert regular_user.password != old_password_hash

    old_password_hash = regular_user.password
    resp = client.put(f"/api/v1/users/{regular_user.external_uuid}/password",
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
