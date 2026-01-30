"""
API tests for notes routes (now serves student record).
"""
import pytest
from unittest.mock import patch


class TestGetNotes:
    """Tests for GET /api/notes endpoint."""

    @pytest.mark.asyncio
    async def test_returns_student_record_content(self, test_client, temp_student_record_file, test_settings):
        """Test retrieving student record content."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.get("/api/notes")

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Student Record" in data["content"]


class TestGetSection:
    """Tests for GET /api/notes/{section} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_section_content(self, test_client, temp_student_record_file, test_settings):
        """Test retrieving a specific section."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.get("/api/notes/goals")

        assert response.status_code == 200
        data = response.json()
        assert data["section"] == "goals"
        assert "content" in data

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_section(self, test_client):
        """Test that 400 is returned for invalid section name."""
        response = await test_client.get("/api/notes/invalid_section")

        assert response.status_code == 400
        assert "Invalid section" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_accepts_all_valid_sections(self, test_client, temp_student_record_file, test_settings):
        """Test that all valid sections are accepted."""
        test_settings.student_record_path = temp_student_record_file

        valid_sections = ["goals", "background", "interests", "preferences", "notes"]

        with patch('app.api.notes.get_settings', return_value=test_settings):
            for section in valid_sections:
                response = await test_client.get(f"/api/notes/{section}")
                assert response.status_code == 200, f"Failed for section: {section}"


class TestUpdateNotes:
    """Tests for PUT /api/notes endpoint."""

    @pytest.mark.asyncio
    async def test_updates_full_student_record(self, test_client, temp_student_record_file, test_settings):
        """Test updating the entire student record file."""
        test_settings.student_record_path = temp_student_record_file
        new_content = "# Student Record\n\n## Goals\nNew goals here"

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.put(
                "/api/notes",
                json={"content": new_content}
            )

        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower()


class TestUpdateSection:
    """Tests for PUT /api/notes/{section} endpoint."""

    @pytest.mark.asyncio
    async def test_replaces_section(self, test_client, temp_student_record_file, test_settings):
        """Test replacing a section's content."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.put(
                "/api/notes/goals",
                json={
                    "action": "replace",
                    "content": "New goals content"
                }
            )

        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_appends_to_section(self, test_client, temp_student_record_file, test_settings):
        """Test appending to a section's content."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.put(
                "/api/notes/notes",
                json={
                    "action": "append",
                    "content": "Additional note"
                }
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_section(self, test_client):
        """Test that 400 is returned for invalid section."""
        response = await test_client.put(
            "/api/notes/invalid",
            json={"action": "replace", "content": "test"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_action(self, test_client, temp_student_record_file, test_settings):
        """Test that 400 is returned for invalid action."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.put(
                "/api/notes/goals",
                json={"action": "invalid_action", "content": "test"}
            )

        assert response.status_code == 400
        assert "Action must be" in response.json()["detail"]


class TestGetTokenCount:
    """Tests for GET /api/notes/token-count endpoint."""

    @pytest.mark.asyncio
    async def test_returns_token_count(self, test_client, temp_student_record_file, test_settings):
        """Test retrieving token count."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.api.notes.get_settings', return_value=test_settings):
            response = await test_client.get("/api/notes/token-count")

        assert response.status_code == 200
        data = response.json()
        assert "token_count" in data
        assert isinstance(data["token_count"], int)
