"""
Tests for the Gemini client.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import google.generativeai as genai

from app.core.gemini_client import GeminiClient
from app.config import Settings
from app.core.tools import ALL_TOOLS


class TestGeminiClientInit:
    """Tests for GeminiClient initialization."""

    def test_initializes_with_settings(self, test_settings):
        """Test that client initializes with provided settings."""
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model:
                client = GeminiClient(test_settings)

                mock_configure.assert_called_once_with(api_key=test_settings.gemini_api_key)
                mock_model.assert_not_called()
                assert client.settings == test_settings
                assert len(client.tools) == len(ALL_TOOLS)

    def test_converts_tools_to_gemini_format(self, test_settings):
        """Test that tools are converted to Gemini format."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                client = GeminiClient(test_settings)

                tool_names = [t.name for t in client.tools]
                expected_names = [tool["name"] for tool in ALL_TOOLS]
                assert tool_names == expected_names


class TestMapType:
    """Tests for the _map_type method."""

    @pytest.fixture
    def client(self, test_settings):
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                return GeminiClient(test_settings)

    def test_maps_string_type(self, client):
        """Test mapping string type."""
        result = client._map_type("string")
        assert result == genai.protos.Type.STRING

    def test_maps_number_type(self, client):
        """Test mapping number type."""
        result = client._map_type("number")
        assert result == genai.protos.Type.NUMBER

    def test_maps_integer_type(self, client):
        """Test mapping integer type."""
        result = client._map_type("integer")
        assert result == genai.protos.Type.INTEGER

    def test_maps_boolean_type(self, client):
        """Test mapping boolean type."""
        result = client._map_type("boolean")
        assert result == genai.protos.Type.BOOLEAN

    def test_maps_array_type(self, client):
        """Test mapping array type."""
        result = client._map_type("array")
        assert result == genai.protos.Type.ARRAY

    def test_maps_object_type(self, client):
        """Test mapping object type."""
        result = client._map_type("object")
        assert result == genai.protos.Type.OBJECT

    def test_defaults_to_string_for_unknown(self, client):
        """Test that unknown types default to string."""
        result = client._map_type("unknown_type")
        assert result == genai.protos.Type.STRING


class TestConvertTools:
    """Tests for tool conversion."""

    def test_converts_all_tools(self, test_settings):
        """Test that all tools are converted."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                client = GeminiClient(test_settings)

                assert len(client.tools) == len(ALL_TOOLS)

    def test_tool_names_preserved(self, test_settings):
        """Test that tool names are preserved during conversion."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                client = GeminiClient(test_settings)

                tool_names = [t.name for t in client.tools]
                assert "manage_student_facts" in tool_names
                assert "manage_grammar" in tool_names


