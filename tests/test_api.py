import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture
def sample_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


def test_get_activities_returns_data_and_no_store_header(client, sample_activities):
    # Arrange
    expected_activities = sample_activities.copy()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client, sample_activities):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in sample_activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client, sample_activities):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert sample_activities["Chess Club"]["participants"].count(email) == 1


def test_signup_returns_not_found_for_unknown_activity(client, sample_activities):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Unknown%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_unregisters_student(client, sample_activities):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.delete("/activities/Chess%20Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in sample_activities["Chess Club"]["participants"]


def test_remove_participant_returns_not_found_for_unregistered_student(client, sample_activities):
    # Arrange
    email = "missing@mergington.edu"

    # Act
    response = client.delete("/activities/Chess%20Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_remove_participant_returns_not_found_for_unknown_activity(client, sample_activities):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown%20Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"