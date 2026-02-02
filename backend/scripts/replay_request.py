#!/usr/bin/env python
"""
Replay a logged LLM request.

Usage:
    cd backend
    ./venv/bin/python scripts/replay_request.py ../logs/ai_interactions/2025-01-31/session_id/12-30-45-123456_iter0_request.json

The script reads a logged payload and makes the exact same request to Gemini,
printing the response. This is useful for debugging and reproducing issues.
"""
import sys
import json
import base64
import google.generativeai as genai

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings


def convert_tools_to_sdk(tools_json):
    """Convert logged tools back to Gemini SDK format."""
    declarations = []
    for tool_group in tools_json:
        for func_decl in tool_group.get("function_declarations", []):
            params = func_decl.get("parameters", {})
            properties = {}
            for k, v in params.get("properties", {}).items():
                type_map = {
                    "string": genai.protos.Type.STRING,
                    "number": genai.protos.Type.NUMBER,
                    "integer": genai.protos.Type.INTEGER,
                    "boolean": genai.protos.Type.BOOLEAN,
                    "array": genai.protos.Type.ARRAY,
                    "object": genai.protos.Type.OBJECT,
                }
                properties[k] = genai.protos.Schema(
                    type=type_map.get(v.get("type", "string"), genai.protos.Type.STRING),
                    description=v.get("description", ""),
                    enum=v.get("enum"),
                )
            declarations.append(genai.protos.FunctionDeclaration(
                name=func_decl["name"],
                description=func_decl.get("description", ""),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties=properties,
                    required=params.get("required", []),
                )
            ))
    return declarations


def convert_parts_to_sdk(parts_json):
    """Convert logged parts back to SDK format."""
    parts = []
    for p in parts_json:
        if "text" in p:
            parts.append(p["text"])
        elif "inline_data" in p:
            # Image data
            parts.append({
                "mime_type": p["inline_data"]["mime_type"],
                "data": base64.b64decode(p["inline_data"]["data"]),
            })
        elif "function_response" in p:
            # Function response - convert to proto
            fr = p["function_response"]
            parts.append(genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=fr["name"],
                    response=fr["response"],
                )
            ))
    return parts


def convert_history_to_sdk(contents_json):
    """Convert logged contents to SDK history format (excluding last message)."""
    history = []
    for msg in contents_json[:-1]:  # Exclude the last message (current)
        role = msg["role"]
        parts = convert_parts_to_sdk(msg["parts"])
        history.append({"role": role, "parts": parts})
    return history


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_request.py <log_file_path>")
        print("\nExample:")
        print("  python scripts/replay_request.py ../logs/ai_interactions/2025-01-31/abc123/12-30-45-000000_iter0_request.json")
        sys.exit(1)

    log_path = sys.argv[1]

    # Load the logged payload
    with open(log_path) as f:
        payload = json.load(f)

    # Extract system instruction if present
    system_instruction = None
    if payload.get("system_instruction"):
        si_parts = payload["system_instruction"].get("parts", [])
        if si_parts and "text" in si_parts[0]:
            system_instruction = si_parts[0]["text"]

    print(f"Replaying request from: {log_path}")
    print(f"Model: {payload['model']}")
    print(f"Iteration: {payload.get('iteration', 0)}")
    print(f"Original timestamp: {payload.get('timestamp', 'unknown')}")
    print(f"Has system instruction: {bool(system_instruction)}")
    print(f"Contents count: {len(payload['contents'])}")
    print("-" * 50)

    # Configure Gemini
    settings = get_settings()
    if not settings.gemini_api_key:
        print("Error: GEMINI_API_KEY not configured")
        sys.exit(1)

    genai.configure(api_key=settings.gemini_api_key)

    # Convert tools
    tools = convert_tools_to_sdk(payload.get("tools", []))

    # Create model with system instruction
    model = genai.GenerativeModel(
        model_name=payload["model"],
        tools=tools if tools else None,
        system_instruction=system_instruction,
    )

    # Convert history and current message
    history = convert_history_to_sdk(payload["contents"])
    current_message_parts = convert_parts_to_sdk(payload["contents"][-1]["parts"])

    # Start chat with history
    chat = model.start_chat(history=history)

    # Send the message
    print("Sending request...")
    response = chat.send_message(current_message_parts)

    # Print response
    print("-" * 50)
    print("Response:")
    print("-" * 50)

    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                print(f"[Function Call] {fc.name}")
                print(f"  Args: {dict(fc.args)}")
            elif hasattr(part, 'text') and part.text:
                print(part.text)

    # Print usage if available
    if hasattr(response, 'usage_metadata'):
        um = response.usage_metadata
        print("-" * 50)
        print(f"Usage: {getattr(um, 'prompt_token_count', 0)} input, {getattr(um, 'candidates_token_count', 0)} output tokens")


if __name__ == "__main__":
    main()
