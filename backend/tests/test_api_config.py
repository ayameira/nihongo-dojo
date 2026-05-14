"""
API tests for configuration routes.
"""
import pytest
from unittest.mock import patch

from app.config import Settings


class TestConfigModels:
    """Tests for GET /api/config/models endpoint."""

    @pytest.mark.asyncio
    async def test_returns_available_chat_models(self, test_client):
        settings = Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            gemini_api_key="test-api-key",
            gemini_model="gemini-3-pro-preview",
        )

        with patch('app.api.config.get_settings', return_value=settings):
            response = await test_client.get("/api/config/models")

        assert response.status_code == 200
        data = response.json()
        assert data["current_model"] == "gemini-3-pro-preview"
        assert {model["id"] for model in data["models"]} == {
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
        }
        assert data["models"][0]["name"]
        assert "input_cost_per_1m" in data["models"][0]
