def test_health(client, admin_user):
    resp = client.get("/status/health")
    assert resp.status_code == 200, resp.data
