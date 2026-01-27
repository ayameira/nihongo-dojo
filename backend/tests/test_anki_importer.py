"""
Tests for the Anki importer module.
"""
import pytest
import os
import tempfile
import sqlite3
import json

from app.services.anki_importer import (
    strip_html,
    has_kanji,
    map_status,
    determine_status,
    extract_vocab_info,
    import_from_export_db,
)


class TestStripHtml:
    """Tests for strip_html function."""

    def test_strips_simple_tags(self):
        """Test stripping simple HTML tags."""
        result = strip_html("<b>bold</b>")
        assert result == "bold"

    def test_strips_nested_tags(self):
        """Test stripping nested HTML tags."""
        result = strip_html("<div><span>text</span></div>")
        assert result == "text"

    def test_handles_empty_string(self):
        """Test handling empty string."""
        result = strip_html("")
        assert result == ""

    def test_handles_none(self):
        """Test handling None input."""
        result = strip_html(None)
        assert result == ""

    def test_strips_whitespace(self):
        """Test that result is stripped."""
        result = strip_html("  <p>text</p>  ")
        assert result == "text"

    def test_preserves_japanese_text(self):
        """Test that Japanese text is preserved."""
        result = strip_html("<ruby>食<rt>た</rt></ruby>べる")
        assert "食" in result
        assert "た" in result
        assert "べる" in result


class TestHasKanji:
    """Tests for has_kanji function."""

    def test_detects_kanji(self):
        """Test detecting kanji characters."""
        assert has_kanji("食べる") is True
        assert has_kanji("日本語") is True
        assert has_kanji("漢字") is True

    def test_returns_false_for_hiragana_only(self):
        """Test hiragana-only strings."""
        assert has_kanji("たべる") is False
        assert has_kanji("これ") is False
        assert has_kanji("あいうえお") is False

    def test_returns_false_for_katakana_only(self):
        """Test katakana-only strings."""
        assert has_kanji("カタカナ") is False
        assert has_kanji("テスト") is False

    def test_returns_false_for_empty(self):
        """Test empty string."""
        assert has_kanji("") is False

    def test_mixed_text_with_kanji(self):
        """Test mixed text containing kanji."""
        assert has_kanji("食べます") is True
        assert has_kanji("日本語を勉強する") is True


class TestMapStatus:
    """Tests for map_status function."""

    def test_maps_mature(self):
        """Test mapping 'mature' status."""
        assert map_status("mature") == "Mature"
        assert map_status("Mature") == "Mature"
        assert map_status("MATURE") == "Mature"

    def test_maps_young_to_learning(self):
        """Test mapping 'young' status to Learning."""
        assert map_status("young") == "Learning"
        assert map_status("Young") == "Learning"

    def test_maps_learning(self):
        """Test mapping 'learning' status."""
        assert map_status("learning") == "Learning"
        assert map_status("Learning") == "Learning"

    def test_maps_new(self):
        """Test mapping 'new' status."""
        assert map_status("new") == "New"
        assert map_status("New") == "New"

    def test_maps_suspended(self):
        """Test mapping 'suspended' status."""
        assert map_status("suspended") == "Suspended"

    def test_defaults_to_new(self):
        """Test that unknown status defaults to New."""
        assert map_status("unknown") == "New"
        assert map_status("") == "New"
        assert map_status(None) == "New"


class TestDetermineStatus:
    """Tests for determine_status function."""

    def test_suspended_cards(self):
        """Test that negative queue means suspended."""
        assert determine_status(c_type=2, c_queue=-1, c_ivl=30) == "Suspended"
        assert determine_status(c_type=0, c_queue=-2, c_ivl=0) == "Suspended"

    def test_new_cards(self):
        """Test new card detection."""
        assert determine_status(c_type=0, c_queue=0, c_ivl=0) == "New"
        assert determine_status(c_type=0, c_queue=1, c_ivl=0) == "New"

    def test_learning_cards(self):
        """Test learning card detection."""
        assert determine_status(c_type=1, c_queue=1, c_ivl=1) == "Learning"
        assert determine_status(c_type=3, c_queue=1, c_ivl=5) == "Learning"

    def test_young_cards_are_learning(self):
        """Test that young cards (interval < 21) are Learning."""
        assert determine_status(c_type=2, c_queue=2, c_ivl=10) == "Learning"
        assert determine_status(c_type=2, c_queue=2, c_ivl=20) == "Learning"

    def test_mature_cards(self):
        """Test mature card detection (interval >= 21)."""
        assert determine_status(c_type=2, c_queue=2, c_ivl=21) == "Mature"
        assert determine_status(c_type=2, c_queue=2, c_ivl=100) == "Mature"


