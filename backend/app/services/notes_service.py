import aiofiles
import os
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_NOTES_TEMPLATE = """# Japanese Study Notes

## Current Focus
<!-- What grammar points or vocabulary themes are we currently working on -->

## Recent Corrections
<!-- Patterns of mistakes the student makes -->

## Recent Vocab
<!-- Words recently taught in conversation -->
"""

DEFAULT_STUDENT_RECORD_TEMPLATE = """# Student Record

## Goals
<!-- The student's language learning goals and aspirations -->

## Background
<!-- Context about the student - why they're learning, their situation -->

## Interests
<!-- Hobbies, topics they enjoy discussing, favorite things -->

## Preferences
<!-- Learning style preferences, what works well for them -->

## Notes
<!-- Other important information about the student -->
"""

SECTION_MAP = {
    "current_focus": "## Current Focus",
    "recent_corrections": "## Recent Corrections",
    "recent_vocab": "## Recent Vocab",
}

STUDENT_RECORD_SECTION_MAP = {
    "goals": "## Goals",
    "background": "## Background",
    "interests": "## Interests",
    "preferences": "## Preferences",
    "notes": "## Notes",
}


class NotesService:
    async def read_notes(self, file_path: str, is_student_record: bool = False) -> str:
        """Read the entire notes file content."""
        default_template = DEFAULT_STUDENT_RECORD_TEMPLATE if is_student_record else DEFAULT_NOTES_TEMPLATE
        # Auto-detect student record by filename
        if "STUDENT_RECORD" in file_path.upper():
            default_template = DEFAULT_STUDENT_RECORD_TEMPLATE

        try:
            if not os.path.exists(file_path):
                await self.write_notes(file_path, default_template)
                return default_template

            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading notes: {e}")
            return default_template

    async def write_notes(self, file_path: str, content: str) -> None:
        """Write content to the notes file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Error writing notes: {e}")
            raise

    async def read_section(self, file_path: str, section: str) -> str:
        """Extract content from a specific section."""
        content = await self.read_notes(file_path)
        header = SECTION_MAP.get(section)

        if not header:
            return ""

        # Find the section
        pattern = rf"{re.escape(header)}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()
        return ""

    async def update_section(
        self,
        file_path: str,
        section: str,
        new_content: str,
        action: str = "replace"
    ) -> None:
        """Update a specific section of the notes."""
        content = await self.read_notes(file_path)
        header = SECTION_MAP.get(section)

        if not header:
            raise ValueError(f"Invalid section: {section}")

        # Find the section boundaries
        pattern = rf"({re.escape(header)}\n)(.*?)(\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            if action == "append":
                existing = match.group(2).strip()
                if existing and not existing.startswith("<!--"):
                    updated = f"{existing}\n{new_content}"
                else:
                    updated = new_content
            else:  # replace
                updated = new_content

            # Rebuild the content
            new_full = content[:match.start()] + match.group(1) + updated + "\n" + match.group(3)
            if match.group(3) == "\n## ":
                new_full = content[:match.start()] + match.group(1) + updated + match.group(3)

            await self.write_notes(file_path, new_full.rstrip() + "\n")
        else:
            # Section not found, append it
            content = content.rstrip() + f"\n\n{header}\n{new_content}\n"
            await self.write_notes(file_path, content)

    async def read_student_record_section(self, file_path: str, section: str) -> str:
        """Extract content from a specific section of the student record."""
        content = await self.read_notes(file_path, is_student_record=True)
        header = STUDENT_RECORD_SECTION_MAP.get(section)

        if not header:
            return ""

        # Find the section
        pattern = rf"{re.escape(header)}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()
        return ""

    async def update_student_record_section(
        self,
        file_path: str,
        section: str,
        new_content: str,
        action: str = "replace"
    ) -> None:
        """Update a specific section of the student record."""
        content = await self.read_notes(file_path, is_student_record=True)
        header = STUDENT_RECORD_SECTION_MAP.get(section)

        if not header:
            raise ValueError(f"Invalid student record section: {section}")

        # Find the section boundaries
        pattern = rf"({re.escape(header)}\n)(.*?)(\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            if action == "append":
                existing = match.group(2).strip()
                if existing and not existing.startswith("<!--"):
                    updated = f"{existing}\n{new_content}"
                else:
                    updated = new_content
            else:  # replace
                updated = new_content

            # Rebuild the content
            new_full = content[:match.start()] + match.group(1) + updated + "\n" + match.group(3)
            if match.group(3) == "\n## ":
                new_full = content[:match.start()] + match.group(1) + updated + match.group(3)

            await self.write_notes(file_path, new_full.rstrip() + "\n")
        else:
            # Section not found, append it
            content = content.rstrip() + f"\n\n{header}\n{new_content}\n"
            await self.write_notes(file_path, content)

    async def get_token_count(self, file_path: str) -> int:
        """Estimate token count in the notes file."""
        content = await self.read_notes(file_path)
        # Simple estimation: ~4 characters per token for mixed content
        # This is a rough approximation
        return len(content) // 4

    async def archive_old_notes(
        self,
        file_path: str,
        token_limit: int = 1000
    ) -> bool:
        """Archive old notes if content exceeds token limit."""
        current_tokens = await self.get_token_count(file_path)

        if current_tokens <= token_limit:
            return False

        content = await self.read_notes(file_path)

        # Determine archive path
        base_dir = os.path.dirname(file_path) or "."
        archive_path = os.path.join(base_dir, "ARCHIVE.md")

        # Read existing archive
        archive_content = ""
        if os.path.exists(archive_path):
            async with aiofiles.open(archive_path, "r", encoding="utf-8") as f:
                archive_content = await f.read()

        # Add timestamp header and current content to archive
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        archive_entry = f"\n\n---\n\n## Archived: {timestamp}\n\n{content}"

        async with aiofiles.open(archive_path, "w", encoding="utf-8") as f:
            if archive_content:
                await f.write(archive_content + archive_entry)
            else:
                await f.write(f"# Archived Study Notes\n{archive_entry}")

        # Reset notes to template
        await self.write_notes(file_path, DEFAULT_NOTES_TEMPLATE)

        logger.info(f"Archived notes to {archive_path}")
        return True
