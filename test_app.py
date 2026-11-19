import pytest
from app import app, calculate_bmi, calculate_calories, init_db


@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test_aceest.db"
    app.config["DATABASE"] = str(db_file)
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as test_client:
        yield test_client


def test_calculate_calories():
    assert calculate_calories(80, "Fat Loss (FL)") == 1760
    assert calculate_calories(70, "Muscle Gain (MG)") == 2450
    assert calculate_calories(60, "Beginner (BG)") == 1560
    assert calculate_calories(-10, "Fat Loss (FL)") is None
    assert calculate_calories(70, "Unknown Program") is None


def test_calculate_bmi():
    assert calculate_bmi(175, 68) == {"bmi": 22.2, "category": "Normal"}
    assert calculate_bmi(180, 55) == {"bmi": 17.0, "category": "Underweight"}
    assert calculate_bmi(170, 80) == {"bmi": 27.7, "category": "Overweight"}
    assert calculate_bmi(165, 95) == {"bmi": 34.9, "category": "Obese"}
    assert calculate_bmi(0, 70) is None


def test_home_and_health_endpoints(client):
    home_res = client.get("/")
    assert home_res.status_code == 200
    data = home_res.get_json()
    assert data["status"] == "running"
    assert data["capacity"] == 150

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.get_json() == {"status": "healthy"}


def test_programs_endpoint(client):
    res = client.get("/programs")
    assert res.status_code == 200
    programs = res.get_json()
    assert "Fat Loss (FL)" in programs
    assert "Muscle Gain (MG)" in programs
    assert "Beginner (BG)" in programs


def test_create_and_fetch_clients(client):
    payload = {
        "name": "Arjun",
        "age": 28,
        "height": 175,
        "weight": 75,
        "program": "Fat Loss (FL)",
    }
    post_res = client.post("/clients", json=payload)
    assert post_res.status_code == 201
    assert post_res.get_json()["client"]["calories"] == 1650

    get_res = client.get("/clients")
    assert get_res.status_code == 200
    clients = get_res.get_json()
    assert len(clients) == 1
    assert clients[0]["name"] == "Arjun"


def test_create_client_validation_error(client):
    res = client.post("/clients", json={"name": "InvalidUser", "program": "Invalid"})
    assert res.status_code == 400


def test_client_bmi_endpoint(client):
    client.post(
        "/clients",
        json={
            "name": "Meera",
            "age": 25,
            "height": 165,
            "weight": 60,
            "program": "Beginner (BG)",
        },
    )
    res = client.get("/clients/Meera/bmi")
    assert res.status_code == 200
    body = res.get_json()
    assert body["client"] == "Meera"
    assert body["category"] == "Normal"

    missing_res = client.get("/clients/Nobody/bmi")
    assert missing_res.status_code == 404


def test_workouts_and_progress_endpoints(client):
    w_res = client.post(
        "/workouts",
        json={
            "client_name": "Arjun",
            "workout_type": "Strength",
            "duration_min": 45,
            "notes": "5x5 Back Squat",
        },
    )
    assert w_res.status_code == 201

    list_res = client.get("/workouts")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 1

    p_res = client.post(
        "/progress",
        json={"client_name": "Arjun", "week": "Week 1", "adherence": 90},
    )
    assert p_res.status_code == 201

    bad_p_res = client.post(
        "/progress",
        json={"client_name": "Arjun", "adherence": 150},
    )
    assert bad_p_res.status_code == 400