class TestExtractVocabInfo:
    """Tests for extract_vocab_info function."""

    def test_extracts_from_characters_field(self):
        """Test extraction from Characters field."""
        data = {
            "Characters": "食べる",
            "Reading": "たべる",
            "Meaning": "to eat",
        }
        result = extract_vocab_info(data, list(data.keys()))

        assert result["kanji"] == "食べる"
        assert result["kana"] == "たべる"
        assert result["meaning"] == "to eat"

    def test_extracts_from_alternative_field_names(self):
        """Test extraction from alternative field names."""
        data = {
            "Word": "飲む",
            "kana": "のむ",
            "English": "to drink",
        }
        result = extract_vocab_info(data, list(data.keys()))

        assert result["kanji"] == "飲む"
        assert result["kana"] == "のむ"
        assert result["meaning"] == "to drink"

    def test_handles_kana_only_words(self):
        """Test handling kana-only words."""
        data = {
            "Characters": "これ",
            "Meaning": "this",
        }
        result = extract_vocab_info(data, list(data.keys()))

        # Kana-only word should have kanji=None
        assert result["kanji"] is None
        assert result["kana"] == "これ"
        assert result["meaning"] == "this"

    def test_strips_html_from_fields(self):
        """Test that HTML is stripped from all fields."""
        data = {
            "Characters": "<b>食</b>べる",
            "Reading": "<span>たべる</span>",
            "Meaning": "<i>to eat</i>",
        }
        result = extract_vocab_info(data, list(data.keys()))

        assert "<" not in result["kanji"]
        assert "<" not in result["kana"]
        assert "<" not in result["meaning"]

    def test_fallback_to_first_field(self):
        """Test fallback to first field when no standard fields found."""
        data = {
            "CustomField": "テスト",
            "CustomMeaning": "test",
        }
        field_names = ["CustomField", "CustomMeaning"]
        result = extract_vocab_info(data, field_names)

        assert result["kana"] == "テスト"


class TestImportFromExportDb:
    """Tests for import_from_export_db function."""

    @pytest.fixture
    def export_db_path(self):
        """Create a temporary export database."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "anki_export.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the expected schema
        cursor.execute("""
            CREATE TABLE notes (
                anki_note_id INTEGER PRIMARY KEY,
                characters TEXT,
                fields TEXT,
                status TEXT,
                interval INTEGER
            )
        """)

        # Insert test data
        test_data = [
            (1, "食べる", json.dumps({"Object_Type": "Vocabulary", "Meaning": "to eat", "Reading": "たべる"}), "mature", 30),
            (2, "飲む", json.dumps({"Object_Type": "Vocabulary", "Meaning": "to drink", "Reading": "のむ"}), "learning", 5),
            (3, "これ", json.dumps({"Object_Type": "Vocabulary", "Meaning": "this"}), "new", 0),
            (4, "日", json.dumps({"Object_Type": "Kanji", "Meaning": "day, sun"}), "mature", 60),
        ]

        cursor.executemany(
            "INSERT INTO notes VALUES (?, ?, ?, ?, ?)",
            test_data
        )

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_imports_vocabulary(self, async_session, export_db_path):
        """Test importing vocabulary from export database."""
        result = await import_from_export_db(export_db_path, async_session)

        assert result["imported"] > 0
        assert result["total_processed"] == 4

    @pytest.mark.asyncio
    async def test_updates_existing_entries(self, async_session, export_db_path):
        """Test updating existing vocabulary entries."""
        from app.db.models import VocabEntry

        # Create existing entry with same anki_note_id
        existing = VocabEntry(
            kanji="食べる",
            kana="たべる",
            meaning="old meaning",
            status="New",
            anki_note_id=1,
        )
        async_session.add(existing)
        await async_session.commit()

        result = await import_from_export_db(export_db_path, async_session)

        assert result["updated"] >= 1

    @pytest.mark.asyncio
    async def test_skips_html_entries(self, async_session):
        """Test that entries with HTML are skipped."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE notes (
                anki_note_id INTEGER PRIMARY KEY,
                characters TEXT,
                fields TEXT,
                status TEXT,
                interval INTEGER
            )
        """)
        cursor.execute(
            "INSERT INTO notes VALUES (?, ?, ?, ?, ?)",
            (1, "<img src='test.png'>", json.dumps({"Object_Type": "Vocabulary"}), "new", 0)
        )
        conn.commit()
        conn.close()

        try:
            result = await import_from_export_db(db_path, async_session)
            assert result["skipped"] >= 1
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_raises_for_missing_file(self, async_session):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            await import_from_export_db("/nonexistent/path.db", async_session)

    @pytest.mark.asyncio
    async def test_maps_status_correctly(self, async_session, export_db_path):
        """Test that Anki status is mapped correctly."""
        from sqlalchemy import select
        from app.db.models import VocabEntry

        await import_from_export_db(export_db_path, async_session)

        stmt = select(VocabEntry)
        result = await async_session.execute(stmt)
        entries = list(result.scalars().all())

        statuses = {e.kana: e.status for e in entries}

        # Check status mapping
        assert statuses.get("たべる") == "Mature"  # mature -> Mature
