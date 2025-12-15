"""
Tests for the Mergington High School API endpoints.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_html(self, client):
        """Test that the root path redirects to the static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities
        assert "Chess Club" in data
        assert "Basketball Team" in data
        assert "Programming Class" in data
    
    def test_get_activities_has_correct_structure(self, client):
        """Test that each activity has the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_participants_count(self, client):
        """Test that activities have the expected number of participants."""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Swimming Club"]["participants"]) == 1
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify the student was added
        activities = client.get("/activities").json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_student(self, client):
        """Test that a student cannot sign up twice for the same activity."""
        email = "michael@mergington.edu"
        
        # This student is already in Chess Club
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for a non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_students(self, client):
        """Test multiple students can sign up for the same activity."""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(f"/activities/Art%20Studio/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students were added
        activities = client.get("/activities").json()
        participants = activities["Art Studio"]["participants"]
        for email in emails:
            assert email in participants
    
    def test_signup_preserves_existing_participants(self, client):
        """Test that signing up preserves existing participants."""
        # Get initial participants
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities["Drama Club"]["participants"])
        
        # Add new student
        response = client.post(
            "/activities/Drama%20Club/signup?email=newdrama@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify count increased by 1
        updated_activities = client.get("/activities").json()
        assert len(updated_activities["Drama Club"]["participants"]) == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"
        
        # Verify student is enrolled
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister the student
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify the student was removed
        activities = client.get("/activities").json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_student_not_enrolled(self, client):
        """Test unregistering a student who is not enrolled returns 400."""
        email = "notenrolled@mergington.edu"
        
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from a non-existent activity returns 404."""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_unregister_preserves_other_participants(self, client):
        """Test that unregistering one student preserves others."""
        # Get initial participants
        activities = client.get("/activities").json()
        initial_participants = activities["Chess Club"]["participants"].copy()
        
        # Remove one student
        email_to_remove = initial_participants[0]
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email_to_remove}")
        assert response.status_code == 200
        
        # Verify only that student was removed
        updated_activities = client.get("/activities").json()
        updated_participants = updated_activities["Chess Club"]["participants"]
        
        assert email_to_remove not in updated_participants
        assert len(updated_participants) == len(initial_participants) - 1
        
        for email in initial_participants:
            if email != email_to_remove:
                assert email in updated_participants
    
    def test_unregister_all_participants(self, client):
        """Test unregistering all participants from an activity."""
        activities = client.get("/activities").json()
        participants = activities["Swimming Club"]["participants"].copy()
        
        # Remove all participants
        for email in participants:
            response = client.delete(f"/activities/Swimming%20Club/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify activity has no participants
        updated_activities = client.get("/activities").json()
        assert len(updated_activities["Swimming Club"]["participants"]) == 0


class TestIntegration:
    """Integration tests for multiple operations."""
    
    def test_signup_and_unregister_workflow(self, client):
        """Test the complete workflow of signing up and unregistering."""
        email = "workflow@mergington.edu"
        activity = "Science Club"
        
        # Get initial state
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities").json()
        assert email in after_signup[activity]["participants"]
        assert len(after_signup[activity]["participants"]) == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        after_unregister = client.get("/activities").json()
        assert email not in after_unregister[activity]["participants"]
        assert len(after_unregister[activity]["participants"]) == initial_count
    
    def test_multiple_activities_same_student(self, client):
        """Test that a student can sign up for multiple activities."""
        email = "multitask@mergington.edu"
        activities_list = ["Chess Club", "Art Studio", "Science Club"]
        
        # Sign up for multiple activities
        for activity in activities_list:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_list:
            assert email in all_activities[activity]["participants"]
