import aiofiles
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RequestLogger:
    """Logs all AI requests and responses to disk for debugging and analysis."""

    def __init__(self, logs_dir: str = "./logs/ai_interactions"):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)

    def _get_log_path(self, session_id: str, timestamp: datetime) -> str:
        """Generate log file path: logs/ai_interactions/YYYY-MM-DD/session_id/timestamp.json"""
        date_dir = timestamp.strftime("%Y-%m-%d")
        full_dir = os.path.join(self.logs_dir, date_dir, session_id)
        os.makedirs(full_dir, exist_ok=True)
        filename = timestamp.strftime("%H-%M-%S-%f") + ".json"
        return os.path.join(full_dir, filename)

    async def log_interaction(
        self,
        session_id: str,
        # Request data
        user_message: str,
        image_data: Optional[str],
        difficulty_feedback: Optional[str],
        # Context data
        system_prompt: str,
        chat_history: List[Dict],
        student_record_content: str,
        vocab_list: List[Dict],
        # Response data
        full_response: str,
        tool_calls: List[Dict],
        usage_data: Optional[Dict],
        # Metadata
        model: str,
        error: Optional[str] = None,
    ) -> str:
        """Log a complete AI interaction to disk."""
        timestamp = datetime.now()
        log_path = self._get_log_path(session_id, timestamp)

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "session_id": session_id,
            "model": model,
            "request": {
                "user_message": user_message,
                "has_image": bool(image_data),
                "image_data": image_data,  # Full base64 included
                "difficulty_feedback": difficulty_feedback,
            },
            "context": {
                "system_prompt": system_prompt,
                "chat_history": chat_history,
                "chat_history_count": len(chat_history),
                "files": {
                    "student_record": student_record_content,
                },
                "vocabulary": {
                    "items": vocab_list,
                    "count": len(vocab_list),
                },
            },
            "response": {
                "content": full_response,
                "tool_calls": tool_calls,
                "tool_calls_count": len(tool_calls),
            },
            "usage": usage_data,
            "error": error,
        }

        try:
            async with aiofiles.open(log_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(log_entry, indent=2, ensure_ascii=False))
            logger.info(f"Logged interaction to {log_path}")
            return log_path
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return ""

    async def log_error(
        self,
        session_id: str,
        user_message: str,
        error: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Log an error that occurred during processing."""
        timestamp = datetime.now()
        log_path = self._get_log_path(session_id, timestamp)

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "session_id": session_id,
            "request": {
                "user_message": user_message,
            },
            "context": context,
            "error": error,
        }

        try:
            async with aiofiles.open(log_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(log_entry, indent=2, ensure_ascii=False))
            logger.info(f"Logged error to {log_path}")
            return log_path
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            return ""
