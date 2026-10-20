def test_register_success(client):
    payload = {
        "email": "newuser@example.com",
        "password": "ValidPassword999!",
        "full_name": "New User"
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"


def test_register_duplicate_email(client, test_user):
    payload = {
        "email": test_user["user"]["email"],
        "password": "AnotherPassword123!",
        "full_name": "Alice Duplicate"
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


def test_register_short_password(client):
    payload = {
        "email": "short@example.com",
        "password": "short",
        "full_name": "Short Pwd"
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 422


def test_login_success(client, test_user):
    payload = {
        "email": test_user["user"]["email"],
        "password": test_user["password"]
    }
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user["user"]["email"]


def test_login_wrong_password(client, test_user):
    payload = {
        "email": test_user["user"]["email"],
        "password": "IncorrectPassword"
    }
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401


def test_get_me_authenticated(client, test_user):
    resp = client.get("/auth/me", headers=test_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_user["user"]["email"]
    assert data["id"] == test_user["user"]["id"]


def test_get_me_unauthorized(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
