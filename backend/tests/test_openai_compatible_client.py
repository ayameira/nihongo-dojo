"""
Tests for OpenAI-compatible LLM providers such as Groq and OpenRouter.
"""
from unittest.mock import AsyncMock

import httpx
import pytest

from app.config import Settings
from app.core.openai_compatible_client import OpenAICompatibleClient


@pytest.fixture
def groq_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        llm_provider="groq",
        llm_api_key="test-groq-key",
    )


class TestOpenAICompatibleClient:
    def test_builds_openai_messages_from_gemini_history(self, groq_settings):
        client = OpenAICompatibleClient(groq_settings)
        context = {
            "system_prompt": "You are a tutor",
            "chat_history": [
                {"role": "user", "parts": ["こんにちは"]},
                {"role": "model", "parts": ["こんにちは！"]},
            ],
        }

        messages = client._build_messages(context, ["今日は"])

        assert messages == [
            {"role": "system", "content": "You are a tutor"},
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "こんにちは！"},
            {"role": "user", "content": "今日は"},
        ]

    @pytest.mark.asyncio
    async def test_generate_with_tools_executes_tool_calls(self, groq_settings):
        client = OpenAICompatibleClient(groq_settings)
        responses = [
            {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "manage_student_facts",
                                        "arguments": '{"action": "add", "content": "likes tea"}',
                                    },
                                }
                            ]
                        }
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 5},
            },
            {
                "choices": [{"message": {"content": "Saved."}}],
                "usage": {"prompt_tokens": 30, "completion_tokens": 10},
            },
        ]
        payloads = []

        async def fake_post_completion(payload):
            payloads.append(payload)
            return responses.pop(0)

        client._post_completion = fake_post_completion
        tool_executor = AsyncMock(return_value="Added fact")

        result = await client.generate_with_tools(
            {
                "system_prompt": "Track useful facts.",
                "user_message": "I like tea.",
            },
            tool_executor,
        )

        tool_executor.assert_awaited_once_with(
            "manage_student_facts",
            {"action": "add", "content": "likes tea"},
        )
        assert result["text_response"] == "Saved."
        assert result["tool_calls"][0]["result"] == "Added fact"
        assert result["usage"]["input_tokens"] == 50
        assert result["usage"]["output_tokens"] == 15
        assert payloads[1]["messages"][-2] == {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "manage_student_facts",
                        "arguments": '{"action": "add", "content": "likes tea"}',
                    },
                }
            ],
        }
        assert payloads[1]["messages"][-1] == {
            "role": "tool",
            "tool_call_id": "call_1",
            "name": "manage_student_facts",
            "content": "Added fact",
        }

    @pytest.mark.asyncio
    async def test_generate_json_parses_fenced_json(self, groq_settings):
        client = OpenAICompatibleClient(groq_settings)

        async def fake_post_completion(payload):
            return {
                "choices": [{"message": {"content": '```json\n{"title": "Tea Chat"}\n```'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            }

        client._post_completion = fake_post_completion

        result = await client.generate_json("Return a title")

        assert result["result"] == {"title": "Tea Chat"}
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 4

    @pytest.mark.asyncio
    async def test_post_completion_includes_error_response_body(self, groq_settings, monkeypatch):
        client = OpenAICompatibleClient(groq_settings)

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, *args, **kwargs):
                return httpx.Response(
                    400,
                    text='{"error":"content must be a string"}',
                    request=httpx.Request("POST", client._chat_completions_url()),
                )

        monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

        with pytest.raises(httpx.HTTPStatusError, match="content must be a string"):
            await client._post_completion({"model": "test", "messages": []})
