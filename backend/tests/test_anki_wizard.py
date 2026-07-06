"""Tests for the Anki setup wizard: collection introspection and config-driven import."""
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import select

from app.db.models import AnkiDeckConfig, VocabEntry
from app.services import anki_introspect
from app.services.anki_importer import import_deck_config, sync_all_decks


def _build_collection(decks):
    """Build a minimal Anki collection.anki2 file.

    `decks` maps deck name -> list of note dicts, each with keys:
      model, fields ({name: value}), and optionally type/queue/ivl.
    """
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, "collection.anki2")
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE decks (id INTEGER PRIMARY KEY, name TEXT)")
    cur.execute("CREATE TABLE notetypes (id INTEGER PRIMARY KEY, name TEXT)")
    cur.execute("CREATE TABLE fields (ntid INTEGER, ord INTEGER, name TEXT)")
    cur.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, mid INTEGER, flds TEXT)")
    cur.execute("CREATE TABLE cards (id INTEGER PRIMARY KEY, nid INTEGER, did INTEGER, type INTEGER, queue INTEGER, ivl INTEGER)")

    note_types = {}  # model name -> (mid, [field names])
    deck_id = 1
    note_id = 1
    card_id = 1
    for deck_name, notes in decks.items():
        cur.execute("INSERT INTO decks VALUES (?, ?)", (deck_id, deck_name))
        for note in notes:
            model = note["model"]
            field_names = list(note["fields"].keys())
            if model not in note_types:
                mid = len(note_types) + 100
                note_types[model] = (mid, field_names)
                cur.execute("INSERT INTO notetypes VALUES (?, ?)", (mid, model))
                for ord_, name in enumerate(field_names):
                    cur.execute("INSERT INTO fields VALUES (?, ?, ?)", (mid, ord_, name))
            mid, names = note_types[model]
            flds = "\x1f".join(note["fields"].get(n, "") for n in names)
            cur.execute("INSERT INTO notes VALUES (?, ?, ?)", (note_id, mid, flds))
            cur.execute(
                "INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?)",
                (card_id, note_id, deck_id, note.get("type", 0), note.get("queue", 0), note.get("ivl", 0)),
            )
            note_id += 1
            card_id += 1
        deck_id += 1
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def wanikani_collection():
    """A collection resembling a WaniKani deck with mixed Vocabulary/Kanji notes."""
    path = _build_collection({
        "Japanese::WaniKani": [
            {"model": "WK", "fields": {"Characters": "食べる", "Reading": "たべる", "Meaning": "to eat", "Object_Type": "Vocabulary"}, "type": 2, "queue": 2, "ivl": 40},
            {"model": "WK", "fields": {"Characters": "飲む", "Reading": "のむ", "Meaning": "to drink", "Object_Type": "Vocabulary"}, "type": 2, "queue": 2, "ivl": 10},
            {"model": "WK", "fields": {"Characters": "日", "Reading": "ひ", "Meaning": "sun", "Object_Type": "Kanji"}, "type": 0, "queue": 0, "ivl": 0},
        ],
        "Core 2k": [
            {"model": "Core", "fields": {"Expression": "これ", "Kana": "これ", "English": "this"}, "type": 1, "queue": 1, "ivl": 1},
        ],
    })
    yield path
    import shutil
    shutil.rmtree(os.path.dirname(path), ignore_errors=True)


class TestIntrospection:
    def test_list_decks(self, wanikani_collection):
        decks = {d["deck_name"]: d["note_count"] for d in anki_introspect.list_decks(wanikani_collection)}
        assert decks == {"Japanese::WaniKani": 3, "Core 2k": 1}

    def test_get_deck_fields_reports_note_types(self, wanikani_collection):
        info = anki_introspect.get_deck_fields(wanikani_collection, "Japanese::WaniKani")
        assert info["note_count"] == 3
        assert info["note_types"][0]["fields"] == ["Characters", "Reading", "Meaning", "Object_Type"]

    def test_suggested_mapping(self, wanikani_collection):
        info = anki_introspect.get_deck_fields(wanikani_collection, "Japanese::WaniKani")
        suggested = info["suggested"]
        assert suggested["kanji_field"] == "Characters"
        assert suggested["kana_field"] == "Reading"
        assert suggested["meaning_field"] == "Meaning"

    def test_missing_collection_raises(self):
        with pytest.raises(FileNotFoundError):
            anki_introspect.list_decks("/nonexistent/collection.anki2")


