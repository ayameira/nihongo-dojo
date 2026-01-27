"""
API tests for telemetry routes.
"""
import pytest
from datetime import datetime, timedelta


class TestGetUsage:
    """Tests for GET /api/telemetry/usage endpoint."""

    @pytest.mark.asyncio
    async def test_returns_usage_for_day(self, test_client, sample_token_logs):
        """Test retrieving usage for day period."""
        response = await test_client.get("/api/telemetry/usage?period=day")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "day"
        assert "totals" in data
        assert "daily_breakdown" in data

    @pytest.mark.asyncio
    async def test_returns_usage_for_week(self, test_client, sample_token_logs):
        """Test retrieving usage for week period."""
        response = await test_client.get("/api/telemetry/usage?period=week")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"

    @pytest.mark.asyncio
    async def test_returns_usage_for_month(self, test_client, sample_token_logs):
        """Test retrieving usage for month period."""
        response = await test_client.get("/api/telemetry/usage?period=month")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "month"

    @pytest.mark.asyncio
    async def test_defaults_to_week(self, test_client):
        """Test that default period is week."""
        response = await test_client.get("/api/telemetry/usage")

        assert response.status_code == 200
        assert response.json()["period"] == "week"

    @pytest.mark.asyncio
    async def test_returns_totals(self, test_client, sample_token_logs):
        """Test that totals are included in response."""
        response = await test_client.get("/api/telemetry/usage")

        totals = response.json()["totals"]
        assert "input_tokens" in totals
        assert "output_tokens" in totals
        assert "total_tokens" in totals
        assert "cost_usd" in totals
        assert "image_count" in totals
        assert "request_count" in totals

    @pytest.mark.asyncio
    async def test_returns_daily_breakdown(self, test_client, sample_token_logs):
        """Test that daily breakdown is included."""
        response = await test_client.get("/api/telemetry/usage")

        data = response.json()
        assert "daily_breakdown" in data
        # daily_breakdown is a dict with date keys

    @pytest.mark.asyncio
    async def test_rejects_invalid_period(self, test_client):
        """Test that invalid period is rejected."""
        response = await test_client.get("/api/telemetry/usage?period=invalid")

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_returns_dates(self, test_client):
        """Test that start and end dates are included."""
        response = await test_client.get("/api/telemetry/usage")

        data = response.json()
        assert "start_date" in data
        assert "end_date" in data


class TestGetLimit:
    """Tests for GET /api/telemetry/limit endpoint."""

    @pytest.mark.asyncio
    async def test_returns_limit_info(self, test_client, test_settings):
        """Test retrieving spending limit info."""
        response = await test_client.get("/api/telemetry/limit")

        assert response.status_code == 200
        data = response.json()
        assert "spent" in data
        assert "limit" in data
        assert "remaining" in data
        assert "period" in data

    @pytest.mark.asyncio
    async def test_returns_weekly_period(self, test_client):
        """Test that period is weekly."""
        response = await test_client.get("/api/telemetry/limit")

        assert response.json()["period"] == "weekly"

    @pytest.mark.asyncio
    async def test_calculates_remaining(self, test_client, test_settings):
        """Test that remaining is calculated correctly."""
        response = await test_client.get("/api/telemetry/limit")

        data = response.json()
        expected_remaining = data["limit"] - data["spent"]
        assert abs(data["remaining"] - expected_remaining) < 0.01

    @pytest.mark.asyncio
    async def test_includes_period_start(self, test_client):
        """Test that period_start is included."""
        response = await test_client.get("/api/telemetry/limit")

        assert "period_start" in response.json()


class TestUpdateLimit:
    """Tests for PUT /api/telemetry/limit endpoint."""

    @pytest.mark.asyncio
    async def test_returns_info_message(self, test_client):
        """Test that update returns info about env var requirement."""
        response = await test_client.put(
            "/api/telemetry/limit",
            json={"limit": 20.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert "environment" in data["message"].lower() or "env" in data["message"].lower()
        assert data["requested_limit"] == 20.0

    @pytest.mark.asyncio
    async def test_accepts_float_limit(self, test_client):
        """Test that float values are accepted."""
        response = await test_client.put(
            "/api/telemetry/limit",
            json={"limit": 15.5}
        )

        assert response.status_code == 200
        assert response.json()["requested_limit"] == 15.5
