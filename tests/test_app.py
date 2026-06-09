"""
Test suite for Mergington High School Activity Management API

Uses AAA (Arrange, Act, Assert) pattern and pytest fixtures for test isolation.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Fixture: Create a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture: Reset activities to known state before and after each test"""
    # Arrange: Store initial state
    original_activities = {
        k: {**v, "participants": v["participants"].copy()}
        for k, v in activities.items()
    }
    
    yield  # Test runs here
    
    # Cleanup: Restore initial state
    for activity_name in list(activities.keys()):
        activities[activity_name]["participants"] = original_activities[
            activity_name
        ]["participants"].copy()


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client, reset_activities):
        # Act
        response = client.get("/activities")
        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_known_activities(self, client, reset_activities):
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        # Act
        response = client.get("/activities")
        data = response.json()
        # Assert
        for activity in expected_activities:
            assert activity in data
            assert "description" in data[activity]
            assert "schedule" in data[activity]
            assert "participants" in data[activity]


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_returns_200(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")
        activities_data = response.json()
        # Assert
        assert email in activities_data[activity_name]["participants"]

    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert
        assert response.status_code == 400
        assert "Already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_normalizes_email_case(self, client, reset_activities):
        # Arrange
        activity_name = "Art Club"
        email_lower = "newuser@mergington.edu"
        email_upper = "NEWUSER@MERGINGTON.EDU"
        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email_lower})
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email_upper})
        # Assert
        assert response.status_code == 400


class TestUnregisterEndpoint:
    """Test suite for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_existing_participant_returns_200(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant_from_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"
        # Act
        client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")
        activities_data = response.json()
        # Assert
        assert email not in activities_data[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"
        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert
        assert response.status_code == 404


class TestIntegrationFlow:
    """Integration tests: Verify end-to-end signup/unregister flow"""

    def test_signup_then_unregister_flow(self, client, reset_activities):
        # Arrange
        activity_name = "Drama Club"
        email = "integration_test@mergington.edu"
        # Act: Signup
        signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert signup succeeded
        assert signup_response.status_code == 200
        # Act: Verify in list
        list_response = client.get("/activities")
        assert email in list_response.json()[activity_name]["participants"]
        # Act: Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        # Assert unregister succeeded
        assert unregister_response.status_code == 200
        # Act: Verify removed from list
        final_response = client.get("/activities")
        assert email not in final_response.json()[activity_name]["participants"]