class TestImportDeckConfig:
    @pytest.mark.asyncio
    async def test_imports_with_field_mapping(self, async_session, wanikani_collection):
        config = AnkiDeckConfig(
            name="WaniKani", collection_path=wanikani_collection,
            deck_name="Japanese::WaniKani", enabled=True,
            kanji_field="Characters", kana_field="Reading", meaning_field="Meaning",
        )
        async_session.add(config)
        await async_session.commit()

        result = await import_deck_config(config, async_session)
        assert result["imported"] == 3

        entries = (await async_session.execute(select(VocabEntry))).scalars().all()
        taberu = next(e for e in entries if e.kana == "たべる")
        assert taberu.kanji == "食べる"
        assert taberu.meaning == "to eat"
        assert taberu.status == "Mature"
        assert taberu.deck_config_id == config.id

    @pytest.mark.asyncio
    async def test_filter_field_restricts_import(self, async_session, wanikani_collection):
        config = AnkiDeckConfig(
            name="WK Vocab only", collection_path=wanikani_collection,
            deck_name="Japanese::WaniKani", enabled=True,
            kanji_field="Characters", kana_field="Reading", meaning_field="Meaning",
            filter_field="Object_Type", filter_value="Vocabulary",
        )
        async_session.add(config)
        await async_session.commit()

        result = await import_deck_config(config, async_session)
        assert result["imported"] == 2  # the Kanji note is filtered out
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_resync_updates_instead_of_duplicating(self, async_session, wanikani_collection):
        config = AnkiDeckConfig(
            name="WaniKani", collection_path=wanikani_collection,
            deck_name="Japanese::WaniKani", enabled=True,
            kanji_field="Characters", kana_field="Reading", meaning_field="Meaning",
        )
        async_session.add(config)
        await async_session.commit()

        await import_deck_config(config, async_session)
        second = await import_deck_config(config, async_session)
        assert second["imported"] == 0
        assert second["updated"] == 3

        total = (await async_session.execute(select(VocabEntry))).scalars().all()
        assert len(total) == 3

    @pytest.mark.asyncio
    async def test_kana_only_word_has_no_kanji(self, async_session, wanikani_collection):
        config = AnkiDeckConfig(
            name="Core", collection_path=wanikani_collection, deck_name="Core 2k",
            enabled=True, kanji_field="Expression", kana_field="Kana", meaning_field="English",
        )
        async_session.add(config)
        await async_session.commit()

        await import_deck_config(config, async_session)
        entry = (await async_session.execute(select(VocabEntry))).scalar_one()
        assert entry.kana == "これ"
        assert entry.kanji is None

    @pytest.mark.asyncio
    async def test_sync_all_decks_reports_per_deck(self, async_session, wanikani_collection):
        for name, deck in [("WaniKani", "Japanese::WaniKani"), ("Core", "Core 2k")]:
            async_session.add(AnkiDeckConfig(
                name=name, collection_path=wanikani_collection, deck_name=deck,
                enabled=True,
                kanji_field="Characters" if deck.startswith("Japanese") else "Expression",
                kana_field="Reading" if deck.startswith("Japanese") else "Kana",
                meaning_field="Meaning" if deck.startswith("Japanese") else "English",
            ))
        await async_session.commit()

        results = await sync_all_decks(async_session)
        assert len(results) == 2
        assert all("error" not in r for r in results)


class TestAnkiAPI:
    @pytest.mark.asyncio
    async def test_upload_collection_lists_decks(
        self,
        test_client,
        wanikani_collection,
        tmp_path,
        monkeypatch,
    ):
        from app.api import anki as anki_api

        monkeypatch.setattr(anki_api, "UPLOADED_COLLECTIONS_DIR", tmp_path)

        with open(wanikani_collection, "rb") as collection:
            res = await test_client.post(
                "/api/anki/upload",
                files={"file": ("collection.anki2", collection, "application/octet-stream")},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "collection.anki2"
        saved_path = Path(data["path"])
        assert saved_path.parent == tmp_path
        assert saved_path.exists()
        assert {d["deck_name"] for d in data["decks"]} == {"Japanese::WaniKani", "Core 2k"}

        res = await test_client.post("/api/anki/configs", json={
            "name": "WaniKani", "collection_path": data["path"],
            "deck_name": "Japanese::WaniKani", "kana_field": "Reading",
            "meaning_field": "Meaning", "kanji_field": "Characters",
        })
        config_id = res.json()["id"]

        res = await test_client.delete(f"/api/anki/configs/{config_id}")
        assert res.status_code == 200
        assert not saved_path.exists()

    @pytest.mark.asyncio
    async def test_list_and_create_config(self, test_client, wanikani_collection):
        # Inspect decks
        res = await test_client.get(f"/api/anki/decks?path={wanikani_collection}")
        assert res.status_code == 200
        assert len(res.json()["decks"]) == 2

        # Create a deck source
        res = await test_client.post("/api/anki/configs", json={
            "name": "WaniKani", "collection_path": wanikani_collection,
            "deck_name": "Japanese::WaniKani", "kana_field": "Reading",
            "meaning_field": "Meaning", "kanji_field": "Characters",
        })
        assert res.status_code == 200
        config_id = res.json()["id"]

        # It shows up in the list
        res = await test_client.get("/api/anki/configs")
        assert len(res.json()) == 1

        # Sync it
        res = await test_client.post(f"/api/anki/configs/{config_id}/sync")
        assert res.status_code == 200
        assert res.json()["imported"] == 3

    @pytest.mark.asyncio
    async def test_delete_config_removes_vocab(self, test_client, wanikani_collection):
        res = await test_client.post("/api/anki/configs", json={
            "name": "WaniKani", "collection_path": wanikani_collection,
            "deck_name": "Japanese::WaniKani", "kana_field": "Reading",
            "meaning_field": "Meaning", "kanji_field": "Characters",
        })
        config_id = res.json()["id"]
        await test_client.post(f"/api/anki/configs/{config_id}/sync")

        res = await test_client.delete(f"/api/anki/configs/{config_id}")
        assert res.status_code == 200
        assert res.json()["vocab_removed"] == 3

        res = await test_client.get("/api/vocab/stats")
        assert res.json()["total"] == 0
