from app import create_app

def test_health_ok():
    app = create_app()
    client = app.test_client()
    r = client.get("/health")
    assert r.status_code == 400
    assert r.json.get("status") == "ok"