class TestStreamChat:
    """Tests for stream_chat method."""

    @staticmethod
    def _mock_response(parts, usage_metadata=None):
        mock_candidate = MagicMock()
        mock_candidate.content.parts = parts

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = usage_metadata
        return mock_response

    @pytest.mark.asyncio
    async def test_yields_text_chunks(self, test_settings):
        """Test that text chunks are yielded."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                # Set up mock response
                mock_part = MagicMock()
                mock_part.text = "Hello"
                mock_part.function_call = None

                mock_response = self._mock_response([mock_part])

                mock_chat = MagicMock()
                mock_chat.send_message.return_value = mock_response

                mock_model = MagicMock()
                mock_model.start_chat.return_value = mock_chat
                mock_model_class.return_value = mock_model

                client = GeminiClient(test_settings)

                context = {"chat_history": [], "system_prompt": "You are a tutor"}
                parts = ["Hello"]

                chunks = []
                async for chunk in client.stream_chat(context, parts):
                    chunks.append(chunk)

                text_chunks = [c for c in chunks if c["type"] == "text"]
                assert len(text_chunks) > 0

    @pytest.mark.asyncio
    async def test_yields_function_calls(self, test_settings):
        """Test that function calls are yielded."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                # Set up mock function call
                mock_fc = MagicMock()
                mock_fc.name = "manage_student_facts"
                mock_fc.args = {"action": "add", "content": "test fact"}

                mock_part = MagicMock()
                mock_part.text = None
                mock_part.function_call = mock_fc

                mock_text_part = MagicMock()
                mock_text_part.text = "Saved"
                mock_text_part.function_call = None

                mock_function_response = self._mock_response([mock_part])
                mock_text_response = self._mock_response([mock_text_part])

                mock_chat = MagicMock()
                mock_chat.send_message.side_effect = [mock_function_response, mock_text_response]

                mock_model = MagicMock()
                mock_model.start_chat.return_value = mock_chat
                mock_model_class.return_value = mock_model

                client = GeminiClient(test_settings)

                context = {"chat_history": []}
                parts = ["Save this word"]
                tool_executor = AsyncMock(return_value="Added fact")

                chunks = []
                async for chunk in client.stream_chat(context, parts, tool_executor=tool_executor):
                    chunks.append(chunk)

                tool_calls = [c for c in chunks if c["type"] == "tool_call"]
                assert len(tool_calls) > 0
                assert tool_calls[0]["name"] == "manage_student_facts"
                tool_executor.assert_called_once_with(
                    "manage_student_facts",
                    {"action": "add", "content": "test fact"},
                )

    @pytest.mark.asyncio
    async def test_yields_error_on_exception(self, test_settings):
        """Test that errors are yielded as error chunks."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                mock_model.start_chat.side_effect = Exception("API Error")
                mock_model_class.return_value = mock_model

                client = GeminiClient(test_settings)

                context = {"chat_history": []}
                parts = ["Hello"]

                chunks = []
                async for chunk in client.stream_chat(context, parts):
                    chunks.append(chunk)

                error_chunks = [c for c in chunks if c["type"] == "error"]
                assert len(error_chunks) > 0
                assert "API Error" in error_chunks[0]["content"]

    @pytest.mark.asyncio
    async def test_includes_system_prompt_for_first_message(self, test_settings):
        """Test that system prompt is included when no history."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_part = MagicMock()
                mock_part.text = "Response"
                mock_part.function_call = None

                mock_response = self._mock_response([mock_part])

                mock_chat = MagicMock()
                mock_chat.send_message.return_value = mock_response

                mock_model = MagicMock()
                mock_model.start_chat.return_value = mock_chat
                mock_model_class.return_value = mock_model

                client = GeminiClient(test_settings)

                context = {
                    "chat_history": [],
                    "system_prompt": "You are a Japanese tutor"
                }
                parts = ["Hello"]

                async for _ in client.stream_chat(context, parts):
                    pass

                # The system prompt should be sent via Gemini's system_instruction,
                # not embedded in the user message parts.
                model_kwargs = mock_model_class.call_args.kwargs
                assert model_kwargs["system_instruction"] == "You are a Japanese tutor"
                call_args = mock_chat.send_message.call_args
                sent_parts = call_args[0][0]
                assert sent_parts == ["Hello"]

    @pytest.mark.asyncio
    async def test_extracts_usage_metadata(self, test_settings):
        """Test that usage metadata is extracted and yielded."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_part = MagicMock()
                mock_part.text = "Response"
                mock_part.function_call = None

                # Set up usage metadata
                mock_usage = MagicMock()
                mock_usage.prompt_token_count = 100
                mock_usage.candidates_token_count = 50

                mock_response = self._mock_response([mock_part], mock_usage)

                mock_chat = MagicMock()
                mock_chat.send_message.return_value = mock_response

                mock_model = MagicMock()
                mock_model.start_chat.return_value = mock_chat
                mock_model_class.return_value = mock_model

                client = GeminiClient(test_settings)

                context = {"chat_history": []}
                parts = ["Hello"]

                chunks = []
                async for chunk in client.stream_chat(context, parts):
                    chunks.append(chunk)

                usage_chunks = [c for c in chunks if c["type"] == "usage"]
                assert len(usage_chunks) == 1
                assert usage_chunks[0]["input_tokens"] == 100
                assert usage_chunks[0]["output_tokens"] == 50
