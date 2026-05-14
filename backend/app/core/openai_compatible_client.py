import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import httpx

from app.config import Settings, get_model_pricing
from app.core.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


class OpenAICompatibleClient:
    """Client for Groq/OpenRouter/Ollama-style chat completion APIs."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.default_model = settings.llm_model

    def _chat_completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.settings.llm_provider == "openrouter":
            headers["X-Title"] = "Nihongo Dojo"
        return headers

    def _tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": tool,
            }
            for tool in ALL_TOOLS
        ]

    def _parts_to_text(self, parts: List[Any]) -> str:
        text_parts = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(str(part["text"]))
            else:
                text_parts.append(str(part))
        return "\n".join(text_parts)

    def _message_parts_to_content(self, parts: List[Any]) -> str | List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []

        for part in parts:
            if isinstance(part, str):
                content.append({"type": "text", "text": part})
            elif isinstance(part, dict) and "data" in part:
                mime_type = part.get("mime_type", "image/jpeg")
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{part['data']}",
                    },
                })

        if len(content) == 1 and content[0]["type"] == "text":
            return content[0]["text"]

        return content

    def _build_messages(self, context: Dict, message_parts: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []

        system_prompt = context.get("system_prompt", "")
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for msg in context.get("chat_history", []):
            role = msg.get("role", "user")
            if role == "model":
                role = "assistant"
            if role not in {"system", "user", "assistant"}:
                role = "user"
            messages.append({
                "role": role,
                "content": self._parts_to_text(msg.get("parts", [])),
            })

        if message_parts is not None:
            messages.append({
                "role": "user",
                "content": self._message_parts_to_content(message_parts),
            })

        return messages

    def _build_payload_for_logging(self, payload: Dict[str, Any], iteration: int = 0) -> Dict[str, Any]:
        logged = dict(payload)
        logged["provider"] = self.settings.llm_provider
        logged["iteration"] = iteration
        logged["timestamp"] = datetime.now().isoformat()
        return logged

    def _usage_from_response(self, usage: Optional[Dict[str, Any]], model_name: str) -> Optional[Dict[str, Any]]:
        if not usage:
            return None

        input_tokens = usage.get("prompt_tokens", 0) or 0
        output_tokens = usage.get("completion_tokens", 0) or 0
        input_cost, output_cost = get_model_pricing(model_name, self.settings)
        cost = (
            (input_tokens * input_cost / 1_000_000) +
            (output_tokens * output_cost / 1_000_000)
        )

        return {
            "type": "usage",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
        }

    def _merge_usage(self, total: Dict[str, int], usage: Optional[Dict[str, Any]]) -> None:
        if not usage:
            return
        total["input_tokens"] += usage.get("prompt_tokens", 0) or 0
        total["output_tokens"] += usage.get("completion_tokens", 0) or 0

    def _usage_from_totals(self, total: Dict[str, int], model_name: str) -> Dict[str, Any]:
        input_cost, output_cost = get_model_pricing(model_name, self.settings)
        cost = (
            (total["input_tokens"] * input_cost / 1_000_000) +
            (total["output_tokens"] * output_cost / 1_000_000)
        )
        return {
            "input_tokens": total["input_tokens"],
            "output_tokens": total["output_tokens"],
            "cost_usd": round(cost, 6),
        }

    async def _post_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._chat_completions_url(),
                headers=self._headers(),
                json=payload,
            )
            if response.is_error:
                detail = response.text.strip()
                message = (
                    f"OpenAI-compatible API returned {response.status_code} "
                    f"{response.reason_phrase} for {response.request.url}"
                )
                if detail:
                    message = f"{message}: {detail[:2000]}"
                raise httpx.HTTPStatusError(
                    message,
                    request=response.request,
                    response=response,
                )
            return response.json()

    def _parse_tool_arguments(self, raw_args: str | Dict[str, Any] | None) -> Dict[str, Any]:
        if isinstance(raw_args, dict):
            return raw_args
        if not raw_args:
            return {}
        try:
            return json.loads(raw_args)
        except json.JSONDecodeError:
            logger.warning("Could not parse tool arguments as JSON: %s", raw_args)
            return {}

    def _tool_call_assistant_message(
        self,
        message: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        content = message.get("content")
        return {
            "role": "assistant",
            "content": "" if content is None else content,
            "tool_calls": tool_calls,
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
        """Stream a chat response from an OpenAI-compatible provider."""
        active_model = model_name or self.default_model
        messages = self._build_messages(context, message_parts)

        try:
            if use_tools and tool_executor:
                async for chunk in self._stream_tool_loop(
                    messages=messages,
                    tool_executor=tool_executor,
                    request_logger=request_logger,
                    model_name=active_model,
                ):
                    yield chunk
                return

            payload = {
                "model": active_model,
                "messages": messages,
                "stream": True,
                "stream_options": {"include_usage": True},
            }

            if request_logger:
                try:
                    await request_logger(self._build_payload_for_logging(payload))
                except Exception as e:
                    logger.warning("Failed to log request payload: %s", e)

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self._chat_completions_url(),
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue

                        data = line.removeprefix("data:").strip()
                        if not data or data == "[DONE]":
                            continue

                        event = json.loads(data)
                        usage_chunk = self._usage_from_response(event.get("usage"), active_model)
                        if usage_chunk:
                            yield usage_chunk
                            continue

                        choices = event.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield {"type": "text", "content": content}

        except Exception as e:
            logger.error("OpenAI-compatible API error: %s", e)
            yield {
                "type": "error",
                "content": str(e),
            }

    async def _stream_tool_loop(
        self,
        messages: List[Dict[str, Any]],
        tool_executor: Callable,
        request_logger: Optional[Callable],
        model_name: str,
    ) -> AsyncGenerator[Dict, None]:
        total_usage = {"input_tokens": 0, "output_tokens": 0}

        for iteration in range(10):
            payload = {
                "model": model_name,
                "messages": messages,
                "tools": self._tools(),
                "tool_choice": "auto",
            }

            if request_logger:
                try:
                    await request_logger(self._build_payload_for_logging(payload, iteration))
                except Exception as e:
                    logger.warning("Failed to log request payload: %s", e)

            response = await self._post_completion(payload)
            self._merge_usage(total_usage, response.get("usage"))

            choices = response.get("choices", [])
            if not choices:
                break

            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls") or []

            if tool_calls:
                messages.append(self._tool_call_assistant_message(message, tool_calls))

                for call in tool_calls:
                    function = call.get("function", {})
                    name = function.get("name", "")
                    args = self._parse_tool_arguments(function.get("arguments"))

                    yield {"type": "tool_call", "name": name, "args": args}
                    result = await tool_executor(name, args)
                    yield {"type": "tool_result", "name": name, "result": result}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "name": name,
                        "content": str(result),
                    })

                continue

            content = message.get("content") or ""
            if content:
                yield {"type": "text", "content": content}
            break

        if total_usage["input_tokens"] or total_usage["output_tokens"]:
            usage = self._usage_from_totals(total_usage, model_name)
            yield {"type": "usage", **usage}

    async def generate_with_tools(
        self,
        context: Dict,
        tool_executor: Callable,
    ) -> Dict:
        """Non-streaming generation with tool loop support."""
        model_name = self.default_model
        messages = self._build_messages(
            {"system_prompt": context.get("system_prompt", ""), "chat_history": []},
            [context.get("user_message", "")],
        )
        total_usage = {"input_tokens": 0, "output_tokens": 0}
        tool_calls_made = []

        for _ in range(10):
            payload = {
                "model": model_name,
                "messages": messages,
                "tools": self._tools(),
                "tool_choice": "auto",
            }

            response = await self._post_completion(payload)
            self._merge_usage(total_usage, response.get("usage"))

            choices = response.get("choices", [])
            if not choices:
                break

            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls") or []

            if tool_calls:
                messages.append(self._tool_call_assistant_message(message, tool_calls))

                for call in tool_calls:
                    function = call.get("function", {})
                    name = function.get("name", "")
                    args = self._parse_tool_arguments(function.get("arguments"))
                    result = await tool_executor(name, args)
                    tool_calls_made.append({
                        "name": name,
                        "args": args,
                        "result": result,
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "name": name,
                        "content": str(result),
                    })

                continue

            return {
                "text_response": message.get("content") or "",
                "tool_calls": tool_calls_made,
                "usage": self._usage_from_totals(total_usage, model_name),
            }

        return {
            "text_response": "",
            "tool_calls": tool_calls_made,
            "usage": self._usage_from_totals(total_usage, model_name),
            "error": "max_tool_iterations_reached",
        }

    def _parse_json_content(self, content: str) -> Dict[str, Any]:
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        return json.loads(stripped)

    async def generate_json(self, prompt: str) -> Dict:
        """Generate a JSON response with an OpenAI-compatible provider."""
        model_name = self.default_model
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": f"{prompt}\n\nReturn only valid JSON.",
                }
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            response = await self._post_completion(payload)
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in {400, 422}:
                raise
            payload.pop("response_format", None)
            response = await self._post_completion(payload)

        choices = response.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") or "{}"

        usage = self._usage_from_response(response.get("usage"), model_name)
        if usage:
            usage = {k: v for k, v in usage.items() if k != "type"}

        return {
            "result": self._parse_json_content(content),
            "usage": usage,
        }
