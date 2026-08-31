"""
Test suite for the Mergington High School Activities API

This module contains happy-path tests for all API endpoints using FastAPI's TestClient.
Tests use the application's in-memory database state.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test that /activities returns all activities with correct structure"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify structure of an activity
        first_activity = next(iter(activities.values()))
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)

    def test_activities_have_participants(self, client):
        """Test that activities have some participants pre-populated"""
        response = client.get("/activities")
        activities = response.json()
        
        # At least some activities should have participants
        has_participants = any(
            len(activity["participants"]) > 0 
            for activity in activities.values()
        )
        assert has_participants


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity(self, client):
        """Test successful signup for an activity"""
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        
        # Get initial participant count
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity_name]["participants"])
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        activities_after = client.get("/activities").json()
        final_count = len(activities_after[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in activities_after[activity_name]["participants"]


class TestRemoveEndpoint:
    """Tests for the POST /activities/{activity_name}/remove endpoint"""

    def test_remove_participant(self, client):
        """Test successful removal of a participant from an activity"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Pre-existing participant
        
        response = client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]

    def test_remove_decreases_participant_count(self, client):
        """Test that removal actually decreases the participant count"""
        activity_name = "Gym Class"
        email = "john@mergington.edu"  # Pre-existing participant
        
        # Get initial participant count
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity_name]["participants"])
        
        # Remove participant
        client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Verify participant was removed
        activities_after = client.get("/activities").json()
        final_count = len(activities_after[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in activities_after[activity_name]["participants"]


class TestSignupAndRemoveFlow:
    """Integration tests combining signup and remove operations"""

    def test_signup_then_remove(self, client):
        """Test the complete flow of signing up and then removing a participant"""
        activity_name = "Art Club"
        email = "temporary@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
        
        # Remove
        remove_response = client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        assert remove_response.status_code == 200
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]
