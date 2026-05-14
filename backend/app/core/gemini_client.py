import google.generativeai as genai
from typing import AsyncGenerator, Callable, Dict, List, Any, Optional
import asyncio
import base64
import logging
from datetime import datetime

from app.config import Settings, get_model_pricing
from app.core.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        genai.configure(api_key=settings.gemini_api_key)

        # Convert tool definitions to Gemini format
        self.tools = self._convert_tools()

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

    def _serialize_parts_for_logging(self, parts: List[Any]) -> List[Dict]:
        """Convert parts to JSON-serializable format for logging.

        Handles:
        - Strings -> {"text": "..."}
        - Image dicts with bytes -> {"inline_data": {"mime_type": "...", "data": "base64..."}}
        - FunctionResponse protos -> {"function_response": {"name": "...", "response": {...}}}
        """
        serialized = []
        for part in parts:
            if isinstance(part, str):
                serialized.append({"text": part})
            elif isinstance(part, dict):
                if "data" in part:
                    # Image data - ensure it's base64 string
                    data = part["data"]
                    if isinstance(data, bytes):
                        data = base64.b64encode(data).decode("utf-8")
                    serialized.append({
                        "inline_data": {
                            "mime_type": part.get("mime_type", "image/jpeg"),
                            "data": data,
                        }
                    })
                else:
                    # Other dict, pass through
                    serialized.append(part)
            elif hasattr(part, "function_response"):
                # FunctionResponse proto
                fr = part.function_response
                serialized.append({
                    "function_response": {
                        "name": fr.name,
                        "response": dict(fr.response),
                    }
                })
            else:
                # Unknown type, try to convert
                serialized.append({"text": str(part)})
        return serialized

    def _build_payload_for_logging(
        self,
        system_prompt: str,
        chat_history: List[Dict],
        current_parts: List[Any],
        iteration: int,
        model_name: Optional[str] = None,
    ) -> Dict:
        """Build the complete payload for logging in Gemini REST API format."""
        # Build contents array: history + current message
        contents = []

        # Add history (already in correct format)
        for msg in chat_history:
            role = msg.get("role", "user")
            parts = msg.get("parts", [])
            # Convert parts to proper format
            formatted_parts = []
            for p in parts:
                if isinstance(p, str):
                    formatted_parts.append({"text": p})
                elif isinstance(p, dict):
                    formatted_parts.append(p)
                else:
                    formatted_parts.append({"text": str(p)})
            contents.append({"role": role, "parts": formatted_parts})

        # Add current message
        contents.append({
            "role": "user",
            "parts": self._serialize_parts_for_logging(current_parts),
        })

        # Build tools in REST API format
        tools = [{
            "function_declarations": ALL_TOOLS
        }]

        return {
            "model": model_name or self.settings.gemini_model,
            "system_instruction": {"parts": [{"text": system_prompt}]} if system_prompt else None,
            "contents": contents,
            "tools": tools,
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
        }

    async def stream_chat(
        self,
        context: Dict,
        message_parts: List[Any],
        tool_executor: Optional[Callable] = None,
        request_logger: Optional[Callable] = None,
        use_tools: bool = True,
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[Dict, None]:
        """Stream a chat response from Gemini with optional tool loop support.

        Args:
            context: Contains system_prompt and chat_history
            message_parts: User message parts (text, images)
            tool_executor: Async function to execute tools: async (name, args) -> result
            request_logger: Async function to log request payload: async (payload) -> None
            use_tools: Whether to enable tool usage (default True, set False for Tutor agent)
        """
        try:
            # Get system prompt and chat history from context
            system_prompt = context.get("system_prompt", "")
            chat_history = context.get("chat_history", [])
            active_model = model_name or self.settings.gemini_model

            # Create model with system instruction (per-request since system prompt varies)
            # Only include tools if use_tools is True
            model = genai.GenerativeModel(
                model_name=active_model,
                tools=self.tools if use_tools else None,
                system_instruction=system_prompt if system_prompt else None,
            )

            # Start chat with history
            chat = model.start_chat(history=chat_history)

            # Prepare user message parts (no longer embedding system prompt)
            parts = []
            for part in message_parts:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "data" in part:
                    # Image data
                    parts.append({
                        "mime_type": part.get("mime_type", "image/jpeg"),
                        "data": base64.b64decode(part["data"]) if isinstance(part["data"], str) else part["data"],
                    })

            total_input_tokens = 0
            total_output_tokens = 0
            max_tool_iterations = 10  # Safety limit
            iteration = 0

            while iteration < max_tool_iterations:
                # Log the exact payload before sending
                if request_logger:
                    # Use chat.history to get current state (grows during tool loop)
                    current_history = [
                        {"role": msg.role, "parts": [p.text if hasattr(p, 'text') else str(p) for p in msg.parts]}
                        for msg in chat.history
                    ] if chat.history else chat_history
                    payload = self._build_payload_for_logging(
                        system_prompt=system_prompt,
                        chat_history=current_history,
                        current_parts=parts,
                        iteration=iteration,
                        model_name=active_model,
                    )
                    try:
                        await request_logger(payload)
                    except Exception as e:
                        logger.warning(f"Failed to log request payload: {e}")

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
                input_cost, output_cost = get_model_pricing(active_model, self.settings)
                cost = (
                    (total_input_tokens * input_cost / 1_000_000) +
                    (total_output_tokens * output_cost / 1_000_000)
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

    async def generate_with_tools(
        self,
        context: Dict,
        tool_executor: Callable,
    ) -> Dict:
        """Non-streaming generation with tool loop support.

        Used by the Listener agent for background fact extraction.

        Args:
            context: Contains system_prompt and user_message
            tool_executor: Async function to execute tools: async (name, args) -> result

        Returns:
            Dict with 'text_response', 'tool_calls', and 'usage'
        """
        try:
            system_prompt = context.get("system_prompt", "")
            user_message = context.get("user_message", "")

            model = genai.GenerativeModel(
                model_name=self.settings.gemini_model,
                tools=self.tools,
                system_instruction=system_prompt if system_prompt else None,
            )

            chat = model.start_chat(history=[])

            total_input_tokens = 0
            total_output_tokens = 0
            tool_calls_made = []
            max_iterations = 10

            parts = [user_message]

            for iteration in range(max_iterations):
                response = await asyncio.to_thread(
                    lambda p=parts: chat.send_message(p)
                )

                # Track usage
                if hasattr(response, 'usage_metadata'):
                    um = response.usage_metadata
                    total_input_tokens += getattr(um, 'prompt_token_count', 0)
                    total_output_tokens += getattr(um, 'candidates_token_count', 0)

                # Check for function calls
                function_calls = []
                text_parts = []

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_calls.append(part.function_call)
                        elif hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)

                if function_calls:
                    function_responses = []
                    for fc in function_calls:
                        result = await tool_executor(fc.name, dict(fc.args))
                        tool_calls_made.append({
                            "name": fc.name,
                            "args": dict(fc.args),
                            "result": result,
                        })
                        function_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fc.name,
                                    response={"result": result}
                                )
                            )
                        )
                    parts = function_responses
                    continue

                # No more function calls, return result
                cost = (
                    (total_input_tokens * self.settings.gemini_input_cost_per_1m / 1_000_000) +
                    (total_output_tokens * self.settings.gemini_output_cost_per_1m / 1_000_000)
                )

                return {
                    "text_response": "".join(text_parts),
                    "tool_calls": tool_calls_made,
                    "usage": {
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "cost_usd": round(cost, 6),
                    },
                }

            # Max iterations reached
            cost = (
                (total_input_tokens * self.settings.gemini_input_cost_per_1m / 1_000_000) +
                (total_output_tokens * self.settings.gemini_output_cost_per_1m / 1_000_000)
            )
            return {
                "text_response": "",
                "tool_calls": tool_calls_made,
                "usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cost_usd": round(cost, 6),
                },
                "error": "max_tool_iterations_reached",
            }

        except Exception as e:
            logger.error(f"Listener generation error: {e}")
            raise

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
