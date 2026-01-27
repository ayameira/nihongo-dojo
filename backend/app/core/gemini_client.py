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
    ) -> AsyncGenerator[Dict, None]:
        """Stream a chat response from Gemini."""
        try:
            # Start chat with history
            chat = self.model.start_chat(
                history=context.get("chat_history", [])
            )

            # Build content with system instruction in first user message
            # Note: Gemini 1.5+ supports system_instruction parameter
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

            # Generate response with streaming
            response = await asyncio.to_thread(
                lambda: chat.send_message(
                    parts,
                    stream=True,
                )
            )

            full_text = ""
            for chunk in response:
                # Check for function calls
                if chunk.candidates and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            yield {
                                "type": "tool_call",
                                "name": fc.name,
                                "args": dict(fc.args),
                            }
                        elif hasattr(part, 'text') and part.text:
                            full_text += part.text
                            yield {
                                "type": "text",
                                "content": part.text,
                            }

            # Get usage metadata
            usage = None
            try:
                # Access the final response for usage metadata
                if hasattr(response, '_result') and response._result:
                    result = response._result
                    if hasattr(result, 'usage_metadata'):
                        um = result.usage_metadata
                        input_tokens = getattr(um, 'prompt_token_count', 0)
                        output_tokens = getattr(um, 'candidates_token_count', 0)

                        # Calculate cost
                        cost = (
                            (input_tokens * self.settings.gemini_input_cost_per_1m / 1_000_000) +
                            (output_tokens * self.settings.gemini_output_cost_per_1m / 1_000_000)
                        )

                        usage = {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cost_usd": round(cost, 6),
                        }
            except Exception as e:
                logger.warning(f"Could not get usage metadata: {e}")

            if usage:
                yield {
                    "type": "usage",
                    **usage,
                }

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            yield {
                "type": "error",
                "content": str(e),
            }
