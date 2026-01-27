"""
Tests for the notes service.
"""
import os
import tempfile
import pytest
from app.services.notes_service import NotesService, SECTION_MAP, DEFAULT_NOTES_TEMPLATE


class TestNotesService:
    """Tests for NotesService class."""

    @pytest.fixture
    def notes_service(self):
        return NotesService()

    @pytest.fixture
    def temp_notes_path(self):
        """Create a temporary directory for notes files."""
        temp_dir = tempfile.mkdtemp()
        yield os.path.join(temp_dir, "test_notes.md")
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_read_notes_creates_default_if_not_exists(self, notes_service, temp_notes_path):
        """Test that reading non-existent notes creates default template."""
        content = await notes_service.read_notes(temp_notes_path)

        assert content == DEFAULT_NOTES_TEMPLATE
        assert os.path.exists(temp_notes_path)

    @pytest.mark.asyncio
    async def test_read_notes_returns_existing_content(self, notes_service, temp_notes_path):
        """Test that reading existing notes returns correct content."""
        test_content = "# My Custom Notes\n\nSome content here"

        # Create file first
        os.makedirs(os.path.dirname(temp_notes_path), exist_ok=True)
        with open(temp_notes_path, 'w', encoding='utf-8') as f:
            f.write(test_content)

        content = await notes_service.read_notes(temp_notes_path)
        assert content == test_content

    @pytest.mark.asyncio
    async def test_write_notes_creates_directories(self, notes_service):
        """Test that write_notes creates parent directories."""
        temp_dir = tempfile.mkdtemp()
        nested_path = os.path.join(temp_dir, "nested", "deep", "notes.md")

        try:
            await notes_service.write_notes(nested_path, "Test content")

            assert os.path.exists(nested_path)
            with open(nested_path, 'r') as f:
                assert f.read() == "Test content"
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_write_notes_with_utf8_content(self, notes_service, temp_notes_path):
        """Test writing Japanese content."""
        japanese_content = "# 日本語ノート\n\n食べる - to eat\n飲む - to drink"

        await notes_service.write_notes(temp_notes_path, japanese_content)

        with open(temp_notes_path, 'r', encoding='utf-8') as f:
            assert f.read() == japanese_content

    @pytest.mark.asyncio
    async def test_read_section_current_focus(self, notes_service, temp_notes_path):
        """Test reading the current_focus section."""
        content = """# Japanese Study Notes

## Current Focus
Learning verb conjugations and て-form

## Recent Corrections
Some corrections here
"""
        await notes_service.write_notes(temp_notes_path, content)

        section = await notes_service.read_section(temp_notes_path, "current_focus")
        assert "Learning verb conjugations" in section
        assert "て-form" in section

    @pytest.mark.asyncio
    async def test_read_section_recent_corrections(self, notes_service, temp_notes_path):
        """Test reading the recent_corrections section."""
        content = """# Notes

## Current Focus
Focus content

## Recent Corrections
- Use は instead of が
- Remember to use polite form

## Recent Vocab
Vocab here
"""
        await notes_service.write_notes(temp_notes_path, content)

        section = await notes_service.read_section(temp_notes_path, "recent_corrections")
        assert "Use は instead of が" in section
        assert "polite form" in section

    @pytest.mark.asyncio
    async def test_read_section_invalid_returns_empty(self, notes_service, temp_notes_path):
        """Test that reading invalid section returns empty string."""
        await notes_service.write_notes(temp_notes_path, DEFAULT_NOTES_TEMPLATE)

        section = await notes_service.read_section(temp_notes_path, "invalid_section")
        assert section == ""

    @pytest.mark.asyncio
    async def test_update_section_replace(self, notes_service, temp_notes_path):
        """Test replacing section content."""
        await notes_service.write_notes(temp_notes_path, DEFAULT_NOTES_TEMPLATE)

        new_content = "New focus: Keigo expressions"
        await notes_service.update_section(
            temp_notes_path,
            "current_focus",
            new_content,
            "replace"
        )

        result = await notes_service.read_section(temp_notes_path, "current_focus")
        assert "New focus: Keigo" in result

    @pytest.mark.asyncio
    async def test_update_section_append(self, notes_service, temp_notes_path):
        """Test appending to section content."""
        initial = """# Notes

## Current Focus
Focus on verbs

## Recent Corrections
First correction
"""
        await notes_service.write_notes(temp_notes_path, initial)

        await notes_service.update_section(
            temp_notes_path,
            "recent_corrections",
            "Second correction",
            "append"
        )

        result = await notes_service.read_section(temp_notes_path, "recent_corrections")
        assert "First correction" in result
        assert "Second correction" in result

    @pytest.mark.asyncio
    async def test_update_section_append_replaces_comment(self, notes_service, temp_notes_path):
        """Test that append replaces comment placeholder."""
        await notes_service.write_notes(temp_notes_path, DEFAULT_NOTES_TEMPLATE)

        await notes_service.update_section(
            temp_notes_path,
            "current_focus",
            "Real content here",
            "append"
        )

        result = await notes_service.read_section(temp_notes_path, "current_focus")
        # Comment should be replaced, not appended to
        assert "Real content here" in result

    @pytest.mark.asyncio
    async def test_update_section_invalid_raises_error(self, notes_service, temp_notes_path):
        """Test that updating invalid section raises ValueError."""
        await notes_service.write_notes(temp_notes_path, DEFAULT_NOTES_TEMPLATE)

        with pytest.raises(ValueError, match="Invalid section"):
            await notes_service.update_section(
                temp_notes_path,
                "nonexistent",
                "content",
                "replace"
            )

    @pytest.mark.asyncio
    async def test_get_token_count(self, notes_service, temp_notes_path):
        """Test token count estimation."""
        # ~100 characters = ~25 tokens
        content = "a" * 100
        await notes_service.write_notes(temp_notes_path, content)

        count = await notes_service.get_token_count(temp_notes_path)
        assert count == 25  # 100 // 4

    @pytest.mark.asyncio
    async def test_archive_old_notes_under_limit(self, notes_service, temp_notes_path):
        """Test that archiving doesn't happen when under limit."""
        short_content = "Short content"
        await notes_service.write_notes(temp_notes_path, short_content)

        archived = await notes_service.archive_old_notes(temp_notes_path, token_limit=1000)

        assert archived is False
        content = await notes_service.read_notes(temp_notes_path)
        assert content == short_content

    @pytest.mark.asyncio
    async def test_archive_old_notes_over_limit(self, notes_service, temp_notes_path):
        """Test that archiving happens when over limit."""
        # Create content that exceeds 10 tokens (40 characters)
        long_content = "x" * 100  # 25 tokens
        await notes_service.write_notes(temp_notes_path, long_content)

        archived = await notes_service.archive_old_notes(temp_notes_path, token_limit=10)

        assert archived is True

        # Check archive file was created
        archive_path = os.path.join(os.path.dirname(temp_notes_path), "ARCHIVE.md")
        assert os.path.exists(archive_path)

        # Check notes were reset
        content = await notes_service.read_notes(temp_notes_path)
        assert content == DEFAULT_NOTES_TEMPLATE

        # Cleanup archive
        if os.path.exists(archive_path):
            os.remove(archive_path)

    @pytest.mark.asyncio
    async def test_archive_appends_to_existing_archive(self, notes_service, temp_notes_path):
        """Test that archiving appends to existing archive file."""
        # Create initial archive
        archive_path = os.path.join(os.path.dirname(temp_notes_path), "ARCHIVE.md")
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with open(archive_path, 'w') as f:
            f.write("# Existing Archive\n\nOld content")

        # Create content to archive
        long_content = "x" * 100
        await notes_service.write_notes(temp_notes_path, long_content)

        await notes_service.archive_old_notes(temp_notes_path, token_limit=10)

        with open(archive_path, 'r') as f:
            archive_content = f.read()

        assert "Existing Archive" in archive_content
        assert "Old content" in archive_content
        assert "Archived:" in archive_content

        # Cleanup
        if os.path.exists(archive_path):
            os.remove(archive_path)


class TestSectionMap:
    """Tests for section mapping constants."""

    def test_section_map_has_all_sections(self):
        """Test that all expected sections are in the map."""
        expected = ["current_focus", "recent_corrections", "recent_vocab"]
        for section in expected:
            assert section in SECTION_MAP

    def test_section_map_values_are_headers(self):
        """Test that section map values are valid markdown headers."""
        for header in SECTION_MAP.values():
            assert header.startswith("## ")
