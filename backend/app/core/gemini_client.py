import google.generativeai as genai
from typing import AsyncGenerator, Dict, List, Any, Optional
import asyncio
import logging

from app.config import Settings
from app.core.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        genai.configure(api_key=settings.gemini_api_key)

        # Convert tool definitions to Gemini format
        self.tools = self._convert_tools()

        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools=self.tools,
        )

    def _convert_tools(self) -> List:
        """Convert our tool definitions to Gemini function declarations."""
        declarations = []
        for tool in ALL_TOOLS:
            declarations.append(genai.protos.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        k: genai.protos.Schema(
                            type=self._map_type(v.get("type", "string")),
                            description=v.get("description", ""),
                            enum=v.get("enum"),
                        )
                        for k, v in tool["parameters"]["properties"].items()
                    },
                    required=tool["parameters"].get("required", []),
                )
            ))
        return declarations

    def _map_type(self, type_str: str):
        """Map JSON schema types to Gemini types."""
        type_map = {
            "string": genai.protos.Type.STRING,
            "number": genai.protos.Type.NUMBER,
            "integer": genai.protos.Type.INTEGER,
            "boolean": genai.protos.Type.BOOLEAN,
            "array": genai.protos.Type.ARRAY,
            "object": genai.protos.Type.OBJECT,
        }
        return type_map.get(type_str, genai.protos.Type.STRING)

    async def stream_chat(
        self,
        context: Dict,
        message_parts: List[Any],
        tool_executor: Optional[callable] = None,
    ) -> AsyncGenerator[Dict, None]:
        """Stream a chat response from Gemini with tool loop support.

        Args:
            context: Contains system_prompt and chat_history
            message_parts: User message parts (text, images)
            tool_executor: Async function to execute tools: async (name, args) -> result
        """
        try:
            # Start chat with history
            chat = self.model.start_chat(
                history=context.get("chat_history", [])
            )

            # Build content with system instruction in first user message
            system_prompt = context.get("system_prompt", "")

            # Prepare parts - include system context
            parts = []
            if system_prompt and not context.get("chat_history"):
                # Include system prompt only if no history (first message)
                parts.append(f"[System Instructions]\n{system_prompt}\n[End System Instructions]\n\n")

            # Add user message parts
            for part in message_parts:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "data" in part:
                    # Image data
                    import base64
                    parts.append({
                        "mime_type": part.get("mime_type", "image/jpeg"),
                        "data": base64.b64decode(part["data"]) if isinstance(part["data"], str) else part["data"],
                    })

            total_input_tokens = 0
            total_output_tokens = 0
            max_tool_iterations = 10  # Safety limit
            iteration = 0

            while iteration < max_tool_iterations:
                iteration += 1

                # Generate response (non-streaming for tool loop, streaming for final)
                # We use non-streaming when we might need to handle tools
                response = await asyncio.to_thread(
                    lambda p=parts: chat.send_message(p)
                )

                # Track usage
                try:
                    if hasattr(response, 'usage_metadata'):
                        um = response.usage_metadata
                        total_input_tokens += getattr(um, 'prompt_token_count', 0)
                        total_output_tokens += getattr(um, 'candidates_token_count', 0)
                except Exception as e:
                    logger.warning(f"Could not get usage metadata: {e}")

                # Check if response has function calls
                function_calls = []
                text_parts = []

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_calls.append(part.function_call)
                        elif hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)

                # If there are function calls, execute them and continue the loop
                if function_calls and tool_executor:
                    function_responses = []

                    for fc in function_calls:
                        # Yield tool call event to frontend
                        yield {
                            "type": "tool_call",
                            "name": fc.name,
                            "args": dict(fc.args),
                        }

                        # Execute the tool
                        result = await tool_executor(fc.name, dict(fc.args))

                        # Yield tool result to frontend
                        yield {
                            "type": "tool_result",
                            "name": fc.name,
                            "result": result,
                        }

                        # Prepare function response for Gemini
                        function_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fc.name,
                                    response={"result": result}
                                )
                            )
                        )

                    # Send function responses back to continue the conversation
                    parts = function_responses
                    # Continue the loop to get the next response
                    continue

                # No function calls - yield the text response and exit loop
                for text in text_parts:
                    yield {
                        "type": "text",
                        "content": text,
                    }
                break

            # Calculate and yield usage
            if total_input_tokens > 0 or total_output_tokens > 0:
                cost = (
                    (total_input_tokens * self.settings.gemini_input_cost_per_1m / 1_000_000) +
                    (total_output_tokens * self.settings.gemini_output_cost_per_1m / 1_000_000)
                )
                yield {
                    "type": "usage",
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cost_usd": round(cost, 6),
                }

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            yield {
                "type": "error",
                "content": str(e),
            }

    async def generate_json(self, prompt: str) -> Dict:
        """Generate a JSON response from Gemini without streaming.

        Used for structured output tasks like memory compaction where
        streaming is not needed and JSON format is required.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Dict with 'result' (parsed JSON) and 'usage' (token/cost info)
        """
        import json as json_module

        try:
            # Create model without tools, with JSON response format
            json_model = genai.GenerativeModel(
                model_name=self.settings.gemini_model,
                generation_config={"response_mime_type": "application/json"},
            )

            response = await asyncio.to_thread(
                json_model.generate_content, prompt
            )

            result = json_module.loads(response.text)

            # Track usage for cost monitoring
            usage = None
            if hasattr(response, 'usage_metadata'):
                um = response.usage_metadata
                input_tokens = getattr(um, 'prompt_token_count', 0)
                output_tokens = getattr(um, 'candidates_token_count', 0)
                cost = (
                    (input_tokens * self.settings.gemini_input_cost_per_1m / 1_000_000) +
                    (output_tokens * self.settings.gemini_output_cost_per_1m / 1_000_000)
                )
                usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost, 6),
                }

            return {"result": result, "usage": usage}

        except Exception as e:
            logger.error(f"Gemini JSON generation error: {e}")
            raise
