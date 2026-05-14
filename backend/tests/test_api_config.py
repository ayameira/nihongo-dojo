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
        gemini_models = [model for model in data["models"] if model["provider"] == "gemini"]
        groq_models = [model for model in data["models"] if model["provider"] == "groq"]
        assert {model["id"] for model in gemini_models} == {
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
        }
        assert all(model["configured"] for model in gemini_models)
        assert all(not model["configured"] for model in groq_models)
        assert gemini_models[0]["name"]
        assert "input_cost_per_1m" in gemini_models[0]

    @pytest.mark.asyncio
    async def test_returns_groq_models_for_groq_provider(self, test_client):
        settings = Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="groq",
            llm_api_key="test-groq-key",
        )

        with patch('app.api.config.get_settings', return_value=settings):
            response = await test_client.get("/api/config/models")

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "groq"
        assert data["current_model"] == "llama-3.1-8b-instant"
        groq_models = [model for model in data["models"] if model["provider"] == "groq"]
        assert "llama-3.1-8b-instant" in {model["id"] for model in groq_models}
        assert all(model["configured"] for model in groq_models)
